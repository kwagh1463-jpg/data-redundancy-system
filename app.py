from flask import Flask, request, jsonify
import psycopg2
import hashlib
import os

app = Flask(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Function to generate hash
def generate_hash(name, email, phone):
    data_string = name.lower().strip() + email.lower().strip() + phone.strip()
    return hashlib.sha256(data_string.encode()).hexdigest()

# Home route
@app.route("/")
def home():
    return "Data Redundancy Removal System Running Successfully"

# Add user route
@app.route("/add_user", methods=["POST"])
def add_user():
    name = request.json.get("name")
    email = request.json.get("email")
    phone = request.json.get("phone")

    # Basic validation
    if not name or not email or not phone:
        return jsonify({"message": "Invalid Input"}), 400

    data_hash = generate_hash(name, email, phone)

    try:
        cur.execute(
            "INSERT INTO users (name, email, phone, data_hash) VALUES (%s,%s,%s,%s)",
            (name, email, phone, data_hash)
        )
        conn.commit()
        return jsonify({"message": "Unique Data Added Successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": "Duplicate or Redundant Data Found"}), 409

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
