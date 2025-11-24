from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from auth_routes import auth
from tasks_routes import tasks
from config import JWT_SECRET_KEY, EMAIL_USER, EMAIL_PASSWORD
import smtplib
from email.mime.text import MIMEText

# Scheduler imports
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from db import get_connection


# ============================================================
# EMAIL SENDER FUNCTION (Gmail SMTP Using App Password)
# ============================================================
def send_email(to, subject, message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to, msg.as_string())

        print("📨 Email sent successfully!")

    except Exception as e:
        print("❌ Email Error:", e)


# ============================================================
# REMINDER EMAIL CHECKER
# ============================================================
def check_reminders():
    print("⏳ Running reminder email check...")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.id, t.title, t.description, t.reminder_datetime, u.email
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        WHERE t.is_completed = FALSE
    """)

    tasks = cur.fetchall()
    now = datetime.now()

    for t in tasks:
        task_id, title, desc, reminder_dt, email = t

        if reminder_dt and reminder_dt <= now:
            subject = f"⏰ Reminder: {title}"
            body = f"Your task is due soon.\n\nTitle: {title}\nDescription: {desc}\nReminder Time: {reminder_dt}"
            send_email(email, subject, body)
            print(f"📨 Reminder sent for task {task_id}")

    cur.close()
    conn.close()


# ============================================================
# OVERDUE EMAIL CHECKER
# ============================================================
def check_overdue():
    print("❗ Running overdue check...")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.id, t.title, t.description, t.due_datetime, u.email
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        WHERE t.is_completed = FALSE
    """)

    tasks = cur.fetchall()
    now = datetime.now()

    for t in tasks:
        task_id, title, desc, due_dt, email = t

        if due_dt and due_dt < now:
            subject = f"⚠️ Overdue Task: {title}"
            body = f"Your task deadline has passed!\n\nTitle: {title}\nDescription: {desc}\nDue Date: {due_dt}"
            send_email(email, subject, body)
            print(f"❌ Overdue email sent for task {task_id}")

    cur.close()
    conn.close()


# ============================================================
# FLASK APP SETUP
# ============================================================
app = Flask(__name__)

# Allow frontend (localhost) to access backend
CORS(app)

# JWT Auth
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
jwt = JWTManager(app)

# Blueprints
app.register_blueprint(auth, url_prefix="/auth")
app.register_blueprint(tasks, url_prefix="/tasks")


# ============================================================
# START BACKGROUND SCHEDULER
# ============================================================
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.add_job(check_overdue, 'interval', minutes=1)
scheduler.start()

print("🚀 APScheduler Started Successfully!")


# ============================================================
# ROOT
# ============================================================
@app.route("/")
def home():
    return "Backend Running Successfully with Email Alerts Enabled + Scheduler Running!"


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
