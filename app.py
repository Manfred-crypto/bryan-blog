import sqlite3,os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
def init_data():
    conn=sqlite3.connect('data.db')
    curse=conn.cursor()
    curse.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Please fill out all fields!", 400
    try:
        with sqlite3.connect('data.db') as conn:
            hash=generate_password_hash(password, method='pbkdf2:sha256')
            curse=conn.cursor()
            curse.execute("INSERT INTO users (username, password) VALUES (?, ?)",(username,hash))
            conn.commit()
        return f"Account created for {username}! ,<a href='/'>Go back to login</a>"
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    with sqlite3.connect('data.db') as conn:
        curse=conn.cursor()
        curse.execute("SELECT * FROM users WHERE username=?",(username,))
        user=curse.fetchone()
    if user:
        datapw=user[2]
        if check_password_hash(datapw, password):
            return f"<h1>Success!</h1> Welcome back {username}."
        else:
            return f"YOU SHALL NOT PASS!"
    else:
        return f"YOU SHALL NOT PASS!"

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

if __name__=='__main__':
    init_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
