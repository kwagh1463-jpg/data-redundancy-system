from flask import Flask, request, jsonify, render_template_string
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

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# -----------------------
# Helper: Generate Hash
# -----------------------
def generate_hash(name, email, phone):
    data_string = name.lower().strip() + email.lower().strip() + phone.strip()
    return hashlib.sha256(data_string.encode()).hexdigest()

# -----------------------
# Auto-create Table
# -----------------------
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

# -----------------------
# HTML Frontend
# -----------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Data Redundancy Removal System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        input, button { padding: 8px; margin: 5px 0; width: 300px; }
        table { border-collapse: collapse; margin-top: 20px; width: 80%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h2>Add User</h2>
    <input type="text" id="name" placeholder="Name"><br>
    <input type="email" id="email" placeholder="Email"><br>
    <input type="text" id="phone" placeholder="Phone"><br>
    <button onclick="addUser()">Add User</button>
    <p id="message"></p>

    <h2>All Users</h2>
    <button onclick="loadUsers()">Refresh Users</button>
    <table id="usersTable">
        <tr>
            <th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Created At</th>
        </tr>
    </table>

<script>
async function addUser() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;

    const response = await fetch("/add_user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, phone })
    });

    const result = await response.json();
    document.getElementById("message").innerText = result.message;
    loadUsers();
}

async function loadUsers() {
    const response = await fetch("/all_users");
    const data = await response.json();

    const table = document.getElementById("usersTable");
    table.innerHTML = "<tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Created At</th></tr>";

    data.users.forEach(user => {
        const row = table.insertRow();
        row.insertCell(0).innerText = user.id;
        row.insertCell(1).innerText = user.name;
        row.insertCell(2).innerText = user.email;
        row.insertCell(3).innerText = user.phone;
        row.insertCell(4).innerText = user.created_at;
    });
}

// Load users on page load
loadUsers();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# -----------------------
# Add User POST Route
# -----------------------
@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"message":"Missing JSON data"}), 400

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    if not name or not email or not phone:
        return jsonify({"message":"Invalid input"}), 400

    data_hash = generate_hash(name, email, phone)
    try:
        cur.execute("INSERT INTO users (name,email,phone,data_hash) VALUES (%s,%s,%s,%s)",
                    (name,email,phone,data_hash))
        conn.commit()
        return jsonify({"message":"Unique Data Added Successfully"})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"message":"Duplicate or Redundant Data Found"}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

# -----------------------
# View All Users
# -----------------------
@app.route("/all_users", methods=["GET"])
def all_users():
    cur.execute("SELECT id,name,email,phone,created_at FROM users ORDER BY id DESC")
    users = cur.fetchall()
    users_list = [{"id":u[0],"name":u[1],"email":u[2],"phone":u[3],"created_at":str(u[4])} for u in users]
    return jsonify({"users":users_list})

# -----------------------
# Run Flask App
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
