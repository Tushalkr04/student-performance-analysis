"""Student Performance Analysis - Flask backend."""
import csv
import io

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   Response, url_for)

import analysis
from database import get_conn, init_db

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
init_db()


@app.route("/")
def dashboard():
    return render_template("index.html", s=analysis.summary(), pass_mark=analysis.PASS_MARK)


@app.route("/api/summary")
def api_summary():
    return jsonify(analysis.summary())


@app.route("/students")
def students():
    q = request.args.get("q", "").strip()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? ORDER BY roll_no",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
    t = analysis.student_table().set_index("student_id")
    data = []
    for r in rows:
        extra = t.loc[r["id"]] if r["id"] in t.index else None
        data.append({"id": r["id"], "roll_no": r["roll_no"], "name": r["name"],
                     "course": r["course"],
                     "average": extra["average"] if extra is not None else "-",
                     "grade": extra["grade"] if extra is not None else "-",
                     "result": extra["result"] if extra is not None else "-"})
    return render_template("students.html", students=data, q=q)


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll = request.form["roll_no"].strip()
        name = request.form["name"].strip()
        course = request.form.get("course", "MCA").strip() or "MCA"
        if not roll or not name:
            flash("Roll number and name are required.", "error")
            return redirect(url_for("add_student"))
        try:
            with get_conn() as conn:
                cur = conn.execute("INSERT INTO students (roll_no, name, course) VALUES (?,?,?)",
                                   (roll, name, course))
            flash("Student added. Now add their marks.", "ok")
            return redirect(url_for("student_detail", sid=cur.lastrowid))
        except Exception:
            flash("That roll number already exists.", "error")
    return render_template("add_student.html")


@app.route("/students/<int:sid>", methods=["GET", "POST"])
def student_detail(sid):
    with get_conn() as conn:
        stu = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
        if not stu:
            flash("Student not found.", "error")
            return redirect(url_for("students"))
        if request.method == "POST":
            subject = request.form["subject"].strip()
            try:
                marks = float(request.form["marks"])
                if not 0 <= marks <= 100:
                    raise ValueError
            except ValueError:
                flash("Marks must be a number between 0 and 100.", "error")
                return redirect(url_for("student_detail", sid=sid))
            conn.execute(
                """INSERT INTO marks (student_id, subject, marks) VALUES (?,?,?)
                   ON CONFLICT(student_id, subject) DO UPDATE SET marks=excluded.marks""",
                (sid, subject, marks))
            flash("Marks saved.", "ok")
            return redirect(url_for("student_detail", sid=sid))
    return render_template("student_detail.html", stu=stu,
                           r=analysis.student_report(sid), pass_mark=analysis.PASS_MARK)


@app.route("/students/<int:sid>/delete", methods=["POST"])
def delete_student(sid):
    with get_conn() as conn:
        conn.execute("DELETE FROM students WHERE id=?", (sid,))
    flash("Student deleted.", "ok")
    return redirect(url_for("students"))


@app.route("/marks/<int:sid>/<subject>/delete", methods=["POST"])
def delete_marks(sid, subject):
    with get_conn() as conn:
        conn.execute("DELETE FROM marks WHERE student_id=? AND subject=?", (sid, subject))
    return redirect(url_for("student_detail", sid=sid))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """CSV columns: roll_no,name,course,subject,marks"""
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename.lower().endswith(".csv"):
            flash("Please choose a .csv file.", "error")
            return redirect(url_for("upload"))
        reader = csv.DictReader(io.StringIO(f.read().decode("utf-8-sig")))
        need = {"roll_no", "name", "course", "subject", "marks"}
        if not reader.fieldnames or not need.issubset(reader.fieldnames):
            flash("CSV must have columns: roll_no, name, course, subject, marks.", "error")
            return redirect(url_for("upload"))
        count = bad = 0
        with get_conn() as conn:
            for row in reader:
                try:
                    m = float(row["marks"])
                    if not 0 <= m <= 100:
                        raise ValueError
                    conn.execute("INSERT OR IGNORE INTO students (roll_no,name,course) VALUES (?,?,?)",
                                 (row["roll_no"].strip(), row["name"].strip(), row["course"].strip()))
                    sid = conn.execute("SELECT id FROM students WHERE roll_no=?",
                                       (row["roll_no"].strip(),)).fetchone()["id"]
                    conn.execute(
                        """INSERT INTO marks (student_id,subject,marks) VALUES (?,?,?)
                           ON CONFLICT(student_id,subject) DO UPDATE SET marks=excluded.marks""",
                        (sid, row["subject"].strip(), m))
                    count += 1
                except Exception:
                    bad += 1
        flash(f"Imported {count} records. Skipped {bad} invalid rows.", "ok")
        return redirect(url_for("dashboard"))
    return render_template("upload.html")


@app.route("/export")
def export():
    df = analysis.load_df().drop(columns=["student_id"])
    return Response(df.to_csv(index=False), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=student_marks.csv"})


if __name__ == "__main__":
    app.run(debug=True)
