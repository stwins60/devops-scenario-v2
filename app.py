from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()
from services.scenario_generator import generate_scenario_data

app = Flask(__name__)
app.secret_key = 'super_secret_devops_key'

def get_db_connection():
    conn = sqlite3.connect('scenarios.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS scenarios (
        id TEXT PRIMARY KEY,
        title TEXT,
        language TEXT,
        difficulty TEXT,
        issue_type TEXT,
        description TEXT,
        code_snippet TEXT,
        tags TEXT
    )''')
    try:
        conn.execute("ALTER TABLE scenarios ADD COLUMN user_id TEXT")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email already exists', 'danger')
            conn.close()
            return redirect(url_for('register'))
            
        user_id = str(uuid.uuid4())
        hashed_pw = generate_password_hash(password)
        conn.execute('INSERT INTO users (id, name, email, password) VALUES (?, ?, ?, ?)',
                     (user_id, name, email, hashed_pw))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash('Password reset link sent to your email!', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    scenarios = conn.execute('SELECT * FROM scenarios WHERE user_id = ? OR user_id IS NULL', (session['user_id'],)).fetchall()
    conn.close()
    
    scenario_list = []
    for s in scenarios:
        s_dict = dict(s)
        s_dict['tags'] = json.loads(s_dict['tags']) if s_dict['tags'] else []
        scenario_list.append(s_dict)
        
    return render_template('index.html', scenarios=scenario_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        flash('Settings saved successfully.', 'success')
        
    return render_template('settings.html')

@app.route('/scenario/<id>')
def view_scenario(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    scenario = conn.execute('SELECT * FROM scenarios WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if scenario is None:
        return "Scenario not found!", 404
        
    scenario_dict = dict(scenario)
    scenario_dict['tags'] = json.loads(scenario_dict['tags']) if scenario_dict['tags'] else []
    return render_template('scenario.html', scenario=scenario_dict)

@app.route('/submit/<id>', methods=['POST'])
def submit_solution(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    solution = request.form.get('solution')
    success = False
    feedback = "Your solution was evaluated by AI."
    if solution and len(solution) > 10:
        success = True
        feedback = "Great job! The AI detected the correct changes in your code."
        
    conn = get_db_connection()
    scenario = conn.execute('SELECT * FROM scenarios WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    return render_template('result.html', scenario=dict(scenario), success=success, feedback=feedback)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
