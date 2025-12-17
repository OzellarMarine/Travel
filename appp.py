from flask import Flask, render_template, request, redirect
import sqlite3
from flask import send_file
import pandas as pd
import json

app = Flask(__name__)

# ---------------------------
# Create Database (FULL VERSION)
# ---------------------------
def init_db():
    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT,
            from_date TEXT,
            to_date TEXT,
            days INTEGER,
            country TEXT,
            port TEXT,
            vessel TEXT,
            purpose TEXT,
            total_cost REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transport_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            travel_id INTEGER,
            mode TEXT,
            cost REAL
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------------------
# Home Page
# ---------------------------
@app.route("/")
def index():
    return render_template("form.html")


# ---------------------------
# Submit Form → Insert into DB
# ---------------------------
@app.route("/submit", methods=["POST"])
def submit():

    # 1. Basic fields
    person = request.form["person_name"]
    from_date = request.form["from_date"]
    to_date = request.form["to_date"]
    days = request.form["days"]
    country = request.form["country"]
    port = request.form["port"]
    vessel = request.form["vessel"]
    purpose = request.form["purpose"]

    # 2. Transport data (multiple rows)
    modes = request.form.getlist("transport_mode[]")
    costs = request.form.getlist("transport_cost[]")

    total_cost = sum(float(c) for c in costs if c)

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    # Insert main table
    cursor.execute("""
        INSERT INTO travel_details 
        (person_name, from_date, to_date, days, country, port, vessel, purpose, total_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (person, from_date, to_date, days, country, port, vessel, purpose, total_cost))

    travel_id = cursor.lastrowid

    # Insert transport list
    for mode, cost in zip(modes, costs):
        cursor.execute("""
            INSERT INTO transport_details (travel_id, mode, cost)
            VALUES (?, ?, ?)
        """, (travel_id, mode, cost))

    conn.commit()
    conn.close()

    return redirect("/records")


# ---------------------------
# View Records Page
# ---------------------------
@app.route("/records")
def records():

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM travel_details")
    rows = cursor.fetchall()

    records = []

    for row in rows:
        id = row[0]

        cursor.execute("SELECT mode, cost FROM transport_details WHERE travel_id=?", (id,))
        transport = cursor.fetchall()

        records.append({
            "id": row[0],
            "person_name": row[1],
            "from_date": row[2],
            "to_date": row[3],
            "days": row[7],
            "country": row[8],
            "port": row[9],
            "vessel": row[5],
            "purpose": row[6],
            "place": row[4],  # not shown in table but preserved
            "total_cost": row[10],
            "transport": transport
        })

    conn.close()

    return render_template("table.html", records=records)


# ---------------------------
# Edit Record Page
# ---------------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    if request.method == "POST":

        person = request.form["person_name"]
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        days = request.form["days"]
        country = request.form["country"]
        port = request.form["port"]
        vessel = request.form["vessel"]
        purpose = request.form["purpose"]

        modes = request.form.getlist("transport_mode[]")
        costs = request.form.getlist("transport_cost[]")

        total_cost = sum(float(c) for c in costs if c)

        # Update main table
        cursor.execute("""
            UPDATE travel_details 
            SET person_name=?, from_date=?, to_date=?, days=?, country=?, port=?,
                vessel=?, purpose=?, total_cost=?
            WHERE id=?
        """, (person, from_date, to_date, days, country, port, vessel, purpose, total_cost, id))

        # Clear old transport rows
        cursor.execute("DELETE FROM transport_details WHERE travel_id=?", (id,))

        # Insert new transport rows
        for mode, cost in zip(modes, costs):
            cursor.execute("""
                INSERT INTO transport_details (travel_id, mode, cost)
                VALUES (?, ?, ?)
            """, (id, mode, cost))

        conn.commit()
        conn.close()
        return redirect("/records")

    # GET → Load existing record
    cursor.execute("SELECT * FROM travel_details WHERE id=?", (id,))
    row = cursor.fetchone()

    cursor.execute("SELECT mode, cost FROM transport_details WHERE travel_id=?", (id,))
    transport = cursor.fetchall()

    conn.close()

    record = {
        "id": row[0],
        "person_name": row[1],
        "from_date": row[2],
        "to_date": row[3],
        "days": row[4],
        "country": row[5],
        "port": row[6],
        "vessel": row[7],
        "purpose": row[8],
        "total_cost": row[9],
        "transport": transport
    }

    return render_template("edit.html", record=record)


# ---------------------------
# Delete Record
# ---------------------------
@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM travel_details WHERE id=?", (id,))
    cursor.execute("DELETE FROM transport_details WHERE travel_id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/records")


# ---------------------------
# Export to Excel
# ---------------------------
@app.route("/export")
def export():
    conn = sqlite3.connect("travel.db")

    df1 = pd.read_sql_query("SELECT * FROM travel_details", conn)
    df2 = pd.read_sql_query("SELECT * FROM transport_details", conn)

    conn.close()

    with pd.ExcelWriter("travel_export.xlsx") as writer:
        df1.to_excel(writer, sheet_name="Travel Info", index=False)
        df2.to_excel(writer, sheet_name="Transport Info", index=False)

    return send_file("travel_export.xlsx", as_attachment=True)


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
