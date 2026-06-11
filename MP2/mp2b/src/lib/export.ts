import type { Study } from "./types";
import { SEVERITY_ORDER } from "./types";

export function studyToMarkdown(study: Study): string {
  const lines: string[] = [];
  lines.push(`# LENS Study Report`);
  lines.push("");
  lines.push(`**Generated:** ${new Date().toLocaleString()}`);
  lines.push(`**Sessions:** ${study.sessions.length}`);
  lines.push("");
  lines.push(`## Study Context`);
  lines.push(study.context || "_No context provided._");
  lines.push("");

  if (study.crossSession?.summary) {
    lines.push(`## Cross-Session Synthesis`);
    lines.push(study.crossSession.summary);
    if (study.crossSession.recurringPatterns.length) {
      lines.push("");
      lines.push(`### Recurring Patterns`);
      for (const p of study.crossSession.recurringPatterns) {
        lines.push(`- **${p.severity}** — ${p.pattern} _(in ${p.sessions.join(", ")})_`);
      }
    }
    if (study.crossSession.highlights.length) {
      lines.push("");
      lines.push(`### Highlights`);
      for (const h of study.crossSession.highlights) lines.push(`- ${h}`);
    }
    lines.push("");
  }

  for (const s of study.sessions) {
    lines.push(`## ${s.participantId}`);
    if (s.note) lines.push(`_${s.note}_`);
    lines.push("");
    if (s.report?.summary) {
      lines.push(`**Summary:** ${s.report.summary}`);
      lines.push("");
    }
    const findings = [...(s.findings ?? [])].sort(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    );
    if (!findings.length) {
      lines.push(`_No findings._`);
      lines.push("");
      continue;
    }
    lines.push(`### Findings (${findings.length})`);
    for (const f of findings) {
      lines.push("");
      lines.push(`#### [${f.severity}] ${f.title}`);
      lines.push(`*Heuristic:* ${f.heuristic}`);
      lines.push("");
      lines.push(f.description);
      lines.push("");
      lines.push(`**How might we:** ${f.hmw}`);
      lines.push("");
      lines.push(`**Recommendation:** ${f.recommendation}`);
      if (f.evidence.length) {
        lines.push("");
        lines.push(`**Evidence:**`);
        for (const e of f.evidence) {
          const t =
            typeof e.timestamp === "number" ? ` _(${formatTs(e.timestamp)})_` : "";
          lines.push(`> "${e.quote}"${t}`);
        }
      }
    }
    lines.push("");
  }

  lines.push("---");
  lines.push(
    "_LENS MVP — transcript-first analysis. Vocal stress and facial-expression layers are on the roadmap._",
  );
  return lines.join("\n");
}

export function formatTs(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function downloadText(filename: string, text: string, mime = "text/markdown") {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function fileToBase64(file: Blob): Promise<string> {
  const buffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(
      null,
      Array.from(bytes.subarray(i, i + chunk)),
    );
  }
  return btoa(binary);
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(sec?: number): string {
  if (!sec || !isFinite(sec)) return "—";
  return formatTs(sec);
}
