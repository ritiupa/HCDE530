import { useState } from "react";
import { ChevronDown, ChevronUp, Sparkles, Lightbulb } from "lucide-react";
import type { Finding } from "@/lib/types";
import { cn } from "@/lib/utils";
import { formatTs } from "@/lib/export";

const severityClass: Record<Finding["severity"], string> = {
  Critical: "bg-critical-soft text-critical border-critical/30",
  Major: "bg-major-soft text-major-foreground border-major/40",
  Minor: "bg-minor-soft text-minor border-minor/30",
};

export function FindingCard({ finding }: { finding: Finding }) {
  const [open, setOpen] = useState(false);

  return (
    <article className="surface-card overflow-hidden transition-shadow hover:shadow-elevated">
      <header
        role="button"
        tabIndex={0}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((o) => !o);
          }
        }}
        className="flex cursor-pointer items-start gap-4 p-5"
      >
        <span
          className={cn(
            "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider shrink-0",
            severityClass[finding.severity],
          )}
        >
          {finding.severity}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-base font-semibold leading-snug text-ink">
            {finding.title}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {finding.description}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-secondary-foreground">
              {finding.heuristic}
            </span>
            {finding.occurrenceCount > 1 && (
              <span className="text-muted-foreground">
                {finding.occurrenceCount}× occurrences
              </span>
            )}
            <span className="text-muted-foreground">
              {finding.evidence.length} evidence
            </span>
          </div>
        </div>
        <button
          aria-label={open ? "Collapse" : "Expand"}
          className="grid h-8 w-8 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-secondary"
        >
          {open ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
      </header>

      {open && (
        <div className="border-t border-border bg-surface-subtle/40 px-5 py-5 space-y-4">
          <p className="text-sm text-ink leading-relaxed">{finding.description}</p>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-surface p-3">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-primary">
                <Sparkles className="h-3 w-3" /> How might we
              </p>
              <p className="mt-1 text-sm text-ink">{finding.hmw}</p>
            </div>
            <div className="rounded-lg border border-border bg-surface p-3">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-gold">
                <Lightbulb className="h-3 w-3" /> Recommendation
              </p>
              <p className="mt-1 text-sm text-ink">{finding.recommendation}</p>
            </div>
          </div>

          {finding.evidence.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Evidence from transcript
              </p>
              <ul className="space-y-2">
                {finding.evidence.map((e, i) => (
                  <li key={i} className="quote-block">
                    <span className="text-sm">"{e.quote}"</span>
                    {typeof e.timestamp === "number" && (
                      <span className="ml-2 font-mono text-[11px] text-muted-foreground not-italic">
                        @ {formatTs(e.timestamp)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
