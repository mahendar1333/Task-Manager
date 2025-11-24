from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_connection
from email_utils import send_email     # <-- EMAIL SUPPORT

tasks = Blueprint('tasks', __name__)


# ---------------------------------------------------------
# Helper: Get user email from DB
# ---------------------------------------------------------
def get_user_email(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else None


# ---------------------------------------------------------
# CREATE TASK (sends email)
# ---------------------------------------------------------
@tasks.route('/create', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    due_datetime = data.get("due_datetime")
    reminder_datetime = data.get("reminder_datetime")

    if not (title and due_datetime and reminder_datetime):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tasks (user_id, title, description, due_datetime, reminder_datetime)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, title, description, due_datetime, reminder_datetime))

    task_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # -------------------- SEND EMAIL --------------------
    user_email = get_user_email(user_id)
    if user_email:
        subject = "🆕 New Task Created"
        body = (
            f"A new task has been created.\n\n"
            f"Title: {title}\n"
            f"Description: {description or '-'}\n"
            f"Due: {due_datetime}\n"
            f"Reminder: {reminder_datetime}\n\n"
            f"Stay productive! 🚀"
        )
        try:
            send_email(user_email, subject, body)
        except Exception as e:
            print("Email error:", e)

    return jsonify({"message": "Task created!", "task_id": task_id}), 201


# ---------------------------------------------------------
# LIST ALL TASKS FOR USER
# ---------------------------------------------------------
@tasks.route('/list', methods=['GET'])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, description, due_datetime, reminder_datetime, is_completed
        FROM tasks
        WHERE user_id = %s
        ORDER BY due_datetime
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    tasks_list = [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "due_datetime": str(r[3]),
            "reminder_datetime": str(r[4]),
            "is_completed": r[5]
        }
        for r in rows
    ]

    return jsonify({"tasks": tasks_list}), 200


# ---------------------------------------------------------
# UPDATE TASK (edit or mark completed) + email if completed
# ---------------------------------------------------------
@tasks.route('/update/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    # Get old status
    cur.execute(
        "SELECT is_completed, title FROM tasks WHERE id = %s AND user_id = %s",
        (task_id, user_id)
    )
    old = cur.fetchone()

    if not old:
        cur.close()
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    old_completed, old_title = old

    # Build update query
    update_fields = []
    update_values = []

    for field in ["title", "description", "due_datetime", "reminder_datetime", "is_completed"]:
        if field in data:
            update_fields.append(f"{field} = %s")
            update_values.append(data[field])

    if not update_fields:
        return jsonify({"error": "Nothing to update"}), 400

    update_values.extend([task_id, user_id])

    cur.execute(f"""
        UPDATE tasks
        SET {', '.join(update_fields)}
        WHERE id = %s AND user_id = %s
    """, tuple(update_values))

    conn.commit()
    cur.close()
    conn.close()

    # ---------------- EMAIL WHEN COMPLETED ----------------
    if "is_completed" in data and data["is_completed"] and not old_completed:
        user_email = get_user_email(user_id)

        if user_email:
            subject = "🎉 Task Completed"
            body = (
                f"Great job! You completed a task:\n\n"
                f"Task: {old_title}\n\n"
                f"Keep going! 💪"
            )
            try:
                send_email(user_email, subject, body)
            except Exception as e:
                print("Email error:", e)

    return jsonify({"message": "Task updated successfully!"}), 200


# ---------------------------------------------------------
# DELETE TASK
# ---------------------------------------------------------
@tasks.route('/delete/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"message": "Task deleted!"}), 200
