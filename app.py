from flask import Flask, render_template, request
import sqlite3
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "appointments.db")

app = Flask(__name__)

# ---------------------------
# Google Sheets setup
# ---------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("booking-app-470114-d1dfa1f1dea5.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Booking details").sheet1  # Replace with your actual Sheet name

# ---------------------------
# Database Initialization
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized at:", DB_PATH)

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def form():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    date = request.form["date"]
    time = request.form["time"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if slot already exists in SQLite
    cursor.execute("SELECT * FROM appointments WHERE date=? AND time=?", (date, time))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return f"❌ Slot already booked on {date} at {time}. Please choose another slot."

    # Save to SQLite
    cursor.execute("INSERT INTO appointments (name, email, phone, date, time) VALUES (?, ?, ?, ?, ?)",
                   (name, email, phone, date, time))
    conn.commit()
    conn.close()

    # Save to Google Sheets
    sheet.append_row([name, email, phone, date, time])

    return f"✅ Appointment booked for {name} on {date} at {time}! (also saved to Google Sheets)"

# ---------------------------
# Start the app
# ---------------------------
if __name__ == "__main__":
    init_db()   # make sure DB and table exist
    app.run(debug=True)
