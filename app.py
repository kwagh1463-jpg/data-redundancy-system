from flask import Flask, request, jsonify
import psycopg2
import hashlib
import os

app = Flask(__name__)

# -----------------------
# Database Connection
# -----------------------
DATABASE_URL = os.environ.get("DATABASE_URL")  # Set this in Render Environment
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set!")

# Connect with SSL (required by Render)
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# -----------------------
# Helper Function: Generate Hash
# -----------------------
def generate_hash(name, email, phone):
    data_string = name.lower().strip() + email.lower().strip() + phone.strip()
    return hashlib.sha256(data_string.encode()).hexdigest()

# -----------------------
# Auto-create Table
# -----------------------
def create_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15) NOT NULL,
            data_hash TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

create_table()  # Run table creation at app startup

# -----------------------
# Home Route
# -----------------------
@app.route("/")
def home():
    return "✅ Data Redundancy Removal System is Running!"

# -----------------------
# Add User Route (POST)
# -----------------------
@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    # Basic validation
    if not name or not email or not phone:
        return jsonify({"message": "Invalid input"}), 400

    data_hash = generate_hash(name, email, phone)

    try:
        cur.execute(
            "INSERT INTO users (name, email, phone, data_hash) VALUES (%s,%s,%s,%s)",
            (name, email, phone, data_hash)
        )
        conn.commit()
        return jsonify({"message": "Unique Data Added Successfully"})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"message": "Duplicate or Redundant Data Found"}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

# -----------------------
# View All Users Route (GET)
# -----------------------
@app.route("/all_users", methods=["GET"])
def all_users():
    cur.execute("SELECT id, name, email, phone, created_at FROM users ORDER BY id DESC")
    users = cur.fetchall()
    users_list = []
    for u in users:
        users_list.append({
            "id": u[0],
            "name": u[1],
            "email": u[2],
            "phone": u[3],
            "created_at": str(u[4])
        })
    return jsonify({"users": users_list})

# -----------------------
# Run Flask App
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
