# UDSM-MBB Field Attachment Station Selection

Web application for University of Dar es Salaam – Molecular Biology & Biotechnology (MBB) students to select their field attachment stations.

Students can choose from available stations based on current capacity. Only students listed in `allowed_students.csv` can successfully submit.

## Features

- Real-name & registration number verification (fuzzy name matching + exact reg. number)
- Real-time station availability & capacity tracking
- Persistent storage using CSV files
- Simple admin view with password protection
- Nice mobile-friendly layout with background image
- Prevents double submissions from the same registration number

## Live Demo

(Once deployed – replace with your actual link)  
→ https://your-username-your-repo-name.streamlit.app

## How to run locally

```bash
# Recommended: use a virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

pip install streamlit pandas

# Make sure these files exist in the same folder:
# allowed_students.csv
# capacities.csv           (will be auto-created if missing)
# attachments.csv          (will be auto-created on first submission)
# background.jpg           (optional)

streamlit run field_attachment_form_official.py

