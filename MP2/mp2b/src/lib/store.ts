import { create } from "zustand";
import type { CrossSession, Study, StudySession, WhisperModel } from "./types";

interface StudyState {
  study: Study;
  setContext: (context: string) => void;
  setWhisperModel: (m: WhisperModel) => void;
  addSession: (s: StudySession) => void;
  updateSession: (id: string, patch: Partial<StudySession>) => void;
  removeSession: (id: string) => void;
  clearSessions: () => void;
  setCrossSession: (c: CrossSession) => void;
  reset: () => void;
}

function newStudy(): Study {
  return {
    id: crypto.randomUUID(),
    context: "",
    whisperModel: "base",
    createdAt: new Date().toISOString(),
    sessions: [],
  };
}

export const useStudy = create<StudyState>((set) => ({
  study: newStudy(),
  setContext: (context) =>
    set((s) => ({ study: { ...s.study, context } })),
  setWhisperModel: (whisperModel) =>
    set((s) => ({ study: { ...s.study, whisperModel } })),
  addSession: (session) =>
    set((s) => ({ study: { ...s.study, sessions: [...s.study.sessions, session] } })),
  updateSession: (id, patch) =>
    set((s) => ({
      study: {
        ...s.study,
        sessions: s.study.sessions.map((x) => (x.id === id ? { ...x, ...patch } : x)),
      },
    })),
  removeSession: (id) =>
    set((s) => ({
      study: { ...s.study, sessions: s.study.sessions.filter((x) => x.id !== id) },
    })),
  clearSessions: () =>
    set((s) => ({ study: { ...s.study, sessions: [], crossSession: undefined } })),
  setCrossSession: (crossSession) =>
    set((s) => ({ study: { ...s.study, crossSession } })),
  reset: () => set({ study: newStudy() }),
}));
