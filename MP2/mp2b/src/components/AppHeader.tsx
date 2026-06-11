import { Link } from "@tanstack/react-router";
import { Aperture } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepperProps {
  current: 1 | 2 | 3;
}

const STEPS = [
  { n: 1, label: "Set up study" },
  { n: 2, label: "Add sessions" },
  { n: 3, label: "Analyze & report" },
] as const;

export function AppHeader({ current }: StepperProps) {
  return (
    <header className="border-b border-border bg-surface/70 backdrop-blur supports-[backdrop-filter]:bg-surface/60">
      <div className="container-page flex h-16 items-center justify-between gap-6">
        <Link to="/" className="flex items-center gap-2.5 group">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm transition-transform group-hover:scale-105">
            <Aperture className="h-4.5 w-4.5" strokeWidth={2.25} />
          </span>
          <span className="flex flex-col leading-none">
            <span className="font-display text-base font-semibold tracking-tight text-ink">
              LENS
            </span>
            <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Evidence Synthesizer
            </span>
          </span>
        </Link>

        <ol className="hidden md:flex items-center gap-2 text-sm">
          {STEPS.map((s, i) => {
            const active = s.n === current;
            const done = s.n < current;
            return (
              <li key={s.n} className="flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex h-6 w-6 items-center justify-center rounded-full border text-[11px] font-semibold transition-colors",
                    active &&
                      "border-primary bg-primary text-primary-foreground",
                    done && "border-primary bg-primary/10 text-primary",
                    !active && !done && "border-border text-muted-foreground",
                  )}
                >
                  {done ? "✓" : s.n}
                </span>
                <span
                  className={cn(
                    "font-medium",
                    active ? "text-ink" : "text-muted-foreground",
                  )}
                >
                  {s.label}
                </span>
                {i < STEPS.length - 1 && (
                  <span className="mx-1 h-px w-8 bg-border" aria-hidden />
                )}
              </li>
            );
          })}
        </ol>

        <a
          href="https://github.com/ritiupa/HCDE530"
          target="_blank"
          rel="noreferrer"
          className="text-xs font-medium text-muted-foreground hover:text-ink transition-colors"
        >
          About
        </a>
      </div>
    </header>
  );
}
