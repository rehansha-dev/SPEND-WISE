from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "change_this_to_a_long_random_secret_key"

DATABASE = "database.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE DATABASE TABLES
# =========================

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_setup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,

            monthly_budget REAL DEFAULT 0,
            bank_balance REAL DEFAULT 0,
            pocket_money REAL DEFAULT 0,
            scholarship_income REAL DEFAULT 0,
            other_income REAL DEFAULT 0,

            hostel_fee REAL DEFAULT 0,
            college_fee REAL DEFAULT 0,
            mess_fee REAL DEFAULT 0,
            transport_fee REAL DEFAULT 0,

            savings_goal REAL DEFAULT 0,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            expense_date TEXT NOT NULL,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# LOGIN REQUIRED
# =========================

def login_required():
    return "user_id" in session


# =========================
# HOME
# =========================

@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    setup = conn.execute(
        "SELECT * FROM financial_setup WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not setup:
        return redirect(url_for("setup"))

    return redirect(url_for("dashboard"))


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("Please fill all the fields.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            cursor = conn.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

            user_id = cursor.lastrowid

            session["user_id"] = user_id
            session["user_name"] = name

            conn.close()

            flash("Welcome to SpendWise! Let's set up your finances.", "success")

            return redirect(url_for("setup"))

        except sqlite3.IntegrityError:
            conn.close()
            flash("This email is already registered.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Welcome back!", "success")

            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# =========================
# FINANCIAL SETUP
# =========================

@app.route("/setup", methods=["GET", "POST"])
def setup():

    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":

        monthly_budget = request.form.get("monthly_budget", 0)
        bank_balance = request.form.get("bank_balance", 0)
        pocket_money = request.form.get("pocket_money", 0)
        scholarship_income = request.form.get("scholarship_income", 0)
        other_income = request.form.get("other_income", 0)

        hostel_fee = request.form.get("hostel_fee", 0)
        college_fee = request.form.get("college_fee", 0)
        mess_fee = request.form.get("mess_fee", 0)
        transport_fee = request.form.get("transport_fee", 0)

        savings_goal = request.form.get("savings_goal", 0)

        conn = get_db_connection()

        existing = conn.execute(
            "SELECT id FROM financial_setup WHERE user_id = ?",
            (session["user_id"],)
        ).fetchone()

        values = (
            monthly_budget,
            bank_balance,
            pocket_money,
            scholarship_income,
            other_income,
            hostel_fee,
            college_fee,
            mess_fee,
            transport_fee,
            savings_goal,
            session["user_id"]
        )

        if existing:

            conn.execute("""
                UPDATE financial_setup
                SET
                    monthly_budget = ?,
                    bank_balance = ?,
                    pocket_money = ?,
                    scholarship_income = ?,
                    other_income = ?,
                    hostel_fee = ?,
                    college_fee = ?,
                    mess_fee = ?,
                    transport_fee = ?,
                    savings_goal = ?
                WHERE user_id = ?
            """, values)

        else:

            conn.execute("""
                INSERT INTO financial_setup (
                    monthly_budget,
                    bank_balance,
                    pocket_money,
                    scholarship_income,
                    other_income,
                    hostel_fee,
                    college_fee,
                    mess_fee,
                    transport_fee,
                    savings_goal,
                    user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

        conn.commit()
        conn.close()

        flash("Financial profile saved successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("setup.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    setup = conn.execute(
        "SELECT * FROM financial_setup WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    if not setup:
        conn.close()
        return redirect(url_for("setup"))

    current_month = datetime.now().strftime("%Y-%m")

    total_spent_row = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
    """, (session["user_id"], current_month)).fetchone()

    total_spent = total_spent_row["total"]

    expenses = conn.execute("""
        SELECT *
        FROM expenses
        WHERE user_id = ?
        ORDER BY expense_date DESC, id DESC
        LIMIT 8
    """, (session["user_id"],)).fetchall()

    categories = conn.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
        GROUP BY category
        ORDER BY total DESC
    """, (session["user_id"], current_month)).fetchall()

    conn.close()

    monthly_budget = setup["monthly_budget"]
    remaining_budget = monthly_budget - total_spent

    percentage_used = 0

    if monthly_budget > 0:
        percentage_used = min(
            round((total_spent / monthly_budget) * 100, 1),
            100
        )

    # ADVICE SYSTEM

    advice = "Your spending looks healthy. Keep tracking your expenses!"

    if percentage_used >= 100:
        advice = "You have exceeded your monthly budget. Avoid unnecessary spending for now."

    elif percentage_used >= 90:
        advice = "You have used more than 90% of your budget. Spend carefully."

    elif percentage_used >= 75:
        advice = "You have crossed 75% of your monthly budget. Start controlling non-essential expenses."

    elif percentage_used >= 50:
        advice = "You have spent over half of your monthly budget. Keep an eye on your daily expenses."

    # CATEGORY ANALYSIS

    highest_category = None

    if categories:
        highest_category = categories[0]

    return render_template(
        "dashboard.html",
        setup=setup,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        percentage_used=percentage_used,
        expenses=expenses,
        categories=categories,
        advice=advice,
        highest_category=highest_category
    )


# =========================
# ADD EXPENSE
# =========================

@app.route("/add-expense", methods=["POST"])
def add_expense():

    if not login_required():
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form.get("description", "").strip()
    expense_date = request.form["expense_date"]

    if not title or not amount or not category or not expense_date:
        flash("Please fill all required fields.", "error")
        return redirect(url_for("expenses"))

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO expenses (
        user_id,
        title,
        amount,
        category,
        description,
        expense_date
    )
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    session["user_id"],
    title,
    float(amount),
    category,
    description,
    expense_date
)
)

    conn.commit()
    conn.close()

    flash("Expense added successfully!", "success")

    return redirect(url_for("expenses"))


# =========================
# EXPENSE PAGE
# =========================

@app.route("/expenses")
def expenses():

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    expenses_list = conn.execute("""
        SELECT *
        FROM expenses
        WHERE user_id = ?
        ORDER BY expense_date DESC, id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expenses_list
    )


# =========================
# DELETE EXPENSE
# =========================

@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM expenses
        WHERE id = ?
        AND user_id = ?
    """, (
        expense_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash("Expense deleted successfully.", "success")

    return redirect(url_for("expenses"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)