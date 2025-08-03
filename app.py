import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="WELLSERV APP", page_icon="favicon.png", layout="wide")

# --- FAVICON SETUP ---
def set_custom_favicon(icon_path):
    with open(icon_path, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    favicon_html = f"""
    <link rel="shortcut icon" type="image/png" href="data:image/png;base64,{b64_encoded}">
    """
    st.markdown(favicon_html, unsafe_allow_html=True)

set_custom_favicon("favicon.png")

# --- HEADER ---
st.title("🧪 WellServ Patient Records")
st.subheader("🧪 July")

# --- GOOGLE SHEETS AUTHENTICATION ---
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)


# --- LOAD SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1De30TwfsBFMXEA5vqE721Db4AhCdWquNoTavWV8Dz90"
sheet = client.open_by_url(SHEET_URL)
db_ws = sheet.worksheet("Database")
notes_ws = sheet.worksheet("Doctor's Notes")

# --- LOAD DATA ---
df_db = pd.DataFrame(db_ws.get_all_records())
df_notes = pd.DataFrame(notes_ws.get_all_records())

# Normalize column names and strip cell whitespace
df_db.columns = df_db.columns.str.strip().str.upper()
df_notes.columns = df_notes.columns.str.strip().str.upper()
df_db = df_db.astype(str).applymap(lambda x: x.strip())
df_notes = df_notes.astype(str).applymap(lambda x: x.strip())

# --- SEARCH ---
search = st.text_input("🔍 Search Patient Name or ID")
st.caption("📌 For Patient ID, use: Surname + Year of Birth (e.g. `DELACRUZ1996`, no spaces)")

if search:
    search_lower = search.lower()
    filtered_db = df_db[df_db.apply(lambda row: search_lower in str(row).lower(), axis=1)]

    if not filtered_db.empty:
        st.write("🧾 **Patient Info:**")
        st.dataframe(filtered_db.reset_index(drop=True).style.hide(axis='index'))

        pid = filtered_db.iloc[0]["PATIENT ID"].upper()
        filtered_notes = df_notes[df_notes["PATIENT ID"] == pid]

        if not filtered_notes.empty:
            st.write("🩺 **Doctor's Notes & Prescriptions:**")
            filtered_notes_display = filtered_notes.reset_index(drop=True)
            filtered_notes_display.index += 1
            st.dataframe(filtered_notes_display)
        else:
            st.info("No doctor's notes found for this patient.")
    else:
        st.warning("No matching patient found.")
else:
    st.dataframe(df_db.reset_index(drop=True).style.hide(axis='index'))

# --- ADD NOTE FORM ---
st.subheader("🩺 Add Doctor's Note")

with st.form("doctor_note_form", clear_on_submit=True):
    patient_id = st.text_input("Patient ID").upper()
    st.caption("📌 Format: Surname + Year of Birth (e.g. `DELACRUZ1996`, no spaces)")
    date = st.date_input("Date of Consultation")
    doctor = st.text_input("Doctor's Name")
    notes = st.text_area("Doctor's Notes")
    prescription = st.text_area("Prescription")
    submit = st.form_submit_button("💾 Save Note")

    if submit:
        if patient_id.strip():
            new_row = [patient_id.strip(), str(date), doctor.strip(), notes.strip(), prescription.strip()]
            notes_ws.append_row(new_row)
            st.success("✅ Note successfully saved to 'Doctor's Notes' tab.")
        else:
            st.error("❌ Please enter a valid Patient ID.")