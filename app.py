
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not app.secret_key or not ADMIN_PASSWORD:
    raise RuntimeError("SECRET_KEY or ADMIN_PASSWORD is missing from .env")


# Database connection
def get_database():
    connection = sqlite3.connect("messages.db")
    connection.row_factory = sqlite3.Row
    return connection


# Create database
def create_database():
    connection = get_database()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Contact form
@app.route("/send-message", methods=["POST"])
def send_message():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("home") + "#contact")

    connection = get_database()

    connection.execute("""
        INSERT INTO messages (name, email, message)
        VALUES (?, ?, ?)
    """, (name, email, message))

    connection.commit()
    connection.close()

    flash("Your message has been sent successfully!", "success")

    return redirect(url_for("home") + "#contact")


# Admin login page
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        password = request.form.get("password", "")

        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect password. Please try again.", "error")

    return render_template("login.html")


# Admin dashboard
@app.route("/admin")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_database()

    messages = connection.execute(
        "SELECT * FROM messages ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template("admin.html", messages=messages)


# Delete a message
@app.route("/delete-message/<int:message_id>", methods=["POST"])
def delete_message(message_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_database()

    connection.execute(
        "DELETE FROM messages WHERE id = ?",
        (message_id,)
    )

    connection.commit()
    connection.close()

    flash("Message deleted successfully!", "success")

    return redirect(url_for("admin_dashboard"))


# Admin logout
@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
