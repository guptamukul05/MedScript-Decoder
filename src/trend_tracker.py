# trend_tracker.py
# SQLite-based report trend tracking

import sqlite3
import json
import os
import re
from datetime import datetime

DB_PATH = "data/medscript.db"

# ── Test name synonym mapping ─────────────────────────────────────
SYNONYMS = {
    # Liver
    "alt/sgpt":         ["alt", "sgpt", "alt (sgpt)", "alt/sgpt",
                         "alanine aminotransferase", "alt(sgpt)"],
    "ast/sgot":         ["ast", "sgot", "ast (sgot)", "ast/sgot",
                         "aspartate aminotransferase", "ast(sgot)"],
    "bilirubin total":  ["bilirubin total", "total bilirubin",
                         "t. bilirubin", "tbil"],
    "bilirubin direct": ["bilirubin direct", "direct bilirubin",
                         "d. bilirubin", "dbil", "conjugated bilirubin"],
    "bilirubin indirect":["bilirubin indirect", "indirect bilirubin",
                          "i. bilirubin", "ibil"],
    "ggtp":             ["ggtp", "ggt", "gamma gt",
                         "gamma glutamyl transferase"],
    "alp":              ["alp", "alkaline phosphatase",
                         "alkaline phosphatase (alp)"],
    # Kidney
    "creatinine":       ["creatinine", "serum creatinine", "s. creatinine"],
    "urea":             ["urea", "blood urea", "serum urea"],
    "uric acid":        ["uric acid", "serum uric acid", "s. uric acid"],
    "bun":              ["bun", "urea nitrogen blood",
                         "blood urea nitrogen"],
    # Blood count
    "hemoglobin":       ["hemoglobin", "hb", "hgb", "haemoglobin"],
    "pcv":              ["pcv", "packed cell volume", "hematocrit", "hct"],
    "rbc count":        ["rbc count", "rbc", "red blood cell count",
                         "red cell count"],
    "wbc/tlc":          ["wbc", "tlc", "total leukocyte count",
                         "total wbc", "total leucocyte count (tlc)",
                         "total leukocyte count (tlc)"],
    "platelet count":   ["platelet count", "platelets", "plt",
                         "thrombocyte count"],
    "rdw":              ["rdw", "red cell distribution width",
                         "red cell distribution width (rdw)"],
    "mcv":              ["mcv", "mean corpuscular volume"],
    "mch":              ["mch", "mean corpuscular hemoglobin"],
    "mchc":             ["mchc", "mean corpuscular hemoglobin concentration"],
    # Sugar
    "blood sugar fasting": ["fbs", "fasting blood sugar",
                            "blood sugar fasting", "glucose fasting",
                            "fasting glucose"],
    "blood sugar pp":   ["ppbs", "pp blood sugar", "post prandial",
                         "blood sugar pp", "glucose pp"],
    "hba1c":            ["hba1c", "glycated hemoglobin", "glycohemoglobin",
                         "hemoglobin a1c"],
    # Thyroid
    "tsh":              ["tsh", "thyroid stimulating hormone",
                         "tsh ultrasensitive",
                         "tsh (thyroid stimulating hormone) ultrasensitive, serum"],
    # Lipids
    "cholesterol":      ["cholesterol", "total cholesterol",
                         "serum cholesterol"],
    "triglycerides":    ["triglycerides", "tgl", "serum triglycerides"],
    "hdl":              ["hdl", "hdl cholesterol", "good cholesterol"],
    "ldl":              ["ldl", "ldl cholesterol", "bad cholesterol"],
    # Electrolytes
    "sodium":           ["sodium", "na", "serum sodium", "s. sodium"],
    "potassium":        ["potassium", "k", "serum potassium", "s. potassium"],
    "chloride":         ["chloride", "cl", "serum chloride"],
    # Others
    "ige":              ["ige", "immunoglobulin ige", "total ige",
                         "immunoglobulin ige (clia)"],
    "esr":              ["esr", "e.s.r.", "erythrocyte sedimentation rate"],
    "vitamin d":        ["vitamin d", "vit d", "25-oh vitamin d",
                         "vitamin d3", "25 hydroxy vitamin d"],
    "vitamin b12":      ["vitamin b12", "vit b12", "cyanocobalamin",
                         "cobalamin"],
}

# Build reverse lookup
REVERSE_SYNONYMS = {}
for standard, variants in SYNONYMS.items():
    for v in variants:
        REVERSE_SYNONYMS[v.lower().strip()] = standard


def normalize_test_name(name):
    """Convert any test name variant to standard form."""
    key = name.lower().strip()
    # Direct lookup
    if key in REVERSE_SYNONYMS:
        return REVERSE_SYNONYMS[key]
    # Partial match
    for variant, standard in REVERSE_SYNONYMS.items():
        if variant in key or key in variant:
            return standard
    # Return cleaned original
    return name.strip().title()


# ── Database setup ────────────────────────────────────────────────
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL UNIQUE,
            created   TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   INTEGER NOT NULL,
            report_date  TEXT NOT NULL,
            lab_name     TEXT,
            uploaded_at  TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            test_name   TEXT NOT NULL,
            std_name    TEXT NOT NULL,
            value       REAL NOT NULL,
            unit        TEXT,
            ref_min     REAL,
            ref_max     REAL,
            status      TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Save report ───────────────────────────────────────────────────
def save_report(patient_name, report_date, abnormal,
                normal, lab_name=""):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # Get or create patient
    c.execute("SELECT id FROM patients WHERE LOWER(name) = LOWER(?)",
              (patient_name,))
    row = c.fetchone()
    if row:
        patient_id = row[0]
    else:
        c.execute(
            "INSERT INTO patients (name, created) VALUES (?, ?)",
            (patient_name.strip().title(),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        patient_id = c.lastrowid

    # Create report entry
    c.execute(
        "INSERT INTO reports (patient_id, report_date, lab_name, uploaded_at)"
        " VALUES (?, ?, ?, ?)",
        (patient_id, report_date, lab_name,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    report_id = c.lastrowid

    # Save all test results
    all_values = abnormal + normal
    for v in all_values:
        std_name = normalize_test_name(v["parameter"])
        c.execute(
            "INSERT INTO test_results "
            "(report_id, test_name, std_name, value, unit,"
            " ref_min, ref_max, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (report_id,
             v["parameter"],
             std_name,
             v["value"],
             v.get("unit", ""),
             v.get("min"),
             v.get("max"),
             v["status"])
        )

    conn.commit()
    conn.close()
    print(f"Report saved for {patient_name} on {report_date}")
    return report_id


# ── Get all patients ──────────────────────────────────────────────
def get_all_patients():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT id, name, created FROM patients ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "created": r[2]} for r in rows]


# ── Get patient reports ───────────────────────────────────────────
def get_patient_reports(patient_name):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute(
        "SELECT r.id, r.report_date, r.lab_name, r.uploaded_at"
        " FROM reports r"
        " JOIN patients p ON r.patient_id = p.id"
        " WHERE LOWER(p.name) = LOWER(?)"
        " ORDER BY r.report_date ASC",
        (patient_name,)
    )
    reports = c.fetchall()

    result = []
    for rep in reports:
        report_id   = rep[0]
        report_date = rep[1]
        lab_name    = rep[2]

        c.execute(
            "SELECT test_name, std_name, value, unit,"
            " ref_min, ref_max, status"
            " FROM test_results WHERE report_id = ?",
            (report_id,)
        )
        tests = c.fetchall()

        test_dict = {}
        for t in tests:
            test_dict[t[1]] = {  # key = std_name
                "original_name": t[0],
                "std_name":      t[1],
                "value":         t[2],
                "unit":          t[3],
                "ref_min":       t[4],
                "ref_max":       t[5],
                "status":        t[6]
            }

        result.append({
            "report_id":   report_id,
            "report_date": report_date,
            "lab_name":    lab_name,
            "tests":       test_dict
        })

    conn.close()
    return result


# ── Build trend table data ────────────────────────────────────────
def build_trend_data(patient_name):
    reports = get_patient_reports(patient_name)
    if not reports:
        return None, []

    # Collect all unique std test names across all reports
    all_tests = set()
    for rep in reports:
        all_tests.update(rep["tests"].keys())

    # Sort dates
    dates = [r["report_date"] for r in reports]

    # Build trend rows
    rows = []
    for test in sorted(all_tests):
        row = {"test_name": test, "values": {}, "unit": ""}

        has_abnormal = False
        first_val    = None
        latest_val   = None
        trend_dir    = "—"

        for rep in reports:
            date = rep["report_date"]
            if test in rep["tests"]:
                t = rep["tests"][test]
                row["values"][date] = {
                    "value":   t["value"],
                    "status":  t["status"],
                    "ref_min": t["ref_min"],
                    "ref_max": t["ref_max"],
                }
                if not row["unit"] and t["unit"]:
                    row["unit"] = t["unit"]
                if t["status"] != "NORMAL":
                    has_abnormal = True

                # Track first and latest value
                if first_val is None:
                    first_val = t["value"]
                latest_val = t["value"]
            else:
                row["values"][date] = None

        # Calculate overall trend — first report vs latest report
        if first_val is not None and latest_val is not None \
                and first_val != latest_val:
            diff = latest_val - first_val
            pct  = abs(diff / first_val * 100) if first_val != 0 else 0

            if abs(diff) < 0.01:
                trend_dir = "→ Stable"
            elif diff > 0:
                # Check if getting worse or better
                # HIGH values going up = worsening
                # LOW values going down = worsening
                latest_status = None
                for rep in reversed(reports):
                    if test in rep["tests"]:
                        latest_status = rep["tests"][test]["status"]
                        break

                if latest_status == "HIGH":
                    trend_dir = f"↑ {pct:.1f}% 🔴 Worsening"
                elif latest_status == "NORMAL":
                    trend_dir = f"↑ {pct:.1f}% 🟢 Improving"
                else:
                    trend_dir = f"↑ {pct:.1f}%"
            else:
                # Value went down
                latest_status = None
                for rep in reversed(reports):
                    if test in rep["tests"]:
                        latest_status = rep["tests"][test]["status"]
                        break

                if latest_status == "LOW":
                    trend_dir = f"↓ {pct:.1f}% 🔴 Worsening"
                elif latest_status == "NORMAL":
                    trend_dir = f"↓ {pct:.1f}% 🟢 Improving"
                else:
                    trend_dir = f"↓ {pct:.1f}%"
        elif first_val is not None and first_val == latest_val:
            trend_dir = "→ Stable"
        row["has_abnormal"] = has_abnormal
        row["trend"]        = trend_dir
        rows.append(row)

    # Sort: abnormal first, then normal
    rows.sort(key=lambda x: (not x["has_abnormal"], x["test_name"]))

    return dates, rows


# ── Delete patient data ───────────────────────────────────────────
def delete_patient_data(patient_name):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT id FROM patients WHERE LOWER(name) = LOWER(?)",
              (patient_name,))
    row = c.fetchone()
    if row:
        pid = row[0]
        # Get all report IDs
        c.execute("SELECT id FROM reports WHERE patient_id = ?", (pid,))
        rids = [r[0] for r in c.fetchall()]
        for rid in rids:
            c.execute("DELETE FROM test_results WHERE report_id = ?",
                      (rid,))
        c.execute("DELETE FROM reports WHERE patient_id = ?", (pid,))
        c.execute("DELETE FROM patients WHERE id = ?", (pid,))
    conn.commit()
    conn.close()