import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import streamlit.components.v1 as components

# -------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------
st.set_page_config(
    page_title="WO Parts On Hold Tracker",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------------------
# REAL-TIME EMAIL TRIGGER FUNCTION
# -------------------------------------------------------------------
def send_owner_alert_email(owner_email, wo_num, parts, hold_eta, reason):
    """
    Sends a real-time caution alert email directly to the submitter's inbox.
    """
    try:
        sender_email = st.secrets["SMTP_EMAIL"]
        sender_password = st.secrets["SMTP_PASSWORD"]
    except Exception:
        return False, "Missing SMTP credentials in .streamlit/secrets.toml!"

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    subject = f"⚠️ CAUTION / ACKNOWLEDGEMENT: WO Parts On Hold [{wo_num}]"
    
    body = f"""Hello,

This is an automated system alert regarding your Work Order submission.

--------------------------------------------------
CAUTION ALERT: WORK ORDER PARTS ON HOLD
--------------------------------------------------
Work Order #: {wo_num}
Owner Email: {owner_email}
Parts Required: {parts}
Hold Reason: {reason}
Estimated Resolution (ETA): {hold_eta}

CAUTION NOTICE:
- Please monitor the ETA closely.
- If the hold ETA exceeds expectation, escalate to your regional PUDO lead immediately.

Thank you,
WO Parts Tracker Automation System
"""

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = owner_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, f"Email delivered to {owner_email}!"
    except Exception as e:
        return False, f"SMTP Error: {str(e)}"

# -------------------------------------------------------------------
# GMAIL / GOOGLE AUTHENTICATION GATEWAY (TUNNEL FRIENDLY)
# -------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# Check Streamlit OIDC user state safely
is_oidc_logged_in = False
try:
    is_oidc_logged_in = hasattr(st, "user") and getattr(st.user, "is_logged_in", False)
except Exception:
    is_oidc_logged_in = False

if not is_oidc_logged_in and not st.session_state.authenticated:
    st.markdown("""
        <div style="background-color: #111827; padding: 30px; border-radius: 16px; border: 1px solid #1F2937; max-width: 450px; margin: 30px auto 20px auto; text-align: center;">
            <h2 style="color: #F8FAFC; margin-bottom: 5px;">🔒 Security Gateway</h2>
            <p style="color: #9CA3AF; font-size: 14px; margin-bottom: 5px;">Work Order & Parts Hold Tracker</p>
            <p style="color: #6B7280; font-size: 12px;">Sign in with your Google / Gmail account to access the portal.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if hasattr(st, "login"):
            if st.button("🔴 Sign in with Google", type="primary", use_container_width=True):
                try:
                    st.login("google")
                except Exception as e:
                    st.error(f"⚠️ Google Login error: {str(e)}")

        st.divider()

        st.caption("💻 Local / Testing Mode Authentication")
        test_email = st.text_input("Enter Gmail Address for Testing", value="dontesting007@gmail.com").strip()
        if st.button("Bypass & Continue (Testing)", use_container_width=True):
            if "@" in test_email:
                st.session_state.authenticated = True
                st.session_state.user_email = test_email
                st.rerun()
            else:
                st.error("Please enter a valid email address.")

    st.stop()

current_user_email = st.user.email if is_oidc_logged_in else st.session_state.user_email

# -------------------------------------------------------------------
# DATA HANDLING
# -------------------------------------------------------------------
DATA_FILE = "tracker_data.csv"

COLUMNS = [
    "Work Order #", "Owner Email", "Parts Required", "Hold ETA Date", 
    "Hold Reason", "Detailed Notes", "PUDO Location", "FSE Name", "Tech ID", "Status", "Created At"
]

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df["Hold ETA Date"] = pd.to_datetime(df["Hold ETA Date"], format="mixed", errors="coerce")
        return df
    else:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# Session state navigation setup
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Dashboard"

params = st.query_params
if "page" in params:
    st.session_state.nav_page = params["page"]

# -------------------------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0B0F19; color: #F8FAFC; }
    section[data-testid="stSidebar"] { display: none; }

    .metric-card {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
        border: 1px solid #1F2937;
        height: 110px;
    }
    .metric-label { font-size: 13px; color: #9CA3AF; font-weight: 500; margin-bottom: 5px; }
    .metric-value-blue { font-size: 28px; font-weight: 700; color: #38BDF8; }
    .metric-value-orange { font-size: 28px; font-weight: 700; color: #FB923C; }
    .metric-value-green { font-size: 28px; font-weight: 700; color: #34D399; }
    .metric-value-red { font-size: 28px; font-weight: 700; color: #F87171; }
    
    .avg-card {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
        border-left: 4px solid #34D399;
        border-top: 1px solid #1F2937;
        border-right: 1px solid #1F2937;
        border-bottom: 1px solid #1F2937;
        height: 110px;
    }

    h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; }
    .stCaption { color: #9CA3AF !important; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# HEADER WITH USER BADGE & REAL-TIME CLOCK
# -------------------------------------------------------------------
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.markdown("<h2 style='margin-bottom: 0px;'>📦 WO Parts On Hold Tracker</h2>", unsafe_allow_html=True)
with top_col2:
    st.caption(f"👤 Logged in: **{current_user_email}**")
    if st.button("Logout", type="secondary", key="logout_btn"):
        if hasattr(st, "logout"):
            try:
                st.logout()
            except Exception:
                pass
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()

clock_html = """
<!DOCTYPE html>
<html>
<head>
<style>
.clock-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #38BDF8;
    background: #111827;
    padding: 8px 20px;
    border-radius: 20px;
    border: 1px solid #1F2937;
    width: fit-content;
    margin: 10px auto;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.clock-time { font-size: 16px; font-weight: 700; color: #34D399; }
.clock-label { font-size: 13px; color: #9CA3AF; }
</style>
</head>
<body>
<div class="clock-container">
    <span class="clock-label">⏰ System Real-Time Clock:</span>
    <span id="liveClock" class="clock-time">--:--:--</span>
    <span class="clock-label">| TAT Active Tracking Engine: <span style="color:#FB923C;">ONLINE</span></span>
</div>
<script>
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString() + " (" + now.toLocaleDateString() + ")";
    document.getElementById('liveClock').textContent = timeStr;
}
setInterval(updateClock, 1000);
updateClock();
</script>
</body>
</html>
"""
components.html(clock_html, height=55)

# -------------------------------------------------------------------
# TOP ANIMATED NAVIGATION BAR
# -------------------------------------------------------------------
pages = ["Dashboard", "Add New Case", "View All Cases", "Modify Record", "Summary"]
active_idx = pages.index(st.session_state.nav_page) if st.session_state.nav_page in pages else 0

navbar_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }}
body {{ background: transparent; display: flex; justify-content: center; padding: 5px 0; }}
.nav-wrapper {{ background-color: #1A1F2C; padding: 6px; border-radius: 14px; display: inline-flex; position: relative; border: 1px solid #2D3748; }}
.nav-item {{ color: #A0AEC0; padding: 10px 22px; font-size: 14px; font-weight: 600; border-radius: 10px; z-index: 2; transition: color 0.3s; cursor: pointer; }}
.nav-item:hover, .nav-item.active {{ color: #FFFFFF; }}
.glider {{ position: absolute; height: calc(100% - 12px); top: 6px; background: linear-gradient(135deg, #1E40AF 0%, #06B6D4 100%); border-radius: 10px; transition: all 0.35s ease; z-index: 1; }}
</style>
</head>
<body>
<div class="nav-wrapper">
    <div class="glider" id="glider"></div>
    {''.join([f'<a class="nav-item {"active" if i == active_idx else ""}" onclick="selectNav(\'{page}\', {i})">{page}</a>' for i, page in enumerate(pages)])}
</div>
<script>
const items = document.querySelectorAll('.nav-item');
const glider = document.getElementById('glider');
function positionGlider(index) {{
    const target = items[index];
    glider.style.width = target.offsetWidth + 'px';
    glider.style.transform = `translateX(${{target.offsetLeft - 6}}px)`;
}}
positionGlider({active_idx});
function selectNav(page, index) {{
    positionGlider(index);
    const url = new URL(window.parent.location);
    url.searchParams.set('page', page);
    window.parent.history.pushState({{}}, '', url);
    window.parent.location.reload();
}}
</script>
</body>
</html>
"""
components.html(navbar_html, height=65)

# -------------------------------------------------------------------
# PAGE 1: DASHBOARD
# -------------------------------------------------------------------
if st.session_state.nav_page == "Dashboard":
    st.caption("Live overview of all work order parts on hold")
    st.write("")

    m1, m2, m3, m4, m5 = st.columns(5)

    total_cnt = len(df)
    open_cnt = len(df[df["Status"] == "Active Hold"]) if not df.empty else 0
    resolved_cnt = len(df[df["Status"] == "Resolved"]) if not df.empty else 0
    cancelled_cnt = len(df[df["Status"] == "Cancelled"]) if not df.empty else 0

    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total cases</div><div class="metric-value-blue">{total_cnt}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Active Holds</div><div class="metric-value-orange">{open_cnt}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Resolved</div><div class="metric-value-green">{resolved_cnt}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cancelled Holds</div><div class="metric-value-red">{cancelled_cnt}</div></div>', unsafe_allow_html=True)
    with m5:
        st.markdown('<div class="avg-card"><div class="metric-label">Avg hold duration</div><div style="font-size: 18px; font-weight: bold; color: #34D399;">— days</div></div>', unsafe_allow_html=True)

    st.write("")

    c_left, c_right = st.columns([2.2, 1])

    with c_left:
        st.markdown("### Recent hold cases")
        if df.empty:
            st.info("No cases yet. Switch to **Add New Case** tab above to get started.")
        else:
            st.dataframe(df.tail(5), use_container_width=True, hide_index=True)

    with c_right:
        st.markdown("### Quick Actions")
        csv_data = df.to_csv(index=False).encode('utf-8') if not df.empty else ""
        st.download_button(
            label="📄 Download Excel / CSV Data",
            data=csv_data,
            file_name="wo_parts_on_hold_tracker.csv",
            mime="text/csv",
            use_container_width=True
        )

# -------------------------------------------------------------------
# PAGE 2: ADD NEW CASE
# -------------------------------------------------------------------
elif st.session_state.nav_page == "Add New Case":
    st.subheader("Add New Hold Case")
    st.caption("Enter work order details. An automated caution email will be sent directly to the owner email.")

    with st.form("add_case_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            wo_num = st.text_input("Work Order # (WO Num)*", placeholder="e.g. WO-98421").strip()
            owner_email = st.text_input("Owner Email*", value=current_user_email, disabled=True)
            parts = st.text_area("Which Parts?*", placeholder="e.g. Motherboard, 16GB RAM").strip()
            hold_eta = st.date_input("Date Till Hold (ETA)*", value=date.today())

        with col2:
            reason = st.selectbox("Reason for Hold*", [
                "Obsolescence (Obs)", 
                "Additional Parts Required", 
                "Backordered", 
                "Wrong Part Delivered"
            ])
            pudo = st.text_input("Which PUDO?*", placeholder="e.g. PUDO-Dallas").strip()
            fse_name = st.text_input("FSE Name*", placeholder="e.g. John Doe").strip()
            tech_id = st.text_input("Tech ID*", placeholder="e.g. TECH-4091").strip()
            status = st.selectbox("Status*", ["Active Hold", "Resolved", "Cancelled"])

        notes = st.text_input("Detailed Notes (Optional)", placeholder="Additional information...").strip()

        submit = st.form_submit_button("Submit Hold Entry", type="primary")

        if submit:
            if not wo_num or not owner_email or not parts or not fse_name or not tech_id or not pudo:
                st.error("❌ All fields marked with * are required.")
            elif not df.empty and wo_num.upper() in df["Work Order #"].astype(str).str.upper().values:
                st.error(f"⚠️ Work Order '{wo_num}' already exists in the tracker!")
            else:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_data = pd.DataFrame([{
                    "Work Order #": wo_num.upper(),
                    "Owner Email": owner_email,
                    "Parts Required": parts,
                    "Hold ETA Date": str(hold_eta),
                    "Hold Reason": reason,
                    "Detailed Notes": notes if notes else "None",
                    "PUDO Location": pudo,
                    "FSE Name": fse_name.title(),
                    "Tech ID": tech_id.upper(),
                    "Status": status,
                    "Created At": created_at
                }])
                df = pd.concat([df, new_data], ignore_index=True)
                save_data(df)

                # 📧 TRIGGER REAL-TIME EMAIL
                email_sent, email_msg = send_owner_alert_email(
                    owner_email=owner_email,
                    wo_num=wo_num.upper(),
                    parts=parts,
                    hold_eta=str(hold_eta),
                    reason=reason
                )

                st.success(f"✅ Work Order {wo_num.upper()} created successfully!")
                if email_sent:
                    st.info(f"📧 Real-time caution alert email delivered to **{owner_email}**!")
                else:
                    st.warning(f"⚠️ Entry saved, but mail sending failed: {email_msg}")

# -------------------------------------------------------------------
# PAGE 3: VIEW ALL CASES
# -------------------------------------------------------------------
elif st.session_state.nav_page == "View All Cases":
    st.subheader("View All Hold Cases")
    st.caption("Track work orders with real-time due date differences and alert status")

    if df.empty:
        st.info("No hold records found.")
    else:
        display_df = df.copy()

        today = pd.to_datetime(date.today())
        display_df["ETA_DT"] = pd.to_datetime(display_df["Hold ETA Date"], errors="coerce")
        display_df["Days_Diff"] = (display_df["ETA_DT"] - today).dt.days

        def generate_alert(row):
            status = str(row["Status"])
            days = row["Days_Diff"]

            if status == "Resolved":
                return "✅ COMPLETED"
            elif status == "Cancelled":
                return "⚪ CANCELLED"
            elif pd.isna(days):
                return "❓ NO ETA"
            elif days < 0:
                return f"🔴 OVERDUE ({abs(int(days))} days ago)"
            elif days == 0:
                return "🟡 DUE TODAY"
            elif days <= 2:
                return f"🟠 DUE SOON (+{int(days)} days)"
            else:
                return f"🟢 ON TRACK (+{int(days)} days)"

        display_df["Due Difference / Alert"] = display_df.apply(generate_alert, axis=1)

        active_holds = display_df[display_df["Status"] == "Active Hold"]
        overdue_count = len(active_holds[active_holds["Days_Diff"] < 0])
        due_today_count = len(active_holds[active_holds["Days_Diff"] == 0])
        due_soon_count = len(active_holds[(active_holds["Days_Diff"] > 0) & (active_holds["Days_Diff"] <= 2)])

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            if overdue_count > 0:
                st.error(f"🔴 **{overdue_count} Overdue Holds** needing urgent action!")
            else:
                st.success("✅ **0 Overdue Holds**")

        with m_col2:
            if due_today_count > 0:
                st.warning(f"🟡 **{due_today_count} Holds Due Today**")
            else:
                st.info("ℹ️ **0 Holds Due Today**")

        with m_col3:
            if due_soon_count > 0:
                st.warning(f"🟠 **{due_soon_count} Holds Due in 1–2 Days**")
            else:
                st.info("ℹ️ **0 Holds Due Soon**")

        st.write("")

        ordered_cols = [
            "Work Order #", 
            "Owner Email",
            "Hold ETA Date", 
            "Due Difference / Alert", 
            "Parts Required", 
            "Hold Reason", 
            "Detailed Notes", 
            "PUDO Location", 
            "FSE Name", 
            "Tech ID", 
            "Status"
        ]
        
        final_cols = [c for c in ordered_cols if c in display_df.columns] + [c for c in display_df.columns if c not in ordered_cols and c not in ["ETA_DT", "Days_Diff"]]

        st.dataframe(
            display_df[final_cols], 
            use_container_width=True, 
            hide_index=True
        )

# -------------------------------------------------------------------
# PAGE 4: MODIFY RECORD
# -------------------------------------------------------------------
elif st.session_state.nav_page == "Modify Record":
    st.subheader("Modify Record")
    st.caption("Double-click any field or use dropdowns to update records directly")

    if df.empty:
        st.info("No hold records available to edit.")
    else:
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active Hold", "Resolved", "Cancelled"],
                    required=True
                ),
                "Hold Reason": st.column_config.SelectboxColumn(
                    "Hold Reason",
                    options=[
                        "Obsolescence (Obs)", 
                        "Additional Parts Required", 
                        "Backordered", 
                        "Wrong Part Delivered"
                    ],
                    required=True
                )
            }
        )

        if st.button("Save Changes", type="primary"):
            save_data(edited_df)
            st.success("✅ Changes saved successfully!")

# -------------------------------------------------------------------
# PAGE 5: SUMMARY
# -------------------------------------------------------------------
elif st.session_state.nav_page == "Summary":
    st.subheader("Summary Analytics")
    if df.empty:
        st.info("No data available for summary.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Holds by Reason Category")
            st.bar_chart(df["Hold Reason"].value_counts())
        with c2:
            st.write("### Holds Managed by FSE")
            st.bar_chart(df["FSE Name"].value_counts())