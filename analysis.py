"""Pandas-based analysis of student performance."""
import pandas as pd
from database import get_conn

PASS_MARK = 40  # minimum marks required in every subject


def grade(m):
    if m >= 90: return "O"
    if m >= 80: return "A+"
    if m >= 70: return "A"
    if m >= 60: return "B"
    if m >= 50: return "C"
    if m >= PASS_MARK: return "D"
    return "F"


GRADE_ORDER = ["O", "A+", "A", "B", "C", "D", "F"]


def load_df():
    with get_conn() as conn:
        return pd.read_sql_query(
            """SELECT s.id AS student_id, s.roll_no, s.name, s.course,
                      m.subject, m.marks
               FROM students s JOIN marks m ON m.student_id = s.id""",
            conn,
        )


def student_table(df=None):
    """One row per student: average, result, grade."""
    df = load_df() if df is None else df
    if df.empty:
        return pd.DataFrame(columns=["student_id", "roll_no", "name", "course",
                                     "average", "lowest", "result", "grade", "rank"])
    g = df.groupby(["student_id", "roll_no", "name", "course"])["marks"]
    t = g.agg(average="mean", lowest="min").reset_index()
    t["average"] = t["average"].round(2)
    t["result"] = t["lowest"].apply(lambda x: "Pass" if x >= PASS_MARK else "Fail")
    t["grade"] = t["average"].apply(grade)
    t["rank"] = t["average"].rank(ascending=False, method="min").astype(int)
    return t.sort_values("rank")


def summary():
    df = load_df()
    t = student_table(df)
    if t.empty:
        return {"empty": True}
    subj = df.groupby("subject")["marks"].agg(["mean", "max", "min"]).round(2)
    subj_pass = df.groupby("subject")["marks"].apply(lambda s: round((s >= PASS_MARK).mean() * 100, 1))
    gd = t["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
    top = t.iloc[0]
    return {
        "empty": False,
        "total_students": int(len(t)),
        "class_average": round(float(t["average"].mean()), 2),
        "pass_percentage": round(float((t["result"] == "Pass").mean() * 100), 1),
        "highest_avg": float(top["average"]),
        "topper": f'{top["name"]} ({top["roll_no"]})',
        "subjects": list(subj.index),
        "subject_avg": subj["mean"].tolist(),
        "subject_max": subj["max"].tolist(),
        "subject_min": subj["min"].tolist(),
        "subject_pass_pct": subj_pass.reindex(subj.index).tolist(),
        "grades": GRADE_ORDER,
        "grade_counts": gd.tolist(),
        "top5": t.head(5)[["rank", "roll_no", "name", "average", "grade"]].to_dict("records"),
        "at_risk": t[(t["result"] == "Fail") | (t["average"] < 50)][
            ["roll_no", "name", "average", "lowest"]].to_dict("records"),
        "hardest_subject": subj["mean"].idxmin(),
        "easiest_subject": subj["mean"].idxmax(),
    }


def student_report(student_id):
    df = load_df()
    d = df[df["student_id"] == student_id]
    if d.empty:
        return None
    class_avg = df.groupby("subject")["marks"].mean().round(2)
    rows = []
    for _, r in d.iterrows():
        diff = round(r["marks"] - class_avg[r["subject"]], 2)
        rows.append({"subject": r["subject"], "marks": r["marks"],
                     "grade": grade(r["marks"]), "class_avg": class_avg[r["subject"]],
                     "diff": diff})
    t = student_table(df)
    me = t[t["student_id"] == student_id].iloc[0]
    best = max(rows, key=lambda x: x["marks"])
    weak = min(rows, key=lambda x: x["marks"])
    return {"rows": rows, "average": me["average"], "rank": int(me["rank"]),
            "total": int(len(t)), "result": me["result"], "grade": me["grade"],
            "best": best["subject"], "weak": weak["subject"]}
