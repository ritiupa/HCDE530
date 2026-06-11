import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import {
  ArrowRight,
  Sparkles,
  Upload,
  Video,
  ChevronDown,
  ChevronUp,
  Trash2,
  Info,
} from "lucide-react";
import { toast } from "sonner";

import { AppHeader } from "@/components/AppHeader";
import { SessionUploader } from "@/components/SessionUploader";
import { SessionRecorder } from "@/components/SessionRecorder";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useStudy } from "@/lib/store";
import type { WhisperModel } from "@/lib/types";
import { formatBytes, formatDuration } from "@/lib/export";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LENS — Set up a usability study" },
      {
        name: "description",
        content:
          "Set up a usability study and add session recordings to generate structured findings reports.",
      },
    ],
  }),
  component: SetupPage,
});

function SetupPage() {
  const navigate = useNavigate();
  const { study, setContext, setWhisperModel, removeSession } = useStudy();
  const [mode, setMode] = useState<"upload" | "record">("upload");
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const canAnalyze = study.context.trim().length > 0 && study.sessions.length > 0;

  // duplicate participant id check
  const dupIds = (() => {
    const counts = new Map<string, number>();
    study.sessions.forEach((s) =>
      counts.set(s.participantId, (counts.get(s.participantId) ?? 0) + 1),
    );
    return [...counts.entries()].filter(([, n]) => n > 1).map(([id]) => id);
  })();

  const onAnalyze = () => {
    if (!canAnalyze) return;
    if (dupIds.length) {
      toast.error(`Duplicate Participant IDs: ${dupIds.join(", ")}`);
      return;
    }
    navigate({ to: "/processing" });
  };

  return (
    <div className="min-h-dvh bg-background">
      <AppHeader current={study.sessions.length ? 2 : 1} />

      {/* Hero */}
      <section className="border-b border-border bg-surface-subtle/50">
        <div className="container-page py-10 md:py-14">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
            Layered Evidence and Narrative Synthesizer
          </p>
          <h1 className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight text-ink md:text-4xl">
            Turn usability sessions into structured findings reports.
          </h1>
          <p className="mt-3 max-w-2xl text-base text-muted-foreground">
            Upload or record moderated think-aloud sessions. LENS transcribes the
            audio, flags friction moments, tags Nielsen heuristics, and produces a
            sortable report with evidence quotes — ready to share with your team.
          </p>
        </div>
      </section>

      <div className="container-page grid gap-8 py-8 md:py-12 lg:grid-cols-[1fr_360px]">
        {/* Main column */}
        <div className="space-y-8">
          {/* Step 1 — Study context */}
          <section className="surface-elevated p-6 md:p-8">
            <SectionTitle
              n={1}
              title="Study context"
              hint="What were participants asked to do? This guides the analysis."
            />
            <div className="mt-5 space-y-2">
              <Label htmlFor="ctx" className="text-sm">
                Describe what was tested
              </Label>
              <Textarea
                id="ctx"
                value={study.context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="e.g., Participants used the p5.js reference docs to locate the documentation for the ellipse() function and explain what its parameters do."
                className="min-h-[120px] resize-y"
              />
              <p className="text-xs text-muted-foreground">
                A short paragraph is enough. LENS uses this to interpret friction
                in context.
              </p>
            </div>

            {/* Advanced */}
            <div className="mt-5">
              <button
                type="button"
                onClick={() => setAdvancedOpen((o) => !o)}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-ink transition-colors"
              >
                {advancedOpen ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
                Advanced settings
              </button>
              {advancedOpen && (
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label className="text-sm">Transcription model</Label>
                    <Select
                      value={study.whisperModel}
                      onValueChange={(v) =>
                        setWhisperModel(v as WhisperModel)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tiny">tiny — fastest, lower accuracy</SelectItem>
                        <SelectItem value="base">base — balanced (default)</SelectItem>
                        <SelectItem value="small">small — slower, higher accuracy</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Hints sent to the analysis pipeline. Larger = slower but
                      more accurate.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Step 2 — Add sessions */}
          <section className="surface-elevated p-6 md:p-8">
            <SectionTitle
              n={2}
              title="Add sessions"
              hint="Upload existing recordings or record live in your browser."
            />

            {/* Segmented control */}
            <div
              role="tablist"
              aria-label="How to add sessions"
              className="mt-5 inline-flex rounded-lg border border-border bg-surface-subtle p-1"
            >
              <button
                role="tab"
                aria-selected={mode === "upload"}
                onClick={() => setMode("upload")}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-3.5 py-1.5 text-sm font-medium transition-all",
                  mode === "upload"
                    ? "bg-surface text-ink shadow-sm"
                    : "text-muted-foreground hover:text-ink",
                )}
              >
                <Upload className="h-3.5 w-3.5" />
                Upload files
              </button>
              <button
                role="tab"
                aria-selected={mode === "record"}
                onClick={() => setMode("record")}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-3.5 py-1.5 text-sm font-medium transition-all",
                  mode === "record"
                    ? "bg-surface text-ink shadow-sm"
                    : "text-muted-foreground hover:text-ink",
                )}
              >
                <Video className="h-3.5 w-3.5" />
                Record live
              </button>
            </div>

            <div className="mt-6">
              {mode === "upload" ? <SessionUploader /> : <SessionRecorder />}
            </div>
          </section>
        </div>

        {/* Sticky summary sidebar */}
        <aside className="lg:sticky lg:top-6 h-fit space-y-4">
          <div className="surface-elevated p-6">
            <h3 className="font-display text-base font-semibold text-ink">
              Ready to analyze
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              {study.sessions.length} session
              {study.sessions.length === 1 ? "" : "s"} queued
            </p>

            {study.sessions.length === 0 ? (
              <div className="mt-5 rounded-lg border border-dashed border-border bg-surface-subtle/40 p-4 text-center">
                <p className="text-xs text-muted-foreground">
                  Add at least one session to analyze.
                </p>
              </div>
            ) : (
              <ul className="mt-5 space-y-2">
                {study.sessions.map((s) => (
                  <li
                    key={s.id}
                    className="flex items-center gap-3 rounded-lg border border-border bg-surface p-2.5"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                      {s.participantId.slice(0, 3)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-ink">
                        {s.participantId}
                      </p>
                      <p className="truncate text-[11px] text-muted-foreground">
                        {s.source === "live" ? "Live · " : ""}
                        {formatDuration(s.durationSec) !== "—"
                          ? `${formatDuration(s.durationSec)} · `
                          : ""}
                        {formatBytes(s.sizeBytes)}
                      </p>
                    </div>
                    <button
                      onClick={() => removeSession(s.id)}
                      aria-label={`Remove ${s.participantId}`}
                      className="grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {dupIds.length > 0 && (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-2 text-xs text-destructive">
                <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                Duplicate IDs: {dupIds.join(", ")}
              </div>
            )}

            <Button
              onClick={onAnalyze}
              disabled={!canAnalyze}
              className="mt-5 w-full gap-2"
              size="lg"
            >
              <Sparkles className="h-4 w-4" />
              Analyze {study.sessions.length > 0 ? `${study.sessions.length} session${study.sessions.length === 1 ? "" : "s"}` : "sessions"}
              <ArrowRight className="h-4 w-4" />
            </Button>
            {!study.context.trim() && (
              <p className="mt-2 text-[11px] text-muted-foreground">
                Add study context to enable analysis.
              </p>
            )}
          </div>

          <div className="rounded-xl border border-border bg-surface-subtle/50 p-5 text-xs text-muted-foreground">
            <p className="font-medium text-ink mb-1">How LENS analyzes</p>
            <ol className="space-y-1.5 list-decimal pl-4">
              <li>Transcribes each recording.</li>
              <li>Detects friction (confusion, hesitation, frustration).</li>
              <li>Tags Nielsen heuristics and severity.</li>
              <li>Synthesizes findings with evidence quotes.</li>
              <li>Cross-session patterns for 2+ participants.</li>
            </ol>
          </div>
        </aside>
      </div>
    </div>
  );
}

function SectionTitle({
  n,
  title,
  hint,
}: {
  n: number;
  title: string;
  hint: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/10 font-display text-sm font-semibold text-primary">
        {n}
      </span>
      <div>
        <h2 className="font-display text-xl font-semibold text-ink">{title}</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">{hint}</p>
      </div>
    </div>
  );
}
