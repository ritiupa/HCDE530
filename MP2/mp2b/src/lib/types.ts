export type Severity = "Critical" | "Major" | "Minor";

export type WhisperModel = "tiny" | "base" | "small";

export interface TranscriptSegment {
  start: number;
  end?: number;
  text: string;
  frictionFlag?: boolean;
  frictionType?: string;
}

export interface Evidence {
  quote: string;
  timestamp?: number;
}

export interface Finding {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  heuristic: string;
  occurrenceCount: number;
  hmw: string;
  recommendation: string;
  evidence: Evidence[];
}

export interface SessionReport {
  summary: string;
  generatedAt: string;
  frictionCount: number;
}

export type SessionSource = "upload" | "live";
export type SessionStatus = "pending" | "analyzing" | "ready" | "error";

export interface StudySession {
  id: string;
  participantId: string;
  note?: string;
  source: SessionSource;
  fileName: string;
  fileType: string;
  sizeBytes: number;
  durationSec?: number;
  blob?: Blob; // not persisted across reloads
  objectUrl?: string;
  status: SessionStatus;
  errorMessage?: string;
  transcript?: TranscriptSegment[];
  findings?: Finding[];
  report?: SessionReport;
}

export interface CrossSession {
  summary: string;
  recurringPatterns: { pattern: string; sessions: string[]; severity: Severity }[];
  highlights: string[];
}

export interface Study {
  id: string;
  context: string;
  whisperModel: WhisperModel;
  createdAt: string;
  sessions: StudySession[];
  crossSession?: CrossSession;
}

export const SEVERITY_ORDER: Record<Severity, number> = {
  Critical: 0,
  Major: 1,
  Minor: 2,
};
