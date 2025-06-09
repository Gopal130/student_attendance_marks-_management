from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import Student, Teacher, Attendance, Session, Marks, Subject
from models import get_db_connection  # required for login auth
import hashlib
import traceback

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Use a strong secret in production


# ---------- ROUTES ----------

@app.route('/')
def home():
    print("Root route '/' accessed.")
    role = session.get('role')
    if role:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/create_student', methods=['GET', 'POST'])
def create_student():
    if session.get('role') != 'teacher':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        try:
            success = Teacher.create_student(username, password, name, email)
            if success:
                flash("Student created successfully!", "success")
            else:
                flash("Failed to create student. Username or email might already exist.", "error")
            return redirect(url_for('create_student'))
        except Exception as e:
            print("ERROR in create_student():", traceback.format_exc())
            flash(f'Error creating student: {str(e)}', 'error')

    return render_template('create_student.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if role == 'student':
                    cursor.execute("SELECT * FROM students WHERE username = ? AND password = ?", (username, hashed_password))
                    student = cursor.fetchone()
                    if student:
                        token = Session.create(student['id'])
                        session['session_token'] = token
                        session['role'] = 'student'
                        return redirect(url_for('dashboard'))
                elif role == 'teacher':
                    cursor.execute("SELECT * FROM teachers WHERE email = ?", (username,))
                    teacher = cursor.fetchone()
                    if teacher:
                        session['teacher_id'] = teacher['id']
                        session['role'] = 'teacher'
                        return redirect(url_for('dashboard'))

            flash('Invalid credentials. Please try again.', 'error')
        except Exception as e:
            print("ERROR in login():", traceback.format_exc())
            flash('An error occurred. Try again.', 'error')

    return render_template('login.html')


@app.route('/register')
def register():
    return "<h2>Registration not implemented yet.</h2>"


@app.route('/assign_marks', methods=['GET', 'POST'])
def assign_marks():
    if session.get('role') != 'teacher':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    teacher_id = session.get('teacher_id')
    subjects = Subject.get_by_teacher(teacher_id)

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        marks = request.form.get('marks')

        try:
            marks = float(marks)
            Teacher.assign_marks(student_id, subject_id, marks)
            flash("Marks assigned successfully.", "success")
        except Exception as e:
            flash("Failed to assign marks. Please check the details.", "error")
            print("Assign marks error:", e)

        return redirect(url_for('assign_marks'))

    with get_db_connection() as conn:
        students = conn.execute("SELECT id, name FROM students").fetchall()

    return render_template('assign_marks.html', students=students, subjects=subjects)


@app.route('/view_students')
def view_students():
    if session.get('role') != 'teacher':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        students = conn.execute("SELECT * FROM students").fetchall()

    return render_template('view_students.html', students=students)


@app.route('/dashboard')
def dashboard():
    role = session.get('role')

    if role == 'student':
        student_id = Session.validate(session.get('session_token'))
        if not student_id:
            session.pop('session_token', None)
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))

        student = Student.get_by_id(student_id)
        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("login"))

        try:
            stats = Attendance.get_attendance_percentage(student_id)
            history = Attendance.get_attendance_history(student_id)
            marks = Marks.get_student_marks(student_id)
        except Exception:
            print("ERROR in student dashboard():", traceback.format_exc())
            return "Internal Server Error", 500

        return render_template('dashboard_student.html',
                               student=student,
                               attendance_stats=stats,
                               attendance_history=history,
                               marks=marks)

    elif role == 'teacher':
        teacher_id = session.get('teacher_id')
        if not teacher_id:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))

        teacher = Teacher.get_by_id(teacher_id)
        subjects = Subject.get_by_teacher(teacher_id)

        return render_template('dashboard_teacher.html',
                               teacher=teacher,
                               subjects=subjects)

    flash('Unauthorized access. Please log in.', 'error')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True)