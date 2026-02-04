
#Run locally:

# streamlit run field_attachment_form.py

#   import required libraries

import streamlit as st
import pandas as pd
import os
import base64

# ────────────────────────────────────────────────
# Background image + white text styling
# ────────────────────────────────────────────────
def add_bg_and_white_text(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        st.markdown(
            f"""
            <style>
            /* Background image */
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/jpeg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}

            [data-testid="stHeader"] {{
                background: rgba(0,0,0,0);
            }}

            /* Semi-transparent white overlay for content area */
            .stApp {{
                background: rgba(255, 255, 255, 0.78);
                border-radius: 12px;
                padding: 1.5rem;
            }}

            /* Force white text on main elements */
            h1, h2, h3, h4, h5, h6, .stMarkdown, p, label, div.st-emotion-cache-1wivap2 {{
                color: white !important;
            }}

            /* Success / error / warning / info messages */
            .stSuccess, .stError, .stWarning, .stInfo {{
                color: white !important;
                background: rgba(0, 0, 0, 0.5) !important;
                border-radius: 8px;
                padding: 12px;
            }}

            /* Form labels and input text */
            .stTextInput label, .stSelectbox label {{
                color: white !important;
            }}

            .stTextInput input, .stSelectbox select {{
                color: white !important;
                background: rgba(0, 0, 0, 0.6) !important;
                border: 1px solid rgba(255,255,255,0.4) !important;
            }}

            /* Station availability text */
            .stWrite {{
                color: white !important;
            }}

            /* Expander header */
            .stExpander summary {{
                color: white !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning(f"Background image '{image_path}' not found.")

# Apply background + white text
add_bg_and_white_text("background.jpg")  # ← change filename if needed

# ────────────────────────────────────────────────
# File paths
# ────────────────────────────────────────────────
data_file     = 'attachments.csv'
capacity_file = 'capacities.csv'

# ────────────────────────────────────────────────
# Create default capacities if missing
# ────────────────────────────────────────────────
if not os.path.exists(capacity_file):
    capacities = {
        'Station A': 5,
        'Station B': 3,
        'Station C': 10,
        'Station D': 8,
        'Station E': 4,
    }
    caps_df = pd.DataFrame.from_dict(capacities, orient='index', columns=['slots'])
    caps_df.index.name = 'station'
    caps_df.to_csv(capacity_file, index=True)

# Load capacities
caps_df = pd.read_csv(capacity_file)
caps = caps_df.set_index('station')['slots'].to_dict()

# ────────────────────────────────────────────────
# Load or initialize submissions
# ────────────────────────────────────────────────
if os.path.exists(data_file):
    try:
        df = pd.read_csv(data_file)
        if 'Student' in df.columns:
            df = df.rename(columns={'Student': 'Name'})
        expected_cols = ['Name', 'RegNumber', 'Station']
        df = df[[c for c in expected_cols if c in df.columns]]
    except Exception as e:
        st.error(f"Error reading attachments.csv: {e}\nStarting fresh.")
        df = pd.DataFrame(columns=['Name', 'RegNumber', 'Station'])
else:
    df = pd.DataFrame(columns=['Name', 'RegNumber', 'Station'])

# Normalize reg number for duplicate check
df['RegNorm'] = df['RegNumber'].astype(str).str.lower().str.replace(r'\s+', '', regex=True)

# ────────────────────────────────────────────────
# Calculate taken & available
# ────────────────────────────────────────────────
taken = df['Station'].value_counts().to_dict()
available = [s for s in caps if taken.get(s, 0) < caps[s]]

# ────────────────────────────────────────────────
# Main App
# ────────────────────────────────────────────────
st.set_page_config(page_title="UDSM-MBB Field Attachment", layout="centered")

st.title("UDSM-MBB Field Attachment Station Selection")
st.markdown("**One submission per student only.** Please use your correct registration number.")

if available:
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. Juma Hussein")
        with col2:
            reg = st.text_input("Registration Number", placeholder="e.g. 2025-04-00215")

        station_choice = st.selectbox("Choose Available Station", available)

        submit = st.form_submit_button("Submit My Choice")

    if submit:
        name_clean = name.strip()
        reg_clean = reg.strip()

        if not name_clean:
            st.error("Full Name is required.")
        elif not reg_clean:
            st.error("Registration Number is required.")
        else:
            reg_norm = reg_clean.lower().replace(" ", "")
            if reg_norm in df['RegNorm'].values:
                st.warning(f"Registration **{reg_clean}** already used. One entry per student only.")
            else:
                new = pd.DataFrame({
                    'Name': [name_clean],
                    'RegNumber': [reg_clean],
                    'Station': [station_choice],
                    'RegNorm': [reg_norm]
                })
                df = pd.concat([df, new], ignore_index=True)
                df.drop(columns=['RegNorm']).to_csv(data_file, index=False)
                st.success(f"Thank you **{name_clean}** ({reg_clean})! Assigned to **{station_choice}**.")
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
    icon = "🟢 Open" if rem > 0 else "🔴 Full"
    st.markdown(f"**{stn}**: {rem} slots left (of {caps[stn]}) {icon}")

# ────────────────────────────────────────────────
# Admin view
# ────────────────────────────────────────────────
with st.expander("Admin – View All Submissions"):
    pw = st.text_input("Admin Password", type="password", key="admin_pw")
    if pw == "mbb2026":  # ← Change in production!
        if not df.empty:
            st.dataframe(
                df[['Name', 'RegNumber', 'Station']].sort_values('Name'),
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Total: {len(df)} submissions")
        else:
            st.info("No submissions yet.")
    elif pw:
        st.error("Wrong password.")