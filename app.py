from flask import Flask, request, jsonify
import psycopg2
import hashlib
import os

app = Flask(__name__)

# -----------------------
# Database Connection
# -----------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
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
# Add User Route (POST JSON)
# -----------------------
@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON data"}), 400

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not name or not email or not phone:
        return jsonify({"message": "Invalid input"}), 400

    data_hash = generate_hash(name, email, phone)

    try:
        cur.execute(
            "INSERT INTO users (name,email,phone,data_hash) VALUES (%s,%s,%s,%s)",
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
# Add User Form (Browser-friendly)
# -----------------------
@app.route("/add_user_form", methods=["GET", "POST"])
def add_user_form():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if not name or not email or not phone:
            return "⚠ Invalid input", 400

        data_hash = generate_hash(name, email, phone)
        try:
            cur.execute(
                "INSERT INTO users (name,email,phone,data_hash) VALUES (%s,%s,%s,%s)",
                (name,email,phone,data_hash)
            )
            conn.commit()
            return "✅ User added successfully"
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return "⚠ Duplicate or redundant user"
        except Exception as e:
            conn.rollback()
            return f"⚠ Error: {str(e)}", 500

    # GET request → show HTML form
    return '''
        <h2>Add User (Browser Form)</h2>
        <form method="POST">
            Name: <input name="name"><br><br>
            Email: <input name="email"><br><br>
            Phone: <input name="phone"><br><br>
            <input type="submit" value="Add User">
        </form>
    '''

# -----------------------
# View All Users Route (GET JSON)
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
