from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
from flask import Flask, render_template, request, jsonify
from webquery import WebQuery
import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from models.recommender import recommend_content

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session management
app.jinja_env.globals.update(enumerate=enumerate)

# Constants
DB_FILE = 'users.json'

TODO_DB_FILE = 'todos.json'

# Initialize the To-Do database
def init_todo_db():
    if not os.path.exists(TODO_DB_FILE):
        with open(TODO_DB_FILE, 'w') as db:
            json.dump({}, db)  # Create an empty dictionary for todos

# Read To-Do List database
def read_todo_db():
    with open(TODO_DB_FILE, 'r') as db:
        try:
            return json.load(db)
        except json.JSONDecodeError:
            return {}

# Update To-Do List database
def update_todo_db(username, todos):
    data = read_todo_db()
    data[username] = todos
    with open(TODO_DB_FILE, 'w') as db:
        json.dump(data, db)
        
# Initialize the database (JSON file)
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as db:
            json.dump([], db)  # Create an empty user list

# Read data from the database
def read_db():
    with open(DB_FILE, 'r') as db:
        try:
            return json.load(db)
        except json.JSONDecodeError:
            return []

# Write data to the database
def write_db(data):
    with open(DB_FILE, 'w') as db:
        json.dump(data, db)

# Load dataset
data = pd.read_csv("data/data.csv")  # Ensure the path is correct and accessible

# Before request handler to check if the user is logged in
@app.before_request
def check_login():
    if not session.get('logged_in') and request.endpoint not in ['login', 'register', 'home', 'static']:
        session['next'] = request.url  # Save the current URL to redirect after login
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))

# Route: Homepage
@app.route("/")
def home():
    return render_template("index.html")

# Route: Tutorials
@app.route("/tutorials")
def tutorials():
    return render_template("tutorials.html")

# Route: Dashboard (requires login)
@app.route("/dashboard")
def dashboard():
    analytics = {
        "followers": 1200,
        "engagement_rate": 8.5,
        "recent_posts": ["How to craft jewelry", "5 tips for better home decor photos"],
    }
    return render_template("dashboard.html", analytics=analytics, username=session.get('username'))

# Route: Recommender
@app.route("/recommender", methods=["GET", "POST"])
def recommender():
    if request.method == "POST":
        # Get form data
        age = int(request.form.get("age", 0))
        content_type = request.form.get("content_type", "")
        skill_level = request.form.get("skill_level", "")

        # Generate recommendations
        recommendations = recommend_content(age, content_type, skill_level)

        # Render results
        return render_template("results.html", recommendations=recommendations)

    return render_template("recommender.html")

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    if not session.get('logged_in'):
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username')
    todos = read_todo_db().get(username, [])  # Fetch user-specific todos

    if request.method == 'POST':
        task = request.form.get('task', '').strip()
        if task:
            todos.append({'task': task, 'completed': False})
            update_todo_db(username, todos)
            flash('Task added successfully!', 'success')
        else:
            flash('Task cannot be empty.', 'danger')

    return render_template('todo.html', todos=todos)

@app.route('/todo/update', methods=['POST'])
def update_todo():
    if not session.get('logged_in'):
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username')
    todos = read_todo_db().get(username, [])

    task_index = int(request.form.get('task_index', -1))
    if 0 <= task_index < len(todos):
        todos[task_index]['completed'] = not todos[task_index]['completed']
        update_todo_db(username, todos)
        flash('Task updated successfully!', 'success')

    return redirect(url_for('todo'))

@app.route('/todo/delete', methods=['POST'])
def delete_todo():
    if not session.get('logged_in'):
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username')
    todos = read_todo_db().get(username, [])

    task_index = int(request.form.get('task_index', -1))
    if 0 <= task_index < len(todos):
        todos.pop(task_index)
        update_todo_db(username, todos)
        flash('Task deleted successfully!', 'info')

    return redirect(url_for('todo'))

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials in the JSON database
        users = read_db()
        user = next((u for u in users if u['username'] == username), None)

        if user:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            
            # Redirect to the next page if it exists or the dashboard
            next_url = session.pop('next', url_for('dashboard'))
            return redirect(next_url)
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Add user to the JSON database
        users = read_db()
        if any(u['username'] == username for u in users):
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users.append({'username': username, 'password': hashed_password})
            write_db(users)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# Global variable for WebQuery instance
webquery_instance = None

@app.route("/chatbot")
def chatbot():
    """Render the chatbot page."""
    return render_template("chat.html")

@app.route("/set_api_key", methods=["POST"])
def set_api_key():
    """Set the OpenAI API key dynamically."""
    global webquery_instance
    api_key = request.form.get("api_key")
    if api_key:
        try:
            webquery_instance = WebQuery(api_key)
            return jsonify({"message": "API key set successfully!"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to set API key: {str(e)}"}), 400
    return jsonify({"error": "Invalid API key."}), 400

@app.route("/ingest_url", methods=["POST"])
def ingest_url():
    """Ingest a specific URL for the WebQuery instance."""
    global webquery_instance
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided."}), 400

    if webquery_instance is None:
        return jsonify({"error": "WebQuery instance not initialized. Set the API key first."}), 400

    result = webquery_instance.ingest(url)
    if "successfully" in result.lower():
        return jsonify({"message": result}), 200
    return jsonify({"error": result}), 400

@app.route("/ask_question", methods=["POST"])
def ask_question():
    """Ask a question to the pre-ingested or dynamically ingested data."""
    global webquery_instance
    question = request.form.get("question")
    if not question:
        return jsonify({"error": "No question provided."}), 400

    if webquery_instance is None:
        return jsonify({"error": "WebQuery instance not initialized. Set the API key first."}), 400

    try:
        answer = webquery_instance.ask(question)
        return jsonify({"answer": answer}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process question: {str(e)}"}), 400

@app.route('/team')
def team():
    # Render the team page and pass any necessary variables (if required)
    return render_template('team.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()  # Initialize user database
    init_todo_db()  # Initialize to-do database
    app.run(debug=True, use_reloader=False, threaded=False)
