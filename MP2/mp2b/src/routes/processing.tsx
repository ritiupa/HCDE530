import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Loader2, AlertCircle, Clock } from "lucide-react";

import { AppHeader } from "@/components/AppHeader";
import { TriviaCarousel } from "@/components/TriviaCarousel";
import { useStudy } from "@/lib/store";
import {
  chooseTargetSampleRate,
  estimateMonoWavBytes,
  extractAudioWavBlob,
  extractAudioWavChunks,
} from "@/lib/audio";
import { detectFriction } from "@/lib/friction";

import { synthesizeCrossSession } from "@/lib/analyze.functions";
import { useServerFn } from "@tanstack/react-start";
import type { Evidence, Finding, TranscriptSegment, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/processing")({
  head: () => ({
    meta: [
      { title: "Analyzing sessions — LENS" },
      {
        name: "description",
        content: "LENS is analyzing your usability sessions.",
      },
    ],
  }),
  component: ProcessingPage,
});

type StepState = "pending" | "active" | "done" | "error";

interface RowState {
  sessionId: string;
  participantId: string;
  step: string;
  state: StepState;
  message?: string;
}

const STEPS = [
  "Extract audio",
  "Transcribe with Whisper",
  "Detect friction",
  "Enrich findings",
  "Generate report",
] as const;

const MAX_ANALYSIS_AUDIO_BYTES = 9 * 1024 * 1024;

type AnalyzeHttpResponse = {
  text?: string;
  error?: string;
  parsed?: {
    summary?: string;
    frictionCount?: number;
    transcript?: TranscriptSegment[];
    findings?: Omit<Finding, "id">[];
  };
};

function ProcessingPage() {
  const navigate = useNavigate();
  const { study, updateSession, setCrossSession } = useStudy();
  const crossFn = useServerFn(synthesizeCrossSession);

  const [rows, setRows] = useState<RowState[]>(() =>
    study.sessions.map((s) => ({
      sessionId: s.id,
      participantId: s.participantId,
      step: "Queued",
      state: "pending",
    })),
  );
  const [crossStep, setCrossStep] = useState<StepState>(
    study.sessions.length >= 2 ? "pending" : "done",
  );
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const ranRef = useRef(false);

  const totalEtaSec = useMemo(() => {
    // ~40s per chunk + ~20s cross-session synthesis when applicable
    const SEC_PER_CHUNK = 40;
    let chunks = 0;
    for (const s of study.sessions) {
      if (!s.blob) {
        chunks += 1;
        continue;
      }
      const sr = chooseTargetSampleRate(s.blob);
      const wavBytes = s.durationSec ? estimateMonoWavBytes(s.durationSec, sr) : s.sizeBytes;
      chunks += Math.max(1, Math.ceil(wavBytes / (MAX_ANALYSIS_AUDIO_BYTES - 256 * 1024)));
    }
    const cross = study.sessions.length >= 2 ? 20 : 0;
    return chunks * SEC_PER_CHUNK + cross;
  }, [study.sessions]);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsedSec(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);


  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    if (study.sessions.length === 0) {
      navigate({ to: "/" });
      return;
    }

    (async () => {
      const summaryShapes: {
        participantId: string;
        summary: string;
        findings: { title: string; severity: string; heuristic: string; description: string }[];
      }[] = [];

      for (let i = 0; i < study.sessions.length; i++) {
        const s = study.sessions[i];
        const setRow = (patch: Partial<RowState>) =>
          setRows((r) =>
            r.map((x) =>
              x.sessionId === s.id ? { ...x, ...patch, state: patch.state ?? x.state } : x,
            ),
          );

        updateSession(s.id, { status: "analyzing" });

        try {
          setRow({ step: STEPS[0], state: "active" });
          if (!s.blob) throw new Error("Session file is no longer available. Please re-add it.");

          setRow({ step: STEPS[1], state: "active" });
          const targetSampleRate = chooseTargetSampleRate(s.blob);
          const estimatedWavBytes = s.durationSec
            ? estimateMonoWavBytes(s.durationSec, targetSampleRate)
            : Number.POSITIVE_INFINITY;
          console.log("[analysis] session-start", {
            participantId: s.participantId,
            sourceSizeBytes: s.sizeBytes,
            durationSec: s.durationSec,
            targetSampleRate,
            estimatedWavBytes,
          });

          setRow({ step: STEPS[3], state: "active" });

          const result =
            estimatedWavBytes <= MAX_ANALYSIS_AUDIO_BYTES
              ? await analyzeSingleChunk({
                  audioBlob: await extractAudioWavBlob(s.blob, targetSampleRate),
                  studyContext: study.context,
                  participantId: s.participantId,
                  participantNote: s.note ?? "",
                })
              : mergeChunkResults(
                  await analyzeInChunks({
                    sourceBlob: s.blob,
                    targetSampleRate,
                    studyContext: study.context,
                    participantId: s.participantId,
                    participantNote: s.note ?? "",
                    setRow,
                  }),
                );

          setRow({ step: STEPS[4], state: "active" });

          // augment transcript with local friction detection if missing
          const transcript: TranscriptSegment[] = (result.transcript ?? []).map((t) => {
            if (t.frictionFlag) return t;
            const m = detectFriction(t.text, t.start);
            return m ? { ...t, frictionFlag: true, frictionType: m.type } : t;
          });

          const findings: Finding[] = (result.findings ?? []).map((f) => ({
            ...f,
            id: crypto.randomUUID(),
            severity:
              f.severity === "Critical" || f.severity === "Major" || f.severity === "Minor"
                ? f.severity
                : "Minor",
            evidence: f.evidence ?? [],
            occurrenceCount: f.occurrenceCount ?? 1,
          }));

          updateSession(s.id, {
            status: "ready",
            transcript,
            findings,
            report: {
              summary: result.summary ?? "",
              generatedAt: new Date().toISOString(),
              frictionCount:
                typeof result.frictionCount === "number"
                  ? result.frictionCount
                  : transcript.filter((t) => t.frictionFlag).length,
            },
          });

          summaryShapes.push({
            participantId: s.participantId,
            summary: result.summary ?? "",
            findings: findings.map((f) => ({
              title: f.title,
              severity: f.severity,
              heuristic: f.heuristic,
              description: f.description,
            })),
          });

          setRow({ step: "Done", state: "done" });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : String(err);
          const normalizedMessage = normalizeAnalysisError(message);
          console.error("[analysis] session-failed", {
            participantId: s.participantId,
            message,
            normalizedMessage,
          });
          updateSession(s.id, { status: "error", errorMessage: normalizedMessage });
          setRow({ step: "Failed", state: "error", message: normalizedMessage });
        }
      }

      if (summaryShapes.length >= 2) {
        setCrossStep("active");
        try {
          const cross = await crossFn({
            data: { studyContext: study.context, sessions: summaryShapes },
          });
          if (cross.ok) {
            const r = cross.result as {
              summary?: string;
              recurringPatterns?: { pattern: string; sessions?: string[]; severity?: string }[];
              highlights?: string[];
            };
            setCrossSession({
              summary: r.summary ?? "",
              recurringPatterns: (r.recurringPatterns ?? []).map((p) => ({
                pattern: p.pattern,
                sessions: p.sessions ?? [],
                severity:
                  p.severity === "Critical" || p.severity === "Major" || p.severity === "Minor"
                    ? p.severity
                    : "Minor",
              })),
              highlights: r.highlights ?? [],
            });
            setCrossStep("done");
          } else {
            setCrossStep("error");
          }
        } catch {
          setCrossStep("error");
        }
      }

      // After everything, navigate to report
      setTimeout(() => navigate({ to: "/report" }), 600);
    })().catch((e) => {
      setGlobalError(e instanceof Error ? e.message : String(e));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-dvh bg-background">
      <AppHeader current={3} />

      <div className="container-page py-10 md:py-16 max-w-3xl">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">Analyzing</p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-ink">
          LENS is reviewing your sessions
        </h1>
        <p className="mt-2 text-muted-foreground">
          Large recordings are split into chunks and analyzed sequentially. You'll be taken to the
          report when it's ready.
        </p>

        {globalError && (
          <div className="mt-6 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            {globalError}
          </div>
        )}

        <div className="mt-8">
          <EtaBanner elapsedSec={elapsedSec} totalEtaSec={totalEtaSec} />
        </div>

        <div className="mt-4">
          <TriviaCarousel />
        </div>


        <ol className="mt-8 space-y-3">
          {rows.map((r) => (
            <li key={r.sessionId} className="surface-card flex items-center gap-4 p-4">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                {r.participantId.slice(0, 3)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-ink">{r.participantId}</p>
                <p
                  className={cn(
                    "text-xs",
                    r.state === "error" ? "text-destructive" : "text-muted-foreground",
                  )}
                >
                  {r.message || r.step}
                </p>
              </div>
              <StateIcon state={r.state} />
            </li>
          ))}

          {study.sessions.length >= 2 && (
            <li className="surface-card flex items-center gap-4 p-4 border-primary/20">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gold/20 text-gold font-display text-xs font-semibold">
                Σ
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-ink">Cross-session synthesis</p>
                <p className="text-xs text-muted-foreground">
                  {crossStep === "done"
                    ? "Done"
                    : crossStep === "active"
                      ? "Finding recurring patterns…"
                      : crossStep === "error"
                        ? "Could not synthesize — per-session findings still available."
                        : "Queued"}
                </p>
              </div>
              <StateIcon state={crossStep} />
            </li>
          )}
        </ol>
      </div>
    </div>
  );
}

async function analyzeSingleChunk({
  audioBlob,
  studyContext,
  participantId,
  participantNote,
  chunkIndex = 0,
  chunkTotal = 1,
  chunkStartSec = 0,
  chunkEndSec = 0,
}: {
  audioBlob: Blob;
  studyContext: string;
  participantId: string;
  participantNote: string;
  chunkIndex?: number;
  chunkTotal?: number;
  chunkStartSec?: number;
  chunkEndSec?: number;
}) {
  const form = new FormData();
  form.append("audio", audioBlob, `audio-${chunkIndex + 1}.wav`);
  form.append("studyContext", studyContext);
  form.append("participantId", participantId);
  form.append("participantNote", participantNote);
  form.append("audioFormat", "wav");
  form.append("chunkIndex", String(chunkIndex));
  form.append("chunkTotal", String(chunkTotal));
  form.append("chunkStartSec", String(chunkStartSec));
  form.append("chunkEndSec", String(chunkEndSec));

  const httpRes = await fetch("/api/analyze", { method: "POST", body: form });
  const res = (await httpRes.json()) as AnalyzeHttpResponse;
  if (!httpRes.ok || res.error) {
    throw new Error(res.error || `HTTP ${httpRes.status}`);
  }

  const parsed = res.parsed ?? (safeParseJson(res.text ?? "") as AnalyzeHttpResponse["parsed"]);
  return {
    summary: parsed?.summary ?? "",
    frictionCount: typeof parsed?.frictionCount === "number" ? parsed.frictionCount : 0,
    transcript: parsed?.transcript ?? [],
    findings: parsed?.findings ?? [],
  };
}

async function analyzeInChunks({
  sourceBlob,
  targetSampleRate,
  studyContext,
  participantId,
  participantNote,
  setRow,
}: {
  sourceBlob: Blob;
  targetSampleRate: number;
  studyContext: string;
  participantId: string;
  participantNote: string;
  setRow: (patch: Partial<RowState>) => void;
}) {
  const chunks = await extractAudioWavChunks(
    sourceBlob,
    targetSampleRate,
    MAX_ANALYSIS_AUDIO_BYTES - 256 * 1024,
  );
  console.log("[analysis] chunk-plan", {
    participantId,
    chunkCount: chunks.length,
    chunkSizes: chunks.map((chunk) => chunk.blob.size),
  });
  const results = [] as {
    summary: string;
    frictionCount: number;
    transcript: TranscriptSegment[];
    findings: Omit<Finding, "id">[];
    startSec: number;
  }[];

  for (const chunk of chunks) {
    setRow({
      step: `Analyzing chunk ${chunk.index + 1} of ${chunk.total}`,
      state: "active",
    });
    const result = await analyzeSingleChunk({
      audioBlob: chunk.blob,
      studyContext,
      participantId,
      participantNote,
      chunkIndex: chunk.index,
      chunkTotal: chunk.total,
      chunkStartSec: chunk.startSec,
      chunkEndSec: chunk.endSec,
    });
    results.push({ ...result, startSec: chunk.startSec });
  }

  return results;
}

function mergeChunkResults(
  results: {
    summary: string;
    frictionCount: number;
    transcript: TranscriptSegment[];
    findings: Omit<Finding, "id">[];
    startSec: number;
  }[],
) {
  const transcript = results.flatMap((chunk) =>
    (chunk.transcript ?? []).map((segment) => ({
      ...segment,
      start: segment.start + chunk.startSec,
      end: typeof segment.end === "number" ? segment.end + chunk.startSec : undefined,
    })),
  );

  const findings = mergeFindings(
    results.flatMap((chunk) =>
      (chunk.findings ?? []).map((finding) => ({
        ...finding,
        evidence: (finding.evidence ?? []).map((e) => ({
          ...e,
          timestamp: typeof e.timestamp === "number" ? e.timestamp + chunk.startSec : e.timestamp,
        })),
      })),
    ),
  );

  const summary = results
    .map((chunk) => chunk.summary.trim())
    .filter(Boolean)
    .join(" ")
    .trim();

  return {
    summary,
    frictionCount:
      results.reduce((sum, chunk) => sum + (chunk.frictionCount ?? 0), 0) ||
      transcript.filter((t) => t.frictionFlag).length,
    transcript,
    findings,
  };
}

function mergeFindings(findings: Omit<Finding, "id">[]) {
  const merged = new Map<string, Omit<Finding, "id">>();

  for (const finding of findings) {
    const key = `${finding.title.toLowerCase()}::${finding.heuristic.toLowerCase()}`;
    const existing = merged.get(key);
    if (!existing) {
      merged.set(key, {
        ...finding,
        occurrenceCount: finding.occurrenceCount ?? 1,
        evidence: dedupeEvidence(finding.evidence ?? []),
      });
      continue;
    }

    existing.description = longestText(existing.description, finding.description);
    existing.recommendation = longestText(existing.recommendation, finding.recommendation);
    existing.hmw = longestText(existing.hmw, finding.hmw);
    existing.occurrenceCount = (existing.occurrenceCount ?? 1) + (finding.occurrenceCount ?? 1);
    existing.severity = maxSeverity(existing.severity, finding.severity);
    existing.evidence = dedupeEvidence([
      ...(existing.evidence ?? []),
      ...(finding.evidence ?? []),
    ]).slice(0, 6);
  }

  return [...merged.values()];
}

function dedupeEvidence(evidence: Evidence[]) {
  const seen = new Set<string>();
  return evidence.filter((item) => {
    const key = `${item.quote}::${item.timestamp ?? "na"}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function longestText(a?: string, b?: string) {
  return (b && b.length > (a?.length ?? 0) ? b : a) ?? "";
}

function maxSeverity(a?: string, b?: string): Severity {
  const order: Record<Severity, number> = { Critical: 3, Major: 2, Minor: 1 };
  const aSeverity: Severity = a === "Critical" || a === "Major" || a === "Minor" ? a : "Minor";
  const bSeverity: Severity = b === "Critical" || b === "Major" || b === "Minor" ? b : "Minor";
  return order[aSeverity] >= order[bSeverity] ? aSeverity : bSeverity;
}

function normalizeAnalysisError(message: string) {
  if (/current analysis limit|split it into shorter sessions/i.test(message)) {
    return "Large recordings are now analyzed in chunks. Please retry once so the refreshed analyzer can process this session.";
  }
  return message;
}

function StateIcon({ state }: { state: StepState }) {
  if (state === "done")
    return (
      <span className="grid h-7 w-7 place-items-center rounded-full bg-primary/10 text-primary">
        <Check className="h-4 w-4" />
      </span>
    );
  if (state === "active")
    return (
      <span className="grid h-7 w-7 place-items-center rounded-full bg-primary/10 text-primary">
        <Loader2 className="h-4 w-4 animate-spin" />
      </span>
    );
  if (state === "error")
    return (
      <span className="grid h-7 w-7 place-items-center rounded-full bg-destructive/10 text-destructive">
        <AlertCircle className="h-4 w-4" />
      </span>
    );
  return (
    <span className="grid h-7 w-7 place-items-center rounded-full border border-border text-muted-foreground text-xs">
      •
    </span>
  );
}

function safeParseJson(raw: string): unknown {
  const cleaned = raw
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    const m = cleaned.match(/\{[\s\S]*\}/);
    if (m) {
      try {
        return JSON.parse(m[0]);
      } catch {
        /* noop */
      }
    }
    return {
      summary: "Could not parse model response.",
      findings: [],
      transcript: [],
      frictionCount: 0,
    };
  }
}

function formatDuration(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  if (m === 0) return `${r}s`;
  if (r === 0) return `${m}m`;
  return `${m}m ${r}s`;
}

function EtaBanner({ elapsedSec, totalEtaSec }: { elapsedSec: number; totalEtaSec: number }) {
  const remaining = Math.max(0, totalEtaSec - elapsedSec);
  const pct = totalEtaSec > 0 ? Math.min(99, Math.round((elapsedSec / totalEtaSec) * 100)) : 0;
  const isOverdue = elapsedSec > totalEtaSec && totalEtaSec > 0;

  return (
    <div className="relative overflow-hidden rounded-xl border border-primary/20 bg-card p-4 md:p-5">
      <div className="flex items-center gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
          <Clock className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Estimated wait time
          </p>
          <p className="mt-0.5 text-sm font-medium text-ink">
            {isOverdue ? (
              <>Wrapping up — almost there…</>
            ) : (
              <>
                ~{formatDuration(remaining)} remaining
                <span className="text-muted-foreground"> · {formatDuration(elapsedSec)} elapsed</span>
              </>
            )}
          </p>
        </div>
        <div className="hidden sm:block text-right">
          <p className="font-display text-xl font-semibold text-primary tabular-nums">
            ~{formatDuration(totalEtaSec)}
          </p>
          <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">total</p>
        </div>
      </div>
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-primary/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-gold transition-all duration-700"
          style={{ width: `${isOverdue ? 99 : pct}%` }}
        />
      </div>
    </div>
  );
}

