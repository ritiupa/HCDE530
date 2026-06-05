"""Design system for LENS Streamlit UI."""

__all__ = ["APP_CSS", "app_header", "metrics_row", "progress_html"]

APP_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  :root {
    --bg-base: #111113;
    --bg-surface: #1a1a1d;
    --bg-raised: #222226;
    --bg-input: #2a2a2f;
    --border: rgba(255, 255, 255, 0.09);
    --border-strong: rgba(255, 255, 255, 0.14);
    --text-primary: #f4f4f5;
    --text-secondary: #a1a1aa;
    --text-muted: #71717a;
    --accent: #3b82f6;
    --accent-soft: rgba(59, 130, 246, 0.14);
    --danger: #ef4444;
    --success: #22c55e;
    --radius: 8px;
    --radius-lg: 12px;
  }

  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
  }

  .stApp { background: var(--bg-base); }
  #MainMenu, footer, header { visibility: hidden; height: 0; }

  .block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 920px !important;
  }

  /* ── App header & step nav ── */
  .app-header {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 1rem;
    margin-bottom: 2rem; padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  .app-brand { font-size: 1.125rem; font-weight: 700; letter-spacing: -0.03em; }
  .app-brand span { color: var(--text-muted); font-weight: 500; font-size: 0.875rem; margin-left: 0.5rem; }
  .step-nav { display: flex; gap: 0.35rem; }
  .step-pill {
    font-size: 0.75rem; font-weight: 500; padding: 0.35rem 0.75rem;
    border-radius: 100px; color: var(--text-muted);
    border: 1px solid transparent;
  }
  .step-pill.active { background: var(--accent-soft); color: #93c5fd; border-color: rgba(59,130,246,0.25); }
  .step-pill.done { color: var(--text-secondary); }

  /* ── Sections ── */
  .section-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.35rem;
    margin-bottom: 1rem;
  }
  .section-label {
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted);
    margin: 0 0 0.75rem 0;
  }
  .section-heading {
    font-size: 1rem; font-weight: 600; margin: 0 0 0.35rem 0;
  }
  .section-desc {
    font-size: 0.8125rem; color: var(--text-secondary); margin: 0 0 1rem 0; line-height: 1.5;
  }

  /* ── Session list ── */
  .session-list { display: flex; flex-direction: column; gap: 0.4rem; }
  .session-item {
    display: grid; grid-template-columns: 64px 1fr auto;
    gap: 0.75rem; align-items: center;
    padding: 0.65rem 0.85rem;
    background: var(--bg-raised); border: 1px solid var(--border);
    border-radius: var(--radius); font-size: 0.8125rem;
  }
  .session-item-id { font-weight: 600; color: var(--accent); }
  .session-item-meta { color: var(--text-secondary); }
  .session-item-source {
    font-size: 0.6875rem; font-weight: 500; text-transform: uppercase;
    color: var(--text-muted); letter-spacing: 0.04em;
  }

  /* ── Processing ── */
  .progress-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 2rem 1.5rem;
    text-align: center;
  }
  .progress-title { font-size: 1.05rem; font-weight: 600; margin-bottom: 0.35rem; }
  .progress-sub { font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 1.75rem; }
  .progress-steps {
    display: flex; justify-content: center; gap: 0.5rem; flex-wrap: wrap;
  }
  .progress-step {
    font-size: 0.6875rem; font-weight: 500; padding: 0.35rem 0.65rem;
    border-radius: 100px; background: var(--bg-raised);
    border: 1px solid var(--border); color: var(--text-muted);
  }
  .progress-step.active { background: var(--accent-soft); color: #93c5fd; border-color: rgba(59,130,246,0.3); }
  .progress-step.done { color: var(--text-secondary); border-color: var(--border-strong); }

  /* ── Report ── */
  .report-page .block-container { max-width: 1080px !important; }

  .eyebrow { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 0.35rem 0; }
  .headline { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.03em; margin: 0 0 0.35rem 0; }
  .section-title { font-size: 0.8rem; font-weight: 600; margin: 0 0 0.2rem 0; }
  .finding-title { font-size: 0.95rem; font-weight: 600; margin: 0 0 0.3rem 0; }
  .finding-body { font-size: 0.85rem; line-height: 1.5; color: var(--text-secondary); margin: 0; }

  .surface-accent {
    background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, var(--bg-surface) 60%);
    border: 1px solid rgba(59, 130, 246, 0.18); border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem; margin-bottom: 0.85rem;
  }

  .metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.5rem; margin-top: 0.85rem; }
  .metric-tile { background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.7rem 0.85rem; }
  .metric-value { font-size: 1.2rem; font-weight: 600; letter-spacing: -0.03em; line-height: 1; margin-bottom: 0.2rem; }
  .metric-label { font-size: 0.65rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; }

  .pill { display: inline-flex; padding: 0.22rem 0.55rem; border-radius: 100px; font-size: 0.68rem; font-weight: 500; background: var(--bg-input); border: 1px solid var(--border); color: var(--text-secondary); margin-right: 0.3rem; }
  .badge { display: inline-flex; padding: 0.18rem 0.5rem; border-radius: 5px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; }
  .badge-critical { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
  .badge-major { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); }
  .badge-minor { background: rgba(34,197,94,0.12); color: #86efac; border: 1px solid rgba(34,197,94,0.22); }

  .participant-row { display: flex; align-items: center; gap: 0.75rem; background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.7rem 0.9rem; margin-bottom: 0.45rem; }
  .participant-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--bg-input); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 600; color: var(--text-secondary); }
  .participant-name { font-size: 0.85rem; font-weight: 500; margin: 0; }
  .participant-meta { font-size: 0.72rem; color: var(--text-muted); margin: 0.1rem 0 0 0; }

  .quote-block { border-left: 2px solid var(--accent); padding: 0.4rem 0 0.4rem 0.85rem; margin: 0.3rem 0; font-size: 0.82rem; color: var(--text-secondary); background: rgba(59,130,246,0.04); border-radius: 0 var(--radius) var(--radius) 0; }
  .insight-box { background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem; height: 100%; }
  .insight-box-accent { background: linear-gradient(160deg, rgba(59,130,246,0.08), var(--bg-raised)); border-color: rgba(59,130,246,0.15); }

  .transcript-wrap { background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.45rem 0.85rem; max-height: 420px; overflow-y: auto; }
  .transcript-row { display: flex; gap: 0.65rem; padding: 0.45rem 0; border-bottom: 1px solid var(--border); align-items: flex-start; }
  .transcript-row:last-child { border-bottom: none; }
  .transcript-ts { font-size: 0.68rem; color: var(--text-muted); min-width: 40px; font-variant-numeric: tabular-nums; }
  .transcript-text { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.45; }
  .transcript-text-friction { font-size: 0.82rem; color: var(--text-primary); line-height: 1.45; }
  .friction-mark { width: 5px; height: 5px; border-radius: 50%; background: var(--danger); margin-top: 0.45rem; flex-shrink: 0; }
  .highlight-card { background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.15rem; margin-bottom: 0.55rem; }
  .error-panel { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.22); border-radius: var(--radius); padding: 0.85rem 1rem; }

  /* ── Streamlit widgets ── */
  .stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: var(--bg-input) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; color: var(--text-primary) !important;
    font-size: 0.875rem !important;
  }
  .stSelectbox > div > div {
    background: var(--bg-input) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
  }
  .stCaption, label[data-testid="stWidgetLabel"] p { font-size: 0.8125rem !important; color: var(--text-muted) !important; }

  [data-testid="stFileUploader"] section {
    background: var(--bg-raised) !important; border: 1px dashed var(--border-strong) !important;
    border-radius: var(--radius) !important;
  }
  [data-testid="stIFrame"] { border-radius: var(--radius-lg); overflow: hidden; border: 1px solid var(--border); }

  .stButton > button[kind="primary"] {
    background: var(--accent) !important; color: white !important;
    border: none !important; border-radius: var(--radius) !important;
    font-weight: 600 !important;
  }
  [data-testid="stBaseButton-secondary"] > button {
    background: var(--bg-input) !important; color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important; border-radius: var(--radius) !important;
  }

  div[data-testid="stSegmentedControl"] {
    background: var(--bg-raised) !important; border-radius: var(--radius) !important;
    padding: 3px !important; border: 1px solid var(--border) !important;
  }

  .stTabs [data-baseweb="tab-list"] { background: var(--bg-raised); border-radius: var(--radius); padding: 3px; border: 1px solid var(--border); }
  .stTabs [aria-selected="true"] { background: var(--bg-input) !important; border-radius: 6px !important; }
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

  hr { border: none; border-top: 1px solid var(--border); margin: 1.25rem 0; }
</style>
"""


def app_header(step: int, subtitle: str = "") -> str:
    labels = ["Setup", "Processing", "Report"]
    pills = "".join(
        f'<span class="step-pill{" active" if i == step else ""}{" done" if i < step else ""}">'
        f'{i + 1}. {label}</span>'
        for i, label in enumerate(labels)
    )
    sub = f'<span>{subtitle}</span>' if subtitle else ""
    return f"""
    <div class="app-header">
      <div class="app-brand">LENS {sub}</div>
      <nav class="step-nav">{pills}</nav>
    </div>
    """


def progress_html(title: str, subtitle: str, steps: list[str], current: int) -> str:
    items = []
    for i, label in enumerate(steps):
        state = "done" if i < current else "active" if i == current else ""
        items.append(f'<span class="progress-step {state}">{label}</span>')
    return f"""
    <div class="progress-card">
      <div class="progress-title">{title}</div>
      <div class="progress-sub">{subtitle}</div>
      <div class="progress-steps">{"".join(items)}</div>
    </div>
    """


def metrics_row(items: list[tuple[str, str]]) -> str:
    tiles = "".join(
        f'<div class="metric-tile"><div class="metric-value">{v}</div>'
        f'<div class="metric-label">{l}</div></div>'
        for v, l in items
    )
    return f'<div class="metrics-row">{tiles}</div>'
