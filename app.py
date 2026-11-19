
import sqlite3
import os

from flask import (
    Flask, render_template, render_template_string,
    request, redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "iris-development-key-change-before-deploy")

DATABASE = "iris.db"


# DATABASE DAN AKUN
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        user = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",)
        ).fetchone()

        if user is None:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ("admin", generate_password_hash("Iris@2026"))
            )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medical_record_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                birth_date TEXT,
                gender TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS examinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                modality TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
# HALAMAN UTAMA
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with sqlite3.connect(DATABASE) as conn:
            user = conn.execute(
                "SELECT id, username, password FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and check_password_hash(user[2], password):
            session.clear()
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("dashboard"))

        flash("Username atau password tidak sesuai.")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DATABASE) as conn:
        total_patients = conn.execute(
            "SELECT COUNT(*) FROM patients"
        ).fetchone()[0]
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IRIS Hospital</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #F7F9FC;
                color: #263445;
            }
            header {
                background: #163A5F;
                color: white;
                padding: 24px 35px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            header h1 { margin: 0; letter-spacing: 2px; }
            header p { margin: 6px 0 0; color: #F3E6CC; }
            .container { padding: 30px 35px; }
            h2 { color: #163A5F; }
            .welcome { margin-bottom: 28px; }
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                gap: 20px;
            }
            .card {
                background: white;
                padding: 24px;
                border-radius: 12px;
                border-left: 5px solid #2878A8;
                box-shadow: 0 3px 12px #163A5F12;
            }
            .card h3 { color: #64748B; font-size: 14px; }
            .number { font-size: 32px; font-weight: bold; color: #163A5F; }
            .section {
                margin-top: 30px;
                background: white;
                padding: 25px;
                border-radius: 12px;
            }
            .tag {
                display: inline-block;
                background: #F3E6CC;
                color: #725A32;
                padding: 7px 12px;
                border-radius: 20px;
                font-size: 13px;
            }
            .logout {
                color: #163A5F;
                background: #F3E6CC;
                padding: 10px 16px;
                border-radius: 20px;
                text-decoration: none;
                font-size: 13px;
            }
            footer {
                text-align: center;
                padding: 25px;
                color: #64748B;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <header>
            <div>
                <h1>IRIS Hospital</h1>
                <p>Integrated Radiology Information System</p>
            </div>
            <div>
                <span class="tag">Radiology Dashboard</span>
                <a class="logout" href="/logout">Logout</a>
            </div>
        </header>

        <main class="container">
            <div class="welcome">
                <h2>Dashboard Overview</h2>
                <p>Welcome, {{ username }}. Welcome to IRIS Hospital.</p>
            </div>

            <div class="cards">
                <div class="card">
                    <h3>Total Patients</h3>
                    <div class="number">{{ total_patients }}</div>
                </div>
                <div class="card">
                    <h3>Today's Studies</h3>
                    <div class="number">36</div>
                </div>
                <div class="card">
                    <h3>In Progress</h3>
                    <div class="number">08</div>
                </div>
                <div class="card">
                    <h3>Reported</h3>
                    <div class="number">28</div>
                </div>
            </div>

            <div class="section">
                <h2>Radiology Information System</h2>
                <p>Manage patients, radiology examinations, worklists,
                imaging studies, and diagnostic reports in one system.</p>
                <span class="tag">Medical Blue & Champagne</span>
            </div>
        </main>

        <footer>
            IRIS Hospital © 2026 | Smart Workflow. Better Imaging. Better Care.
        </footer>
    </body>
    </html>
    """, username=session.get("username"), total_patients=total_patients)

# REGISTRASI PASIEN
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        mrn = request.form.get("medical_record_number", "").strip()
        name = request.form.get("full_name", "").strip()
        birth_date = request.form.get("birth_date", "")
        gender = request.form.get("gender", "")
        phone = request.form.get("phone", "").strip()

        if not mrn or not name:
            flash("Nomor rekam medis dan nama pasien wajib diisi.")
            return redirect(url_for("patients"))

        try:
            with sqlite3.connect(DATABASE) as conn:
                conn.execute("""
                    INSERT INTO patients
                    (medical_record_number, full_name, birth_date, gender, phone)
                    VALUES (?, ?, ?, ?, ?)
                """, (mrn, name, birth_date, gender, phone))

            flash("Data pasien berhasil disimpan.")
        except sqlite3.IntegrityError:
            flash("Nomor rekam medis sudah terdaftar.")

        return redirect(url_for("patients"))

    with sqlite3.connect(DATABASE) as conn:
        patient_list = conn.execute("""
            SELECT * FROM patients ORDER BY id DESC
        """).fetchall()

    return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrasi Pasien | IRIS Hospital</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 30px;
            font-family: Arial, sans-serif;
            background: #F7F9FC;
            color: #263445;
        }
        .container {
            max-width: 850px;
            margin: auto;
        }
        header {
            background: #163A5F;
            color: white;
            padding: 25px;
            border-radius: 12px;
        }
        header h1 { margin: 0; }
        .form-box {
            background: white;
            padding: 30px;
            margin-top: 25px;
            border-radius: 12px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid #CBD5E1;
            border-radius: 7px;
        }
        button {
            margin-top: 22px;
            padding: 13px 22px;
            border: none;
            border-radius: 7px;
            background: #2878A8;
            color: white;
            cursor: pointer;
        }
        .message {
            background: #F3E6CC;
            padding: 12px;
            border-radius: 7px;
            margin-bottom: 15px;
        }
        a { color: #2878A8; }
        @media(max-width: 600px) {
            .form-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>IRIS Hospital</h1>
        <p>Registrasi Pasien</p>
    </header>

    <div class="form-box">
        <h2>Formulir Data Pasien</h2>
        <p>Masukkan identitas pasien untuk pendaftaran pemeriksaan radiologi.</p>

        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="message">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        <form method="POST">
            <div class="form-grid">
                <div>
                    <label>Nomor Rekam Medis</label>
                    <input name="medical_record_number" required>
                </div>
                <div>
                    <label>Nama Lengkap</label>
                    <input name="full_name" required>
                </div>
                <div>
                    <label>Tanggal Lahir</label>
                    <input type="date" name="birth_date">
                </div>
                <div>
                    <label>Jenis Kelamin</label>
                    <select name="gender">
                        <option value="">Pilih jenis kelamin</option>
                        <option value="Laki-laki">Laki-laki</option>
                        <option value="Perempuan">Perempuan</option>
                    </select>
                </div>
                <div>
                    <label>Nomor Telepon</label>
                    <input name="phone" type="tel">
                </div>
            </div>

            <button type="submit">Simpan Data Pasien</button>
        </form>
<h2>Daftar Pasien Terdaftar</h2>

<table style="width:100%; border-collapse:collapse; margin-top:20px;">
    <tr style="background:#163A5F; color:white;">
        <th style="padding:12px;">No. RM</th>
        <th>Nama Pasien</th>
        <th>Tanggal Lahir</th>
        <th>Jenis Kelamin</th>
        <th>Telepon</th>
    </tr>

    {% for patient in patient_list %}
    <tr style="text-align:center; border-bottom:1px solid #ddd;">
        <td style="padding:12px;">{{ patient[1] }}</td>
        <td>{{ patient[2] }}</td>
        <td>{{ patient[3] }}</td>
        <td>{{ patient[4] }}</td>
        <td>{{ patient[5] }}</td>
    </tr>
    {% else %}
    <tr>
        <td colspan="5" style="padding:15px; text-align:center;">
            Belum ada pasien terdaftar.
        </td>
    </tr>
    {% endfor %}
</table>
        <p><a href="/dashboard">← Kembali ke Dashboard</a></p>
    </div>
</div>
</body>
</html>
""", patient_list=patient_list)

# FORM ORDER PEMERIKSAAN
@app.route("/orders", methods=["GET", "POST"])
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        modality = request.form.get("modality")
        exam_name = request.form.get("exam_name", "").strip()

        if not patient_id or not modality or not exam_name:
            return "Semua kolom wajib diisi."

        with sqlite3.connect(DATABASE) as conn:
            conn.execute("""
                INSERT INTO examinations
                (patient_id, modality, exam_name, status)
                VALUES (?, ?, ?, 'Scheduled')
            """, (patient_id, modality, exam_name))

        return redirect(url_for("worklist"))

    with sqlite3.connect(DATABASE) as conn:
        patient_list = conn.execute("""
            SELECT id, medical_record_number, full_name
            FROM patients
            ORDER BY full_name
        """).fetchall()

    return render_template_string("""
        <h1>Order Pemeriksaan Radiologi</h1>

        <form method="POST">
            <label>Pilih Pasien</label><br>
            <select name="patient_id" required>
                <option value="">-- Pilih Pasien --</option>
                {% for patient in patient_list %}
                <option value="{{ patient[0] }}">
                    {{ patient[1] }} - {{ patient[2] }}
                </option>
                {% endfor %}
            </select>

            <br><br>

            <label>Modalitas</label><br>
            <select name="modality" required>
                <option value="">-- Pilih Modalitas --</option>
                <option value="X-Ray">X-Ray</option>
                <option value="CT Scan">CT Scan</option>
                <option value="MRI">MRI</option>
            </select>

            <br><br>

            <label>Nama Pemeriksaan</label><br>
            <input type="text" name="exam_name" required>

            <br><br>

            <button type="submit">Simpan Order</button>
        </form>

        <br>
        <a href="/dashboard">Kembali ke Dashboard</a>
    """, patient_list=patient_list)

# WORKLIST PEMERIKSAAN
@app.route("/worklist")
def worklist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect(DATABASE) as conn:
        worklist_data = conn.execute("""
            SELECT
                examinations.id,
                patients.medical_record_number,
                patients.full_name,
                examinations.modality,
                examinations.exam_name,
                examinations.status
            FROM examinations
            JOIN patients ON examinations.patient_id = patients.id
            ORDER BY examinations.id DESC
        """).fetchall()

    return render_template_string("""
        <h1>Worklist Pemeriksaan IRIS</h1>
        <p>Daftar pemeriksaan radiologi pasien.</p>

        <table border="1" cellpadding="10">
            <tr>
                <th>No.</th>
                <th>No. RM</th>
                <th>Nama Pasien</th>
                <th>Modalitas</th>
                <th>Pemeriksaan</th>
                <th>Status</th>
<th>Update</th>
            </tr>

            {% for item in worklist_data %}
            {% for value in item %}
<td>{{ value }}</td>
{% endfor %}
<td>
    <form method="POST" action="/update-status/{{ item[0] }}">
        <select name="status">
            <option>Scheduled</option>
            <option>In Progress</option>
            <option>Completed</option>
            <option>Reported</option>
        </select>
        <button type="submit">Update</button>
    </form>
</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6">Belum ada pemeriksaan.</td>
            </tr>
            {% endfor %}
        </table>

        <p><a href="/dashboard">Kembali ke Dashboard</a></p>
    """, worklist_data=worklist_data)

# UPDATE STATUS PEMERIKSAAN
@app.route("/update-status/<int:exam_id>", methods=["POST"])
def update_status(exam_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.form.get("status")
    allowed_status = ["Scheduled", "In Progress", "Completed", "Reported"]

    if status in allowed_status:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("""
                UPDATE examinations
                SET status = ?
                WHERE id = ?
            """, (status, exam_id))

    return redirect(url_for("worklist"))

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
