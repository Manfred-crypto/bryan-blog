import sqlite3, os, mimetypes, glob, math
from flask import Flask, render_template, request, redirect, url_for, abort, session
from cryptography.fernet import Fernet

mimetypes.add_type('text/css', '.css')

SECRET_KEY=b'7_W2N6K4XzR7u1BlM09zS_VvKxN_d8Y3ZpQ2tW4eF1g='
cipher=Fernet(SECRET_KEY)

app=Flask(__name__, static_folder='static')
app.secret_key='VvhVVyZ9yJDDaUMDC8rp7FxX6xqEyGuSlsKSyNvDULmoeU7HTTq78dMhQNH0k5FipR48qmvgHV1vwDBBTpROuG0c48tGoIgubyCpzOEy20dKzCaD9Vzf1QlaqzpH0iFF'

def styed(msg, stat):
    return f'''
    <link rel="stylesheet" href="{url_for('static', filename='sty.css')}">
    <div class="card" style="margin: 50px auto; max-width: 400px; padding: 20px;">
        <h2>Oops!</h2>
        <p>{msg}</p>
        <a href="/">Go Back</a>
    </div>
    ''', stat

def init_data():
    conn=sqlite3.connect('data.db')
    curse=conn.cursor()
    curse.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, charisma INTEGER DEFAULT 0)''')
    curse.execute('''CREATE TABLE IF NOT EXISTS hexes(hex TEXT PRIMARY KEY, name TEXT NOT NULL, char INTEGER DEFAULT 1)''')
    curse.execute('''CREATE TABLE IF NOT EXISTS user_codes(id INTEGER, hex TEXT, PRIMARY KEY (id, hex), FOREIGN KEY (id) REFERENCES users(id), FOREIGN KEY (hex) REFERENCES hexes(hex))''')
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip():
                    parts=line.strip().split(',')
                    if len(parts)==3:
                        curse.execute("INSERT OR IGNORE INTO hexes (hex, name, char) VALUES (?, ?, ?)", (parts[0], parts[1], int(parts[2])))
    conn.commit()
    conn.close()

init_data()

def get_latest_blog_post():
    search_path=os.path.join('templates', 'blog', '*', '*', '*.html')
    files=glob.glob(search_path)
    if not files: return None
    clean_files=[os.path.normpath(f) for f in files]
    clean_files.sort(reverse=True)
    latest_file=clean_files[0]
    parts=latest_file.replace('\\', '/').split('/')
    return f'/blog/{parts[-3]}/{int(parts[-2]):02d}/{int(parts[-1].replace(".html", "")):02d}'

def get_latest_micro_post():
    files=glob.glob('templates/micro/*.html')
    if not files: return None
    latest_id=max(int(os.path.basename(f).replace('.html', '')) for f in files)
    return f"micro/{latest_id}"

@app.route('/')
def home():
    latest_blog=get_latest_blog_post() or '/blog/2026/05/31'
    latest_micro=get_latest_micro_post()
    if 'username' in session:
        username=session['username']
        with sqlite3.connect('data.db') as conn:
            curse=conn.cursor()
            curse.execute("SELECT id, charisma FROM users WHERE username=?", (username,))
            user=curse.fetchone()
            if user is None:
                session.pop('username', None)
                return redirect(url_for('home'))
            uid, total=user[0], user[1]
            curse.execute("SELECT COUNT(*) FROM hexes")
            total_codes=curse.fetchone()[0]
            curse.execute("SELECT COUNT(*) FROM user_codes WHERE id=?", (uid,))
            redeemed=curse.fetchone()[0]
            curse.execute('SELECT uc.hex, sc.name FROM user_codes uc JOIN hexes sc ON uc.hex=sc.hex WHERE uc.id=?', (uid,))
            rows=curse.fetchall()
            diamonds=[{"hex": row[0], "name": row[1]} for row in rows]
        return render_template('index.html', logged_in=True, latest=latest_blog, latest_micro=latest_micro, charisma_score=total, level=math.floor(math.sqrt(total)), diamonds=diamonds, remaining=total_codes-redeemed)
    return render_template('index.html', logged_in=False, latest=latest_blog, latest_micro=latest_micro)

@app.route('/leaderboard')
def leaderboard():
    with sqlite3.connect('data.db') as conn:
        top_users=conn.cursor().execute("SELECT username, charisma FROM users ORDER BY charisma DESC LIMIT 10").fetchall()
    return render_template('leaderboard.html', users=top_users)

@app.route('/micro/<int:post_id>')
def micro_blog(post_id):
    try: return render_template(f'micro/{post_id}.html', logged_in=('username' in session))
    except Exception: abort(404)

@app.route('/signup_page')
def signup_page(): return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    username, password=request.form.get('username'), request.form.get('password')
    if not username or not password: return styed("Fields cannot be blank!", 400)
    try:
        with sqlite3.connect('data.db') as conn:
            conn.cursor().execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, cipher.encrypt(password.encode()).decode()))
            conn.commit()
        return render_template('signup_success.html', username=username)
    except sqlite3.IntegrityError: return styed("Username in use.", 400)

@app.route('/redeem', methods=['POST'])
def redeem():
    if 'username' not in session: return styed("Please log in first", 401)
    hex_code=request.form.get('hex', '').strip()
    with sqlite3.connect('data.db') as conn:
        curse=conn.cursor()
        curse.execute("SELECT id FROM users WHERE username=?", (session['username'],))
        uid=curse.fetchone()[0]
        curse.execute("SELECT char FROM hexes WHERE hex=?", (hex_code,))
        code_data=curse.fetchone()
        if not code_data: return styed("Invalid code!", 400)
        curse.execute("INSERT OR IGNORE INTO user_codes (id, hex) VALUES (?, ?)", (uid, hex_code))
        if curse.rowcount>0:
            curse.execute("UPDATE users SET charisma=charisma+? WHERE id=?", (code_data[0], uid))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username, password=request.form.get('username'), request.form.get('password')
    with sqlite3.connect('data.db') as conn:
        user=conn.cursor().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if user:
        try:
            if cipher.decrypt(user[2].encode()).decode()==password:
                session['username']=username
                return redirect(url_for('home'))
        except Exception: pass
    return render_template('login_fail.html'), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/blog/<year>/<month>/<day>')
def dynamic_blog(year, month, day):
    try: return render_template(f'blog/{year}/{month}/{day}.html', logged_in='username' in session)
    except Exception: abort(404)

@app.route('/hex')
def gate(): return "You entered the gate." if request.args.get('key') else abort(400)

@app.errorhandler(404)
def pnf(e): return render_template('404.html'), 404

@app.errorhandler(400)
def br(e): return render_template('400.html'), 400
