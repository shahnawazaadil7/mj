from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
import os
import pandas as pd
from werkzeug.security import generate_password_hash
from models.recommender import recommend_content
from dataset import chatbot_data

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
        
# Initialize the user database (JSON file)
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as db:
            json.dump([], db)  # Create an empty user list

# Read data from the user database
def read_db():
    with open(DB_FILE, 'r') as db:
        try:
            return json.load(db)
        except json.JSONDecodeError:
            return []

# Write data to the user database
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

# Route: To-Do List
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

# Route: Update To-Do List
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

# Route: Delete To-Do
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
            
            # Redirect to the next page if it exists or the homepage
            next_url = session.pop('next', url_for('home'))
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

# Get response from dataset
def get_response(user_input):
    responses = chatbot_data()  # Load the dataset (dictionary)
    return responses.get(user_input.lower(), "Sorry, I didn't understand that.")

# Route: Chatbot
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        data = request.json
        user_input = data.get("message", "").strip()  # Get input message
        response = get_response(user_input)  # Get chatbot response
        return jsonify({"response": response})  # Return JSON response
    return render_template("chat.html")

# Route: Team Page
@app.route('/team')
def team():
    return render_template('team.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Initialize databases and run the app
if __name__ == "__main__":
    init_db()  # Initialize user database
    init_todo_db()  # Initialize to-do database
    app.run(debug=True)