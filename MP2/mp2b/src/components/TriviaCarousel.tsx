import { useEffect, useMemo, useState } from "react";
import { Lightbulb, Quote, Sparkles, Brain, Eye, Hand, Clock, Zap, Target, Users } from "lucide-react";
import { cn } from "@/lib/utils";

type Card =
  | { kind: "trivia"; icon: "bulb" | "brain" | "eye" | "hand" | "zap" | "target" | "users" | "clock"; title: string; body: string }
  | { kind: "quote"; body: string; author: string }
  | { kind: "stat"; value: string; label: string; body: string };

const CARDS: Card[] = [
  { kind: "stat", value: "5", label: "users", body: "Nielsen found that testing with just 5 users uncovers about 85% of usability problems." },
  { kind: "quote", body: "If the user can't find it, the function isn't there.", author: "IBM, design principle" },
  { kind: "trivia", icon: "eye", title: "F-pattern reading", body: "Eye-tracking shows users scan pages in an F-shape — the first two lines and the left edge get the most attention." },
  { kind: "stat", value: "0.05s", label: "to judge", body: "Users form a visual first impression of an interface in roughly 50 milliseconds." },
  { kind: "quote", body: "Design is not just what it looks like and feels like. Design is how it works.", author: "Steve Jobs" },
  { kind: "trivia", icon: "brain", title: "Hick's Law", body: "Decision time grows logarithmically with the number of choices. Fewer options = faster action." },
  { kind: "trivia", icon: "hand", title: "Fitts's Law", body: "Time to hit a target depends on its size and distance. Bigger, closer buttons are faster to click." },
  { kind: "stat", value: "10", label: "heuristics", body: "Nielsen's 10 usability heuristics, published in 1994, are still the most cited UX framework in industry." },
  { kind: "quote", body: "The details are not the details. They make the design.", author: "Charles Eames" },
  { kind: "trivia", icon: "bulb", title: "Jakob's Law", body: "Users spend most of their time on other sites. They expect yours to work the same way." },
  { kind: "trivia", icon: "clock", title: "The Doherty Threshold", body: "Productivity soars when a system responds in under 400ms — anything slower breaks flow." },
  { kind: "stat", value: "7±2", label: "items", body: "Miller's Law: short-term memory holds roughly 7 chunks. Group related controls to reduce load." },
  { kind: "trivia", icon: "zap", title: "Peak-End Rule", body: "People judge an experience mostly by its most intense moment and its ending — not the average." },
  { kind: "stat", value: "88%", label: "won't return", body: "88% of users are less likely to return to a site after a single bad experience." },
  { kind: "quote", body: "You are not your user.", author: "Don Norman" },
  { kind: "trivia", icon: "target", title: "Goal-Gradient Effect", body: "People accelerate toward a goal as they get closer. Progress bars increase completion rates." },
  { kind: "stat", value: "3 clicks", label: "is a myth", body: "Research shows users don't quit after 3 clicks — they quit when they feel lost. Clarity beats brevity." },
  { kind: "trivia", icon: "brain", title: "Von Restorff Effect", body: "When multiple similar objects are present, the one that differs is the most likely to be remembered." },
  { kind: "quote", body: "Good design is invisible.", author: "Dieter Rams" },
  { kind: "trivia", icon: "users", title: "Social Proof", body: "Users follow the behavior of others. Reviews, ratings, and counts reduce decision anxiety." },
  { kind: "stat", value: "94%", label: "design first", body: "94% of first impressions of a website are design-related, not content-related (Stanford)." },
  { kind: "trivia", icon: "eye", title: "Serial Position", body: "Users remember the first and last items in a list best. Put critical items at the ends." },
  { kind: "quote", body: "Simplicity is the ultimate sophistication.", author: "Leonardo da Vinci" },
  { kind: "trivia", icon: "hand", title: "Thumb Zone", body: "On phones, the bottom-center of the screen is easiest to reach. Top-corner taps are the slowest." },
  { kind: "stat", value: "2.6s", label: "attention", body: "Users' eyes lock onto a key element within 2.6 seconds — it shapes whether they stay or bounce." },
];

const ICONS = {
  bulb: Lightbulb,
  brain: Brain,
  eye: Eye,
  hand: Hand,
  zap: Zap,
  target: Target,
  users: Users,
  clock: Clock,
};

function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function TriviaCarousel() {
  const cards = useMemo(() => shuffle(CARDS), []);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIndex((i) => (i + 1) % cards.length), 6500);
    return () => clearInterval(id);
  }, [cards.length]);

  const card = cards[index];

  return (
    <div className="relative overflow-hidden rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/5 via-background to-gold/5 p-6 md:p-8">
      <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full border border-primary/15 [animation:lens-pulse_4s_ease-in-out_infinite]" />
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full border border-primary/10 [animation:lens-pulse_4s_ease-in-out_infinite_0.6s]" />
      <div className="pointer-events-none absolute -left-20 -bottom-20 h-56 w-56 rounded-full border border-gold/20 [animation:lens-pulse_5s_ease-in-out_infinite_1.2s]" />

      <div className="pointer-events-none absolute inset-x-0 top-0 h-px overflow-hidden">
        <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-primary to-transparent [animation:lens-scan_3.5s_linear_infinite]" />
      </div>

      <div className="relative flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-primary">
        <Sparkles className="h-3.5 w-3.5" />
        While you wait — a UX moment
      </div>

      <div key={index} className="relative mt-5 min-h-[140px] animate-fade-in">
        {card.kind === "trivia" && <TriviaView card={card} />}
        {card.kind === "quote" && <QuoteView card={card} />}
        {card.kind === "stat" && <StatView card={card} />}
      </div>

      <div className="relative mt-6 flex items-center gap-1.5">
        {cards.map((_, i) => (
          <span
            key={i}
            className={cn(
              "h-1 rounded-full transition-all duration-500",
              i === index ? "w-6 bg-primary" : "w-1 bg-primary/20",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function TriviaView({ card }: { card: Extract<Card, { kind: "trivia" }> }) {
  const Icon = ICONS[card.icon];
  return (
    <div className="flex gap-4">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <p className="font-display text-lg font-semibold text-ink">{card.title}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{card.body}</p>
      </div>
    </div>
  );
}

function QuoteView({ card }: { card: Extract<Card, { kind: "quote" }> }) {
  return (
    <div className="flex gap-4">
      <Quote className="h-7 w-7 shrink-0 text-gold/80" />
      <div>
        <p className="font-display text-lg leading-snug text-ink">"{card.body}"</p>
        <p className="mt-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">
          — {card.author}
        </p>
      </div>
    </div>
  );
}

function StatView({ card }: { card: Extract<Card, { kind: "stat" }> }) {
  return (
    <div className="flex items-center gap-5">
      <div className="shrink-0 text-right">
        <div className="font-display text-5xl font-semibold leading-none text-primary">
          {card.value}
        </div>
        <div className="mt-1 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          {card.label}
        </div>
      </div>
      <div className="h-12 w-px bg-border" />
      <p className="text-sm leading-relaxed text-muted-foreground">{card.body}</p>
    </div>
  );
}
