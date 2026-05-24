import sqlite3,os
import mimetypes
mimetypes.add_type('text/css', '.css')
from flask import Flask, render_template, request, redirect, url_for, abort
# from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
SECRET_KEY=b'7_W2N6K4XzR7u1BlM09zS_VvKxN_d8Y3ZpQ2tW4eF1g='
cipher=Fernet(SECRET_KEY)
app=Flask(__name__)
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
        encrypted_bytes=cipher.encrypt(password.encode())
        encrypted_string=encrypted_bytes.decode()
        with sqlite3.connect('data.db') as conn:
            curse=conn.cursor()
            curse.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_string))
            conn.commit()
        return f"Account created for {username}! <a href='/'>Go back to login</a>"
    except sqlite3.IntegrityError:
        return "That username is already taken! <a href='/signup_page'>Try a different one</a>", 400
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    with sqlite3.connect('data.db') as conn:
        curse = conn.cursor()
        curse.execute("SELECT * FROM users WHERE username=?", (username,))
        user = curse.fetchone()
    if user:
        stored_encrypted_string=user[2]
        try:
            decrypted_bytes=cipher.decrypt(stored_encrypted_string.encode())
            plain_text_password=decrypted_bytes.decode()
            if plain_text_password==password:
                return f"<h1>Success!</h1> Welcome back, {username}!"
        except Exception:
            pass
    return render_template('login_fail.html'), 401

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

@app.route('/hex')
def gate():
    key=request.args.get('key')
    if not key:
        abort(400)
    return "You entered the gate."

if __name__=='__main__':
    init_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
