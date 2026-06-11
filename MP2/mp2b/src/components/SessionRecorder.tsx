import { useEffect, useRef, useState } from "react";
import {
  Camera,
  CircleDot,
  Pause,
  Play,
  Square,
  RotateCcw,
  Check,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useStudy } from "@/lib/store";
import type { StudySession } from "@/lib/types";
import { formatBytes, formatDuration } from "@/lib/export";
import { cn } from "@/lib/utils";

type Quality = "standard" | "balanced" | "extended";

const QUALITY: Record<
  Quality,
  { label: string; bitrate: number; hint: string }
> = {
  standard: {
    label: "Standard · 720p · best clarity",
    bitrate: 2_500_000,
    hint: "~10 min within 200 MB",
  },
  balanced: {
    label: "Balanced · 540p",
    bitrate: 1_200_000,
    hint: "~20 min within 200 MB",
  },
  extended: {
    label: "Extended · 360p · longest",
    bitrate: 600_000,
    hint: "~40 min within 200 MB",
  },
};

type Phase = "idle" | "recording" | "paused" | "review";

export function SessionRecorder() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const reviewRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef<number>(0);
  const elapsedBeforePauseRef = useRef<number>(0);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [quality, setQuality] = useState<Quality>("balanced");
  const [elapsed, setElapsed] = useState(0);
  const [bytes, setBytes] = useState(0);
  const [participantId, setParticipantId] = useState("");
  const [note, setNote] = useState("");
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);

  const addSession = useStudy((s) => s.addSession);
  const sessions = useStudy((s) => s.study.sessions);

  // Auto-assign participant ID
  useEffect(() => {
    if (!participantId) {
      const used = new Set(sessions.map((s) => s.participantId));
      let i = 1;
      while (used.has(`P${i}`)) i++;
      setParticipantId(`P${i}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Start camera preview on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
        setCameraReady(true);
      } catch (e) {
        setError(
          e instanceof Error
            ? e.message
            : "Could not access camera or microphone.",
        );
      }
    })();
    return () => {
      cancelled = true;
      if (tickRef.current) clearInterval(tickRef.current);
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        try {
          recorderRef.current.stop();
        } catch {
          /* noop */
        }
      }
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startTick = () => {
    if (tickRef.current) clearInterval(tickRef.current);
    tickRef.current = setInterval(() => {
      const now = Date.now();
      setElapsed(
        Math.floor((elapsedBeforePauseRef.current + (now - startedAtRef.current)) / 1000),
      );
      const total = chunksRef.current.reduce((a, b) => a + b.size, 0);
      setBytes(total);
      if (total > 200 * 1024 * 1024) {
        handleStop();
      }
    }, 250);
  };

  const handleStart = () => {
    if (!streamRef.current) return;
    setError(null);
    chunksRef.current = [];
    elapsedBeforePauseRef.current = 0;
    startedAtRef.current = Date.now();
    setElapsed(0);
    setBytes(0);

    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
      ? "video/webm;codecs=vp9,opus"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus")
        ? "video/webm;codecs=vp8,opus"
        : "video/webm";

    const rec = new MediaRecorder(streamRef.current, {
      mimeType: mime,
      videoBitsPerSecond: QUALITY[quality].bitrate,
    });
    recorderRef.current = rec;
    rec.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };
    rec.onstop = () => {
      if (tickRef.current) clearInterval(tickRef.current);
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      setRecordedBlob(blob);
      setRecordedUrl(url);
      setPhase("review");
    };
    rec.start(500);
    setPhase("recording");
    startTick();
  };

  const handlePause = () => {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.pause();
      elapsedBeforePauseRef.current += Date.now() - startedAtRef.current;
      if (tickRef.current) clearInterval(tickRef.current);
      setPhase("paused");
    }
  };
  const handleResume = () => {
    if (recorderRef.current?.state === "paused") {
      recorderRef.current.resume();
      startedAtRef.current = Date.now();
      startTick();
      setPhase("recording");
    }
  };
  const handleStop = () => {
    if (
      recorderRef.current &&
      recorderRef.current.state !== "inactive"
    ) {
      recorderRef.current.stop();
    }
  };
  const handleRedo = () => {
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedBlob(null);
    setRecordedUrl(null);
    setElapsed(0);
    setBytes(0);
    setPhase("idle");
  };
  const handleSave = () => {
    if (!recordedBlob) return;
    if (!participantId.trim()) {
      setError("Add a Participant ID before saving.");
      return;
    }
    const session: StudySession = {
      id: crypto.randomUUID(),
      participantId: participantId.trim(),
      note: note.trim() || undefined,
      source: "live",
      fileName: `${participantId.trim()}-${Date.now()}.webm`,
      fileType: "video/webm",
      sizeBytes: recordedBlob.size,
      durationSec: elapsed,
      blob: recordedBlob,
      objectUrl: recordedUrl ?? undefined,
      status: "pending",
    };
    addSession(session);
    // reset for next recording
    setRecordedBlob(null);
    setRecordedUrl(null);
    setElapsed(0);
    setBytes(0);
    setNote("");
    setPhase("idle");
    const used = new Set([...sessions.map((s) => s.participantId), session.participantId]);
    let i = 1;
    while (used.has(`P${i}`)) i++;
    setParticipantId(`P${i}`);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
      {/* Preview */}
      <div className="space-y-3">
        <div className="relative aspect-video w-full overflow-hidden rounded-2xl border border-border bg-ink">
          {phase === "review" ? (
            <video
              ref={reviewRef}
              src={recordedUrl ?? undefined}
              controls
              className="h-full w-full object-cover"
            />
          ) : (
            <video
              ref={videoRef}
              muted
              playsInline
              className="h-full w-full object-cover"
            />
          )}

          {!cameraReady && phase === "idle" && (
            <div className="absolute inset-0 grid place-items-center text-primary-foreground/80">
              <div className="text-center">
                <Camera className="mx-auto h-8 w-8 opacity-60" />
                <p className="mt-2 text-sm">Requesting camera & mic…</p>
              </div>
            </div>
          )}

          {(phase === "recording" || phase === "paused") && (
            <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-black/55 px-3 py-1.5 text-xs font-medium text-white backdrop-blur">
              <span
                className={cn(
                  "h-2 w-2 rounded-full bg-destructive",
                  phase === "recording" && "rec-dot",
                )}
              />
              <span className="tabular-nums">{formatDuration(elapsed)}</span>
              <span className="opacity-50">·</span>
              <span className="tabular-nums">{formatBytes(bytes)}</span>
              {phase === "paused" && (
                <span className="text-amber-300">Paused</span>
              )}
            </div>
          )}
        </div>

        {/* Control bar */}
        <div className="surface-card flex items-center justify-between gap-3 p-3">
          <div className="flex items-center gap-2">
            {phase === "idle" && (
              <Button
                onClick={handleStart}
                disabled={!cameraReady}
                className="gap-2"
              >
                <CircleDot className="h-4 w-4" /> Start recording
              </Button>
            )}
            {phase === "recording" && (
              <>
                <Button variant="secondary" onClick={handlePause} className="gap-2">
                  <Pause className="h-4 w-4" /> Pause
                </Button>
                <Button variant="destructive" onClick={handleStop} className="gap-2">
                  <Square className="h-4 w-4" /> Stop
                </Button>
              </>
            )}
            {phase === "paused" && (
              <>
                <Button onClick={handleResume} className="gap-2">
                  <Play className="h-4 w-4" /> Resume
                </Button>
                <Button variant="destructive" onClick={handleStop} className="gap-2">
                  <Square className="h-4 w-4" /> Stop
                </Button>
              </>
            )}
            {phase === "review" && (
              <>
                <Button onClick={handleSave} className="gap-2">
                  <Check className="h-4 w-4" /> Save session
                </Button>
                <Button variant="ghost" onClick={handleRedo} className="gap-2">
                  <RotateCcw className="h-4 w-4" /> Redo
                </Button>
              </>
            )}
          </div>
          <p className="text-xs text-muted-foreground hidden sm:block">
            {phase === "idle" &&
              "Camera ready — press Start when the participant begins."}
            {phase === "recording" && "Recording. Press Stop to review."}
            {phase === "paused" && "Paused. Resume or Stop to review."}
            {phase === "review" && "Review your recording, then save or redo."}
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" /> {error}
          </div>
        )}
      </div>

      {/* Side panel */}
      <aside className="space-y-4">
        <div className="surface-card p-4 space-y-3">
          <h3 className="text-sm font-semibold text-ink">Session details</h3>
          <div className="space-y-2">
            <Label htmlFor="pid" className="text-xs">
              Participant ID
            </Label>
            <Input
              id="pid"
              value={participantId}
              onChange={(e) => setParticipantId(e.target.value)}
              placeholder="P1"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="note" className="text-xs">
              Note <span className="text-muted-foreground">(optional)</span>
            </Label>
            <Input
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g., first-time user"
            />
          </div>
        </div>

        <div className="surface-card p-4 space-y-3">
          <h3 className="text-sm font-semibold text-ink">Recording quality</h3>
          <Select value={quality} onValueChange={(v) => setQuality(v as Quality)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(QUALITY) as Quality[]).map((k) => (
                <SelectItem key={k} value={k}>
                  {QUALITY[k].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {QUALITY[quality].hint}. Hard cap 200 MB — auto-stops at the limit.
          </p>
        </div>
      </aside>
    </div>
  );
}
