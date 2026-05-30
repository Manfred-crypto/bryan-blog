import sqlite3, os, mimetypes, glob, math

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
            password TEXT NOT NULL,
            charisma INTEGER DEFAULT 0
        )
    ''')
    curse.execute('''
        CREATE TABLE IF NOT EXISTS secret_codes(
            hex TEXT PRIMARY KEY,
            display_name TEXT NOT NULL DEFAULT 'Mystery Secret',
            points_value INTEGER DEFAULT 1
        )
    ''')
    curse.execute('''
        CREATE TABLE IF NOT EXISTS user_codes(
            user_id INTEGER,
            hex TEXT,
            PRIMARY KEY (user_id, hex),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (hex) REFERENCES secret_codes(hex)
        )
    ''')
    diamonds=[
        ('5468697349734372756369616c', 'Readme!', 4),
        ('4e6175676874794368696c64', '400', 2),
        ('506c656173654765744f7574', '404', 0),
        ('466c697020616c6c20302f31', 'Beginner!', 7),
        ('b993968fdf9e9393dfcfd0ce', 'Puzzle solved.', 14)
    ]
    curse.executemany("INSERT OR IGNORE INTO secret_codes (hex, display_name, points_value) VALUES (?, ?, ?)", diamonds)
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
    latest=get_latest_blog_post() or '/blog/2026/05/30'
    if 'username' in session:
        username=session['username']
        with sqlite3.connect('data.db') as conn:
            curse=conn.cursor()
            curse.execute("SELECT id, charisma FROM users WHERE username=?", (username,))
            user=curse.fetchone()
            user_id, total=user[0], user[1]
            calculated_level=math.floor(math.sqrt(total))
            curse.execute('''
                SELECT uc.hex, sc.display_name
                FROM user_codes uc
                JOIN secret_codes sc ON uc.hex = sc.hex
                WHERE uc.user_id = ?
            ''', (user_id,))
            rows=curse.fetchall()
            found_diamonds=[]
            for row in rows:
                found_diamonds.append({"hex": row[0], "name": row[1]})
        return render_template('index.html',
                               logged_in=True,
                               latest=latest,
                               charisma_score=total,
                               level=calculated_level,
                               diamonds=found_diamonds)
    return render_template('index.html', logged_in=False)

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

@app.route('/redeem', methods=['POST'])
def redeem():
    if 'username' not in session:
        return "Please log in first", 401
    hex=request.form.get('hex', '').strip()
    username=session['username']
    if len(hex)<24 or len(hex)>26:
        return "Invalid code length!", 400
    with sqlite3.connect('data.db') as conn:
        curse=conn.cursor()
        curse.execute("SELECT id FROM users WHERE username=?", (username,))
        user_id=curse.fetchone()[0]
        curse.execute("SELECT points_value FROM secret_codes WHERE hex=?", (hex,))
        code_data=curse.fetchone()
        if not code_data:
            return "That code is invalid!", 400
        points=code_data[0]
        curse.execute("SELECT 1 FROM user_codes WHERE user_id=? AND hex=?", (user_id, hex))
        if curse.fetchone():
            return "You have already redeemed this code!", 400
        curse.execute("INSERT INTO user_codes (user_id, hex) VALUES (?, ?)", (user_id, hex))
        curse.execute("UPDATE users SET charisma=charisma+? WHERE id=?", (points, user_id))
        conn.commit()
    return redirect(url_for('home'))

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
                return redirect(url_for('home'))
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
