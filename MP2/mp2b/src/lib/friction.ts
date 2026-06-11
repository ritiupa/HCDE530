/**
 * Local friction pattern detection — fallback / pre-analysis pass.
 * Detects think-aloud phrases that indicate confusion or struggle.
 */

export interface FrictionPattern {
  type: string;
  regex: RegExp;
  heuristic: string;
}

export const FRICTION_PATTERNS: FrictionPattern[] = [
  {
    type: "uncertainty",
    regex: /\b(i'?m not sure|i don'?t know|not certain|i guess|maybe|i think it'?s)\b/i,
    heuristic: "Visibility of system status",
  },
  {
    type: "search-confusion",
    regex: /\b(where is|where'?s|can'?t find|where do i|how do i find)\b/i,
    heuristic: "Recognition rather than recall",
  },
  {
    type: "expression-of-confusion",
    regex: /\b(that'?s confusing|confused|don'?t understand|doesn'?t make sense|unclear)\b/i,
    heuristic: "Match between system and the real world",
  },
  {
    type: "frustration",
    regex: /\b(ugh|argh|frustrating|annoying|why doesn'?t|this is hard)\b/i,
    heuristic: "User control and freedom",
  },
  {
    type: "expectation-mismatch",
    regex: /\b(i expected|i thought|supposed to|should be|why is)\b/i,
    heuristic: "Consistency and standards",
  },
  {
    type: "navigation-loss",
    regex: /\b(go back|how did i|lost|wait what|hmm)\b/i,
    heuristic: "Help users recognize, diagnose, and recover",
  },
];

export interface FrictionMatch {
  text: string;
  type: string;
  heuristic: string;
  timestamp?: number;
}

export function detectFriction(text: string, timestamp?: number): FrictionMatch | null {
  for (const p of FRICTION_PATTERNS) {
    if (p.regex.test(text)) {
      return { text, type: p.type, heuristic: p.heuristic, timestamp };
    }
  }
  return null;
}
