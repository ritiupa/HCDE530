import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { generateText } from "ai";



const AnalyzeInput = z.object({
  studyContext: z.string().min(1),
  participantId: z.string().min(1),
  participantNote: z.string().optional(),
  audioBase64: z.string().min(1),
  audioFormat: z.enum(["wav", "mp3"]).default("wav"),
});

const CrossInput = z.object({
  studyContext: z.string(),
  sessions: z.array(
    z.object({
      participantId: z.string(),
      summary: z.string(),
      findings: z.array(
        z.object({
          title: z.string(),
          severity: z.string(),
          heuristic: z.string(),
          description: z.string(),
        }),
      ),
    }),
  ),
});

const ANALYZE_SYSTEM = `You are LENS, a senior UX research analyst.
You analyze a moderated usability test recording (audio or audio+video) and return STRICT JSON only.

Your job:
1. Transcribe the participant's think-aloud speech with approximate timestamps in seconds.
2. Flag friction moments (confusion, hesitation, struggle, frustration, expectation mismatches).
3. Synthesize findings, each mapped to a Nielsen heuristic and severity (Critical | Major | Minor).
4. For each finding: include a How-Might-We question, a concrete recommendation, and 1-3 evidence quotes (real verbatim from the transcript with timestamps).
5. Produce a short executive summary of this single session.

Severity guide:
- Critical: blocks task completion or causes major confusion.
- Major: meaningful struggle, slows the user, requires recovery.
- Minor: mild friction, polish-level.

Heuristics: use Nielsen's 10. Common ones:
"Visibility of system status", "Match between system and the real world",
"User control and freedom", "Consistency and standards",
"Error prevention", "Recognition rather than recall",
"Flexibility and efficiency of use", "Aesthetic and minimalist design",
"Help users recognize, diagnose, and recover from errors", "Help and documentation".

OUTPUT FORMAT — return ONLY valid JSON, no markdown fences:
{
  "summary": "2-3 sentence executive summary of this session.",
  "frictionCount": <int>,
  "transcript": [
    { "start": <seconds>, "text": "...", "frictionFlag": <bool>, "frictionType": "..." }
  ],
  "findings": [
    {
      "title": "Short finding title (max 8 words)",
      "description": "1-2 sentences describing what happened and why it matters.",
      "severity": "Critical" | "Major" | "Minor",
      "heuristic": "Nielsen heuristic name",
      "occurrenceCount": <int>,
      "hmw": "How might we ...?",
      "recommendation": "Concrete actionable recommendation.",
      "evidence": [
        { "quote": "verbatim participant quote", "timestamp": <seconds> }
      ]
    }
  ]
}

Be honest. If the recording is short or has no friction, return fewer findings (or an empty array) rather than fabricating issues. NEVER invent quotes that weren't said.`;

const CROSS_SYSTEM = `You are LENS performing cross-session synthesis across multiple usability sessions.
Identify recurring patterns (same friction type or heuristic appearing across 2+ participants), produce an executive summary, and surface highlights.

Return STRICT JSON ONLY:
{
  "summary": "3-4 sentence cross-session executive summary.",
  "recurringPatterns": [
    {
      "pattern": "Short pattern title.",
      "sessions": ["P1","P2",...],
      "severity": "Critical" | "Major" | "Minor"
    }
  ],
  "highlights": ["Bullet-style insight", "..."]
}`;

function stripFences(s: string): string {
  return s
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

function safeJson<T>(raw: string, fallback: T): T {
  try {
    return JSON.parse(stripFences(raw)) as T;
  } catch {
    const m = raw.match(/\{[\s\S]*\}$/);
    if (m) {
      try {
        return JSON.parse(m[0]) as T;
      } catch {
        /* noop */
      }
    }
    return fallback;
  }
}

export const analyzeSession = createServerFn({ method: "POST" })
  .inputValidator((d: unknown) => AnalyzeInput.parse(d))
  .handler(async ({ data }) => {
    const key = process.env.LOVABLE_API_KEY;
    if (!key) throw new Error("LOVABLE_API_KEY is not configured.");




    const userText = `STUDY CONTEXT:\n${data.studyContext}\n\nPARTICIPANT: ${data.participantId}${
      data.participantNote ? `\nNOTE: ${data.participantNote}` : ""
    }\n\nAnalyze the attached recording and return the JSON described.`;

    try {
      // Direct OpenAI-compatible call to Lovable AI Gateway with input_audio.
      const res = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Lovable-API-Key": key,
          "X-Lovable-AIG-SDK": "vercel-ai-sdk",
        },
        body: JSON.stringify({
          model: "google/gemini-2.5-flash",
          messages: [
            { role: "system", content: ANALYZE_SYSTEM },
            {
              role: "user",
              content: [
                { type: "text", text: userText },
                {
                  type: "input_audio",
                  input_audio: { data: data.audioBase64, format: data.audioFormat },
                },
              ],
            },
          ],
        }),
      });

      if (!res.ok) {
        const body = await res.text();
        return {
          ok: false as const,
          error: `Gateway ${res.status}: ${body.slice(0, 500)}`,
        };
      }

      const json = (await res.json()) as {
        choices?: { message?: { content?: string } }[];
      };
      const text = json.choices?.[0]?.message?.content ?? "";

      const parsed = safeJson(text, {
        summary: "Analysis returned an unparseable response.",
        frictionCount: 0,
        transcript: [],
        findings: [],
      });

      return { ok: true as const, result: parsed };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false as const, error: message };

    }
  });

export const synthesizeCrossSession = createServerFn({ method: "POST" })
  .inputValidator((d: unknown) => CrossInput.parse(d))
  .handler(async ({ data }) => {
    const key = process.env.LOVABLE_API_KEY;
    if (!key) throw new Error("LOVABLE_API_KEY is not configured.");
    if (data.sessions.length < 2) {
      return {
        ok: true as const,
        result: { summary: "", recurringPatterns: [], highlights: [] },
      };
    }

    const { createLovableAiGatewayProvider } = await import("./ai-gateway.server");
    const gateway = createLovableAiGatewayProvider(key);
    const model = gateway("google/gemini-2.5-flash");

    const userText = `STUDY CONTEXT:\n${data.studyContext}\n\nSESSIONS:\n${JSON.stringify(
      data.sessions,
      null,
      2,
    )}`;

    try {
      const { text } = await generateText({
        model,
        system: CROSS_SYSTEM,
        prompt: userText,
      });
      const parsed = safeJson(text, {
        summary: "",
        recurringPatterns: [],
        highlights: [],
      });
      return { ok: true as const, result: parsed };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      return { ok: false as const, error: message };
    }
  });
