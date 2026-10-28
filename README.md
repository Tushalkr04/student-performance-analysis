# Student Performance Analysis (Mini Project)

A Flask + SQLite + Pandas web app that stores student marks and analyses class performance.

## Features
- Add students and subject marks (add / update / remove)
- Import marks from CSV and export everything back to CSV
- Dashboard: class average, pass rate, topper, subject-wise averages,
  grade distribution, subject pass %, top 5 list, students needing attention
- Per-student report: rank, grade, strongest/weakest subject, comparison with class average
- JSON endpoint `/api/summary`

## Run in VS Code
1. Unzip and open the folder in VS Code (`File > Open Folder`).
2. Open a terminal (`Ctrl + ~`) and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # macOS / Linux
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open http://127.0.0.1:5000 and use **Import CSV** to load `sample_data.csv`.

(Charts load Chart.js from a CDN, so an internet connection is needed for the graphs.)

## Project structure
```
app.py          routes (Flask)
database.py     SQLite connection and tables
analysis.py     Pandas analysis: averages, grades, ranks, pass rate
templates/      HTML pages (Jinja2)
static/         CSS
sample_data.csv 20 students x 5 subjects of demo data
```

## Rules used
- Pass: at least 40 marks in every subject
- Grades: O 90+, A+ 80+, A 70+, B 60+, C 50+, D 40+, F below 40
- "Needs attention": failed any subject or average below 50

## Ideas to extend
Attendance tracking, login for teachers, semester-wise marks, PDF report cards,
a simple prediction model (scikit-learn) for final-result forecasting.
