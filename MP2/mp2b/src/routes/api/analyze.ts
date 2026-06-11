import { createFileRoute } from "@tanstack/react-router";

interface AnalyzeResponse {
  summary: string;
  frictionCount: number;
  transcript: { start: number; text: string; frictionFlag?: boolean; frictionType?: string }[];
  findings: {
    title: string;
    description: string;
    severity: "Critical" | "Major" | "Minor";
    heuristic: string;
    occurrenceCount?: number;
    hmw?: string;
    recommendation?: string;
    evidence?: { quote: string; timestamp?: number }[];
  }[];
}

const ANALYZE_SYSTEM = `You are LENS, a senior UX research analyst.
You analyze a moderated usability test recording (audio) and return STRICT JSON only.

Your job:
1. Transcribe the participant's think-aloud speech with approximate timestamps in seconds.
2. Flag friction moments (confusion, hesitation, struggle, frustration, expectation mismatches).
3. Synthesize findings, each mapped to a Nielsen heuristic and severity (Critical | Major | Minor).
4. For each finding: include a How-Might-We question, a concrete recommendation, and 1-3 evidence quotes (real verbatim from the transcript with timestamps).
5. Produce a short executive summary of this single session.

Severity: Critical = blocks task; Major = meaningful struggle; Minor = polish.

OUTPUT FORMAT — return ONLY valid JSON, no markdown fences:
{
  "summary": "2-3 sentence executive summary.",
  "frictionCount": <int>,
  "transcript": [{ "start": <sec>, "text": "...", "frictionFlag": <bool>, "frictionType": "..." }],
  "findings": [{
    "title": "Short title (≤8 words)",
    "description": "1-2 sentences.",
    "severity": "Critical" | "Major" | "Minor",
    "heuristic": "Nielsen heuristic",
    "occurrenceCount": <int>,
    "hmw": "How might we ...?",
    "recommendation": "Concrete recommendation.",
    "evidence": [{ "quote": "verbatim quote", "timestamp": <sec> }]
  }]
}

Be honest. Never invent quotes.`;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const MAX_AUDIO_BYTES = 9 * 1024 * 1024;

function arrayBufferToBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  // btoa exists in workers
  return btoa(binary);
}

function safeParseJson(raw: string): AnalyzeResponse {
  const cleaned = raw
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
  try {
    return JSON.parse(cleaned) as AnalyzeResponse;
  } catch {
    const m = cleaned.match(/\{[\s\S]*\}/);
    if (m) {
      try {
        return JSON.parse(m[0]) as AnalyzeResponse;
      } catch {
        /* noop */
      }
    }
  }

  return { summary: "", frictionCount: 0, transcript: [], findings: [] };
}

export const Route = createFileRoute("/api/analyze")({
  server: {
    handlers: {
      OPTIONS: async () => new Response(null, { status: 204, headers: CORS }),
      POST: async ({ request }) => {
        const key = process.env.LOVABLE_API_KEY;
        if (!key)
          return new Response(JSON.stringify({ error: "LOVABLE_API_KEY not configured" }), {
            status: 500,
            headers: { "Content-Type": "application/json", ...CORS },
          });

        let form: FormData;
        try {
          form = await request.formData();
        } catch (e) {
          return new Response(JSON.stringify({ error: `Bad form data: ${(e as Error).message}` }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        }

        const audio = form.get("audio");
        const studyContext = String(form.get("studyContext") ?? "");
        const participantId = String(form.get("participantId") ?? "");
        const participantNote = String(form.get("participantNote") ?? "");
        const audioFormat = String(form.get("audioFormat") ?? "wav");
        const chunkIndex = Number(form.get("chunkIndex") ?? 0);
        const chunkTotal = Number(form.get("chunkTotal") ?? 1);
        const chunkStartSec = Number(form.get("chunkStartSec") ?? 0);
        const chunkEndSec = Number(form.get("chunkEndSec") ?? 0);

        if (!(audio instanceof Blob)) {
          return new Response(JSON.stringify({ error: "Missing audio file" }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        }
        if (!studyContext || !participantId) {
          return new Response(JSON.stringify({ error: "Missing studyContext or participantId" }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        }

        const ab = await audio.arrayBuffer();
        if (ab.byteLength > MAX_AUDIO_BYTES) {
          return new Response(
            JSON.stringify({
              error:
                "Audio payload is too large for a single request. The app should retry automatically in smaller chunks; if this persists, try again.",
            }),
            { status: 413, headers: { "Content-Type": "application/json", ...CORS } },
          );
        }
        const audioBase64 = arrayBufferToBase64(ab);

        const userText = `STUDY CONTEXT:\n${studyContext}\n\nPARTICIPANT: ${participantId}${
          participantNote ? `\nNOTE: ${participantNote}` : ""
        }\n${
          chunkTotal > 1
            ? `\nCHUNK: ${chunkIndex + 1} of ${chunkTotal} covering ${Math.round(chunkStartSec)}s to ${Math.round(chunkEndSec)}s of the original session.`
            : ""
        }\n\nAnalyze the attached recording and return JSON as specified.`;

        try {
          const upstream = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
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
                      input_audio: { data: audioBase64, format: audioFormat },
                    },
                  ],
                },
              ],
            }),
          });

          if (!upstream.ok) {
            const body = await upstream.text();
            return new Response(
              JSON.stringify({
                error: `Gateway ${upstream.status}: ${body.slice(0, 800)}`,
              }),
              { status: 502, headers: { "Content-Type": "application/json", ...CORS } },
            );
          }

          const json = (await upstream.json()) as {
            choices?: { message?: { content?: string } }[];
          };
          const text = json.choices?.[0]?.message?.content ?? "";
          const parsed = safeParseJson(text);

          return new Response(JSON.stringify({ text, parsed }), {
            status: 200,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        } catch (e) {
          return new Response(
            JSON.stringify({ error: `Upstream fetch failed: ${(e as Error).message}` }),
            { status: 502, headers: { "Content-Type": "application/json", ...CORS } },
          );
        }
      },
    },
  },
});
