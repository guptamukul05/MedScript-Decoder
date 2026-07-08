# app.py — MedScript Decoder Main Application

import streamlit as st

# ── Page config — must be first streamlit command ─────────────────
st.set_page_config(
    page_title="MedScript Decoder",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for premium UI ─────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #0f1117;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background: #1a1d27;
        border-right: 1px solid #2d3748;
    }

    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(79,70,229,0.4);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #e0e7ff;
        font-size: 0.95rem;
        margin: 0.5rem 0 0;
    }

    .dashboard-card {
        background: #1e2130;
        border: 1px solid #2d3748;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .medicine-card {
        background: #1e2130;
        border: 1px solid #3d4a6b;
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .medicine-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #a5b4fc;
        margin-bottom: 0.6rem;
        text-transform: capitalize;
    }
    .medicine-detail {
        font-size: 0.88rem;
        color: #cbd5e1;
        margin: 4px 0;
        line-height: 1.5;
    }
    .medicine-detail strong {
        color: #f1f5f9;
        font-weight: 600;
    }

    .timing-badge {
        display: inline-block;
        background: #312e81;
        border: 1px solid #4f46e5;
        color: #c7d2fe;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        margin: 2px;
        font-weight: 500;
    }

    .urgency-urgent {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(220,38,38,0.4);
    }
    .urgency-soon {
        background: linear-gradient(135deg, #d97706, #f59e0b);
        color: #1c1917;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(217,119,6,0.4);
    }
    .urgency-normal {
        background: linear-gradient(135deg, #059669, #10b981);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(5,150,105,0.3);
    }
    .urgency-routine {
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(2,132,199,0.3);
    }

    .value-abnormal {
        background: #2d1515;
        border: 1px solid #7f1d1d;
        border-left: 3px solid #ef4444;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .value-normal {
        background: #14291e;
        border: 1px solid #14532d;
        border-left: 3px solid #22c55e;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .value-label {
        font-size: 0.78rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
    }
    .value-number {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .value-status-high { color: #fca5a5; font-size: 0.82rem; font-weight: 600; }
    .value-status-low  { color: #fde68a; font-size: 0.82rem; font-weight: 600; }
    .value-status-ok   { color: #86efac; font-size: 0.82rem; font-weight: 600; }

    .section-header {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e2e8f0;
        padding: 0.4rem 0;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid #2d3748;
    }

    .info-tag {
        display: inline-block;
        background: #1e3a5f;
        color: #93c5fd;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        margin: 2px;
        border: 1px solid #2d5a8e;
        font-weight: 500;
    }

    .warning-box {
        background: #2d2000;
        border: 1px solid #92400e;
        border-left: 3px solid #f59e0b;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        color: #fde68a;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }

    .disclaimer {
        background: #1e2130;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        color: #94a3b8;
        font-size: 0.82rem;
        text-align: center;
        margin-top: 1.5rem;
    }

    .patient-info-card {
        background: #1a2744;
        border: 1px solid #2d4a7a;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1rem;
        color: #bfdbfe;
        font-size: 0.88rem;
    }

    [data-testid="stFileUploader"] {
        background: #1e2130;
        border: 2px dashed #4f46e5;
        border-radius: 12px;
        padding: 1rem;
    }

    .stTextArea textarea {
        background: #1e2130 !important;
        border: 1px solid #374151 !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        width: 100% !important;
        font-size: 0.95rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #1e2130;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8;
        border-radius: 8px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: #ffffff !important;
    }
    div[data-testid="stMetricValue"] {
        color: #a5b4fc !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.82rem !important;
    }
    p, label, .stMarkdown {
        color: #cbd5e1 !important;
    }
    h1, h2, h3 {
        color: #f1f5f9 !important;
    }
    .stRadio label {
        color: #cbd5e1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
import tempfile
from PIL import Image

from src.ocr_pipeline     import run_ocr_pipeline
from src.ner_pipeline     import load_ner_model, extract_entities
from src.report_generator import generate_full_report, analyze_report_values
from src.openfda_api      import get_drug_info
from src.rxnorm_api       import get_complete_drug_profile

# ── Cache expensive model loading ────────────────────────────────
@st.cache_resource
def load_models():
    return load_ner_model()

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0;'>
        <div style='font-size:2.5rem;'>🏥</div>
        <div style='color:white;font-size:1.1rem;
        font-weight:700;'>MedScript</div>
        <div style='color:rgba(255,255,255,0.4);
        font-size:0.75rem;'>Decoder v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Patient Portal Login/Register ─────────────────────────────
    from src.patient_portal import (
        init_portal_db, register_user, login_user,
        update_profile, save_medical_record,
        get_user_records, get_user_stats, delete_record
    )
    init_portal_db()

    if st.session_state.get('portal_user'):
        user = st.session_state['portal_user']

        # Logged in view
        st.markdown(f"""
        <div style='background:#1a2744;border:1px solid #2d4a7a;
        border-radius:10px;padding:10px 12px;margin-bottom:8px;'>
            <div style='color:#a5b4fc;font-size:0.85rem;
            font-weight:600;'>👤 {user['full_name']}</div>
            <div style='color:#64748b;font-size:0.75rem;'>
            {user['email']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📁 My Patient Portal",
                     key="open_portal",
                     use_container_width=True):
            st.session_state['show_portal'] = True

        if st.button("🚪 Logout",
                     key="logout_btn",
                     use_container_width=True):
            st.session_state['portal_user'] = None
            st.session_state['show_portal'] = False
            st.rerun()

    else:
        # Not logged in
        st.markdown("""
        <div style='color:rgba(255,255,255,0.6);font-size:0.82rem;
        margin-bottom:8px;'>
            🔐 Patient Portal
        </div>
        """, unsafe_allow_html=True)

        portal_action = st.radio(
            "Action",
            ["Login", "Register"],
            horizontal=True,
            key="portal_action",
            label_visibility="collapsed"
        )

        # Login method selector
        login_method = st.radio(
            "Login with",
            ["Email", "Mobile Number"],
            horizontal=True,
            key="login_method_sel"
        )

        if portal_action == "Login":
            if login_method == "Email":
                login_id = st.text_input(
                    "Email",
                    key="login_email",
                    placeholder="your@email.com"
                )
                login_type = "email"
            else:
                login_id = st.text_input(
                    "Mobile Number",
                    key="login_phone",
                    placeholder="10-digit mobile number"
                )
                login_type = "phone"

            login_pass = st.text_input(
                "Password",
                key="login_pass",
                type="password",
                placeholder="Password"
            )

            if st.button("Login", key="login_btn",
                         use_container_width=True):
                if login_id and login_pass:
                    success, user, msg = login_user(
                        login_id, login_type, login_pass
                    )
                    if success:
                        st.session_state['portal_user'] = user
                        st.session_state['show_portal'] = False
                        st.success(f"Welcome {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Enter credentials.")

        else:  # Register
            reg_name = st.text_input(
                "Full Name",
                key="reg_name",
                placeholder="Your full name"
            )

            if login_method == "Email":
                reg_id   = st.text_input(
                    "Email",
                    key="reg_email",
                    placeholder="your@email.com"
                )
                reg_type = "email"
            else:
                reg_id   = st.text_input(
                    "Mobile Number",
                    key="reg_phone",
                    placeholder="10-digit mobile number"
                )
                reg_type = "phone"

            reg_pass = st.text_input(
                "Password",
                key="reg_pass",
                type="password",
                placeholder="Min 6 characters"
            )

            # Date of birth — calendar picker
            max_dob = date.today().replace(
                year=date.today().year - 1
            )
            min_dob = date.today().replace(
                year=date.today().year - 120
            )

            reg_dob = st.date_input(
                "Date of Birth",
                value=date(2000, 1, 1),
                min_value=min_dob,
                max_value=max_dob,
                key="reg_dob"
            )

            # Show calculated age
            if reg_dob:
                from src.patient_portal import calculate_age
                calc_age = calculate_age(reg_dob.strftime("%Y-%m-%d"))
                if calc_age is not None:
                    st.markdown(f"""
                    <div style='color:#86efac;font-size:0.78rem;
                    margin-top:-8px;margin-bottom:4px;'>
                        Age: {calc_age} years
                    </div>
                    """, unsafe_allow_html=True)

            reg_gender = st.selectbox(
                "Gender",
                ["", "Male", "Female", "Other"],
                key="reg_gender"
            )
            reg_blood = st.selectbox(
                "Blood Group",
                ["", "A+", "A-", "B+", "B-",
                 "O+", "O-", "AB+", "AB-"],
                key="reg_blood"
            )

            if st.button("Register", key="reg_btn",
                         use_container_width=True):
                if reg_name and reg_id and reg_pass:
                    success, msg = register_user(
                        full_name   = reg_name,
                        login_id    = reg_id,
                        login_type  = reg_type,
                        password    = reg_pass,
                        dob_str     = reg_dob.strftime("%Y-%m-%d")
                                      if reg_dob else "",
                        gender      = reg_gender,
                        blood_group = reg_blood
                    )
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Name, contact and password required.")
    st.markdown("---")

    # Language selector
    st.markdown("""
    <div style='color:rgba(255,255,255,0.7);font-size:0.85rem;
    font-weight:600;margin-bottom:8px;'>
        🌐 Output Language
    </div>
    """, unsafe_allow_html=True)

    language_options = [
        "English", "Hindi", "Bengali", "Tamil",
        "Telugu", "Marathi", "Gujarati", "Kannada",
        "Malayalam", "Punjabi"
    ]

    selected_language = st.selectbox(
        "Select language",
        language_options,
        index=0,
        key="output_language",
        label_visibility="collapsed"
    )

    if selected_language != "English":
        st.markdown(f"""
        <div style='background:#1a2744;border:1px solid #2d4a7a;
        border-radius:6px;padding:6px 10px;
        color:#93c5fd;font-size:0.78rem;'>
            🌐 Output in {selected_language}
        </div>
        """, unsafe_allow_html=True)

    st.session_state['selected_language'] = selected_language

    st.markdown("---")
    st.markdown("""
    <div style='color:rgba(255,255,255,0.3);font-size:0.72rem;
    text-align:center;'>
        ⚠️ For informational purposes only.<br>
        Always consult a qualified doctor.
    </div>
    """, unsafe_allow_html=True)

# ── Patient Portal Page ───────────────────────────────────────────
if st.session_state.get('show_portal') and \
   st.session_state.get('portal_user'):

    user  = st.session_state['portal_user']
    stats = get_user_stats(user['id'])

    # Portal header
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#1e2130,#1a2744);
    border:1px solid #2d4a7a;border-radius:16px;
    padding:1.5rem 2rem;margin-bottom:1.5rem;'>
        <div style='display:flex;justify-content:space-between;
        align-items:center;'>
            <div>
                <div style='color:#a5b4fc;font-size:1.4rem;
                font-weight:700;'>
                    👤 {user['full_name']}
                </div>
                <div style='color:#64748b;font-size:0.85rem;
                margin-top:2px;'>{user['email']}</div>
            </div>
            <div style='text-align:right;'>
                <div style='color:#94a3b8;font-size:0.8rem;'>
                    Blood Group
                </div>
                <div style='color:#f1f5f9;font-size:1.2rem;
                font-weight:700;'>
                    {user.get('blood_group','Not set') or 'Not set'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Portal tabs
    p_tab1, p_tab2, p_tab3 = st.tabs([
        "📊 Overview",
        "📁 My Records",
        "⚙️ Profile"
    ])

    # ── Tab 1: Overview ───────────────────────────────────────────
    with p_tab1:
        st.markdown("<br>", unsafe_allow_html=True)

        # Stats cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Records",  stats['total'])
        with c2:
            st.metric("Prescriptions",  stats['prescriptions'])
        with c3:
            st.metric("Lab Reports",    stats['reports'])
        with c4:
            st.metric("Test Results",   stats['tests'])

        st.markdown("<br>", unsafe_allow_html=True)

        # Patient info card
        st.markdown("""
        <div class='section-header'>👤 Patient Information</div>
        """, unsafe_allow_html=True)

        info_cols = st.columns(3)
        fields = [
            ("Age",          user.get('age',         'Not set')),
            ("Gender",       user.get('gender',      'Not set')),
            ("Blood Group",  user.get('blood_group', 'Not set')),
            ("Phone",        user.get('phone',       'Not set')),
            ("Last Visit",   stats['last_visit']),
        ]
        for i, (label, value) in enumerate(fields):
            with info_cols[i % 3]:
                st.markdown(f"""
                <div class='dashboard-card'
                style='padding:0.8rem 1rem;'>
                    <div style='color:#64748b;font-size:0.75rem;
                    text-transform:uppercase;
                    letter-spacing:0.05em;'>
                        {label}
                    </div>
                    <div style='color:#f1f5f9;font-size:1rem;
                    font-weight:600;margin-top:2px;'>
                        {value or 'Not set'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Recent records
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class='section-header'>🕐 Recent Records</div>
        """, unsafe_allow_html=True)

        recent = get_user_records(user['id'], sort="Newest First")[:5]
        if recent:
            for rec in recent:
                type_icon = (
                    "📋" if rec['record_type'] == "Prescription" else
                    "🧪" if rec['record_type'] == "Lab Report"  else
                    "🔬"
                )
                type_color = (
                    "#a5b4fc" if rec['record_type'] == "Prescription" else
                    "#6ee7b7" if rec['record_type'] == "Lab Report"   else
                    "#fde68a"
                )
                st.markdown(f"""
                <div class='dashboard-card'
                style='padding:0.8rem 1rem;margin-bottom:6px;'>
                    <div style='display:flex;
                    justify-content:space-between;
                    align-items:center;'>
                        <div>
                            <span style='font-size:0.9rem;
                            color:{type_color};font-weight:500;'>
                                {type_icon} {rec['record_name']}
                            </span>
                            <span style='color:#64748b;
                            font-size:0.78rem;margin-left:8px;'>
                                {rec['record_type']}
                            </span>
                        </div>
                        <div style='color:#64748b;font-size:0.78rem;'>
                            📅 {rec['visit_date']}
                        </div>
                    </div>
                    <div style='color:#94a3b8;font-size:0.78rem;
                    margin-top:4px;'>
                        👨‍⚕️ {rec['doctor_name'] or 'N/A'}
                        &nbsp;|&nbsp;
                        🏥 {rec['clinic_name'] or 'N/A'}
                        &nbsp;|&nbsp;
                        📝 {rec['reason'] or 'N/A'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='color:rgba(255,255,255,0.3);
            font-size:0.9rem;text-align:center;padding:2rem;'>
                No records yet. Add your first record in My Records tab.
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: My Records ─────────────────────────────────────────
    with p_tab2:
        st.markdown("<br>", unsafe_allow_html=True)

        rec_left, rec_right = st.columns([1, 1.5], gap="large")

        with rec_left:
            st.markdown("""
            <div class='section-header'>➕ Add New Record</div>
            """, unsafe_allow_html=True)

            rec_name = st.text_input(
                "Record Name",
                placeholder="e.g. Fever Prescription Jan 2026",
                key="rec_name"
            )
            rec_type = st.selectbox(
                "Record Type",
                ["Prescription", "Lab Report", "Test Result", "Other"],
                key="rec_type"
            )
            rec_date = st.date_input(
                "Visit Date",
                value=datetime.today(),
                key="rec_date"
            )
            rec_doctor = st.text_input(
                "Doctor Name",
                placeholder="Dr. Name",
                key="rec_doctor"
            )
            rec_clinic = st.text_input(
                "Clinic / Hospital",
                placeholder="Clinic or hospital name",
                key="rec_clinic"
            )
            rec_reason = st.text_input(
                "Reason for Visit",
                placeholder="e.g. Fever, Routine checkup, Diabetes followup",
                key="rec_reason"
            )
            rec_file = st.file_uploader(
                "Upload Document (optional)",
                type=["pdf", "jpg", "jpeg", "png"],
                key="rec_file"
            )
            rec_notes = st.text_area(
                "Notes (optional)",
                placeholder="Any additional notes...",
                height=80,
                key="rec_notes"
            )

            if st.button("💾 Save Record",
                         key="save_rec_btn",
                         use_container_width=True):
                if rec_name.strip() and rec_reason.strip():
                    file_bytes = None
                    file_ext   = ".pdf"
                    if rec_file:
                        file_bytes = rec_file.getvalue()
                        file_ext   = os.path.splitext(
                            rec_file.name
                        )[1] or ".pdf"

                    save_medical_record(
                        user_id     = user['id'],
                        record_name = rec_name,
                        record_type = rec_type,
                        visit_date  = rec_date.strftime("%Y-%m-%d"),
                        doctor_name = rec_doctor,
                        clinic_name = rec_clinic,
                        reason      = rec_reason,
                        file_bytes  = file_bytes,
                        file_ext    = file_ext,
                        notes       = rec_notes
                    )
                    st.success(f"✅ {rec_name} saved successfully!")
                    st.rerun()
                else:
                    st.warning("Record name and reason are required.")

        with rec_right:
            st.markdown("""
            <div class='section-header'>🔍 Search Records</div>
            """, unsafe_allow_html=True)

            s1, s2, s3 = st.columns([2, 1.5, 1.5])
            with s1:
                search_query = st.text_input(
                    "Search",
                    placeholder="Name, doctor, reason...",
                    key="search_query",
                    label_visibility="collapsed"
                )
            with s2:
                filter_type = st.selectbox(
                    "Type",
                    ["All", "Prescription",
                     "Lab Report", "Test Result", "Other"],
                    key="filter_type",
                    label_visibility="collapsed"
                )
            with s3:
                sort_order = st.selectbox(
                    "Sort",
                    ["Newest First", "Oldest First"],
                    key="sort_order",
                    label_visibility="collapsed"
                )

            records = get_user_records(
                user['id'],
                search      = search_query,
                record_type = filter_type,
                sort        = sort_order
            )

            st.markdown(f"""
            <div style='color:#64748b;font-size:0.8rem;
            margin-bottom:8px;'>
                {len(records)} record{'s' if len(records)!=1 else ''} found
            </div>
            """, unsafe_allow_html=True)

            if not records:
                st.markdown("""
                <div style='color:rgba(255,255,255,0.3);
                font-size:0.85rem;text-align:center;padding:2rem;'>
                    No records found.
                </div>
                """, unsafe_allow_html=True)
            else:
                for rec in records:
                    type_icon = (
                        "📋" if rec['record_type'] == "Prescription" else
                        "🧪" if rec['record_type'] == "Lab Report"   else
                        "🔬" if rec['record_type'] == "Test Result"  else
                        "📄"
                    )
                    type_color = (
                        "#a5b4fc" if rec['record_type'] == "Prescription" else
                        "#6ee7b7" if rec['record_type'] == "Lab Report"   else
                        "#fde68a" if rec['record_type'] == "Test Result"  else
                        "#94a3b8"
                    )

                    with st.expander(
                        f"{type_icon} {rec['record_name']} — {rec['visit_date']}",
                        expanded=False
                    ):
                        d1, d2 = st.columns(2)
                        with d1:
                            st.markdown(f"""
                            <div style='font-size:0.83rem;
                            color:#cbd5e1;line-height:1.8;'>
                                <b style='color:#94a3b8;'>Type:</b>
                                <span style='color:{type_color};'>
                                {rec['record_type']}</span><br>
                                <b style='color:#94a3b8;'>Doctor:</b>
                                {rec['doctor_name'] or 'N/A'}<br>
                                <b style='color:#94a3b8;'>Clinic:</b>
                                {rec['clinic_name'] or 'N/A'}
                            </div>
                            """, unsafe_allow_html=True)
                        with d2:
                            st.markdown(f"""
                            <div style='font-size:0.83rem;
                            color:#cbd5e1;line-height:1.8;'>
                                <b style='color:#94a3b8;'>Date:</b>
                                {rec['visit_date']}<br>
                                <b style='color:#94a3b8;'>Reason:</b>
                                {rec['reason'] or 'N/A'}<br>
                                <b style='color:#94a3b8;'>Notes:</b>
                                {rec['notes'] or 'N/A'}
                            </div>
                            """, unsafe_allow_html=True)

                        # Action buttons
                        btn1, btn2, btn3 = st.columns(3)

                        # View/Download file
                        with btn1:
                            if rec['file_path'] and \
                               os.path.exists(rec['file_path']):
                                with open(rec['file_path'], "rb") as f:
                                    file_bytes = f.read()
                                ext = os.path.splitext(
                                    rec['file_path']
                                )[1]
                                mime = (
                                    "application/pdf"
                                    if ext == ".pdf"
                                    else "image/jpeg"
                                )
                                st.download_button(
                                    "⬇️ Download",
                                    data      = file_bytes,
                                    file_name = f"{rec['record_name']}{ext}",
                                    mime      = mime,
                                    key       = f"dl_{rec['id']}"
                                )

                        # Open in analyzer
                        with btn2:
                            if rec['file_path'] and \
                               os.path.exists(rec['file_path']):
                                if rec['record_type'] == "Prescription":
                                    if st.button(
                                        "📋 Analyze",
                                        key=f"analyze_{rec['id']}"
                                    ):
                                        with open(
                                            rec['file_path'], "rb"
                                        ) as f:
                                            file_data = f.read()
                                        st.session_state[
                                            'portal_analyze_file'
                                        ] = file_data
                                        st.session_state[
                                            'portal_analyze_type'
                                        ] = "prescription"
                                        st.session_state[
                                            'show_portal'
                                        ] = False
                                        st.rerun()

                                elif rec['record_type'] == "Lab Report":
                                    if st.button(
                                        "🧪 Analyze",
                                        key=f"analyze_{rec['id']}"
                                    ):
                                        with open(
                                            rec['file_path'], "rb"
                                        ) as f:
                                            file_data = f.read()
                                        st.session_state[
                                            'portal_analyze_file'
                                        ] = file_data
                                        st.session_state[
                                            'portal_analyze_type'
                                        ] = "report"
                                        st.session_state[
                                            'show_portal'
                                        ] = False
                                        st.rerun()

                        # Delete
                        with btn3:
                            if st.button(
                                "🗑️ Delete",
                                key=f"del_{rec['id']}"
                            ):
                                delete_record(rec['id'], user['id'])
                                st.rerun()

    # ── Tab 3: Profile ────────────────────────────────────────────
    with p_tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class='section-header'>⚙️ Edit Profile</div>
        """, unsafe_allow_html=True)

        prof_cols = st.columns(2)
        with prof_cols[0]:
            p_name = st.text_input(
                "Full Name",
                value=user.get('full_name', ''),
                key="p_name"
            )
            p_email = st.text_input(
                "Email",
                value=user.get('email', '') or '',
                key="p_email",
                placeholder="your@email.com"
            )
            p_phone = st.text_input(
                "Mobile Number",
                value=user.get('phone', '') or '',
                key="p_phone",
                placeholder="10-digit mobile number"
            )

        with prof_cols[1]:
            # DOB picker
            current_dob = user.get('dob', '')
            if current_dob:
                try:
                    default_dob = datetime.strptime(
                        current_dob, "%Y-%m-%d"
                    ).date()
                except Exception:
                    default_dob = date(2000, 1, 1)
            else:
                default_dob = date(2000, 1, 1)

            p_dob = st.date_input(
                "Date of Birth",
                value=default_dob,
                min_value=date(
                    date.today().year - 120, 1, 1
                ),
                max_value=date(
                    date.today().year - 1, 12, 31
                ),
                key="p_dob"
            )

            # Show calculated age
            if p_dob:
                calc_age = calculate_age(
                    p_dob.strftime("%Y-%m-%d")
                )
                if calc_age:
                    st.markdown(f"""
                    <div style='color:#86efac;font-size:0.82rem;'>
                        Age: {calc_age} years
                    </div>
                    """, unsafe_allow_html=True)

            gender_options = ["", "Male", "Female", "Other"]
            p_gender = st.selectbox(
                "Gender",
                gender_options,
                index=gender_options.index(
                    user.get('gender', '')
                ) if user.get('gender') in gender_options else 0,
                key="p_gender"
            )
            blood_options = [
                "", "A+", "A-", "B+", "B-",
                "O+", "O-", "AB+", "AB-"
            ]
            p_blood = st.selectbox(
                "Blood Group",
                blood_options,
                index=blood_options.index(
                    user.get('blood_group', '')
                ) if user.get('blood_group') in blood_options else 0,
                key="p_blood"
            )

        if st.button("💾 Save Profile", key="save_profile_btn"):
            # Validate email if provided
            if p_email and not is_valid_email(p_email):
                st.error("Invalid email format.")
            elif p_phone and not is_valid_phone(p_phone):
                st.error("Invalid phone number format.")
            else:
                success, new_age = update_profile(
                    user['id'], p_name,
                    p_dob.strftime("%Y-%m-%d") if p_dob else "",
                    p_gender, p_blood, p_phone, p_email
                )
                st.session_state['portal_user'].update({
                    'full_name':   p_name,
                    'dob':         p_dob.strftime("%Y-%m-%d")
                                   if p_dob else "",
                    'age':         new_age,
                    'gender':      p_gender,
                    'blood_group': p_blood,
                    'phone':       p_phone,
                    'email':       p_email
                })
                st.success("Profile updated successfully!")
                st.rerun()

# ── Main header ───────────────────────────────────────────────────
st.markdown("""
<div class='main-header'>
    <h1>🏥 MedScript Decoder</h1>
    <p>AI-powered prescription & medical report analyzer — 
    Upload your documents for instant insights</p>
</div>
""", unsafe_allow_html=True)

# ── Metric overview row ───────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Best Model", "PubMedBERT", "F1: 0.9248")
with col2:
    st.metric("Models Compared", "3", "BioBERT, PubMedBERT, ClinicalBERT")
with col3:
    st.metric("APIs Connected", "2", "OpenFDA + RxNorm")
with col4:
    st.metric("Diseases Covered", "BC5CDR", "Chemical + Disease NER")

st.markdown("<br>", unsafe_allow_html=True)

# ── Two dashboard tabs ────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋  Prescription Dashboard",
    "🧪  Medical Report Dashboard",
    "🔄  Combined Analysis",
    "📈  Report Trends"
])

# ════════════════════════════════════════════════════════════════
# DASHBOARD 1 — PRESCRIPTION
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    left, right = st.columns([1, 1], gap="large")
    
    with left:
        st.markdown("""
        <div class='dashboard-card'>
            <div class='section-header'>📤 Upload Prescription</div>
        </div>
        """, unsafe_allow_html=True)

        upload_type = st.radio(
            "Input type",
            ["Upload File (PDF / Image)", "Type or Paste Text"],
            horizontal=True,
            key="pres_input_type"
        )

        prescription_text = ""

        if upload_type == "Upload File (PDF / Image)":
            uploaded_file = st.file_uploader(
                "Upload prescription",
                type=["jpg", "jpeg", "png", "bmp", "pdf"],
                key="pres_image"
            )

            if uploaded_file:
                if uploaded_file.type != "application/pdf":
                    st.image(
                        Image.open(uploaded_file),
                        caption="Uploaded Prescription",
                        use_container_width=True
                    )
                else:
                    st.success(f"PDF uploaded: {uploaded_file.name}")

                if st.button("Extract Text", key="run_ocr"):
                    with st.spinner("Extracting text..."):
                        import tempfile
                        suffix = ".pdf" if "pdf" in uploaded_file.type else ".jpg"
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=suffix
                        ) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        extracted, pres_type = run_ocr_pipeline(tmp_path)
                        os.unlink(tmp_path)

                        st.session_state["raw_ocr_text"]   = extracted
                        st.session_state["pres_type"]      = pres_type

            # Show extracted text
            if st.session_state.get("raw_ocr_text"):
                pres_type = st.session_state.get("pres_type", "typed")

                if pres_type == "handwritten":
                    # Handwritten — show correction box
                    st.markdown("""
                    <div style='background:#1a2744;border:1px solid #2d4a7a;
                    border-radius:8px;padding:8px 12px;margin-bottom:6px;
                    color:#93c5fd;font-size:0.82rem;'>
                        ✏️ Handwritten prescription detected —
                        please review and correct extracted text
                    </div>
                    """, unsafe_allow_html=True)
                    prescription_text = st.text_area(
                        "Review extracted text",
                        value=st.session_state["raw_ocr_text"],
                        height=200,
                        key="corrected_text"
                    )
                else:
                    # Typed/PDF — use directly, no correction needed
                    st.markdown("""
                    <div style='background:#14291e;border:1px solid #14532d;
                    border-radius:8px;padding:8px 12px;margin-bottom:6px;
                    color:#86efac;font-size:0.82rem;'>
                        ✅ Typed prescription detected — extracted successfully
                    </div>
                    """, unsafe_allow_html=True)
                    prescription_text = st.session_state["raw_ocr_text"]

                    # Show preview in expander
                    with st.expander("Preview extracted text", expanded=False):
                        st.code(prescription_text, language=None)

        else:
            st.markdown("""
            <div style='background:#1a2744;border:1px solid #2d4a7a;
            border-radius:8px;padding:8px 12px;margin-bottom:8px;
            color:#93c5fd;font-size:0.82rem;'>
                💡 Type medicines clearly like:<br>
                Tab Cepodem 200mg twice daily 15 days<br>
                After breakfast and dinner
            </div>
            """, unsafe_allow_html=True)

            prescription_text = st.text_area(
                "Type or paste prescription",
                placeholder="""TAB CEPODEM 200 - 15 days
    After breakfast and dinner
    TAB PANTOCID 40 - 15 days
    After breakfast and dinner
    TAB LORFAST AM - 15 days
    After breakfast and dinner""",
                height=280,
                key="pres_text_manual"
            )

        analyze_btn = st.button(
            "Analyze Prescription",
            key="analyze_pres",
            disabled=not bool(prescription_text.strip()
                            if prescription_text else False)
        )
        
    with right:
        # Auto-load file from patient portal
        if st.session_state.get('portal_analyze_file') and \
           st.session_state.get('portal_analyze_type') == "prescription":
            st.markdown("""
            <div style='background:#14291e;border:1px solid #14532d;
            border-radius:8px;padding:8px 12px;margin-bottom:8px;
            color:#86efac;font-size:0.83rem;'>
                📋 File loaded from Patient Portal — click Analyze
            </div>
            """, unsafe_allow_html=True)
        
        if analyze_btn:
            if not prescription_text or not prescription_text.strip():
                st.error("Please upload a file and extract text, or paste prescription text first.")
            else:
                with st.spinner(""):
                    progress = st.progress(0)
                    status   = st.empty()

                    status.markdown("""
                    <div style='color:#a78bfa; font-size:0.9rem;'>
                        🧠 Extracting medical entities with PubMedBERT...
                    </div>""", unsafe_allow_html=True)
                    progress.progress(40)

                    ocr_text = prescription_text

                    ner      = load_models()
                    entities = extract_entities(ner, ocr_text)

                    status.markdown("""
                    <div style='color:#a78bfa; font-size:0.9rem;'>
                        💊 Fetching medicine information...
                    </div>""", unsafe_allow_html=True)
                    progress.progress(75)

                    report = generate_full_report(entities, ocr_text=ocr_text)

                    progress.progress(100)
                    status.markdown("""
                    <div style='color:#38ef7d; font-size:0.9rem;'>
                        ✅ Analysis complete!
                    </div>""", unsafe_allow_html=True)
                    time.sleep(0.5)
                    progress.empty()
                    status.empty()

                st.session_state['pres_report']   = report
                st.session_state['pres_entities'] = entities
                st.session_state['pres_ocr_text'] = ocr_text
                # Clear translation cache for new prescription
                for key in ['translated_report', 'translation_lang']:
                    if key in st.session_state:
                        del st.session_state[key]
                for key in ['translated_report', 'translation_lang',
                    'voice_audio_path', 'voice_spoken_text']:
                    if key in st.session_state:
                        del st.session_state[key]
                                            

                # ── Patient and Doctor Info Card ─────────────────────────────────
                patient = entities.get('patient_info', {})
                doctor  = entities.get('doctor_info', {})

                if patient or doctor:
                    info_parts = []
                    if patient.get('name'):
                        info_parts.append(f"👤 <strong>Patient:</strong> {patient['name']}")
                    if patient.get('age'):
                        info_parts.append(f"🎂 <strong>Age:</strong> {patient['age']} yrs")
                    if patient.get('gender'):
                        info_parts.append(f"⚧ <strong>Gender:</strong> {patient['gender']}")
                    if patient.get('date'):
                        info_parts.append(f"📅 <strong>Date:</strong> {patient['date']}")
                    if doctor.get('doctor_name'):
                        info_parts.append(f"👨‍⚕️ <strong>Doctor:</strong> {doctor['doctor_name']}")
                    if doctor.get('clinic'):
                        info_parts.append(f"🏥 <strong>Clinic:</strong> {doctor['clinic']}")
                    if doctor.get('reg_number'):
                        info_parts.append(f"🪪 <strong>Reg No:</strong> {doctor['reg_number']}")
                    
                    info_html = " &nbsp;|&nbsp; ".join(info_parts)
                    st.markdown(f"""
                    <div class='patient-info-card'>
                        {info_html}
                    </div>
                    """, unsafe_allow_html=True)
                
                # ── Prescription Authenticity ─────────────────────────
                from src.ner_pipeline import check_prescription_authenticity
                auth = check_prescription_authenticity(
                    st.session_state.get('pres_ocr_text', ''),
                    entities
                )

                with st.expander(
                    f"{auth['color']} Prescription Authenticity — "
                    f"{auth['text']} ({auth['percentage']}%)",
                    expanded=False
                ):
                    # Progress bar
                    st.progress(auth['percentage'] / 100)

                    st.markdown(f"""
                    <div style='color:#94a3b8;font-size:0.83rem;
                    margin-bottom:12px;'>
                        {auth['detail']}
                    </div>
                    """, unsafe_allow_html=True)

                    # Checks table
                    for check in auth['checks']:
                        status_color = (
                            "#86efac" if check['status'] == "found"   else
                            "#fde68a" if check['status'] == "invalid" else
                            "#fca5a5"
                        )
                        bg_color = (
                            "#14291e" if check['status'] == "found"   else
                            "#2d2500" if check['status'] == "invalid" else
                            "#2d1515"
                        )
                        border_color = (
                            "#14532d" if check['status'] == "found"   else
                            "#92400e" if check['status'] == "invalid" else
                            "#7f1d1d"
                        )
                        st.markdown(f"""
                        <div style='background:{bg_color};
                        border:1px solid {border_color};
                        border-radius:8px;padding:8px 12px;
                        margin-bottom:6px;display:flex;
                        justify-content:space-between;
                        align-items:center;'>
                            <span style='color:{status_color};
                            font-size:0.85rem;font-weight:500;'>
                                {check['icon']} {check['item']}
                            </span>
                            <span style='color:#94a3b8;
                            font-size:0.82rem;'>
                                {check['value']}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("""
                    <div style='color:rgba(255,255,255,0.3);
                    font-size:0.75rem;margin-top:8px;'>
                        ⚠️ Authenticity check is based on structural
                        completeness only. Always verify prescriptions
                        with a licensed pharmacist.
                    </div>
                    """, unsafe_allow_html=True)

                # ── Symptoms ──────────────────────────────────────────────────────
                if entities.get('symptoms'):
                    st.markdown(
                        "<div class='section-header'>🤒 Symptoms / Complaints</div>",
                        unsafe_allow_html=True
                    )
                    tags = " ".join([
                        f"<span class='info-tag'>{s}</span>"
                        for s in entities['symptoms']
                    ])
                    st.markdown(tags, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                        
        
        # Display results if available
        if 'pres_report' in st.session_state:
            report   = st.session_state['pres_report']
            entities = st.session_state['pres_entities']
            
            
            # ── Extracted text ────────────────────────────────────
            with st.expander("📄 Extracted Text", expanded=False):
                st.code(st.session_state.get('pres_report_text', ''), language=None)
            
            # ── Symptoms and tests ────────────────────────────────
            if entities.get('symptoms') or report.get('tests_ordered'):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("<div class='section-header'>🤒 Symptoms Detected</div>",
                                unsafe_allow_html=True)
                    if entities.get('symptoms'):
                        tags = " ".join([f"<span class='info-tag'>{s}</span>"
                                        for s in entities['symptoms']])
                        st.markdown(tags, unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:rgba(255,255,255,0.4);"
                                    "font-size:0.85rem'>None detected</span>",
                                    unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown("<div class='section-header'>🔬 Tests Ordered</div>",
                                unsafe_allow_html=True)
                    if report.get('tests_ordered'):
                        tags = " ".join([f"<span class='info-tag'>{t}</span>"
                                        for t in report['tests_ordered']])
                        st.markdown(tags, unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:rgba(255,255,255,0.4);"
                                    "font-size:0.85rem'>None detected</span>",
                                    unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ── Medicine cards ────────────────────────────────────
            st.markdown("<div class='section-header'>💊 Medicines Prescribed</div>",
                        unsafe_allow_html=True)
            if report.get('medicines'):

                # Check if translation needed
                selected_lang = st.session_state.get(
                    'selected_language', 'English'
                )
                translated = None

                if selected_lang != "English":
                    if st.session_state.get('translated_report') and \
                       st.session_state.get('translation_lang') == selected_lang:
                        translated = st.session_state['translated_report']
                    else:
                        with st.spinner(
                            f"Translating to {selected_lang}..."
                        ):
                            from src.report_generator import translate_report
                            translated = translate_report(
                                report, selected_lang
                            )
                            if translated:
                                st.session_state['translated_report'] = translated
                                st.session_state['translation_lang'] = selected_lang

                # Display medicine cards
                for idx, med in enumerate(report['medicines']):
                    # Get translated content if available
                    t_med = None
                    if translated and idx < len(
                        translated.get('medicines', [])
                    ):
                        t_med = translated['medicines'][idx]

                    timing_badges = " ".join([
                        f"<span class='timing-badge'>"
                        f"{t}</span>"
                        for t in (
                            t_med.get('timing_translated', med.get('timing', []))
                            if t_med else med.get('timing', [])
                        )
                    ])
                    brand_names = ", ".join(
                        med.get('brand_names', [])[:3]
                    ) or "N/A"

                    purpose = (
                        t_med.get('purpose_translated',
                                  med.get('purpose', 'N/A'))
                        if t_med else med.get('purpose', 'N/A')
                    )
                    warnings = (
                        t_med.get('warnings_translated',
                                  med.get('warnings', 'N/A'))
                        if t_med else med.get('warnings', 'N/A')
                    )
                    frequency = (
                        t_med.get('frequency_translated',
                                  med.get('frequency', 'N/A'))
                        if t_med else med.get('frequency', 'N/A')
                    )
                    duration = (
                        t_med.get('duration_translated',
                                  med.get('duration', 'N/A'))
                        if t_med else med.get('duration', 'N/A')
                    )
                    food_text = (
                        translated.get('take_with_food', 'Take with food')
                        if translated else 'Take with food'
                    )

                    st.markdown(f"""
                    <div class='medicine-card'>
                        <div class='medicine-name'>
                            💊 {med['name'].title()}
                            <span style='font-size:0.75rem;
                            color:#64748b;font-weight:400;'>
                            ({med.get('form','Tab')})</span>
                        </div>
                        <div class='medicine-detail'>
                            <strong>Purpose:</strong> {purpose[:150]}
                        </div>
                        <div class='medicine-detail'>
                            <strong>Dosage:</strong> {med.get('dosage','N/A')}
                            &nbsp;|&nbsp;
                            <strong>Frequency:</strong> {frequency}
                            &nbsp;|&nbsp;
                            <strong>Duration:</strong> {duration}
                        </div>
                        <div class='medicine-detail' style='margin-top:6px'>
                            <strong>Take at:</strong> {timing_badges}
                        </div>
                        <div class='medicine-detail'>
                            <strong>With food:</strong> ✅ {food_text}
                            &nbsp;|&nbsp;
                            <strong>Brand names:</strong> {brand_names}
                        </div>
                        <div class='medicine-detail'>
                            <strong>Drug class:</strong>
                            {med.get('drug_class','N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if med.get('warnings') and \
                       med['warnings'] != 'N/A':
                        st.markdown(f"""
                        <div class='warning-box'>
                            ⚠️ <strong>Warning:</strong>
                            {warnings[:150]}
                        </div>
                        """, unsafe_allow_html=True)

                # Show translated symptoms if available
                if translated and \
                   translated.get('symptoms_translated'):
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        "<div class='section-header'>"
                        f"🤒 Symptoms ({selected_lang})</div>",
                        unsafe_allow_html=True
                    )
                    tags = " ".join([
                        f"<span class='info-tag'>{s}</span>"
                        for s in translated['symptoms_translated']
                    ])
                    st.markdown(tags, unsafe_allow_html=True)

            else:
                st.markdown("""
                <div style='color:rgba(255,255,255,0.4); font-size:0.9rem;
                text-align:center; padding:2rem;'>
                    No medicines detected. Try uploading a clearer image
                    or paste the prescription text directly.
                </div>
                """, unsafe_allow_html=True)
            
            # ── Medicine Interaction Checker ──────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<div class='section-header'>"
                "💊 Medicine Interaction Checker</div>",
                unsafe_allow_html=True
            )

            # Ask if user has regular medicines
            has_regular = st.radio(
                "Do you take any other regular medicines "
                "(apart from this prescription)?",
                ["No", "Yes"],
                horizontal=True,
                key="has_regular_meds"
            )

            if has_regular == "Yes":
                st.markdown("""
                <div style='background:#1a2744;border:1px solid #2d4a7a;
                border-radius:8px;padding:8px 12px;margin:8px 0;
                color:#93c5fd;font-size:0.82rem;'>
                    💡 Enter your regular medicines one per line.
                    We will check them against your prescription medicines.
                </div>
                """, unsafe_allow_html=True)

                regular_meds_input = st.text_area(
                    "Your regular medicines",
                    placeholder="Example:\nMetformin 500mg\nAmlodipine 5mg\nThyronorm 50mcg",
                    height=120,
                    key="regular_meds_input"
                )

                check_btn = st.button(
                    "🔍 Check Interactions",
                    key="check_interactions_btn"
                )

                if check_btn and regular_meds_input.strip():
                    # Parse regular medicines
                    regular_list = [
                        re.sub(r"\d+.*$", "", line.strip()).strip()
                        for line in regular_meds_input.strip().split("\n")
                        if line.strip()
                    ]

                    # Get prescription medicines
                    pres_meds = [
                        m['name'] for m in report.get('medicines', [])
                    ]

                    # Combine all medicines
                    all_meds = pres_meds + regular_list
                    all_meds = [m for m in all_meds if m]

                    if len(all_meds) < 2:
                        st.warning(
                            "Need at least 2 medicines to check interactions."
                        )
                    else:
                        with st.spinner(
                            "Checking interactions with AI..."
                        ):
                            from src.openfda_api import \
                                check_drug_interactions
                            interactions = check_drug_interactions(
                                all_meds
                            )
                            st.session_state['interactions'] = \
                                interactions
                            st.session_state['all_meds_checked'] = \
                                all_meds

            # Display interaction results
            if st.session_state.get('interactions') is not None:
                interactions = st.session_state['interactions']
                all_meds_checked = st.session_state.get(
                    'all_meds_checked', []
                )

                st.markdown("<br>", unsafe_allow_html=True)

                # Show medicines being checked
                meds_tags = " ".join([
                    f"<span class='info-tag'>{m.title()}</span>"
                    for m in all_meds_checked
                ])
                st.markdown(
                    f"<div style='margin-bottom:10px;'>"
                    f"Checking: {meds_tags}</div>",
                    unsafe_allow_html=True
                )

                if not interactions:
                    # All clear
                    st.markdown("""
                    <div style='background:#14291e;border:1px solid
                    #14532d;border-left:4px solid #22c55e;
                    border-radius:10px;padding:14px 16px;'>
                        <div style='color:#86efac;font-size:0.95rem;
                        font-weight:600;'>
                            ✅ No significant interactions found
                        </div>
                        <div style='color:#94a3b8;font-size:0.83rem;
                        margin-top:4px;'>
                            All your medicines appear safe to take
                            together. Continue as prescribed by
                            your doctor.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    # Show interactions
                    serious  = [i for i in interactions
                                if i['severity'] == 'serious']
                    moderate = [i for i in interactions
                                if i['severity'] == 'moderate']
                    mild     = [i for i in interactions
                                if i['severity'] == 'mild']

                    # Serious first
                    if serious:
                        st.markdown("""
                        <div style='color:#fca5a5;font-size:0.85rem;
                        font-weight:600;margin-bottom:6px;'>
                            🔴 Serious Interactions — Consult Doctor
                        </div>
                        """, unsafe_allow_html=True)
                        for item in serious:
                            st.markdown(f"""
                            <div style='background:#2d1515;
                            border:1px solid #7f1d1d;
                            border-left:4px solid #ef4444;
                            border-radius:10px;padding:12px 14px;
                            margin-bottom:8px;'>
                                <div style='color:#fca5a5;
                                font-size:0.9rem;font-weight:600;'>
                                    🔴 {item['drug_a'].title()}
                                    + {item['drug_b'].title()}
                                </div>
                                <div style='color:#fecaca;
                                font-size:0.83rem;margin-top:4px;'>
                                    {item['desc']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Moderate
                    if moderate:
                        st.markdown("""
                        <div style='color:#fde68a;font-size:0.85rem;
                        font-weight:600;margin:8px 0 6px;'>
                            🟡 Moderate Interactions — Monitor Carefully
                        </div>
                        """, unsafe_allow_html=True)
                        for item in moderate:
                            st.markdown(f"""
                            <div style='background:#2d2000;
                            border:1px solid #92400e;
                            border-left:4px solid #f59e0b;
                            border-radius:10px;padding:12px 14px;
                            margin-bottom:8px;'>
                                <div style='color:#fde68a;
                                font-size:0.9rem;font-weight:600;'>
                                    🟡 {item['drug_a'].title()}
                                    + {item['drug_b'].title()}
                                </div>
                                <div style='color:#fef3c7;
                                font-size:0.83rem;margin-top:4px;'>
                                    {item['desc']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Mild
                    if mild:
                        st.markdown("""
                        <div style='color:#fed7aa;font-size:0.85rem;
                        font-weight:600;margin:8px 0 6px;'>
                            🟠 Minor Interactions — Be Aware
                        </div>
                        """, unsafe_allow_html=True)
                        for item in mild:
                            st.markdown(f"""
                            <div style='background:#2d1a00;
                            border:1px solid #9a3412;
                            border-left:4px solid #f97316;
                            border-radius:10px;padding:12px 14px;
                            margin-bottom:8px;'>
                                <div style='color:#fed7aa;
                                font-size:0.9rem;font-weight:600;'>
                                    🟠 {item['drug_a'].title()}
                                    + {item['drug_b'].title()}
                                </div>
                                <div style='color:#ffedd5;
                                font-size:0.83rem;margin-top:4px;'>
                                    {item['desc']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Disclaimer
                    st.markdown("""
                    <div style='background:rgba(255,255,255,0.03);
                    border:1px solid #374151;border-radius:8px;
                    padding:8px 12px;margin-top:8px;
                    color:#94a3b8;font-size:0.78rem;'>
                        ⚠️ These interactions are AI-generated based on
                        known pharmacological data. Always inform your
                        doctor about ALL medicines you are taking.
                        Do not stop or change any medicine without
                        consulting your doctor.
                    </div>
                    """, unsafe_allow_html=True)


            # ── Calendar Enhancement ──────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<div class='section-header'>📅 Medicine Reminders</div>",
                unsafe_allow_html=True
            )

            # Show calendar button only if medicines found
            if report.get('medicines'):
                show_calendar = st.checkbox(
                    "Add medicine schedule to my calendar",
                    key="show_calendar_option"
                )

                if show_calendar:
                    st.markdown("""
                    <div style='background:#1a2744;border:1px solid #2d4a7a;
                    border-radius:8px;padding:10px 14px;margin-bottom:10px;
                    color:#93c5fd;font-size:0.85rem;'>
                        📅 Select the date you want to START taking medicines.
                        Reminders will be created for each medicine till its end date.
                    </div>
                    """, unsafe_allow_html=True)

                    from datetime import date
                    start_date = st.date_input(
                        "Start date",
                        value=date.today(),
                        key="cal_start_date"
                    )

                    if st.button("📅 Generate Calendar File",
                                 key="generate_cal"):
                        from src.report_generator import generate_ics_calendar
                        import os

                        medicines_for_cal = report.get('medicines', [])
                        ics_content, total_events = generate_ics_calendar(
                            medicines_for_cal,
                            start_date.strftime("%Y-%m-%d")
                        )

                        # Save to outputs
                        os.makedirs("outputs", exist_ok=True)
                        ics_path = "outputs/medicine_reminders.ics"
                        with open(ics_path, "w", encoding="utf-8") as f:
                            f.write(ics_content)

                        st.success(
                            f"✅ Calendar file created with "
                            f"{total_events} reminders!"
                        )

                        # Download button
                        with open(ics_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Medicine Reminders",
                                data=f,
                                file_name="MedScript_Medicine_Reminders.ics",
                                mime="text/calendar",
                                key="download_cal"
                            )

                        # Instructions
                        st.markdown("""
                        <div style='background:#1e2130;border:1px solid #374151;
                        border-radius:10px;padding:14px 16px;margin-top:12px;'>
                            <div style='color:#e2e8f0;font-size:0.9rem;
                            font-weight:600;margin-bottom:8px;'>
                                📋 How to add to your calendar:
                            </div>
                            <div style='color:#94a3b8;font-size:0.83rem;
                            line-height:1.9;'>
                                <b style='color:#a5b4fc'>Google Calendar:</b><br>
                                1. Download the file above<br>
                                2. Open Google Calendar on your browser<br>
                                3. Click ⚙️ Settings → Import & Export → Import<br>
                                4. Select the downloaded .ics file → Import<br>
                                5. All reminders added automatically ✅<br><br>

                                <b style='color:#a5b4fc'>iPhone / iPad:</b><br>
                                1. Download the file on your phone<br>
                                2. Tap the file → It opens in Calendar automatically<br>
                                3. Tap "Add All" → Done ✅<br><br>

                                <b style='color:#a5b4fc'>Android:</b><br>
                                1. Download the file<br>
                                2. Open Google Calendar app<br>
                                3. Tap the downloaded file → Import ✅<br><br>

                                <b style='color:#a5b4fc'>Outlook:</b><br>
                                1. Download the file<br>
                                2. Double-click it → Outlook opens automatically<br>
                                3. Click "Import" → Done ✅
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='color:rgba(255,255,255,0.4);font-size:0.85rem;'>
                    No medicines detected — calendar reminders not available.
                </div>
                """, unsafe_allow_html=True)
            

            # ── Voice Output ──────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<div class='section-header'>🔊 Voice Report</div>",
                unsafe_allow_html=True
            )

            selected_lang = st.session_state.get(
                'selected_language', 'English'
            )

            st.markdown(f"""
            <div style='background:#1a2744;border:1px solid #2d4a7a;
            border-radius:8px;padding:8px 12px;margin-bottom:10px;
            color:#93c5fd;font-size:0.83rem;'>
                🔊 Listen to your medicine report in
                <strong>{selected_lang}</strong>.
                Change language from the sidebar.
            </div>
            """, unsafe_allow_html=True)

            generate_voice_btn = st.button(
                "🔊 Generate Voice Report",
                key="generate_voice"
            )

            if generate_voice_btn:
                with st.spinner(
                    f"Generating audio in {selected_lang}..."
                ):
                    try:
                        from src.report_generator import \
                            generate_voice_report

                        audio_path, spoken_text = generate_voice_report(
                            report,
                            st.session_state.get('pres_entities', {}),
                            language=selected_lang
                        )

                        st.session_state['voice_audio_path'] = audio_path
                        st.session_state['voice_spoken_text'] = spoken_text
                        st.success("✅ Audio generated!")

                    except Exception as e:
                        st.error(f"Voice generation failed: {e}")

            # Show audio player if audio exists
            if st.session_state.get('voice_audio_path'):
                audio_path = st.session_state['voice_audio_path']

                if os.path.exists(audio_path):
                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()

                    st.audio(audio_bytes, format="audio/mp3")

                    # Download button
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=audio_bytes,
                        file_name=f"medicine_report_{selected_lang}.mp3",
                        mime="audio/mp3",
                        key="download_audio"
                    )

                    # Show spoken text
                    with st.expander(
                        "📄 View spoken text", expanded=False
                    ):
                        st.markdown(f"""
                        <div style='color:#cbd5e1;font-size:0.85rem;
                        line-height:1.8;'>
                            {st.session_state.get('voice_spoken_text','')}
                        </div>
                        """, unsafe_allow_html=True)
            # ── Disclaimer ────────────────────────────────────────
            st.markdown("""
            <div class='disclaimer'>
                ⚠️ This analysis is AI-generated and for informational 
                purposes only. Always consult a qualified doctor before 
                taking any medication.
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# DASHBOARD 2 — MEDICAL REPORTS
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    
    left2, right2 = st.columns([1, 1], gap="large")
    
    with left2:
        report_file       = None
        report_text_input = ""
        st.markdown("""
        <div class='dashboard-card'>
            <div class='section-header'>📤 Upload Medical Report</div>
        </div>
        """, unsafe_allow_html=True)
        report_input_type = st.radio(
            "Input type",
            ["Upload File (PDF / Image)", "Paste Text"],
            horizontal=True,
            index=0,
            key="report_input_type"
        )
        report_text_input = ""
        if report_input_type == "Upload File (PDF / Image)":
            report_file = st.file_uploader(
                "Upload medical report (PDF or Image)",
                type=["jpg", "jpeg", "png", "bmp", "pdf"],
                key="report_image"
            )
            if report_file:
                if report_file.type == "application/pdf":
                    st.success(f"✅ PDF uploaded: {report_file.name}")
                else:
                    st.image(Image.open(report_file),
                            caption="Uploaded Report",
                            use_container_width=True)
        else:
            report_text_input = st.text_area(
                "Paste report values here",
                placeholder="""Hemoglobin: 11.2 g/dL
        Blood Sugar Fasting: 126 mg/dL
        TSH: 6.8 mIU/L
        Platelet Count: 180 thousand/uL
        Creatinine: 0.9 mg/dL""",
                height=250,
                key="report_text"
            )
        analyze_report_btn = st.button(
            "🔬  Analyze Report",
            key="analyze_report"
        )
    
    with right2:
        # Auto-load file from patient portal
        if st.session_state.get('portal_analyze_file') and \
           st.session_state.get('portal_analyze_type') == "report":
            st.markdown("""
            <div style='background:#14291e;border:1px solid #14532d;
            border-radius:8px;padding:8px 12px;margin-bottom:8px;
            color:#86efac;font-size:0.83rem;'>
                🧪 Report loaded from Patient Portal — click Analyze
            </div>
            """, unsafe_allow_html=True)
        if analyze_report_btn:
            for key in ['ai_symptoms', 'ai_diseases']:
                if key in st.session_state:
                    del st.session_state[key]
            final_report_text = ""

            if report_input_type == "Upload File (PDF / Image)":
                if report_file is not None:
                    with st.spinner("Extracting text from report..."):
                        import tempfile
                        suffix = ".pdf" if report_file.type == "application/pdf" \
                                else ".jpg"
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=suffix
                        ) as tmp:
                            tmp.write(report_file.getvalue())
                            tmp_path = tmp.name
                        final_report_text, _ = run_ocr_pipeline(tmp_path)
                        os.unlink(tmp_path)
                else:
                    st.error("Please upload a report file first.")
            else:
                final_report_text = report_text_input

            if final_report_text and final_report_text.strip():
                with st.spinner("Analyzing report values..."):
                    progress2 = st.progress(0)
                    status2   = st.empty()

                    status2.markdown("""
                    <div style='color:#a78bfa; font-size:0.9rem;'>
                        🔍 Extracting values from report...
                    </div>""", unsafe_allow_html=True)
                    progress2.progress(40)

                    abnormal, normal = analyze_report_values(final_report_text)

                    from src.report_generator import calculate_urgency
                    urgency = calculate_urgency(abnormal)

                    progress2.progress(100)
                    status2.empty()
                    progress2.empty()

                st.session_state['report_abnormal'] = abnormal
                st.session_state['report_normal']   = normal
                st.session_state['report_urgency']  = urgency
                st.session_state['report_text_raw'] = final_report_text
            elif report_file is not None or report_text_input.strip():
                st.error("Could not extract text from the uploaded file. "
                        "Try pasting the values manually.")
        # Display report results
        if st.session_state.get('report_abnormal') is not None:
            abnormal = st.session_state['report_abnormal']
            normal   = st.session_state['report_normal']

            # ── No abnormal values ────────────────────────────────
            if not abnormal:
                st.markdown("""
                <div class='urgency-normal'>
                    🟢 All Report Values Normal
                </div>
                <div style='color:rgba(255,255,255,0.5);font-size:0.85rem;
                text-align:center;margin-top:8px;'>
                    All tested parameters are within normal range.
                    Continue healthy habits and routine checkups.
                </div>
                """, unsafe_allow_html=True)

            else:
                # ── Abnormal values table ─────────────────────────
                st.markdown(
                    "<div class='section-header'>⚠️ Abnormal Values</div>",
                    unsafe_allow_html=True
                )

                import pandas as pd
                table_data = []
                for v in abnormal:
                    ref_range = ""
                    if v.get("min") and v.get("max"):
                        ref_range = f"{v['min']} - {v['max']}"
                    elif v.get("max"):
                        ref_range = f"< {v['max']}"
                    elif v.get("min"):
                        ref_range = f"> {v['min']}"

                    table_data.append({
                        "Parameter":    v["parameter"],
                        "Your Value":   f"{v['value']} {v['unit']}",
                        "Normal Range": ref_range,
                        "Status":       v["status"]
                    })

                df = pd.DataFrame(table_data)

                # Style the table
                def color_status(val):
                    if val == "HIGH":
                        return "background-color: #2d1515; color: #fca5a5; font-weight: bold"
                    elif val == "LOW":
                        return "background-color: #2d2500; color: #fde68a; font-weight: bold"
                    return ""

                styled = df.style.applymap(
                    color_status, subset=["Status"]
                ).set_properties(**{
                    "background-color": "#1e2130",
                    "color": "#e2e8f0",
                    "border": "1px solid #374151"
                })
                st.dataframe(styled, use_container_width=True,
                             hide_index=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── AI suggests possible symptoms ─────────────────
                if 'ai_symptoms' not in st.session_state:
                    with st.spinner("Analyzing your report values..."):
                        from src.report_generator import get_ai_analysis
                        ai_symptoms = get_ai_analysis(
                            abnormal, mode="symptoms"
                        )
                        st.session_state['ai_symptoms'] = ai_symptoms

                if st.session_state.get('ai_symptoms'):
                    st.markdown("""
                    <div class='section-header'>
                        🩺 Possible Symptoms Based on Your Report
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class='dashboard-card' style='color:#cbd5e1;
                    font-size:0.9rem;line-height:1.7;'>
                        {st.session_state['ai_symptoms'].replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── Ask user about symptoms ───────────────────
                    st.markdown("""
                    <div style='color:#e2e8f0;font-size:0.95rem;
                    font-weight:500;margin-bottom:8px;'>
                        Are you experiencing any of these symptoms?
                    </div>
                    """, unsafe_allow_html=True)

                    symptom_choice = st.radio(
                        "Symptom confirmation",
                        ["Yes, I have some of these symptoms",
                         "No, I have different symptoms",
                         "No symptoms at all (routine checkup)"],
                        key="symptom_choice",
                        label_visibility="collapsed"
                    )

                    # ── Branch based on choice ────────────────────
                    if symptom_choice == "Yes, I have some of these symptoms":
                        if st.button("Get Possible Conditions",
                                     key="get_diseases"):
                            with st.spinner("Analyzing..."):
                                from src.report_generator import get_ai_analysis
                                ai_diseases = get_ai_analysis(
                                    abnormal,
                                    user_symptoms="Patient confirms experiencing the suggested symptoms",
                                    mode="diseases"
                                )
                                st.session_state['ai_diseases'] = ai_diseases

                    elif symptom_choice == "No, I have different symptoms":
                        user_symptoms = st.text_area(
                            "Describe your symptoms",
                            placeholder="Example: I have been feeling very tired, "
                                        "my skin looks slightly yellow, "
                                        "I have pain in my upper right abdomen...",
                            height=100,
                            key="user_symptoms_input"
                        )
                        if st.button("Analyze My Symptoms",
                                     key="analyze_symptoms"):
                            if user_symptoms.strip() and \
                               user_symptoms.strip().lower() not in \
                               ["nil", "no", "none", "nothing"]:
                                with st.spinner("Analyzing your symptoms..."):
                                    from src.report_generator import get_ai_analysis
                                    ai_diseases = get_ai_analysis(
                                        abnormal,
                                        user_symptoms=user_symptoms,
                                        mode="diseases"
                                    )
                                    st.session_state['ai_diseases'] = ai_diseases
                            else:
                                # Nil symptoms — routine advisory
                                with st.spinner("Generating advisory..."):
                                    from src.report_generator import get_ai_analysis
                                    ai_diseases = get_ai_analysis(
                                        abnormal, mode="routine"
                                    )
                                    st.session_state['ai_diseases'] = ai_diseases

                    else:  # No symptoms — routine checkup
                        if st.button("Get Routine Advisory",
                                     key="get_routine"):
                            with st.spinner("Generating advisory..."):
                                from src.report_generator import get_ai_analysis
                                ai_diseases = get_ai_analysis(
                                    abnormal, mode="routine"
                                )
                                st.session_state['ai_diseases'] = ai_diseases

                    # ── Show AI disease/advisory output ───────────
                    if st.session_state.get('ai_diseases'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("""
                        <div class='section-header'>
                            🔬 Analysis & Recommendations
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class='dashboard-card'
                        style='color:#cbd5e1;font-size:0.88rem;line-height:1.8;'>
                            {st.session_state['ai_diseases'].replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

                    # ── Urgency ───────────────────────────────────
                    st.markdown("<br>", unsafe_allow_html=True)
                    urgency = st.session_state.get('report_urgency', {})
                    if urgency:
                        urgency_class = {
                            'urgent':  'urgency-urgent',
                            'soon':    'urgency-soon',
                            'normal':  'urgency-normal',
                            'routine': 'urgency-routine'
                        }.get(urgency.get('level', 'routine'),
                              'urgency-routine')
                        st.markdown(f"""
                        <div class='{urgency_class}'>
                            {urgency.get('color','')} {urgency.get('text','N/A')}
                        </div>
                        <div style='color:rgba(255,255,255,0.5);
                        font-size:0.8rem;text-align:center;margin-top:6px;'>
                            {urgency.get('reason','')}
                        </div>
                        """, unsafe_allow_html=True)

            # ── Disclaimer ────────────────────────────────────────
            st.markdown("""
            <div class='disclaimer'>
                ⚠️ This analysis is AI-generated and for informational
                purposes only. These are NOT diagnoses. Always consult
                a qualified doctor for proper medical interpretation.
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# DASHBOARD 3 — COMBINED ANALYSIS
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='dashboard-card'>
        <div class='section-header'>🔄 Combined Prescription + Report Analysis</div>
        <div style='color:rgba(255,255,255,0.5); font-size:0.85rem;'>
            Upload both your prescription and medical reports 
            for a complete cross-referenced analysis
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2, gap="large")
    
    with col_a:
        st.markdown(
            "<div class='section-header'>📋 Prescription</div>",
            unsafe_allow_html=True
        )
        combined_pres_text = st.text_area(
            "Paste prescription text",
            placeholder="Paste prescription text here...",
            height=180,
            key="combined_pres"
        )
    
    with col_b:
        st.markdown(
            "<div class='section-header'>🧪 Report Values</div>",
            unsafe_allow_html=True
        )
        combined_report_text = st.text_area(
            "Paste report values",
            placeholder="Paste report values here...",
            height=180,
            key="combined_report"
        )
    
    combined_btn = st.button(
        "🔄  Run Combined Analysis",
        key="combined_analyze"
    )
    
    if combined_btn:
        if not combined_pres_text and not combined_report_text:
            st.error("Please provide at least one input — "
                     "prescription text or report values.")
        else:
            with st.spinner("Running full analysis..."):
                progress3 = st.progress(0)
                
                entities = {
                    'drugs': [], 'dosages': [], 'frequencies': [],
                    'durations': [], 'symptoms': [], 'diagnoses': [],
                    'tests': []
                }
                
                if combined_pres_text:
                    progress3.progress(30)
                    ner      = load_models()
                    entities = extract_entities(ner, combined_pres_text)
                
                progress3.progress(60)
                report = generate_full_report(
                    entities,
                    ocr_text=combined_pres_text,
                    report_text=combined_report_text
                )
                progress3.progress(100)
                progress3.empty()
            
            st.session_state['combined_report'] = report
            st.session_state['combined_entities'] = entities
    
    # Display combined results
    if st.session_state.get('combined_report') and st.session_state.get('combined_entities'):
        report   = st.session_state['combined_report']
        entities = st.session_state['combined_entities']
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── Summary metrics ───────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Medicines", len(report.get('medicines', [])))
        with m2:
            st.metric("Tests Ordered", len(report.get('tests_ordered', [])))
        with m3:
            st.metric("Abnormal Values",
                      len(report['report_analysis'].get('abnormal', [])))
        with m4:
            urgency_text = report.get('urgency', {}).get('text', 'N/A')
            st.metric("Urgency", urgency_text[:15])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        res_col1, res_col2 = st.columns(2, gap="large")
        
        with res_col1:
            # Medicines
            st.markdown(
                "<div class='section-header'>💊 Medicines</div>",
                unsafe_allow_html=True
            )
            for med in report.get('medicines', []):
                timing = ", ".join(med.get('timing', ['As directed']))
                st.markdown(f"""
                <div class='medicine-card'>
                    <div class='medicine-name'>💊 {med['name'].title()}</div>
                    <div class='medicine-detail'>
                        <strong>Purpose:</strong> {med.get('purpose','N/A')[:100]}
                    </div>
                    <div class='medicine-detail'>
                        <strong>Dose:</strong> {med.get('dosage','N/A')} |
                        <strong>When:</strong> {timing}
                    </div>
                    <div class='medicine-detail'>
                        <strong>Duration:</strong> {med.get('duration','N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tests ordered
            if report.get('tests_ordered'):
                st.markdown(
                    "<div class='section-header'>🔬 Tests Ordered</div>",
                    unsafe_allow_html=True
                )
                tags = " ".join([f"<span class='info-tag'>{t}</span>"
                                for t in report['tests_ordered']])
                st.markdown(tags, unsafe_allow_html=True)
        
        with res_col2:
            # Urgency
            urgency = report.get('urgency', {})
            urgency_class = {
                'urgent':   'urgency-urgent',
                'soon':     'urgency-soon',
                'normal':   'urgency-normal',
                'routine':  'urgency-routine'
            }.get(urgency.get('level', 'normal'), 'urgency-normal')
            
            st.markdown(f"""
            <div class='{urgency_class}'>
                {urgency.get('color','')} {urgency.get('text','N/A')}
            </div>
            <div style='color:rgba(255,255,255,0.5); font-size:0.8rem;
            text-align:center; margin: 6px 0 1rem;'>
                {urgency.get('reason','')}
            </div>
            """, unsafe_allow_html=True)
            
            # Report values
            abnormal = report['report_analysis'].get('abnormal', [])
            normal   = report['report_analysis'].get('normal', [])
            
            if abnormal:
                st.markdown(
                    "<div class='section-header'>⚠️ Abnormal Values</div>",
                    unsafe_allow_html=True
                )
                for v in abnormal:
                    status_icon = '↑' if v['status'] == 'HIGH' else '↓'
                    st.markdown(f"""
                    <div class='value-abnormal'>
                        <div class='value-label'>
                            {v['parameter'].replace('_',' ').title()}
                        </div>
                        <div>
                            <span class='value-number'>
                                {v['value']} {v['unit']}
                            </span>
                            <span class='value-status-high'>
                                {status_icon} {v['status']}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            if normal:
                st.markdown(
                    "<div class='section-header'>✅ Normal Values</div>",
                    unsafe_allow_html=True
                )
                for v in normal:
                    st.markdown(f"""
                    <div class='value-normal'>
                        <div class='value-label'>
                            {v['parameter'].replace('_',' ').title()}
                        </div>
                        <span class='value-number'>
                            {v['value']} {v['unit']}
                        </span>
                        <span class='value-status-ok'> ✓ NORMAL</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Cross reference
        if report.get('tests_ordered') and combined_report_text:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<div class='section-header'>🔗 Cross Reference</div>",
                unsafe_allow_html=True
            )
            for test in report['tests_ordered']:
                found = test.lower() in combined_report_text.lower()
                icon  = "✅" if found else "❌"
                msg   = "Report uploaded" if found else "Report not uploaded"
                st.markdown(f"""
                <div class='dashboard-card' style='padding:0.7rem 1rem;'>
                    {icon} <strong>{test}</strong> — {msg}
                </div>
                """, unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("""
        <div class='disclaimer'>
            ⚠️ This analysis is AI-generated and for informational purposes 
            only. Always consult a qualified doctor for proper medical advice.
        </div>
        """, unsafe_allow_html=True)
# ════════════════════════════════════════════════════════════════
# DASHBOARD 4 — REPORT TRENDS
# ════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class='dashboard-card'>
        <div class='section-header'>📈 Report Trend Tracker</div>
        <div style='color:rgba(255,255,255,0.5);font-size:0.85rem;'>
            Upload multiple reports over time to track how your
            health values change. The system remembers your history.
        </div>
    </div>
    """, unsafe_allow_html=True)

    from src.trend_tracker import (
        save_report, get_all_patients, get_patient_reports,
        build_trend_data, delete_patient_data, init_db
    )
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    from datetime import datetime

    init_db()

    # ── Two columns layout ────────────────────────────────────────
    t4_left, t4_right = st.columns([1, 1.5], gap="large")

    with t4_left:
        st.markdown(
            "<div class='section-header'>💾 Save New Report</div>",
            unsafe_allow_html=True
        )

        # Patient name input
        patient_name_input = st.text_input(
            "Your name (used to identify your records)",
            placeholder="e.g. Vishal Gupta",
            key="trend_patient_name"
        )

        # Report date
        report_date_input = st.date_input(
            "Report date",
            value=datetime.today(),
            key="trend_report_date"
        )

        # Lab name
        lab_name_input = st.text_input(
            "Lab name (optional)",
            placeholder="e.g. Dr Lal PathLabs",
            key="trend_lab_name"
        )

        # Check if report analysis is available
        has_report = (
            st.session_state.get('report_abnormal') is not None
            and (
                len(st.session_state.get('report_abnormal', [])) > 0
                or len(st.session_state.get('report_normal', [])) > 0
            )
        )

        if has_report:
            st.markdown("""
            <div style='background:#14291e;border:1px solid #14532d;
            border-radius:8px;padding:8px 12px;margin:8px 0;
            color:#86efac;font-size:0.82rem;'>
                ✅ Report from Dashboard 2 is ready to save
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#2d2500;border:1px solid #92400e;
            border-radius:8px;padding:8px 12px;margin:8px 0;
            color:#fde68a;font-size:0.82rem;'>
                ⚠️ Go to Dashboard 2 first, upload and analyze a
                report, then come back here to save it.
            </div>
            """, unsafe_allow_html=True)

        save_btn = st.button(
            "💾 Save Report to History",
            key="save_trend_report",
            disabled=not (has_report and patient_name_input.strip())
        )

        if save_btn and has_report and patient_name_input.strip():
            abnormal = st.session_state.get('report_abnormal', [])
            normal   = st.session_state.get('report_normal', [])

            report_id = save_report(
                patient_name  = patient_name_input.strip(),
                report_date   = report_date_input.strftime("%Y-%m-%d"),
                abnormal      = abnormal,
                normal        = normal,
                lab_name      = lab_name_input.strip()
            )

            st.success(
                f"✅ Report saved for {patient_name_input.strip()} "
                f"on {report_date_input.strftime('%d %b %Y')}!"
            )
            st.session_state['trend_saved_name'] = \
                patient_name_input.strip()

        # ── Existing patients ─────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='section-header'>👥 Saved Patients</div>",
            unsafe_allow_html=True
        )
        patients = get_all_patients()
        if patients:
            for p in patients:
                reps = get_patient_reports(p['name'])
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"""
                    <div style='color:#e2e8f0;font-size:0.88rem;
                    padding:4px 0;'>
                        👤 <b>{p['name']}</b>
                        <span style='color:#64748b;font-size:0.8rem;'>
                        — {len(reps)} report{'s' if len(reps)!=1 else ''}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    if st.button("🗑️", key=f"del_{p['id']}",
                                 help=f"Delete {p['name']}"):
                        delete_patient_data(p['name'])
                        st.rerun()
        else:
            st.markdown("""
            <div style='color:rgba(255,255,255,0.3);font-size:0.85rem;'>
                No saved patients yet.
            </div>
            """, unsafe_allow_html=True)

    with t4_right:
        st.markdown(
            "<div class='section-header'>📊 View Trends</div>",
            unsafe_allow_html=True
        )

        # Patient selector
        all_patients = get_all_patients()
        if not all_patients:
            st.markdown("""
            <div style='color:rgba(255,255,255,0.4);font-size:0.9rem;
            text-align:center;padding:3rem;'>
                No reports saved yet.<br>Save a report from the left panel first.
            </div>
            """, unsafe_allow_html=True)
        else:
            patient_names = [p['name'] for p in all_patients]

            # Auto-select if just saved
            default_idx = 0
            if st.session_state.get('trend_saved_name') in patient_names:
                default_idx = patient_names.index(
                    st.session_state['trend_saved_name']
                )

            selected_patient = st.selectbox(
                "Select patient",
                patient_names,
                index=default_idx,
                key="trend_select_patient"
            )

            dates, rows = build_trend_data(selected_patient)

            if not dates or not rows:
                st.info("No data found for this patient.")
            else:
                reports_list = get_patient_reports(selected_patient)

                # ── Summary metrics ───────────────────────────────
                total_reports  = len(dates)
                total_abnormal = sum(
                    1 for r in rows if r['has_abnormal']
                )
                total_params   = len(rows)

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Reports", total_reports)
                with m2:
                    st.metric("Parameters Tracked", total_params)
                with m3:
                    st.metric("Abnormal Parameters", total_abnormal)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Trend Table ───────────────────────────────────
                st.markdown(
                    "<div class='section-header'>"
                    "📋 Complete Trend Table</div>",
                    unsafe_allow_html=True
                )

                # Build table data
                table_rows = []
                for row in rows:
                    tr = {
                        "Parameter": f"{row['test_name'].title()} "
                                     f"({row['unit']})"
                                     if row['unit']
                                     else row['test_name'].title()
                    }

                    prev_val = None
                    for date in dates:
                        date_label = datetime.strptime(
                            date, "%Y-%m-%d"
                        ).strftime("%d %b %Y")

                        val_data = row['values'].get(date)
                        if val_data is None:
                            tr[date_label] = "Not tested"
                        else:
                            val    = val_data['value']
                            status = val_data['status']
                            indicator = (
                                "🔴" if status == "HIGH" else
                                "🟡" if status == "LOW"  else
                                "🟢"
                            )
                            tr[date_label] = f"{indicator} {val}"

                    # Trend column
                    tr["Trend"] = row['trend']

                    table_rows.append(tr)

                if table_rows:
                    df_trend = pd.DataFrame(table_rows)

                    # Style the dataframe
                    st.dataframe(
                        df_trend,
                        use_container_width=True,
                        hide_index=True,
                        height=min(
                            50 + len(table_rows) * 35, 500
                        )
                    )

                # ── Trend Graphs ──────────────────────────────────
                if len(dates) >= 2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        "<div class='section-header'>"
                        "📈 Trend Graphs</div>",
                        unsafe_allow_html=True
                    )

                    # Parameter selector
                    param_options = [
                        r['test_name'].title() for r in rows
                        if sum(
                            1 for d in dates
                            if r['values'].get(d) is not None
                        ) >= 2
                    ]

                    if param_options:
                        selected_params = st.multiselect(
                            "Select parameters to plot",
                            param_options,
                            default=param_options[:4],
                            key="trend_params"
                        )

                        if selected_params:
                            # Create plotly figure
                            fig = go.Figure()

                            date_labels = [
                                datetime.strptime(
                                    d, "%Y-%m-%d"
                                ).strftime("%d %b %Y")
                                for d in dates
                            ]

                            colors = [
                                "#6366f1", "#f59e0b", "#10b981",
                                "#ef4444", "#8b5cf6", "#06b6d4",
                                "#f97316", "#84cc16"
                            ]

                            for idx, param in enumerate(selected_params):
                                # Find row for this param
                                row_data = next(
                                    (r for r in rows
                                     if r['test_name'].lower() ==
                                     param.lower()),
                                    None
                                )
                                if not row_data:
                                    continue

                                y_vals  = []
                                x_dates = []
                                for date in dates:
                                    val_data = row_data['values'].get(date)
                                    if val_data is not None:
                                        y_vals.append(val_data['value'])
                                        x_dates.append(
                                            datetime.strptime(
                                                date, "%Y-%m-%d"
                                            ).strftime("%d %b %Y")
                                        )

                                if len(y_vals) < 2:
                                    continue

                                color = colors[idx % len(colors)]

                                fig.add_trace(go.Scatter(
                                    x=x_dates,
                                    y=y_vals,
                                    mode="lines+markers",
                                    name=param,
                                    line=dict(
                                        color=color, width=2.5
                                    ),
                                    marker=dict(
                                        size=8, color=color,
                                        line=dict(
                                            color="white", width=1.5
                                        )
                                    ),
                                    hovertemplate=(
                                        f"<b>{param}</b><br>"
                                        "Date: %{x}<br>"
                                        "Value: %{y}<br>"
                                        "<extra></extra>"
                                    )
                                ))

                                # Add normal range band if available
                                first_val = next(
                                    (row_data['values'][d]
                                     for d in dates
                                     if row_data['values'].get(d)),
                                    None
                                )
                                if (first_val
                                        and first_val.get('ref_min')
                                        and first_val.get('ref_max')):
                                    fig.add_hrect(
                                        y0=first_val['ref_min'],
                                        y1=first_val['ref_max'],
                                        fillcolor=color,
                                        opacity=0.07,
                                        line_width=0,
                                        annotation_text="Normal range",
                                        annotation_position="top left"
                                    )

                            fig.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(30,33,48,0.8)",
                                font=dict(
                                    color="#e2e8f0", size=12
                                ),
                                legend=dict(
                                    bgcolor="rgba(30,33,48,0.9)",
                                    bordercolor="#374151",
                                    borderwidth=1
                                ),
                                xaxis=dict(
                                    gridcolor="#374151",
                                    tickfont=dict(color="#94a3b8")
                                ),
                                yaxis=dict(
                                    gridcolor="#374151",
                                    tickfont=dict(color="#94a3b8")
                                ),
                                hovermode="x unified",
                                height=420,
                                margin=dict(
                                    l=40, r=40, t=30, b=40
                                )
                            )

                            st.plotly_chart(
                                fig,
                                use_container_width=True
                            )

                    else:
                        st.info(
                            "Need at least 2 reports to show trends. "
                            "Save another report to see graphs."
                        )

                elif len(dates) == 1:
                    st.markdown("""
                    <div style='background:#1a2744;border:1px solid
                    #2d4a7a;border-radius:8px;padding:10px 14px;
                    color:#93c5fd;font-size:0.85rem;'>
                        📊 Save at least 2 reports to see trend graphs.
                        Upload and save another report after some time.
                    </div>
                    """, unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────
    st.markdown("""
    <div class='disclaimer'>
        ⚠️ Trend data is stored locally on this device only.
        Always consult your doctor to interpret trends in your reports.
    </div>
    """, unsafe_allow_html=True)