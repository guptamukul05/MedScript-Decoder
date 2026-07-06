# patient_portal.py
# Complete patient portal with authentication and medical records

import re
import sqlite3
import hashlib
import os
import json
import shutil
from datetime import datetime
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
            email        TEXT NOT NULL UNIQUE,
            password     TEXT NOT NULL,
            age          TEXT,
            gender       TEXT,
            blood_group  TEXT,
            phone        TEXT,
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
def register_user(full_name, email, password, age="",
                  gender="", blood_group="", phone=""):
    init_portal_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # Check if email already exists
    c.execute("SELECT id FROM portal_users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "Email already registered. Please login."

    hashed = hash_password(password)
    c.execute(
        "INSERT INTO portal_users "
        "(full_name, email, password, age, gender, "
        "blood_group, phone, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (full_name.strip().title(), email.strip().lower(),
         hashed, age, gender, blood_group, phone,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return True, "Registration successful! Please login."


# ── User login ────────────────────────────────────────────────────
def login_user(email, password):
    init_portal_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute(
        "SELECT id, full_name, password, age, gender, "
        "blood_group, phone FROM portal_users WHERE email = ?",
        (email.strip().lower(),)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return False, None, "Email not found. Please register first."

    if verify_password(password, row[2]):
        user = {
            "id":          row[0],
            "full_name":   row[1],
            "email":       email,
            "age":         row[3],
            "gender":      row[4],
            "blood_group": row[5],
            "phone":       row[6]
        }
        return True, user, "Login successful!"
    else:
        return False, None, "Incorrect password. Please try again."


# ── Update profile ────────────────────────────────────────────────
def update_profile(user_id, full_name, age,
                   gender, blood_group, phone):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        "UPDATE portal_users SET full_name=?, age=?, "
        "gender=?, blood_group=?, phone=? WHERE id=?",
        (full_name, age, gender, blood_group, phone, user_id)
    )
    conn.commit()
    conn.close()
    return True


# ── Save medical record ───────────────────────────────────────────
def save_medical_record(user_id, record_name, record_type,
                        visit_date, doctor_name, clinic_name,
                        reason, file_bytes=None,
                        file_ext=".pdf", notes=""):
    init_portal_db()

    # Save file to disk
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
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    query  = "SELECT * FROM medical_records WHERE user_id = ?"
    params = [user_id]

    if record_type != "All":
        query  += " AND record_type = ?"
        params.append(record_type)

    if search.strip():
        query  += (" AND (record_name LIKE ? OR doctor_name LIKE ?"
                   " OR clinic_name LIKE ? OR reason LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s, s, s])

    order = ("DESC" if sort == "Newest First" else "ASC")
    query += f" ORDER BY visit_date {order}"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    records = []
    for row in rows:
        records.append({
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
        })
    return records


# ── Get record stats ──────────────────────────────────────────────
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

    # Get file path before deleting
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