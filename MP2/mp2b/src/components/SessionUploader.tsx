import { useRef, useState } from "react";
import { Upload, X, FileVideo, FileAudio } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStudy } from "@/lib/store";
import { formatBytes } from "@/lib/export";
import type { StudySession } from "@/lib/types";
import { Input } from "@/components/ui/input";

const ACCEPTED = ".mp4,.mov,.webm,.wav,.mp3,.m4a,video/*,audio/*";

export function SessionUploader() {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessions = useStudy((s) => s.study.sessions);
  const addSession = useStudy((s) => s.addSession);
  const updateSession = useStudy((s) => s.updateSession);
  const removeSession = useStudy((s) => s.removeSession);

  const uploadSessions = sessions.filter((s) => s.source === "upload");

  const nextParticipantId = (): string => {
    const used = new Set(sessions.map((s) => s.participantId));
    let i = 1;
    while (used.has(`P${i}`)) i++;
    return `P${i}`;
  };

  const handleFiles = (files: FileList | File[]) => {
    Array.from(files).forEach((file) => {
      if (file.size > 200 * 1024 * 1024) {
        // 200 MB cap
        return;
      }
      const url = URL.createObjectURL(file);
      const session: StudySession = {
        id: crypto.randomUUID(),
        participantId: nextParticipantId(),
        source: "upload",
        fileName: file.name,
        fileType: file.type || "video/mp4",
        sizeBytes: file.size,
        blob: file,
        objectUrl: url,
        status: "pending",
      };
      addSession(session);
    });
  };

  return (
    <div className="space-y-5">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={cn(
          "group cursor-pointer rounded-2xl border-2 border-dashed bg-surface-subtle/40 px-6 py-12 text-center transition-all",
          dragOver
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/40 hover:bg-surface-subtle",
        )}
      >
        <span className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">
          <Upload className="h-5 w-5" />
        </span>
        <p className="font-display text-base font-medium text-ink">
          Drag and drop session recordings
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          or <span className="text-primary font-medium">browse files</span> —
          MP4, MOV, WEBM, WAV, MP3, M4A · up to 200 MB each
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) handleFiles(e.target.files);
            e.currentTarget.value = "";
          }}
        />
      </div>

      {uploadSessions.length > 0 && (
        <ul className="space-y-2">
          {uploadSessions.map((s) => {
            const isVideo = s.fileType.startsWith("video");
            return (
              <li
                key={s.id}
                className="surface-card flex items-center gap-3 p-3"
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-secondary text-primary">
                  {isVideo ? (
                    <FileVideo className="h-5 w-5" />
                  ) : (
                    <FileAudio className="h-5 w-5" />
                  )}
                </span>
                <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">
                      {s.fileName}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(s.sizeBytes)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      ID
                    </label>
                    <Input
                      value={s.participantId}
                      onChange={(e) =>
                        updateSession(s.id, { participantId: e.target.value })
                      }
                      className="h-8 w-20"
                    />
                    <Input
                      placeholder="Note (optional)"
                      value={s.note ?? ""}
                      onChange={(e) =>
                        updateSession(s.id, { note: e.target.value })
                      }
                      className="h-8 w-44"
                    />
                  </div>
                </div>
                <button
                  onClick={() => removeSession(s.id)}
                  aria-label={`Remove ${s.fileName}`}
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
