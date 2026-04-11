"""
app.py — SafeNest v4
Changes:
  CUSTOMER UI
  - Removed Quick queries from sidebar
  - 5 predefined suggestion chips above query box (clicked = fires query)
  - Used suggestion chips are removed from display after click
  - Large rounded sticky query box fixed at bottom-centre
  - Responses render above the query box
  - Sidebar keeps only: logo + user info + token limit bar + logout

  ADMIN UI
  - Full cost / token / API usage visible (hidden from customers)
  - Per-user token limit reset button
  - Reset all users button
  - User search: type username → see full history + bank data in formatted table
"""

import streamlit as st
import sys, os, re
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from auth.auth            import login, enforce_access, is_logged_in
from llm.groq_client      import detect_intent, format_response
from coordinator.coordinator import route
from utils.cache  import (
    get as cache_get, set as cache_set,
    record_usage, record_cache_hit,
    get_all_user_stats, get_user_stats,
    clear_cache, cache_size,
)
from utils.logger import (
    log_login, log_query, log_access_denied,
    log_cache_hit, log_error, log_admin_action, log_logout,
)
import pandas as pd

CUSTOMERS_PATH = os.path.join(BASE, "data", "customers.csv")
DAILY_LIMIT    = 5

# ─── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="SafeNest Banking",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ──────────────────────────────────────── */
[data-testid="stAppViewContainer"]{background:#F0F3FA;}
/* Sidebar */
[data-testid="stSidebar"]{background:#1E2761 !important;}
[data-testid="stSidebar"] * {color:#C8D4F0 !important;}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] strong {color:#ffffff !important;}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.15)!important;}
[data-testid="stSidebar"] .stButton>button{
  background:rgba(255,255,255,.08)!important;
  border:1px solid rgba(255,255,255,.18)!important;
  color:#fff!important;border-radius:10px!important;
  transition:background .2s!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
  background:rgba(255,255,255,.18)!important;
}
/* ── Banner ──────────────────────────────────────── */
.sn-banner{
  background:linear-gradient(135deg,#1E2761 0%,#2D3D8E 100%);
  border-radius:14px;padding:.75rem 1.5rem;margin-bottom:.5rem;
  box-shadow:0 3px 14px rgba(30,39,97,.16);
}
.sn-banner h2{color:#fff;margin:0;font-size:1.2rem;font-weight:700;}
.sn-banner p{color:#C0CFEE;margin:.1rem 0 0;font-size:.8rem;}
/* ── Suggestion panel ────────────────────────────── */
.sugg-panel{
  background:#fff;border-radius:16px;border:1.5px solid #E2E8F5;
  padding:.9rem .85rem;
  box-shadow:0 2px 10px rgba(30,39,97,.06);
}
.sugg-panel-title{
  font-size:.74rem;font-weight:700;color:#8893B0;
  text-transform:uppercase;letter-spacing:.07em;
  margin-bottom:.65rem;padding-bottom:.32rem;
  border-bottom:1px solid #EEF1F8;
}
/* clickable suggestion item */
.sug-item-btn>button{
  background:#F7F9FF !important;
  border:1.5px solid #C5D0E8 !important;
  border-radius:12px !important;
  padding:.6rem .85rem !important;
  font-size:.88rem !important;
  color:#1E2761 !important;
  font-weight:600 !important;
  text-align:left !important;
  margin-bottom:.4rem !important;
  transition:all .18s !important;
  line-height:1.38 !important;
  min-height:40px !important;
  width:100% !important;
}
.sug-item-btn>button:hover{
  background:#EEF1FB !important;
  border-color:#2D3D8E !important;
  color:#2D3D8E !important;
  box-shadow:0 2px 8px rgba(45,61,142,.15) !important;
  transform:translateX(2px) !important;
}
/* asked / used item — stays in place, highlighted amber */
.sug-item-used{
  border:1.5px solid #E8A020;
  border-radius:12px;
  padding:.55rem .85rem;
  font-size:.88rem;
  font-weight:600;
  color:#7A4A00;
  background:#FFFBEF;
  margin-bottom:.4rem;
  line-height:1.38;
  display:flex;
  align-items:center;
  justify-content:space-between;
  min-height:40px;
}
.freq-badge{
  flex-shrink:0;
  font-size:.7rem;
  background:#FEF3CD;color:#A06000;
  border-radius:7px;padding:.05rem .4rem;
  margin-left:.4rem;font-weight:700;
  border:1px solid #F4C842;
}
/* ── Token limit banner ──────────────────────────── */
.limit-banner{
  background:#FFF8E6;border:1.5px solid #F4A034;border-radius:14px;
  padding:.75rem 1.2rem;margin-bottom:.6rem;text-align:center;
  font-size:.92rem;font-weight:600;color:#854F0B;
}
/* ── Response area ───────────────────────────────── */
.resp-area{padding-bottom:10px;}
/* ── Capability mini cards ───────────────────────── */
.mini-cards{display:flex;gap:8px;flex-wrap:nowrap;margin-bottom:.5rem;}
.mini-card{
  flex:1;min-width:0;background:#fff;border-radius:12px;
  border:1.5px solid #DDE4EC;padding:.45rem .6rem;
  transition:border-color .2s,box-shadow .2s,transform .12s;cursor:default;
}
.mini-card:hover{border-color:#2D3D8E;
  box-shadow:0 2px 8px rgba(45,61,142,.12);transform:translateY(-1px);}
.mini-card .mc-icon{font-size:1.1rem;margin-bottom:.15rem;}
.mini-card .mc-title{font-weight:700;color:#1E2761;font-size:.76rem;}
.mini-card .mc-desc{color:#6B7A9F;font-size:.68rem;margin-top:.05rem;}
/* ── Response cards ──────────────────────────────── */
.resp-card{
  background:#fff;border-radius:14px;border:1px solid #DDE4EC;
  padding:.7rem .95rem;margin-bottom:.45rem;
  box-shadow:0 2px 6px rgba(30,39,97,.05);
}
.resp-card:hover{box-shadow:0 3px 12px rgba(30,39,97,.09);}
.resp-q{font-weight:700;color:#1E2761;font-size:.85rem;margin-bottom:.3rem;}
.resp-body{color:#1A2A1A;font-size:.88rem;line-height:1.5;}
.resp-meta{margin-top:.5rem;display:flex;flex-wrap:wrap;gap:6px;}
.pill{border-radius:20px;padding:.2rem .7rem;font-size:.76rem;font-weight:600;display:inline-block;}
.pill-agent{background:#EEF1FB;color:#2D3D8E;}
.pill-intent{background:#FDF3E7;color:#854F0B;}
.pill-cache{background:#EAF3DE;color:#3B6D11;}
.pill-denied{background:#FFF0F0;color:#A32D2D;}
.pill-limit{background:#FFF8E6;color:#854F0B;}
/* ── Denied card ─────────────────────────────────── */
.denied-card{
  background:#FFF4F4;border:1.5px solid #E24B4A;border-radius:16px;
  padding:.9rem 1.1rem;margin-bottom:.65rem;
}
.denied-title{font-weight:700;color:#A32D2D;margin-bottom:.3rem;}
.denied-body{color:#501313;font-size:.9rem;}
/* ── Limit card ──────────────────────────────────── */
.limit-card{
  background:#FFF8E6;border:1.5px solid #F4A034;border-radius:16px;
  padding:.9rem 1.1rem;margin-bottom:.65rem;
}
.limit-title{font-weight:700;color:#854F0B;margin-bottom:.25rem;}
.limit-body{color:#633806;font-size:.9rem;}
/* ── Token bar (sidebar) ─────────────────────────── */
.tok-bar{
  background:rgba(255,255,255,.08);border-radius:10px;
  padding:.6rem .85rem;margin-bottom:.5rem;
}
.tok-label{font-size:.78rem;font-weight:700;color:#fff!important;margin-bottom:.28rem;}
.tok-track{background:rgba(255,255,255,.18);border-radius:5px;height:7px;}
.tok-fill{border-radius:5px;height:7px;transition:width .3s;}
.tok-count{font-size:.74rem;color:#A0B0D8!important;margin-top:.22rem;}
/* ── Sidebar user identity card ─────────────────── */
.sid-user-card{
  background:rgba(255,255,255,.07);border-radius:14px;
  padding:.85rem 1rem;margin-bottom:.5rem;
}
.sid-avatar{
  width:42px;height:42px;border-radius:50%;
  background:rgba(255,255,255,.18);
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;font-weight:700;color:#fff;
  margin-bottom:.6rem;
}
.sid-name{
  font-size:1rem;font-weight:700;color:#fff;
  margin-bottom:.5rem;line-height:1.2;
}
.sid-row{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:.28rem;
}
.sid-lbl{
  font-size:.73rem;color:#8898C8;font-weight:600;
  text-transform:uppercase;letter-spacing:.05em;
}
.sid-val{
  font-size:.78rem;color:#C8D4F0;font-weight:500;
  text-align:right;max-width:62%;word-break:break-all;
}
/* ── Admin table ─────────────────────────────────── */
.admin-user-card{
  background:#fff;border-radius:14px;border:1px solid #DDE4EC;
  padding:1rem 1.2rem;margin-bottom:.7rem;
}
.admin-user-card h4{margin:0 0 .5rem;color:#1E2761;}
.data-table{width:100%;border-collapse:collapse;font-size:.86rem;}
.data-table th{background:#1E2761;color:#fff;padding:.4rem .7rem;text-align:left;}
.data-table td{padding:.35rem .7rem;border-bottom:1px solid #EEF1F8;color:#2A3550;}
.data-table tr:last-child td{border-bottom:none;}
.data-table tr:nth-child(even) td{background:#F7F9FD;}
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────
for k, v in {
    "logged_in_user":  None,
    "history":         [],
    "query_input":     "",
    "daily_counts":    {},
    "used_chips":      [],    # tracks which suggestion chips were clicked
    "submit_query":    "",    # chip click fires query via this
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Constants ────────────────────────────────────────────────
INTENT_LABELS = {
    "loan_check": "Loan Eligibility", "transaction_issue": "Transaction Issue",
    "fraud_check": "Fraud Detection",  "compliance_check": "Compliance Check",
    "general_query": "General Support",
}
AGENT_META = {
    "Loan Eligibility Agent": ("💰", "pill-agent"),
    "Transaction Agent":      ("🔍", "pill-agent"),
    "Fraud Detection Agent":  ("🛡️", "pill-agent"),
    "Compliance Agent":       ("📋", "pill-agent"),
    "Support Agent":          ("🎧", "pill-agent"),
    "Authorization Guard":    ("🚫", "pill-denied"),
}
ALL_SUGGESTIONS = [
    "Am I eligible for a personal loan?",
    "Why was my last transaction blocked?",
    "Is there suspicious activity on the account?",
    "Is the account compliant with banking rules?",
    "How do I increase my transfer limit?",
]

# ─── Daily limit helpers ──────────────────────────────────────
def _dkey(u): return f"{u}:{date.today().isoformat()}"
def _live_today(u): return st.session_state.daily_counts.get(_dkey(u), 0)
def _inc_live(u):
    k = _dkey(u)
    st.session_state.daily_counts[k] = st.session_state.daily_counts.get(k, 0) + 1
def _limit_ok(u): return _live_today(u) < DAILY_LIMIT

def _reset_user_limit(username: str):
    """Admin action — wipes today's counter for a user."""
    k = _dkey(username)
    if k in st.session_state.daily_counts:
        del st.session_state.daily_counts[k]

def _reset_all_limits():
    today = date.today().isoformat()
    keys = [k for k in st.session_state.daily_counts if today in k]
    for k in keys:
        del st.session_state.daily_counts[k]


# ════════════════════════════════════════════════════════════
#  LOGIN SCREEN
# ════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
<div style="text-align:center;margin:2rem 0 1.5rem;">
  <div style="font-size:3rem;"></div>
  <h1 style="font-size:2.2rem;margin:.2rem 0;color:#1E2761;">SafeNest</h1>
  <p style="color:#8893B0;font-size:1rem;">Intelligent Banking System</p>
</div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("#### Sign In")
        username = st.text_input("Username", placeholder="e.g. arjun")
        password = st.text_input("Password", type="password")
        if st.button("Log In →", type="primary", use_container_width=True):
            if not username or not password:
                st.warning("Enter both username and password.")
            else:
                user = login(username, password)
                if user:
                    st.session_state.logged_in_user = user
                    st.session_state.history        = []
                    st.session_state.used_chips     = []
                    log_login(username, success=True, role=user["role"])
                    st.rerun()
                else:
                    log_login(username, success=False)
                    st.error("Invalid credentials.")
        st.divider()
        st.markdown("**Demo accounts:**")
        for u, p, n in [
            ("arjun","arjun123","Arjun Das"),("rahul","rahul123","Rahul Sharma"),
            ("anita","anita123","Anita Patel"),("vikram","vikram123","Vikram Singh"),
            ("priya","priya123","Priya Menon"),("admin","admin123","System Admin"),
        ]:
            st.caption(f"`{u}` / `{p}` — {n}")


# ════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ════════════════════════════════════════════════════════════
def show_admin():
    user = st.session_state.logged_in_user
    admin_name = user["username"]

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("##  Admin Panel")
        st.markdown(f"**{user['name']}**")
        st.divider()
        if st.button("🗑 Clear all cache", use_container_width=True):
            clear_cache()
            log_admin_action(admin_name, "cleared_cache")
            st.success("Cache cleared.")
        if st.button("🔄 Reset ALL token limits", use_container_width=True):
            _reset_all_limits()
            log_admin_action(admin_name, "reset_all_limits")
            st.success("All limits reset.")
            st.rerun()
        st.divider()
        if st.button(" Logout", use_container_width=True):
            log_logout(admin_name)
            st.session_state.logged_in_user = None
            st.rerun()

    # ── Header ────────────────────────────────────────────────
    st.markdown("""
<div class="sn-banner">
  <h2> Admin Monitoring Dashboard</h2>
  <p>Full system access · Cost tracking · Token limits · User data · Live log</p>
</div>""", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    tab_overview, tab_users, tab_search, tab_log = st.tabs(
        [" Overview", " Per-User Usage", " User Search", " Live Log"]
    )

    all_stats = get_all_user_stats()

    # ═══ TAB 1: Overview ═════════════════════════════════════
    with tab_overview:
        if not all_stats:
            st.info("No activity recorded yet.")
        else:
            total_q  = sum(s["total_queries"] for s in all_stats.values())
            total_c  = sum(s["est_cost_usd"]  for s in all_stats.values())
            total_ch = sum(s["cache_hits"]    for s in all_stats.values())
            total_tk = sum(s["tokens_in"] + s["tokens_out"] for s in all_stats.values())

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total queries",   total_q)
            c2.metric("Total cache hits", total_ch)
            c3.metric("Total tokens",    f"{total_tk:,}")
            c4.metric("Total API cost",  f"${total_c:.5f}")

            st.caption(f"Cache entries in memory: **{cache_size()}**")

    # ═══ TAB 2: Per-user ══════════════════════════════════════
    with tab_users:
        if not all_stats:
            st.info("No activity yet.")
        else:
            df_rows = []
            for uname, s in sorted(all_stats.items(), key=lambda x: -x[1]["total_queries"]):
                live = _live_today(uname)
                df_rows.append({
                    "User":        uname,
                    "Queries":     s["total_queries"],
                    "Cache hits":  s["cache_hits"],
                    "Tokens in":   s["tokens_in"],
                    "Tokens out":  s["tokens_out"],
                    "API cost $":  round(s["est_cost_usd"], 6),
                    "Live today":  f"{live}/{DAILY_LIMIT}",
                })

            st.dataframe(df_rows, use_container_width=True)
            st.divider()

            # Per-user token reset
            st.markdown("#### Reset individual token limits")
            all_users = [r["User"] for r in df_rows]
            sel = st.selectbox("Select user", options=all_users, key="reset_sel")
            if st.button(f"🔄 Reset {sel}'s token limit today", type="primary"):
                _reset_user_limit(sel)
                log_admin_action(admin_name, f"reset_limit:{sel}")
                st.success(f"Token limit reset for {sel}.")
                st.rerun()

    # ═══ TAB 3: User Search ═══════════════════════════════════
    with tab_search:
        st.markdown("#### Search user — view account data and query history")
        search_input = st.text_input("Type username", placeholder="e.g. arjun",
                                     key="admin_search")

        if search_input.strip():
            _show_user_detail(search_input.strip().lower(), all_stats)

    # ═══ TAB 4: Live Log ══════════════════════════════════════
    with tab_log:
        log_path = os.path.join(BASE, "safenest.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                lines = f.readlines()
            st.markdown(f"Showing last **{min(80, len(lines))}** lines")
            st.code("".join(lines[-80:]), language=None)
        else:
            st.caption("No log file yet.")


def _show_user_detail(username: str, all_stats: dict):
    """Admin: show bank data + query history for a given username."""
    # Load customer record
    try:
        df = pd.read_csv(CUSTOMERS_PATH)
        cust_row = df[df["username"] == username]
    except Exception:
        cust_row = pd.DataFrame()

    if cust_row.empty:
        st.warning(f"No customer found with username **{username}**.")
        return

    c = cust_row.iloc[0]
    cid = int(c["customer_id"])

    # ── Bank account data ─────────────────────────────────────
    acct_no = str(c.get('account_number', 'N/A'))
    branch  = str(c.get('branch', 'N/A'))
    st.markdown(f"""
<div class="admin-user-card">
  <h4>👤 {c['name']} ({username})</h4>
  <table class="data-table">
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Customer ID</td><td>{cid}</td></tr>
    <tr><td>Full Name</td><td>{c['name']}</td></tr>
    <tr><td>Username</td><td>{username}</td></tr>
    <tr><td>Account Number</td><td>{acct_no}</td></tr>
    <tr><td>Branch</td><td>{branch}</td></tr>
    <tr><td>Monthly Income</td><td>Rs. {int(c['income']):,}</td></tr>
    <tr><td>Credit Score</td><td>{int(c['credit_score'])}</td></tr>
    <tr><td>Existing Loans</td><td>{int(c['existing_loans'])}</td></tr>
  </table>
</div>""", unsafe_allow_html=True)

    # ── Transactions ──────────────────────────────────────────
    try:
        txns = pd.read_csv(os.path.join(BASE, "data", "transactions.csv"))
        user_txns = txns[txns["customer_id"] == cid]
        st.markdown("**Transactions on file:**")
        if user_txns.empty:
            st.caption("No transactions found.")
        else:
            st.dataframe(user_txns.reset_index(drop=True), use_container_width=True)
    except Exception:
        pass

    # ── Loans ─────────────────────────────────────────────────
    try:
        loans = pd.read_csv(os.path.join(BASE, "data", "loans.csv"))
        user_loans = loans[loans["customer_id"] == cid]
        st.markdown("**Active loans:**")
        if user_loans.empty:
            st.caption("No loans on file.")
        else:
            st.dataframe(user_loans.reset_index(drop=True), use_container_width=True)
    except Exception:
        pass

    # ── Usage stats ────────────────────────────────────────────
    s = all_stats.get(username)
    live = _live_today(username)
    st.markdown("**Usage stats:**")
    if s:
        st.markdown(f"""
<div class="admin-user-card">
  <table class="data-table">
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Total queries (all time)</td><td>{s['total_queries']}</td></tr>
    <tr><td>Cache hits</td><td>{s['cache_hits']}</td></tr>
    <tr><td>Tokens in</td><td>{s['tokens_in']:,}</td></tr>
    <tr><td>Tokens out</td><td>{s['tokens_out']:,}</td></tr>
    <tr><td>Estimated API cost</td><td>${s['est_cost_usd']:.6f}</td></tr>
    <tr><td>Live queries today</td><td>{live} / {DAILY_LIMIT}</td></tr>
  </table>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No query activity yet.")

    # ── Admin action: reset this user's limit ──────────────────
    if st.button(f"🔄 Reset {username}'s token limit", key=f"reset_{username}"):
        _reset_user_limit(username)
        log_admin_action("admin", f"reset_limit:{username}")
        st.success(f"Token limit reset for {username}.")
        st.rerun()


# ════════════════════════════════════════════════════════════
#  CUSTOMER INTERFACE
# ════════════════════════════════════════════════════════════
def show_customer():
    user     = st.session_state.logged_in_user
    own_id   = user["customer_id"]
    own_name = user["name"]
    username = user["username"]

    live_today = _live_today(username)
    pct        = min(100, int((live_today / DAILY_LIMIT) * 100))
    bar_col    = "#E24B4A" if live_today >= DAILY_LIMIT else "#4FC38A"
    has_history = bool(st.session_state.history)

    # Suggestions that have NOT been used yet
    avail_chips  = [q for q in ALL_SUGGESTIONS if q not in st.session_state.used_chips]
    # Suggestions that HAVE been used (shown highlighted in left panel)
    used_chips   = [q for q in ALL_SUGGESTIONS if q in st.session_state.used_chips]

    # ── Load account details from CSV ────────────────────────
    try:
        _cdf = pd.read_csv(CUSTOMERS_PATH)
        _crow = _cdf[_cdf["customer_id"] == own_id].iloc[0]
        acct_no = str(_crow.get("account_number", "N/A"))
        branch  = str(_crow.get("branch", "N/A"))
    except Exception:
        acct_no = "N/A"
        branch  = "N/A"

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("##  SafeNest")
        bar_col_side = "#E24B4A" if live_today >= DAILY_LIMIT else "#4FC38A"
        # Rich user identity card
        st.markdown(f"""
<div class="sid-user-card">
  <div class="sid-avatar">{own_name[0].upper()}</div>
  <div class="sid-name">{own_name}</div>
  <div class="sid-row"><span class="sid-lbl">Account</span><span class="sid-val">{acct_no}</span></div>
  <div class="sid-row"><span class="sid-lbl">Branch</span><span class="sid-val">{branch}</span></div>
</div>""", unsafe_allow_html=True)
        st.divider()
        st.markdown(f"""
<div class="tok-bar">
  <div class="tok-label">Token Limit</div>
  <div class="tok-track">
    <div class="tok-fill" style="width:{pct}%;background:{bar_col_side};"></div>
  </div>
  <div class="tok-count">{live_today} / {DAILY_LIMIT} searches used</div>
</div>""", unsafe_allow_html=True)
        if live_today >= DAILY_LIMIT:
            st.warning("Limit exceeded — try after 24 hours")
        st.divider()
        if st.button(" Logout", use_container_width=True):
            log_logout(username)
            st.session_state.logged_in_user = None
            st.session_state.history        = []
            st.session_state.used_chips     = []
            st.rerun()

    # ─────────────────────────────────────────────────────────
    #  TOP SECTION: Banner + mini capability cards (always full width)
    # ─────────────────────────────────────────────────────────
    st.markdown(f"""
<div class="sn-banner">
  <h2>  Welcome, {own_name}</h2>
  <p>Your money. Your goals. Our support · 24/7 availability</p>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div class="mini-cards">
  <div class="mini-card"><div class="mc-icon">💰</div>
    <div class="mc-title">Loan Eligibility</div><div class="mc-desc">Instant decision</div></div>
  <div class="mini-card"><div class="mc-icon">🔍</div>
    <div class="mc-title">Transactions</div><div class="mc-desc">Explain blocks</div></div>
  <div class="mini-card"><div class="mc-icon">🛡️</div>
    <div class="mc-title">Fraud Detection</div><div class="mc-desc">Real-time alerts</div></div>
  <div class="mini-card"><div class="mc-icon">📋</div>
    <div class="mc-title">Compliance</div><div class="mc-desc">Rule validation</div></div>
  <div class="mini-card"><div class="mc-icon">🎧</div>
    <div class="mc-title">Support</div><div class="mc-desc">Past case match</div></div>
</div>""", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────
    #  LAYOUT:
    #   Left col (1) = Suggestion panel — always visible, fixed
    #   Right col (3) = Responses stack from top
    #   Bottom — full-width HERO query box below both columns
    # ─────────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 3])

    with left_col:
        # ── Suggestion panel — all 5 always shown ─────────────
        # Used items highlighted amber, unused are clickable
        panel_html = '<div class="sugg-panel"><div class="sugg-panel-title">Most Used Queries</div>'
        for chip in ALL_SUGGESTIONS:
            is_used = chip in st.session_state.used_chips
            if is_used:
                panel_html += (
                    f'<div class="sug-item-used">'
                    f'{chip}'
                    f'<span class="freq-badge">✓ asked</span>'
                    f'</div>'
                )
        # Close panel HTML for used items display
        panel_html += '</div>'
        # We render used items as pure HTML, unused as Streamlit buttons
        # So we split: first render the panel shell + used items,
        # then render buttons for unused items inside a fresh container

        st.markdown('<div class="sugg-panel">', unsafe_allow_html=True)
        st.markdown('<div class="sugg-panel-title">Most Used Queries</div>',
                    unsafe_allow_html=True)

        for i, chip in enumerate(ALL_SUGGESTIONS):
            is_used = chip in st.session_state.used_chips
            if is_used:
                st.markdown(
                    f'<div class="sug-item-used">{chip}'
                    f'<span class="freq-badge">✓ asked</span></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown('<div class="sug-item-btn">', unsafe_allow_html=True)
                if st.button(chip, key=f"chip_{i}", use_container_width=True):
                    st.session_state.used_chips.append(chip)
                    st.session_state.submit_query = chip
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        # ── Responses — newest at top ─────────────────────────
        if st.session_state.history:
            st.markdown('<div class="resp-area">', unsafe_allow_html=True)
            for item in st.session_state.history:
                _render_card(item)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='color:#9BA5C2;font-size:.95rem;"
                "text-align:center;padding:2rem 0 .5rem;'>"
                "Ask a question below to get started</div>",
                unsafe_allow_html=True
            )

        # ── Query input — sits right below responses/prompt ───
        if live_today >= DAILY_LIMIT:
            st.markdown(
                '<div class="limit-banner">'
                '⏳ Daily Token Limit Reached — '
                f'Daily limit of {DAILY_LIMIT} searches reached. Try after 24 hours.'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            with st.form("query_form", clear_on_submit=True):
                col_q, col_b = st.columns([8, 1])
                with col_q:
                    query = st.text_input(
                        "",
                        placeholder="Ask anything about the account…",
                        label_visibility="collapsed",
                        key="main_qinput",
                    )
                with col_b:
                    submitted = st.form_submit_button(
                        "Ask 🡩", type="primary", use_container_width=True
                    )
            if submitted and query.strip():
                _process_query(query.strip(), own_id, username)
                st.rerun()

    # ── Handle chip-triggered submit ─────────────────────────
    if st.session_state.submit_query:
        q = st.session_state.submit_query
        st.session_state.submit_query = ""
        _process_query(q, own_id, username)
        st.rerun()

# ════════════════════════════════════════════════════════════
#  CORE PIPELINE
# ════════════════════════════════════════════════════════════
def _process_query(query: str, own_id: int, username: str):

    # Step 1 — name detection (bank-grade, zero-token security check)
    # ANY third-party name reference → blocked before LLM is called
    match = _detect_other_customer(query, own_id)
    if match == "BLOCKED":
        log_access_denied(username, own_id, -1, query)
        st.session_state.history.insert(
            0, _note_entry(query, "Unable to fetch the user — Try Again.")
        )
        return

    # Step 2 — cache (unlimited, no daily count)
    cached = cache_get(username, own_id, query)
    if cached:
        log_cache_hit(username, "hit")
        record_cache_hit(username)
        entry = dict(cached)
        entry["from_cache"] = True
        st.session_state.history.insert(0, entry)
        return

    # Step 3 — daily limit check
    if not _limit_ok(username):
        st.session_state.history.insert(0, _limit_entry(query))
        return

    # Step 4 — live LLM pipeline
    with st.spinner("SafeNest is thinking…"):
        try:
            intent, itokens = detect_intent(query)
            result = route(intent, query, own_id, st.session_state.logged_in_user)

            if result["access_denied"]:
                log_access_denied(username, own_id, own_id, query)
                e = _denied_entry(query, result["raw_result"])
                e["intent"] = intent
                st.session_state.history.insert(0, e)
                return

            response, t_in, t_out = format_response(query, result["raw_result"], intent)
            cost = ((itokens + t_in) / 1_000_000) * 0.59 + (t_out / 1_000_000) * 0.79

            record_usage(username, itokens + t_in, t_out)
            log_query(username, own_id, query, intent,
                      result["agent"], itokens + t_in, t_out)
            _inc_live(username)

            entry = {
                "query": query, "intent": intent,
                "agent": result["agent"],
                "raw_result": result["raw_result"],
                "response": response,
                "access_denied": False, "from_cache": False,
                "limit_hit": False, "note": False,
                "tokens_in": itokens + t_in, "tokens_out": t_out,
                "cost": cost,
            }
            cache_set(username, own_id, query, entry)
            st.session_state.history.insert(0, entry)

        except Exception as e:
            log_error(username, str(e), context="_process_query")
            st.error(f"Something went wrong: {e}")


# ════════════════════════════════════════════════════════════
#  NAME DETECTION — bank-grade security (3-pass)
#
#  Returns "BLOCKED" if ANY third-person name detected in query.
#  Returns None  if query is safely about the logged-in user only.
#  Zero tokens charged for BLOCKED queries.
#
#  Pass 1: Capitalised word not in own name         → BLOCKED
#  Pass 2: Lowercase after preposition not own name → BLOCKED
#  Pass 3: Any word matching another customer       → BLOCKED
# ════════════════════════════════════════════════════════════
def _detect_other_customer(query: str, own_id: int):
    STOP = {
        "why","was","what","when","how","the","my","is","are","do","did","can",
        "show","check","get","tell","give","find","account","transaction","loan",
        "blocked","declined","charged","card","balance","transfer","upi","limit",
        "eligibility","status","compliance","fraud","suspicious","activity",
        "bank","banking","amount","payment","this","that","about","from","for",
        "with","after","before","there","here","please","help","need","want",
        "twice","once","again","still","now","today","yesterday","last","next",
        "has","have","been","too","also","only","just","very","much","more",
        "know","tell","check","give","show","want","need","please","could","would",
        "should","their","them","they","him","her","his","its","and","but",
        "yes","not","any","all","some","each","done","make","take","your",
        "than","then","into","onto","upon","over","under","above","below","like",
        "able","same","such","both","even","most","other","through","between",
        "loan","credit","debit","payment","transfer","amount","balance","score",
        "limit","rule","record","data","info","details","history","report",
        "personal","savings","current","fixed","deposit","interest","rate",
    }
    NAME_PREP = {"of","for","about","regarding","on","by","from"}
    try:
        df = pd.read_csv(CUSTOMERS_PATH)
        own_row = df[df["customer_id"] == own_id]
        own_tokens: set = set()
        if not own_row.empty:
            own_tokens = (
                set(str(own_row.iloc[0]["name"]).lower().split())
                | {str(own_row.iloc[0]["username"]).lower()}
            )
        other_tokens: set = set()
        for _, row in df.iterrows():
            if int(row["customer_id"]) == own_id:
                continue
            for part in str(row["name"]).lower().split():
                if len(part) >= 3:
                    other_tokens.add(part)
            other_tokens.add(str(row["username"]).lower())

        q_lower     = query.lower()
        words_orig  = re.findall(r"[A-Za-z]+", query)
        words_lower = re.findall(r"[a-z]+", q_lower)

        # Pass 1 — capitalised word that matches another registered customer
        for w in words_orig:
            if (w[0].isupper() and len(w) >= 3
                    and w.lower() not in STOP
                    and w.lower() not in own_tokens
                    and w.lower() in other_tokens):
                return "BLOCKED"

        # Pass 2 — lowercase word after preposition that matches another customer
        for i, w in enumerate(words_lower):
            if w in NAME_PREP and i + 1 < len(words_lower):
                nxt = words_lower[i + 1]
                if (len(nxt) >= 3
                        and nxt not in STOP
                        and nxt not in own_tokens
                        and nxt in other_tokens):
                    return "BLOCKED"

        # Pass 3 — any word matching another registered customer
        for w in words_lower:
            if w in other_tokens:
                return "BLOCKED"

        return None
    except Exception:
        return None

# ════════════════════════════════════════════════════════════
#  ENTRY BUILDERS
# ════════════════════════════════════════════════════════════
def _denied_entry(q, msg):
    return {"query":q,"intent":"—","agent":"Authorization Guard","response":msg,
            "access_denied":True,"from_cache":False,"limit_hit":False,"note":False,
            "tokens_in":0,"tokens_out":0,"cost":0.0}
def _limit_entry(q):
    return {"query":q,"intent":"—","agent":"—",
            "response":f"Daily limit of {DAILY_LIMIT} searches reached. Try after 24 hours.",
            "access_denied":False,"from_cache":False,"limit_hit":True,"note":False,
            "tokens_in":0,"tokens_out":0,"cost":0.0}
def _note_entry(q, msg):
    return {"query":q,"intent":"—","agent":"—","response":msg,
            "access_denied":False,"from_cache":False,"limit_hit":False,"note":True,
            "tokens_in":0,"tokens_out":0,"cost":0.0}


# ════════════════════════════════════════════════════════════
#  RENDER — single response card
# ════════════════════════════════════════════════════════════
def _render_card(item: dict):
    icon, pill_cls = AGENT_META.get(item["agent"], ("🤖", "pill-agent"))
    ilbl = INTENT_LABELS.get(item["intent"], item["intent"])

    if item.get("limit_hit"):
        st.markdown(f"""
<div class="limit-card">
  <div class="limit-title">⏳ Daily Token Limit Reached</div>
  <div class="limit-body">{item['response']}</div>
</div>""", unsafe_allow_html=True)
        return

    if item.get("note"):
        st.info(f"ℹ️ {item['response']}")
        return

    if item.get("access_denied"):
        st.markdown(f"""
<div class="denied-card">
  <div class="denied-title">🚫 Access Denied</div>
  <div class="denied-body">{item['response']}</div>
</div>""", unsafe_allow_html=True)
        return

    # Normal response
    cache_badge = '<span class="pill pill-cache">⚡ Cached</span>' \
                  if item.get("from_cache") else ""
    st.markdown(f"""
<div class="resp-card">
  <div class="resp-q">▸ {item['query']}</div>
  <div class="resp-body">{item['response']}</div>
  <div class="resp-meta">
    <span class="pill {pill_cls}">{icon} {item['agent']}</span>
    <span class="pill pill-intent">🎯 {ilbl}</span>
    {cache_badge}
  </div>
</div>""", unsafe_allow_html=True)

    if not item.get("from_cache"):
        with st.expander("Debug — raw agent output"):
            st.code(item.get("raw_result", ""), language=None)


# ════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════
if not is_logged_in(st.session_state.logged_in_user):
    show_login()
elif st.session_state.logged_in_user["role"] == "admin":
    show_admin()
else:
    show_customer()
