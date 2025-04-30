# Streamlit run resumeanalyzer.py

# resumeanalyzer.py
import os
import re
import streamlit as st
from dotenv import load_dotenv
import io
import secrets
import string

# Load environment variables and configure page
load_dotenv()
st.set_page_config(page_title="Smart Resume & JD Analyzer Chatbot", layout="wide")

# Initialize session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "generated_username" not in st.session_state:
    st.session_state.generated_username = ""
if "generated_password" not in st.session_state:
    st.session_state.generated_password = ""

# Import blob helpers
from utils import download_blob_to_stream, upload_file_to_blob

# -------------------------
# Helper Functions
# -------------------------

def generate_username(length=8, prefix="user"):
    """Generate a unique username not already stored in blob."""
    while True:
        random_part = ''.join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length)
        )
        candidate = f"{prefix}_{random_part}"
        try:
            download_blob_to_stream(f"security/userid/{candidate}.txt")
        except Exception:
            return candidate


def generate_password(length=12):
    """Generate a strong random password with at least one digit and one special char."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isdigit() for c in pwd)
            and any(c in string.punctuation for c in pwd)
            and len(pwd) >= 6
        ):
            return pwd

# -------------------------
# Authentication Forms
# -------------------------

def login_form():
    with st.sidebar.form("login_form"):
        st.subheader("🔒 Login")
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
        if submitted:
            # Validate input lengths and patterns
            if len(user_id) < 5:
                st.sidebar.error("User ID must be at least 5 characters.")
                return
            if len(password) < 6 or not re.search(r"\d", password) or not re.search(r"\W", password):
                st.sidebar.error("Password must be ≥6 chars, include a number and a special character.")
                return
            # Attempt to fetch stored creds
            try:
                id_blob = download_blob_to_stream(f"security/userid/{user_id}.txt")
                pwd_blob = download_blob_to_stream(f"security/password/{user_id}.txt")
                stored_id = id_blob.read().decode().strip()
                stored_pw = pwd_blob.read().decode().strip()
            except Exception:
                st.sidebar.error("Invalid credentials.")
                return
            # Compare credentials
            if stored_id == user_id and stored_pw == password:
                st.session_state.logged_in = True
            else:
                st.sidebar.error("Invalid credentials.")


def signup_form():
    st.sidebar.subheader("🆕 Create Account")
    # Suggest username and password
    if st.sidebar.button("Suggest Username"):
        st.session_state.generated_username = generate_username()
    if st.sidebar.button("Suggest Password"):
        st.session_state.generated_password = generate_password()
    # Display suggestions
    if st.session_state.generated_username:
        st.sidebar.info(f"Suggested Username: {st.session_state.generated_username}")
    if st.session_state.generated_password:
        st.sidebar.info(f"Suggested Password: {st.session_state.generated_password}")
    with st.sidebar.form("signup_form"):
        new_user = st.text_input(
            "Choose User ID",
            value=st.session_state.generated_username,
            key="new_user_input"
        )
        pwd = st.text_input(
            "Choose Password",
            type="password",
            value=st.session_state.generated_password,
            key="pwd_input"
        )
        confirm = st.text_input(
            "Confirm Password",
            type="password",
            value=st.session_state.generated_password,
            key="confirm_input"
        )
        submitted = st.form_submit_button("Sign up")
        if submitted:
            # Validate ID and password
            if len(new_user) < 5:
                st.sidebar.error("User ID must be at least 5 characters.")
                return
            if len(pwd) < 6 or not re.search(r"\d", pwd) or not re.search(r"\W", pwd):
                st.sidebar.error("Password must be ≥6 chars, include a number and a special character.")
                return
            if pwd != confirm:
                st.sidebar.error("Passwords do not match.")
                return
            # Ensure uniqueness
            try:
                download_blob_to_stream(f"security/userid/{new_user}.txt")
                st.sidebar.error("User ID already exists. Please choose another.")
                return
            except Exception:
                pass
            # Upload new credentials
            id_bytes = io.BytesIO(new_user.encode())
            id_bytes.name = f"{new_user}.txt"
            upload_file_to_blob(id_bytes, "security/userid")
            pwd_bytes = io.BytesIO(pwd.encode())
            pwd_bytes.name = f"{new_user}.txt"
            upload_file_to_blob(pwd_bytes, "security/password")
            st.sidebar.success("Account created! You are now logged in.")
            st.session_state.logged_in = True

# -------------------------
# Authentication Gate
# -------------------------

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Authentication", ["Login", "Sign up"])
    if auth_mode == "Login":
        login_form()
    else:
        signup_form()
else:
    # -------------------------
    # Main Resume Analyzer Interface
    # -------------------------
    from resumebot import run_smart_resume_analyzer
    from resumebotai import run_ai_resume_analyzer

    st.sidebar.title("Resume Analyzer Options")
    model_type = st.sidebar.radio(
        "Select your model:",
        ["Smart Resume Analyzer", "AI Resume Analyzer"],
        key="model_type_radio"
    )
    st.sidebar.markdown(f"**Selected Model:** {model_type}")

    if model_type == "Smart Resume Analyzer":
        run_smart_resume_analyzer()
    else:
        run_ai_resume_analyzer()



