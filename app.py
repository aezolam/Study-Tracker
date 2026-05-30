from flask import Flask, request, render_template, session, redirect, url_for
import pymysql
from werkzeug.security import check_password_hash
from models import NormalUser

app = Flask(__name__)
# This secret key is required by Flask to securely remember who is logged in
app.secret_key = 'verdacore_secure_key_2026'

# --- DATABASE CONNECTION ---


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='verdacore_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# --- ROUTES ---


@app.route('/')
def home():
    return "<h1>Welcome to VerdaCore!</h1> <br> <a href='/register'>Register</a> | <a href='/login'>Login</a>"

# REGISTRATION ROUTE 


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        program = request.form['program']
        year_level = request.form['year_level']

        new_user = NormalUser(username, password, program, year_level)
        hashed_pw = new_user.get_hashed_password()

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql_user = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
                cursor.execute(sql_user, (new_user.username, hashed_pw))
                user_id = cursor.lastrowid

                sql_profile = "INSERT INTO user_profiles (user_id, program, year_level) VALUES (%s, %s, %s)"
                cursor.execute(
                    sql_profile, (user_id, new_user.program, new_user.year_level))

            connection.commit()
            # Send them to login after registering!
            return redirect(url_for('login'))

        except Exception as e:
            return f"<h1>Error! That username might already be taken.</h1> <p>{e}</p>"
        finally:
            connection.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    # We must remember their role!
                    session['role'] = user['role']

                    # The Split: Send Admins to the Admin page, Students to Dashboard
                    if user['role'] == 'Admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    return "<h1>Invalid username or password. Please try again.</h1>"
        finally:
            connection.close()

    return render_template('login.html')

# NEW: ADMIN DASHBOARD ROUTE


@app.route('/admin')
def admin_dashboard():
    # Security Check: Kick them out if they are not logged in OR not an Admin
    if 'user_id' not in session or session.get('role') != 'Admin':
        return "<h1>ACCESS DENIED. You are not an Admin.</h1>"

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch all users so the Admin can see who is registered
            cursor.execute("SELECT * FROM users")
            all_users = cursor.fetchall()

            # Fetch the Audit Logs (The Security Camera)
            cursor.execute(
                "SELECT * FROM admin_audit_logs ORDER BY created_at DESC")
            all_logs = cursor.fetchall()

            # Secretly log that the Admin viewed the dashboard
            log_sql = "INSERT INTO admin_audit_logs (admin_username, action) VALUES (%s, %s)"
            cursor.execute(
                log_sql, (session['username'], "Viewed the Admin Dashboard"))
            connection.commit()
    finally:
        connection.close()

    return render_template('admin.html', username=session['username'], users=all_users, logs=all_logs)
# NEW: DASHBOARD ROUTE (Now with Notes, Timer, AND Calendar!)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    user_id = session['user_id']

    if request.method == 'POST':
        # 1. Saving a NOTE
        if 'note_title' in request.form:
            title = request.form['note_title']
            note_type = request.form['note_type']
            content = request.form['content']
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO notez (user_id, note_title, note_type, content) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (user_id, title, note_type, content))
                connection.commit()
            except Exception as e:
                print(f"Error saving note: {e}")

        # 2. Saving a STUDY SESSION
        elif 'duration_minutes' in request.form:
            duration = request.form['duration_minutes']
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO study_sessions (user_id, duration_minutes) VALUES (%s, %s)"
                    cursor.execute(sql, (user_id, duration))
                connection.commit()
            except Exception as e:
                print(f"Error saving session: {e}")

        # 3. Saving a CALENDAR EVENT
        elif 'event_title' in request.form:
            event_title = request.form['event_title']
            event_type = request.form['event_type']
            event_date = request.form['event_date']
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO calendar_events (user_id, event_title, event_type, event_date) VALUES (%s, %s, %s, %s)"
                    cursor.execute(
                        sql, (user_id, event_title, event_type, event_date))
                connection.commit()
            except Exception as e:
                print(f"Error saving event: {e}")

    # Fetch EVERYTHING to display on the dashboard
    try:
        with connection.cursor() as cursor:
            # Fetch Notes
            cursor.execute(
                "SELECT * FROM notez WHERE user_id = %s ORDER BY date_made DESC", (user_id,))
            user_notes = cursor.fetchall()

            # Fetch Study Sessions
            cursor.execute(
                "SELECT * FROM study_sessions WHERE user_id = %s ORDER BY start_time DESC", (user_id,))
            user_sessions = cursor.fetchall()

            # Fetch Calendar Events (Ordered by closest date first!)
            cursor.execute(
                "SELECT * FROM calendar_events WHERE user_id = %s ORDER BY event_date ASC", (user_id,))
            user_events = cursor.fetchall()
    finally:
        connection.close()

    return render_template('dashboard.html', username=session['username'], notes=user_notes, sessions=user_sessions, events=user_events)

# NEW: LOGOUT ROUTE


@app.route('/logout')
def logout():
    session.clear()  # Erase their memory from the server
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
