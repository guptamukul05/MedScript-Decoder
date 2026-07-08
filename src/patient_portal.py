# patient_portal.py
# Complete patient portal with authentication and medical records

import re
import sqlite3
import hashlib
import os
from datetime import datetime, date

DB_PATH      = "data/medscript.db"
UPLOADS_PATH = "data/patient_uploads"


# ── Database initialization ───────────────────────────────────────
def init_portal_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs(UPLOADS_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS portal_users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name    TEXT NOT NULL,
            email        TEXT UNIQUE,
            phone        TEXT UNIQUE,
            password     TEXT NOT NULL,
            dob          TEXT,
            age          INTEGER,
            gender       TEXT,
            blood_group  TEXT,
            created_at   TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            record_name   TEXT NOT NULL,
            record_type   TEXT NOT NULL,
            visit_date    TEXT NOT NULL,
            doctor_name   TEXT,
            clinic_name   TEXT,
            reason        TEXT,
            file_path     TEXT,
            notes         TEXT,
            created_at    TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES portal_users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Validation helpers ────────────────────────────────────────────
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def is_valid_phone(phone):
    # Indian mobile number — 10 digits starting with 6-9
    pattern = r"^[6-9]\d{9}$"
    return bool(re.match(pattern, phone.strip()))


def calculate_age(dob_str):
    """Calculate age from date of birth string YYYY-MM-DD"""
    try:
        dob   = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age   = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        return age
    except Exception:
        return None


# ── Password hashing ──────────────────────────────────────────────
def hash_password(password):
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt, 100000
    )
    return (salt + key).hex()


def verify_password(password, stored_hash):
    try:
        stored_bytes = bytes.fromhex(stored_hash)
        salt         = stored_bytes[:32]
        stored_key   = stored_bytes[32:]
        key          = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt, 100000
        )
        return key == stored_key
    except Exception:
        return False


# ── User registration ─────────────────────────────────────────────
def register_user(full_name, login_id, login_type,
                  password, dob_str="", gender="", blood_group=""):
    """
    login_type = 'email' or 'phone'
    login_id   = email address or phone number
    """
    init_portal_db()

    # Validate format
    if login_type == "email":
        if not is_valid_email(login_id):
            return False, "Invalid email format. Use format: name@example.com"
    else:
        if not is_valid_phone(login_id):
            return False, "Invalid phone number. Enter 10-digit Indian mobile number."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    # Calculate age from DOB
    age = None
    if dob_str:
        age = calculate_age(dob_str)
        if age is not None and age < 0:
            return False, "Invalid date of birth."
        if age is not None and age > 120:
            return False, "Invalid date of birth."

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # Check if already registered
    if login_type == "email":
        c.execute(
            "SELECT id FROM portal_users WHERE email = ?",
            (login_id.strip().lower(),)
        )
    else:
        c.execute(
            "SELECT id FROM portal_users WHERE phone = ?",
            (login_id.strip(),)
        )

    if c.fetchone():
        conn.close()
        return False, (
            "Email already registered. Please login."
            if login_type == "email"
            else "Phone number already registered. Please login."
        )

    hashed = hash_password(password)

    if login_type == "email":
        c.execute(
            "INSERT INTO portal_users "
            "(full_name, email, phone, password, dob, age, "
            "gender, blood_group, created_at) "
            "VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)",
            (full_name.strip().title(),
             login_id.strip().lower(),
             hashed, dob_str, age,
             gender, blood_group,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    else:
        c.execute(
            "INSERT INTO portal_users "
            "(full_name, email, phone, password, dob, age, "
            "gender, blood_group, created_at) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)",
            (full_name.strip().title(),
             login_id.strip(),
             hashed, dob_str, age,
             gender, blood_group,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

    conn.commit()
    conn.close()
    return True, "Registration successful! Please login."


# ── User login ────────────────────────────────────────────────────
def login_user(login_id, login_type, password):
    """
    login_type = 'email' or 'phone'
    """
    init_portal_db()

    # Validate format first
    if login_type == "email":
        if not is_valid_email(login_id):
            return False, None, "Invalid email format."
    else:
        if not is_valid_phone(login_id):
            return False, None, "Invalid phone number format."

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    if login_type == "email":
        c.execute(
            "SELECT id, full_name, password, dob, age, "
            "gender, blood_group, phone, email "
            "FROM portal_users WHERE email = ?",
            (login_id.strip().lower(),)
        )
    else:
        c.execute(
            "SELECT id, full_name, password, dob, age, "
            "gender, blood_group, phone, email "
            "FROM portal_users WHERE phone = ?",
            (login_id.strip(),)
        )

    row = c.fetchone()
    conn.close()

    if not row:
        return False, None, (
            "Email not found. Please register first."
            if login_type == "email"
            else "Phone number not found. Please register first."
        )

    if verify_password(password, row[2]):
        # Recalculate age from DOB on login (keeps age current)
        current_age = row[4]
        if row[3]:
            recalculated = calculate_age(row[3])
            if recalculated is not None:
                current_age = recalculated

        user = {
            "id":          row[0],
            "full_name":   row[1],
            "dob":         row[3],
            "age":         current_age,
            "gender":      row[5],
            "blood_group": row[6],
            "phone":       row[7],
            "email":       row[8]
        }
        return True, user, "Login successful!"
    else:
        return False, None, "Incorrect password. Please try again."


# ── Update profile ────────────────────────────────────────────────
def update_profile(user_id, full_name, dob_str,
                   gender, blood_group, phone, email):
    age = None
    if dob_str:
        age = calculate_age(dob_str)

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        "UPDATE portal_users SET full_name=?, dob=?, age=?, "
        "gender=?, blood_group=?, phone=?, email=? WHERE id=?",
        (full_name, dob_str, age,
         gender, blood_group, phone, email, user_id)
    )
    conn.commit()
    conn.close()
    return True, age


# ── Save medical record ───────────────────────────────────────────
def save_medical_record(user_id, record_name, record_type,
                        visit_date, doctor_name, clinic_name,
                        reason, file_bytes=None,
                        file_ext=".pdf", notes=""):
    init_portal_db()

    file_path = None
    if file_bytes:
        user_dir = os.path.join(UPLOADS_PATH, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w]", "_", record_name)[:30]
        filename  = f"{timestamp}_{safe_name}{file_ext}"
        file_path = os.path.join(user_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        "INSERT INTO medical_records "
        "(user_id, record_name, record_type, visit_date, "
        "doctor_name, clinic_name, reason, file_path, "
        "notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, record_name.strip(), record_type,
         visit_date, doctor_name.strip() if doctor_name else "",
         clinic_name.strip() if clinic_name else "",
         reason.strip() if reason else "",
         file_path,
         notes.strip() if notes else "",
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    record_id = c.lastrowid
    conn.commit()
    conn.close()
    return record_id


# ── Get records ───────────────────────────────────────────────────
def get_user_records(user_id, search="", record_type="All",
                     sort="Newest First"):
    conn   = sqlite3.connect(DB_PATH)
    c      = conn.cursor()
    query  = "SELECT * FROM medical_records WHERE user_id = ?"
    params = [user_id]

    if record_type != "All":
        query += " AND record_type = ?"
        params.append(record_type)

    if search.strip():
        query += (" AND (record_name LIKE ? OR doctor_name LIKE ?"
                  " OR clinic_name LIKE ? OR reason LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s, s, s])

    order  = "DESC" if sort == "Newest First" else "ASC"
    query += f" ORDER BY visit_date {order}"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    return [{
        "id":          row[0],
        "user_id":     row[1],
        "record_name": row[2],
        "record_type": row[3],
        "visit_date":  row[4],
        "doctor_name": row[5],
        "clinic_name": row[6],
        "reason":      row[7],
        "file_path":   row[8],
        "notes":       row[9],
        "created_at":  row[10]
    } for row in rows]


# ── Get stats ─────────────────────────────────────────────────────
def get_user_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute(
        "SELECT COUNT(*) FROM medical_records WHERE user_id=?",
        (user_id,)
    )
    total = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM medical_records "
        "WHERE user_id=? AND record_type='Prescription'",
        (user_id,)
    )
    prescriptions = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM medical_records "
        "WHERE user_id=? AND record_type='Lab Report'",
        (user_id,)
    )
    reports = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM medical_records "
        "WHERE user_id=? AND record_type='Test Result'",
        (user_id,)
    )
    tests = c.fetchone()[0]

    c.execute(
        "SELECT visit_date FROM medical_records "
        "WHERE user_id=? ORDER BY visit_date DESC LIMIT 1",
        (user_id,)
    )
    last_visit = c.fetchone()

    conn.close()
    return {
        "total":         total,
        "prescriptions": prescriptions,
        "reports":       reports,
        "tests":         tests,
        "last_visit":    last_visit[0] if last_visit else "No records yet"
    }


# ── Delete record ─────────────────────────────────────────────────
def delete_record(record_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        "SELECT file_path FROM medical_records "
        "WHERE id=? AND user_id=?",
        (record_id, user_id)
    )
    row = c.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        os.remove(row[0])
    c.execute(
        "DELETE FROM medical_records WHERE id=? AND user_id=?",
        (record_id, user_id)
    )
    conn.commit()
    conn.close()