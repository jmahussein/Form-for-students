# Run locally: streamlit run field_attachment_form_official.py

import streamlit as st
import pandas as pd
import os
import base64
import re



# ──── Simple app-level password protection ────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("UDSM-MBB Field Attachment – Login")
    password = st.text_input("Enter access password", type="password", key="login")
    
    if st.button("Login"):
        if password == "mbbfield_PT":   # ← CHANGE THIS to something stronger
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()



# ────────────────────────────────────────────────
# Background image + white text + custom button
# ────────────────────────────────────────────────
def add_bg_and_white_text(image_path):
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/jpeg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
            h1, h2, h3, p, label, .stMarkdown {{
                color: white !important;
            }}
            .stTextInput input, .stSelectbox select {{
                color: white !important;
                background: rgba(0,0,0,0.6) !important;
            }}
            .stSuccess, .stError, .stWarning, .stInfo {{
                color: white !important;
                background: rgba(0,0,0,0.6) !important;
                border-radius: 8px;
                padding: 12px;
            }}
            .stApp {{ background: rgba(255,255,255,0.78); border-radius: 12px; padding: 1.5rem; }}

            /* White background + black text for station dropdown */
            .stSelectbox [data-testid="stSelectbox"] > div > div {{
                background-color: white !important;
                color: black !important;
            }}
            .stSelectbox div[role="listbox"] div {{
                background-color: white !important;
                color: black !important;
            }}
            .stSelectbox div[role="listbox"] div:hover {{
                background-color: #f0f0f0 !important;
            }}

            /* Submit button: grey background like inputs + black text */
            button[kind="primary"],
            button[kind="primary"] > div {{
                background-color: rgba(0,0,0,0.6) !important;
                color: black !important;
                border: 1px solid rgba(255,255,255,0.3) !important;
                border-radius: 6px !important;
                font-weight: bold !important;
                padding: 0.7rem 1.5rem !important;
                transition: all 0.2s !important;
                min-height: 48px !important;
            }}
            button[kind="primary"]:hover,
            button[kind="primary"]:focus {{
                background-color: rgba(0,0,0,0.75) !important;   /* slightly darker on hover */
                color: black !important;
                border-color: rgba(255,255,255,0.5) !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
            }}
            button[kind="primary"]:active {{
                background-color: rgba(0,0,0,0.85) !important;
                transform: translateY(1px) !important;
            }}
            /* Force text color black even on child elements */
            button[kind="primary"] p,
            button[kind="primary"] span {{
                color: black !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning(f"Image '{image_path}' not found.")

add_bg_and_white_text("background.jpg")

# ────────────────────────────────────────────────
# File paths
# ────────────────────────────────────────────────
allowed_file  = 'allowed_students.csv'
data_file     = 'attachments.csv'
capacity_file = 'capacities.csv'

# ────────────────────────────────────────────────
# Load allowed students
# ────────────────────────────────────────────────
if not os.path.exists(allowed_file):
    st.error(f"Required file **{allowed_file}** not found.")
    st.stop()

allowed = pd.read_csv(allowed_file)

# Normalize names consistently
allowed['Name_clean'] = (
    allowed['Name']
    .astype(str)
    .str.lower()
    .str.replace(',', ' ')
    .str.replace(r'\s+', ' ', regex=True)
    .str.strip()
)

allowed['Name_words'] = allowed['Name_clean'].str.split()
allowed['Reg_norm']   = allowed['RegNumber'].astype(str).str.lower().str.replace(r'\s+', '', regex=True)

# ────────────────────────────────────────────────
# Capacities (with encoding fallback)
# ────────────────────────────────────────────────
if not os.path.exists(capacity_file):
    capacities = {
        'Station A': 5, 'Station B': 3, 'Station C': 10,
        'Station D': 8, 'Station E': 4,
    }
    pd.DataFrame.from_dict(capacities, orient='index', columns=['slots'])\
      .rename_axis('station').to_csv(capacity_file)

try:
    caps_df = pd.read_csv(capacity_file, encoding='utf-8')
except UnicodeDecodeError:
    try:
        caps_df = pd.read_csv(capacity_file, encoding='latin1')
    except UnicodeDecodeError:
        caps_df = pd.read_csv(capacity_file, encoding='cp1252')

caps = caps_df.set_index('station')['slots'].to_dict()

# ────────────────────────────────────────────────
# Load submissions
# ────────────────────────────────────────────────
if os.path.exists(data_file):
    df = pd.read_csv(data_file)
    if 'Student' in df.columns:
        df = df.rename(columns={'Student': 'Name'})
    df = df.reindex(columns=['Name', 'RegNumber', 'Station'])
else:
    df = pd.DataFrame(columns=['Name', 'RegNumber', 'Station'])

df['RegNorm'] = df['RegNumber'].astype(str).str.lower().str.replace(r'\s+', '', regex=True)

# ────────────────────────────────────────────────
# Taken & available stations
# ────────────────────────────────────────────────
taken = df['Station'].value_counts().to_dict()
available = [s for s in caps if taken.get(s, 0) < caps[s]]

# ────────────────────────────────────────────────
# App layout
# ────────────────────────────────────────────────
st.set_page_config(page_title="UDSM-MBB Field Attachment", layout="centered")

st.title("UDSM-MBB Field Attachment Station Selection")
st.markdown("**Only registered students can submit.** Use your exact registration number.")

if available:
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            name_in = st.text_input("Full Name", placeholder="e.g. Juma Hussein")
        with col2:
            reg_in = st.text_input("Registration Number", placeholder="e.g. 2025-04-00215")

        station_choice = st.selectbox("Choose Available Station", available)

        submit = st.form_submit_button("SUBMIT")

    if submit:
        name_clean = name_in.strip()
        reg_clean = reg_in.strip()

        if not name_clean:
            st.error("Full Name is required.")
        elif not reg_clean:
            st.error("Registration Number is required.")
        else:
            # Normalize entered name
            temp = name_clean.lower().replace(',', ' ')
            name_norm = re.sub(r'\s+', ' ', temp).strip()
            name_words_entered = set(name_norm.split())

            reg_norm = reg_clean.lower().replace(" ", "")

            # Check 1: registration already used?
            if reg_norm in df['RegNorm'].values:
                st.warning(f"Registration **{reg_clean}** has already been used.")
            else:
                # Check 2: name match + reg match
                found_match = False
                for idx, row in allowed.iterrows():
                    allowed_words = set(row['Name_words'])
                    if (len(name_words_entered & allowed_words) >= 2 
                        and reg_norm == row['Reg_norm']):
                        found_match = True
                        break

                if not found_match:
                    st.error(
                        "**Incorrect name or registration number.**\n"
                        "Please use the exact details from the official student list.\n"
                        "(Note: You can enter two or three names — commas are ignored.)"
                    )
                else:
                    new_row = pd.DataFrame({
                        'Name': [name_clean],
                        'RegNumber': [reg_clean],
                        'Station': [station_choice]
                    })
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(data_file, index=False)
                    st.success(
                        f"Thank you **{name_clean}** ({reg_clean})! "
                        f"Assigned to **{station_choice}**."
                    )
                    st.balloons()
else:
    st.error("All stations are currently full.")
    st.info("Contact **Dr. Mpinda** for waiting list or assistance.")

# ────────────────────────────────────────────────
# Availability display
# ────────────────────────────────────────────────
st.subheader("Current Station Availability")
for stn in sorted(caps):
    rem = caps[stn] - taken.get(stn, 0)
    status = '🟢 Open' if rem > 0 else '🔴 Full'
    st.markdown(f"**{stn}**: {rem} / {caps[stn]}  {status}")

# ────────────────────────────────────────────────
# Admin view
# ────────────────────────────────────────────────
with st.expander("Admin – View Submissions"):
    pw = st.text_input("Admin Password", type="password")
    if pw == "mbb2026":
        if not df.empty:
            st.dataframe(
                df[['Name', 'RegNumber', 'Station']].sort_values('Name'),
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Total submissions: {len(df)}")
        else:
            st.info("No submissions yet.")
    elif pw:
        st.error("Wrong password.")