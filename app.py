import sqlite3,os
import mimetypes
mimetypes.add_type('text/css', '.css')
from flask import Flask, render_template, request, redirect, url_for, abort, request
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
            return f'''
            <style>
                .earthquake {{
                    display: inline-block;
                    animation: shake 0.2s infinite;
                    color: #ff00ff;
                    font-size: 3rem;
                    text-shadow: 0 0 20px #ff00ff;
                }}
                @keyframes shake {{
                    0% {{ transform: translate(1px, 1px) rotate(0deg); }}
                    10% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
                    20% {{ transform: translate(-3px, 0px) rotate(1deg); }}
                    30% {{ transform: translate(3px, 2px) rotate(0deg); }}
                    40% {{ transform: translate(1px, -1px) rotate(1deg); }}
                    50% {{ transform: translate(-1px, 2px) rotate(-1deg); }}
                    60% {{ transform: translate(-3px, 1px) rotate(0deg); }}
                    70% {{ transform: translate(3px, 1px) rotate(-1deg); }}
                    80% {{ transform: translate(-1px, -1px) rotate(1deg); }}
                    90% {{ transform: translate(1px, 2px) rotate(0deg); }}
                    100% {{ transform: translate(1px, -2px) rotate(-1deg); }}
                }}
            </style>
            <h1 class="earthquake">YOU SHALL NOT PASS</h1>
            '''
    else:
        return f'''
        <style>
            .earthquake {{
                display: inline-block;
                animation: shake 0.2s infinite;
                color: #ff00ff;
                font-size: 3rem;
                text-shadow: 0 0 20px #ff00ff;
            }}
            @keyframes shake {{
                0% {{ transform: translate(1px, 1px) rotate(0deg); }}
                10% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
                20% {{ transform: translate(-3px, 0px) rotate(1deg); }}
                30% {{ transform: translate(3px, 2px) rotate(0deg); }}
                40% {{ transform: translate(1px, -1px) rotate(1deg); }}
                50% {{ transform: translate(-1px, 2px) rotate(-1deg); }}
                60% {{ transform: translate(-3px, 1px) rotate(0deg); }}
                70% {{ transform: translate(3px, 1px) rotate(-1deg); }}
                80% {{ transform: translate(-1px, -1px) rotate(1deg); }}
                90% {{ transform: translate(1px, 2px) rotate(0deg); }}
                100% {{ transform: translate(1px, -2px) rotate(-1deg); }}
            }}
        </style>
        <h1 class="earthquake">YOU SHALL NOT PASS</h1>
        '''

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(400)
def page_not_found(e):
    return render_template('400.html'), 400

from flask import abort, request

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
