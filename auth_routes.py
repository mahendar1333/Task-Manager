from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from db import get_connection

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not (name and email and password):
        return jsonify({"error": "Name, email, and password required"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash) VALUES (%s, %s, %s, %s)",
            (name, email, phone, hashed_password)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "User registered successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get("email")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id, password_hash = user

    if not bcrypt.check_password_hash(password_hash, password):
        return jsonify({"error": "Incorrect password"}), 400

    token = create_access_token(identity=str(user_id))

    return jsonify({"message": "Login successful", "token": token}), 200
