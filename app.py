import sqlite3
import os
import mimetypes
import glob

mimetypes.add_type('text/css', '.css')

from flask import Flask, render_template, request, redirect, url_for, abort, session
from cryptography.fernet import Fernet

SECRET_KEY=b'7_W2N6K4XzR7u1BlM09zS_VvKxN_d8Y3ZpQ2tW4eF1g='
cipher=Fernet(SECRET_KEY)

app=Flask(__name__)
app.secret_key='VvhVVyZ9yJDDaUMDC8rp7FxX6xqEyGuSlsKSyNvDULmoeU7HTTq78dMhQNH0k5FipR48qmvgHV1vwDBBTpROuG0c48tGoIgubyCpzOEy20dKzCaD9Vzf1QlaqzpH0iFF'

def init_data():
    conn=sqlite3.connect('data.db')
    curse=conn.cursor()
    curse.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_data()

def get_latest_blog_post():
    search_path=os.path.join('templates', 'blog', '*', '*', '*.html')
    files=glob.glob(search_path)
    if not files:
        return None

    clean_files=[os.path.normpath(f) for f in files]
    clean_files.sort(reverse=True)
    latest_file=clean_files[0]

    clean_path=latest_file.replace('\\', '/')
    parts=clean_path.split('/')

    year=parts[-3]
    month=parts[-2]
    day=parts[-1].replace('.html', '')

    return f'/blog/{year}/{month}/{day}'

@app.route('/')
def home():
    latest=get_latest_blog_post()
    if not latest:
        latest='/blog/2026/05/30'

    if 'username' in session:
        return redirect(latest)

    return render_template('index.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    username=request.form.get('username')
    password=request.form.get('password')

    if not username or not password:
        return "Fields cannot be blank!", 400

    encrypted_password=cipher.encrypt(password.encode()).decode()

    try:
        with sqlite3.connect('data.db') as conn:
            curse=conn.cursor()
            curse.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
            conn.commit()
        return f"<h1>Success!</h1> Account created for {username}! <a href='/'>Go log in</a>"
    except sqlite3.IntegrityError:
        return "<h1>Error</h1> That username is already in use. Choose another one", 400

@app.route('/login', methods=['POST'])
def login():
    username=request.form.get('username')
    password=request.form.get('password')

    with sqlite3.connect('data.db') as conn:
        curse=conn.cursor()
        curse.execute("SELECT * FROM users WHERE username=?", (username,))
        user=curse.fetchone()

    if user:
        stored_encrypted_string=user[2]
        try:
            decrypted_bytes=cipher.decrypt(stored_encrypted_string.encode())
            plain_text_password=decrypted_bytes.decode()
            if plain_text_password==password:
                session['username']=username
                latest=get_latest_blog_post() or '/blog/2026/05/30'
                return redirect(latest)
        except Exception:
            pass

    return render_template('login_fail.html'), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/blog/<year>/<month>/<day>')
def dynamic_blog(year, month, day):
    try:
        logged_in='username' in session
        return render_template(f'blog/{year}/{month}/{day}.html', logged_in=logged_in)
    except Exception:
        abort(404)