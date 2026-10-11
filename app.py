"""
SOC COMMAND CENTER - premium blue/purple UI for the SOC Threat Dashboard.

Only the UI is new. Data collection and detection are unchanged:
    from detector import detect_brute_force
    from windows_logs import get_recent_failed_logins
"""

import html
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from detector import detect_brute_force
from windows_logs import get_recent_failed_logins

try:  # Plotly is optional: the app still runs without it.
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

st.set_page_config(
    page_title="SOC Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# 1. STYLING (custom CSS)
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--card:rgba(17,24,54,.62);--line:rgba(129,140,248,.22);--text:#e6e9ff;--muted:#8f98c7;
--blue:#4f8cff;--violet:#8b5cf6;--cyan:#38bdf8;}
html,body,.stApp,[class*="css"]{font-family:'Inter','Segoe UI',system-ui,sans-serif;}
.stApp{background:radial-gradient(circle at 10% 0%,rgba(99,102,241,.24),transparent 42%),
radial-gradient(circle at 95% 6%,rgba(37,99,235,.20),transparent 40%),
linear-gradient(180deg,#070b1a 0%,#05070f 100%);color:var(--text);}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding:1.6rem 2.2rem 3rem;max-width:1600px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(52,211,153,.55);}70%{box-shadow:0 0 0 8px rgba(52,211,153,0);}100%{box-shadow:0 0 0 0 rgba(52,211,153,0);}}
@keyframes blink{50%{opacity:0;}}

/* Sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0f27 0%,#0c0a24 100%);border-right:1px solid var(--line);}
[data-testid="stSidebar"] *{color:var(--text);}
[data-testid="stSidebar"] label p,[data-testid="stSidebar"] .stCaption{color:var(--muted)!important;}
.brand{display:flex;gap:.7rem;align-items:center;padding:.3rem .2rem 1rem;}
.brand-logo{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;
background:linear-gradient(135deg,var(--blue),var(--violet));box-shadow:0 0 22px rgba(99,102,241,.55);}
.brand-name{font-weight:800;letter-spacing:.06em;font-size:.95rem;}
.brand-sub{font-size:.7rem;color:var(--muted);letter-spacing:.08em;}
.side-label{font-size:.68rem;letter-spacing:.14em;color:var(--muted);margin:1.1rem 0 .3rem;font-weight:600;}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:.3rem;}
[data-testid="stSidebar"] div[role="radiogroup"]>label{width:100%;padding:.55rem .8rem;border-radius:12px;border:1px solid transparent;transition:all .2s ease;cursor:pointer;}
[data-testid="stSidebar"] div[role="radiogroup"]>label:hover{background:rgba(99,102,241,.12);border-color:var(--line);transform:translateX(2px);}
[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked){background:linear-gradient(90deg,rgba(79,140,255,.26),rgba(139,92,246,.26));border-color:rgba(139,92,246,.55);box-shadow:0 0 18px rgba(99,102,241,.25);}
[data-testid="stSidebar"] label[data-baseweb="radio"]>div:first-child{display:none;}
div[data-baseweb="select"]>div,.stTextInput input{background:rgba(15,21,48,.85)!important;border:1px solid var(--line)!important;border-radius:12px!important;color:var(--text)!important;}
div.stButton>button{width:100%;border-radius:12px;border:1px solid rgba(139,92,246,.6);color:#fff;font-weight:600;padding:.6rem 1rem;
background:linear-gradient(90deg,#3b6fe0,#7c4ddb);transition:all .2s ease;box-shadow:0 4px 18px rgba(99,102,241,.3);}
div.stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 26px rgba(124,77,219,.5);border-color:#a78bfa;color:#fff;}

/* Glass cards */
.glass{background:var(--card);border:1px solid var(--line);border-radius:18px;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
box-shadow:0 8px 30px rgba(3,6,20,.55),inset 0 1px 0 rgba(255,255,255,.04);animation:fadeUp .5s ease both;}
.glass:hover{border-color:rgba(139,92,246,.45);}
[data-testid="stPlotlyChart"]{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:.5rem;backdrop-filter:blur(14px);box-shadow:0 8px 30px rgba(3,6,20,.55);}

/* Header */
.hero{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;padding:1.3rem 1.6rem;margin-bottom:1rem;}
.hero-eyebrow{font-size:.7rem;letter-spacing:.22em;color:var(--cyan);font-weight:600;}
.hero-title{font-size:2rem;font-weight:800;letter-spacing:.05em;margin:.1rem 0;background:linear-gradient(90deg,#7db0ff,#b69cff);-webkit-background-clip:text;background-clip:text;color:transparent;}
.hero-sub{color:var(--muted);font-size:.88rem;}
.hero-right{display:flex;gap:.5rem;flex-wrap:wrap;}
.pill{display:inline-flex;align-items:center;gap:.45rem;padding:.38rem .8rem;border-radius:999px;font-size:.75rem;font-weight:600;border:1px solid var(--line);background:rgba(15,21,48,.7);}
.pill .dot{width:8px;height:8px;border-radius:50%;display:inline-block;}
.pill.ok{color:#6ee7b7;border-color:rgba(52,211,153,.4);} .pill.ok .dot{background:#34d399;animation:pulse 2s infinite;}
.pill.warn{color:#fbbf24;border-color:rgba(251,191,36,.45);} .pill.warn .dot{background:#fbbf24;}
.pill.demo{color:#c4b5fd;border-color:rgba(167,139,250,.5);}
.pill.live{color:#7dd3fc;border-color:rgba(56,189,248,.5);}
.pill.muted{color:var(--muted);font-family:'JetBrains Mono',monospace;font-weight:400;}
.banner{padding:.7rem 1rem;border-radius:12px;font-size:.84rem;margin-bottom:1rem;border:1px solid var(--line);}
.banner.demo{background:rgba(139,92,246,.12);border-color:rgba(167,139,250,.4);color:#d8ccff;}
.banner.live{background:rgba(56,189,248,.10);border-color:rgba(56,189,248,.4);color:#bfe9ff;}

/* Metric cards */
.metric{display:flex;gap:1rem;align-items:center;padding:1.15rem 1.3rem;transition:transform .25s ease,box-shadow .25s ease;position:relative;overflow:hidden;}
.metric:hover{transform:translateY(-4px);box-shadow:0 14px 38px rgba(79,70,229,.35);}
.metric::after{content:"";position:absolute;right:-40px;top:-40px;width:120px;height:120px;border-radius:50%;background:radial-gradient(circle,rgba(139,92,246,.28),transparent 70%);}
.metric-icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex:none;
background:linear-gradient(135deg,rgba(79,140,255,.35),rgba(139,92,246,.35));border:1px solid var(--line);}
.metric-label{font-size:.72rem;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;font-weight:600;}
.metric-value{font-size:2.1rem;font-weight:800;line-height:1.15;}
.metric-note{font-size:.72rem;color:var(--muted);}
.metric.danger .metric-icon{background:linear-gradient(135deg,rgba(255,77,109,.35),rgba(139,92,246,.3));}

/* Section titles */
.section-title{display:flex;align-items:center;gap:.6rem;font-size:1.02rem;font-weight:700;margin:1.3rem 0 .6rem;}
.section-title::before{content:"";width:4px;height:18px;border-radius:2px;background:linear-gradient(var(--blue),var(--violet));}
.tag{font-size:.62rem;letter-spacing:.12em;padding:.15rem .5rem;border-radius:6px;font-weight:700;}
.tag-demo{background:rgba(139,92,246,.2);color:#c4b5fd;} .tag-live{background:rgba(56,189,248,.18);color:#7dd3fc;}

/* HTML tables */
.tbl-wrap{overflow:auto;padding:.3rem .5rem .6rem;}
table.soc{width:100%;border-collapse:collapse;font-size:.83rem;}
table.soc th{position:sticky;top:0;background:#101739;text-align:left;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:.7rem .8rem;border-bottom:1px solid var(--line);white-space:nowrap;}
table.soc td{padding:.62rem .8rem;border-bottom:1px solid rgba(129,140,248,.09);white-space:nowrap;}
table.soc tr:hover td{background:rgba(99,102,241,.1);}
.mono{font-family:'JetBrains Mono',Consolas,monospace;font-size:.78rem;color:#b9c4ff;}
.badge{display:inline-block;padding:.18rem .65rem;border-radius:999px;font-size:.7rem;font-weight:700;letter-spacing:.04em;border:1px solid;}
.sev-critical{color:#ff6b86;background:rgba(255,77,109,.14);border-color:rgba(255,77,109,.5);box-shadow:0 0 12px rgba(255,77,109,.2);}
.sev-high{color:#ffb15e;background:rgba(255,159,69,.13);border-color:rgba(255,159,69,.5);}
.sev-medium{color:#b6a8ff;background:rgba(139,124,255,.15);border-color:rgba(139,124,255,.5);}
.sev-low{color:#7dd3fc;background:rgba(56,189,248,.13);border-color:rgba(56,189,248,.5);}
.sev-unknown,.st-other{color:#aab2d5;background:rgba(148,163,184,.12);border-color:rgba(148,163,184,.35);}
.st-open{color:#93b4ff;background:rgba(79,140,255,.15);border-color:rgba(79,140,255,.5);}
.st-closed{color:#6ee7b7;background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.4);}
.chip{padding:.15rem .55rem;border-radius:8px;background:rgba(99,102,241,.16);color:#c7d0ff;font-size:.76rem;}

/* Terminal */
.term{overflow:hidden;}
.term-bar{display:flex;align-items:center;gap:.4rem;padding:.6rem .9rem;background:rgba(8,12,32,.9);border-bottom:1px solid var(--line);font-size:.72rem;color:var(--muted);}
.term-bar i{width:10px;height:10px;border-radius:50%;display:inline-block;}
.term-body{background:#050814;font-family:'JetBrains Mono',Consolas,monospace;font-size:.76rem;line-height:1.7;padding:.8rem 1rem;max-height:340px;overflow:auto;color:#a8b3e8;}
.t-note{color:#a78bfa;} .t-time{color:#5c6ba8;} .t-type{color:#7dd3fc;} .t-alert{color:#ff6b86;font-weight:600;}
.cursor{display:inline-block;width:8px;height:14px;background:#8b5cf6;vertical-align:middle;animation:blink 1s step-end infinite;}

/* Status / rules */
.row{display:flex;justify-content:space-between;gap:1rem;padding:.65rem .2rem;border-bottom:1px solid rgba(129,140,248,.1);font-size:.88rem;}
.row span:first-child{color:var(--muted);}
.empty{padding:1.6rem;text-align:center;color:var(--muted);font-size:.9rem;}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--line)!important;border-radius:16px;}
.foot{color:var(--muted);font-size:.75rem;text-align:center;margin-top:2rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 2. SMALL HELPERS
# ----------------------------------------------------------------------------
SEV_ORDER = ["Critical", "High", "Medium", "Low"]
SEV_COLORS = {"Critical": "#ff4d6d", "High": "#ff9f45", "Medium": "#8b7cff",
              "Low": "#38bdf8", "Unknown": "#64748b"}
NAV_ICONS = {"Overview": "◈", "Security Events": "▤", "Detected Incidents": "⚠",
             "Detection Rules": "⚙", "System Status": "◉"}
TS_KEYS = ["timestamp", "time", "time_created", "TimeCreated", "last_seen", "first_seen"]
IP_KEYS = ["source_ip", "ip", "src_ip", "ip_address"]
USER_KEYS = ["username", "user", "account", "target_user"]
NAME_KEYS = ["detection", "detection_name", "rule_name", "rule", "alert", "name", "title"]
COUNT_KEYS = ["count", "attempts", "failed_attempts", "event_count"]


def esc(value):
    """Escape text before placing it inside HTML."""
    return html.escape(str(value))


def pick(record, keys, default="—"):
    """Return the first non-empty value found under any of `keys`."""
    if not isinstance(record, dict):
        return default
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip() not in ("", "nan", "NaT"):
            return value
    return default


def to_dt(value):
    """Convert a value to a naive Python datetime, or None if impossible."""
    try:
        ts = pd.to_datetime(value)
        if ts is None or pd.isna(ts):
            return None
        if getattr(ts, "tzinfo", None) is not None:
            ts = ts.tz_localize(None)
        return ts.to_pydatetime()
    except Exception:
        return None


def fmt_time(value):
    dt = to_dt(value)
    if dt is not None:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "—" if value in (None, "") else str(value)


def severity_class(sev):
    return "sev-" + (sev.lower() if sev.title() in SEV_ORDER else "unknown")


def status_class(status):
    s = str(status).lower()
    if s == "open":
        return "st-open"
    if s in ("closed", "resolved"):
        return "st-closed"
    return "st-other"


def section_title(text, show_tag=True):
    tag = ""
    if show_tag:
        css, label = ("tag-demo", "SIMULATED") if IS_DEMO else ("tag-live", "WINDOWS LOG")
        tag = f'<span class="tag {css}">{label}</span>'
    st.markdown(f'<div class="section-title">{esc(text)}{tag}</div>', unsafe_allow_html=True)


def empty_state(message):
    st.markdown(f'<div class="glass empty">{esc(message)}</div>', unsafe_allow_html=True)


def html_table(df, max_rows=200, max_height=380):
    """Render a DataFrame as a styled HTML table with badges."""
    if df is None or df.empty:
        return '<div class="glass empty">No data to display.</div>'
    shown = df.head(max_rows)
    cols = list(shown.columns)
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = []
    for rec in shown.to_dict("records"):
        cells = []
        for col in cols:
            val = rec.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                val = "—"
            key = str(col).lower().replace(" ", "_")
            if key == "severity":
                cell = f'<span class="badge {severity_class(str(val))}">{esc(str(val).upper())}</span>'
            elif key == "status":
                cell = f'<span class="badge {status_class(val)}">{esc(str(val).upper())}</span>'
            elif key in ("event_type", "type"):
                cell = f'<span class="chip">{esc(val)}</span>'
            elif key in ("source_ip", "ip", "timestamp", "time"):
                cell = f'<span class="mono">{esc(val)}</span>'
            else:
                cell = esc(val)
            cells.append(f"<td>{cell}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    note = ""
    if len(df) > max_rows:
        note = f'<div class="empty">Showing first {max_rows} of {len(df)} rows.</div>'
    return (f'<div class="glass tbl-wrap" style="max-height:{max_height}px">'
            f'<table class="soc"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>{note}</div>')


def show_df(df):
    """st.dataframe that works on old and new Streamlit versions."""
    try:
        st.dataframe(df, use_container_width=True, hide_index=True)
    except TypeError:
        st.dataframe(df, width="stretch", hide_index=True)


def show_plot(fig):
    try:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except TypeError:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ----------------------------------------------------------------------------
# 3. SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-logo">🛡️</div><div>'
        '<div class="brand-name">SOC COMMAND</div><div class="brand-sub">THREAT MONITORING</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", list(NAV_ICONS.keys()),
                    format_func=lambda p: f"{NAV_ICONS[p]}  {p}",
                    label_visibility="collapsed")
    st.markdown('<div class="side-label">DATA SOURCE</div>', unsafe_allow_html=True)
    mode = st.radio("Data Source", ["Demo Mode", "Windows Live Logs"],
                    label_visibility="collapsed")
    st.markdown('<div class="side-label">LOG PERIOD</div>', unsafe_allow_html=True)
    period = st.selectbox("Log period", [1, 6, 12, 24], index=3,
                          format_func=lambda h: f"Last {h} hour" + ("s" if h > 1 else ""),
                          label_visibility="collapsed")
    st.caption("Applies to Windows Live Logs only.")
    st.write("")
    refresh = st.button("🔄 Refresh Dashboard")
    st.caption("Data is loaded each time the page refreshes. There is no automatic background collection.")

IS_DEMO = mode == "Demo Mode"

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if refresh:
    st.session_state.last_refresh = datetime.now()

# ----------------------------------------------------------------------------
# 4. DATA LOADING + DETECTION (same logic as the original app)
# ----------------------------------------------------------------------------
events = []
alerts = []
error_message = None

if mode == "Demo Mode":
    now = datetime.now()
    events = [
        {
            "timestamp": (now - timedelta(seconds=30 * i)).isoformat(),
            "event_type": "failed_login",
            "source_ip": "192.168.1.100",
            "username": "test_user",
        }
        for i in range(5)
    ]
    events += [
        {
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
            "event_type": "failed_login",
            "source_ip": "10.0.0.25",
            "username": "admin",
        },
        {
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "event_type": "successful_login",
            "source_ip": "192.168.1.10",
            "username": "ajay",
        },
    ]
else:
    try:
        events = get_recent_failed_logins(minutes=period * 60)
        if events is None:
            events = []
    except Exception as exc:
        error_message = str(exc)

try:
    alerts = detect_brute_force(events)
    if alerts is None:
        alerts = []
except Exception as exc:
    error_message = str(exc)
    alerts = []

# Defensive clean-up: keep only dict records so the UI never crashes.
events = [e for e in events if isinstance(e, dict)]
alerts = [a for a in alerts if isinstance(a, dict)]

total_events = len(events)
total_alerts = len(alerts)
critical = sum(1 for a in alerts if str(a.get("severity", "")).lower() == "critical")
high = sum(1 for a in alerts if str(a.get("severity", "")).lower() == "high")
open_alerts = sum(1 for a in alerts if str(a.get("status", "Open")).lower() == "open")

severity_counts = {}
for a in alerts:
    sev = str(a.get("severity", "Unknown")).title()
    severity_counts[sev] = severity_counts.get(sev, 0) + 1


# ----------------------------------------------------------------------------
# 5. DATA SHAPING FOR THE UI
# ----------------------------------------------------------------------------
def alerts_dataframe(alert_list):
    """Normalise alert dicts into a tidy table (tolerates missing fields)."""
    rows = []
    for a in alert_list:
        rows.append({
            "Detection": pick(a, NAME_KEYS, "Brute-Force Detection"),
            "Source IP": pick(a, IP_KEYS),
            "Username": pick(a, USER_KEYS),
            "Severity": str(pick(a, ["severity"], "Unknown")).title(),
            "Time": fmt_time(pick(a, TS_KEYS, None)),
            "Status": str(pick(a, ["status"], "Open")).title(),
            "Attempts": pick(a, COUNT_KEYS, None),
        })
    rows.sort(key=lambda r: SEV_ORDER.index(r["Severity"]) if r["Severity"] in SEV_ORDER else 9)
    df = pd.DataFrame(rows)
    if not df.empty and df["Attempts"].isna().all():
        df = df.drop(columns=["Attempts"])
    return df


def events_dataframe(event_list):
    df = pd.DataFrame(event_list)
    first = [c for c in ["timestamp", "source_ip", "username", "event_type"] if c in df.columns]
    return df[first + [c for c in df.columns if c not in first]]


# ----------------------------------------------------------------------------
# 6. CHARTS
# ----------------------------------------------------------------------------
def style_fig(fig, height):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#aab2e0", family="Inter, Segoe UI, sans-serif"),
        hoverlabel=dict(bgcolor="#141b45", bordercolor="#8b5cf6", font_color="#e6e9ff"),
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
    )
    return fig


def severity_donut(counts):
    labels = [s for s in SEV_ORDER] + [s for s in counts if s not in SEV_ORDER]
    values = [counts.get(s, 0) for s in labels]
    total = sum(values)
    if total == 0:
        fig = go.Figure(go.Pie(labels=["No alerts"], values=[1], hole=0.74, textinfo="none",
                               hoverinfo="skip", marker=dict(colors=["rgba(148,163,184,.18)"]),
                               showlegend=False))
    else:
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.74, sort=False, textinfo="none",
            marker=dict(colors=[SEV_COLORS.get(s, SEV_COLORS["Unknown"]) for s in labels],
                        line=dict(color="#0a0e1f", width=3)),
            hovertemplate="<b>%{label}</b><br>%{value} alert(s) · %{percent}<extra></extra>",
        ))
    fig.add_annotation(text=f"<b style='font-size:30px;color:#e6e9ff'>{total}</b><br>"
                            f"<span style='font-size:12px;color:#8f98c7'>ALERTS</span>",
                       showarrow=False)
    return style_fig(fig, 320)


def timeline_figure(event_list):
    rows = []
    for e in event_list:
        ts = to_dt(pick(e, TS_KEYS, None))
        if ts is not None:
            rows.append({"ts": ts, "type": str(pick(e, ["event_type", "type"], "event"))})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    secs = (df["ts"].max() - df["ts"].min()).total_seconds()
    if secs <= 1800:
        freq = "1min"
    elif secs <= 10800:
        freq = "5min"
    elif secs <= 43200:
        freq = "15min"
    elif secs <= 259200:
        freq = "60min"
    else:
        freq = "1440min"
    df["bucket"] = df["ts"].dt.floor(freq)
    counts = df.groupby(["bucket", "type"]).size().unstack(fill_value=0)
    counts = counts.reindex(pd.date_range(counts.index.min(), counts.index.max(), freq=freq),
                            fill_value=0)
    palette = ["#4f8cff", "#8b5cf6", "#38bdf8", "#c084fc", "#818cf8"]
    fig = go.Figure()
    for i, col in enumerate(counts.columns):
        fig.add_trace(go.Scatter(
            x=counts.index, y=counts[col], name=str(col).replace("_", " ").title(),
            mode="lines+markers", stackgroup="events",
            line=dict(width=2, color=palette[i % len(palette)]), marker=dict(size=6),
            hovertemplate="%{y} event(s)<extra>" + str(col) + "</extra>",
        ))
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(showgrid=False, color="#8f98c7")
    fig.update_yaxes(gridcolor="rgba(129,140,248,.10)", color="#8f98c7", rangemode="tozero",
                     title_text="Events")
    return style_fig(fig, 320)


# ----------------------------------------------------------------------------
# 7. PAGE SECTIONS
# ----------------------------------------------------------------------------
def render_header():
    if error_message:
        status = '<span class="pill warn"><i class="dot"></i>Attention needed</span>'
    else:
        status = '<span class="pill ok"><i class="dot"></i>Dashboard online</span>'
    source = ('<span class="pill demo">Demo mode · simulated data</span>' if IS_DEMO
              else '<span class="pill live">Windows live logs</span>')
    stamp = st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        '<div class="hero glass"><div><div class="hero-eyebrow">SECURITY OPERATIONS</div>'
        '<div class="hero-title">SOC COMMAND CENTER</div>'
        '<div class="hero-sub">Threat detection &amp; incident monitoring · snapshot view</div></div>'
        f'<div class="hero-right">{status}{source}'
        f'<span class="pill muted">Last refresh · {stamp}</span></div></div>',
        unsafe_allow_html=True,
    )
    if IS_DEMO:
        st.markdown('<div class="banner demo"><b>Demo Mode.</b> All events below are simulated by the '
                    'dashboard for demonstration. They are not real security telemetry.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner live"><b>Windows Live Logs.</b> Events were read from this '
                    'machine when the page last loaded. This is a snapshot, not continuous '
                    'monitoring. Press Refresh to reload.</div>', unsafe_allow_html=True)
    if error_message:
        st.warning(f"Data collection notice: {error_message}")


def metric_card(icon, label, value, note, extra=""):
    return (f'<div class="glass metric {extra}"><div class="metric-icon">{icon}</div><div>'
            f'<div class="metric-label">{label}</div><div class="metric-value">{value}</div>'
            f'<div class="metric-note">{note}</div></div></div>')


def render_metrics():
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric_card("📡", "Total Events", total_events, "Loaded this refresh"), unsafe_allow_html=True)
    c2.markdown(metric_card("🚨", "Total Alerts", total_alerts, "From brute-force rule"), unsafe_allow_html=True)
    c3.markdown(metric_card("🔥", "High / Critical", high + critical,
                            f"{critical} critical · {high} high", "danger"), unsafe_allow_html=True)
    c4.markdown(metric_card("📂", "Open Incidents", open_alerts, "Awaiting review"), unsafe_allow_html=True)


def render_severity_chart():
    section_title("Alert Severity")
    if PLOTLY_OK:
        show_plot(severity_donut(severity_counts))
    elif severity_counts:
        st.bar_chart(pd.DataFrame({"Alerts": severity_counts}))
    else:
        empty_state("No alerts detected.")
    if not alerts:
        st.caption("No alerts detected for the selected data source.")


def render_timeline():
    section_title("Security Event Activity")
    fig = timeline_figure(events) if PLOTLY_OK else None
    if fig is not None:
        show_plot(fig)
    elif not PLOTLY_OK:
        empty_state("Install Plotly to see the activity timeline:  python -m pip install plotly")
    else:
        empty_state("No timestamped events available for the timeline.")


def render_recent_alerts(limit=8):
    section_title("Recent Alerts")
    if alerts:
        st.markdown(html_table(alerts_dataframe(alerts), max_rows=limit, max_height=340),
                    unsafe_allow_html=True)
    else:
        empty_state("No brute-force alerts detected.")


def render_terminal():
    section_title("Activity Feed")
    if IS_DEMO:
        note = "# DEMO MODE: simulated events, not real telemetry"
    else:
        stamp = st.session_state.last_refresh.strftime("%H:%M:%S")
        note = f"# Windows Event Log snapshot (page loaded {stamp}), not a live stream"
    lines = [f'<div class="t-note">{esc(note)}</div>']
    stamped = [(to_dt(pick(e, TS_KEYS, None)) or datetime.min, i, e) for i, e in enumerate(events)]
    stamped.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for dt, _, e in stamped[:12]:
        ts = dt.strftime("%H:%M:%S") if dt != datetime.min else "--:--:--"
        etype = str(pick(e, ["event_type", "type"], "event")).upper()
        lines.append(f'<div><span class="t-time">[{ts}]</span> <span class="t-type">{esc(etype)}</span> '
                     f'src={esc(pick(e, IP_KEYS))} user={esc(pick(e, USER_KEYS))}</div>')
    if not events:
        lines.append('<div class="t-time">no events loaded</div>')
    for a in alerts[:4]:
        lines.append(f'<div><span class="t-alert">[ALERT]</span> {esc(pick(a, NAME_KEYS, "Brute-Force Detection"))} '
                     f'src={esc(pick(a, IP_KEYS))} severity={esc(str(pick(a, ["severity"], "unknown")).upper())}</div>')
    lines.append('<div>$ end of snapshot <span class="cursor"></span></div>')
    st.markdown('<div class="glass term"><div class="term-bar"><i style="background:#ff4d6d"></i>'
                '<i style="background:#ffb15e"></i><i style="background:#34d399"></i>'
                '&nbsp; activity-feed · snapshot</div>'
                f'<div class="term-body">{"".join(lines)}</div></div>', unsafe_allow_html=True)


def render_explorer(key_prefix):
    section_title("Security Event Explorer")
    if not events:
        empty_state("No events available. In Windows Live Logs mode, reading the Security log "
                    "may require running PowerShell as Administrator.")
        return
    df = events_dataframe(events)
    f1, f2 = st.columns([1, 2])
    if "event_type" in df.columns:
        types = ["All"] + sorted(df["event_type"].dropna().astype(str).unique().tolist())
        selected = f1.selectbox("Event type", types, key=f"{key_prefix}_type")
        if selected != "All":
            df = df[df["event_type"].astype(str) == selected]
    query = f2.text_input("Search events", placeholder="IP, username, event type...",
                          key=f"{key_prefix}_search")
    if query.strip():
        mask = df.astype(str).apply(
            lambda col: col.str.contains(query.strip(), case=False, regex=False)).any(axis=1)
        df = df[mask]
    st.caption(f"{len(df)} of {total_events} events shown")
    st.markdown(html_table(df, max_rows=200, max_height=420), unsafe_allow_html=True)


def render_rules():
    section_title("Detection Rules", show_tag=False)
    with st.expander("🧠 Rule BF-001 — Brute-Force Login Detection", expanded=True):
        st.markdown("""
- Monitors failed-login events.
- Groups events by source IP address.
- Flags repeated failures within a five-minute window.
- Exact thresholds and severity logic live in `detector.py`.
- This is a detection indicator, not proof of a successful attack.
""")
        st.markdown(
            '<div class="row"><span>Rule ID</span><span>BF-001</span></div>'
            '<div class="row"><span>Input</span><span>Failed-login events</span></div>'
            '<div class="row"><span>Grouping</span><span>Source IP address</span></div>'
            '<div class="row"><span>Window</span><span>5 minutes</span></div>',
            unsafe_allow_html=True)


def render_status():
    section_title("System Status", show_tag=False)
    collection = f"Issue: {error_message}" if error_message else "OK"
    rows = [
        ("Dashboard", "Running"),
        ("Data source", mode + (" (simulated)" if IS_DEMO else "")),
        ("Data collection", collection),
        ("Events loaded", total_events),
        ("Alerts detected", total_alerts),
        ("Last dashboard refresh", st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S")),
        ("Refresh method", "Manual (Refresh button or changing a control)"),
        ("Streamlit version", st.__version__),
        ("Plotly charts", "Available" if PLOTLY_OK else "Not installed"),
    ]
    with st.expander("🖥️ System Status", expanded=True):
        st.markdown("".join(f'<div class="row"><span>{esc(k)}</span><span>{esc(v)}</span></div>'
                            for k, v in rows), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# 8. PAGE ROUTING
# ----------------------------------------------------------------------------
render_header()
render_metrics()

if page == "Overview":
    left, right = st.columns([1, 2])
    with left:
        render_severity_chart()
    with right:
        render_timeline()
    a, b = st.columns([3, 2])
    with a:
        render_recent_alerts()
    with b:
        render_terminal()
    render_explorer("ov")

elif page == "Security Events":
    render_timeline()
    render_explorer("ev")
    render_terminal()

elif page == "Detected Incidents":
    left, right = st.columns([1, 2])
    with left:
        render_severity_chart()
    with right:
        section_title("Detected Incidents")
        if alerts:
            st.markdown(html_table(alerts_dataframe(alerts), max_rows=200, max_height=330),
                        unsafe_allow_html=True)
        else:
            empty_state("No brute-force alerts detected.")
    if alerts:
        with st.expander("Raw alert data (sortable)"):
            show_df(pd.DataFrame(alerts))

elif page == "Detection Rules":
    render_rules()

else:
    render_status()

st.markdown('<div class="foot">SOC Command Center · Educational monitoring project</div>',
            unsafe_allow_html=True)
