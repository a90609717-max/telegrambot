# admin_panel.py - Веб-панель адміністратора
import os
import hashlib
from datetime import datetime
from functools import wraps

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
import database as db

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key-change-me")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Карта Тривог</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1419; color: #e7e9ea; min-height: 100vh; }
        .navbar { background: #1d2126; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2f3336; }
        .navbar h1 { color: #1d9bf0; font-size: 1.5rem; }
        .navbar a { color: #e7e9ea; text-decoration: none; margin-left: 1.5rem; }
        .navbar a:hover { color: #1d9bf0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .card { background: #1d2126; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #2f3336; }
        .card h2 { margin-bottom: 1rem; color: #1d9bf0; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
        .stat-card { background: #2f3336; border-radius: 12px; padding: 1.5rem; text-align: center; }
        .stat-card h3 { font-size: 2.5rem; color: #1d9bf0; }
        .stat-card p { color: #71767b; margin-top: 0.5rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #2f3336; }
        th { color: #71767b; font-weight: 500; }
        .btn { background: #1d9bf0; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 9999px; cursor: pointer; font-size: 1rem; }
        .btn:hover { background: #1a8cd8; }
        .btn-danger { background: #f4212e; }
        .btn-danger:hover { background: #dc1d28; }
        input, textarea { width: 100%; padding: 1rem; border: 1px solid #2f3336; border-radius: 8px; background: #0f1419; color: #e7e9ea; margin-bottom: 1rem; font-size: 1rem; }
        input:focus, textarea:focus { outline: none; border-color: #1d9bf0; }
        .alert { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
        .alert-success { background: #00ba7c20; border: 1px solid #00ba7c; color: #00ba7c; }
        .alert-error { background: #f4212e20; border: 1px solid #f4212e; color: #f4212e; }
        .login-container { max-width: 400px; margin: 100px auto; }
        .badge { padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; }
        .badge-mod { background: #7856ff20; color: #7856ff; }
        .badge-user { background: #71767b20; color: #71767b; }
        @media (max-width: 768px) { .container { padding: 1rem; } .stats-grid { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <nav class="navbar">
        <h1>🇺🇦 Карта Тривог</h1>
        <div>
            <a href="{{ url_for('dashboard') }}">📊 Дашборд</a>
            <a href="{{ url_for('users') }}">👥 Користувачі</a>
            <a href="{{ url_for('broadcast') }}">📢 Розсилка</a>
            <a href="{{ url_for('shelters') }}">🛡 Укриття</a>
            <a href="{{ url_for('logout') }}">🚪 Вихід</a>
        </div>
    </nav>
    {% endif %}
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="login-container">
    <div class="card">
        <h2>🔐 Вхід в адмін-панель</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Логін" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit" class="btn" style="width:100%">Увійти</button>
        </form>
    </div>
</div>
""")

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<h2 style="margin-bottom: 1.5rem;">📊 Панель управління</h2>
<div class="stats-grid">
    <div class="stat-card">
        <h3>{{ users_count }}</h3>
        <p>👥 Користувачів</p>
    </div>
    <div class="stat-card">
        <h3>{{ regions_count }}</h3>
        <p>🗺 Областей</p>
    </div>
    <div class="stat-card">
        <h3>{{ shelters_count }}</h3>
        <p>🛡 Укриттів</p>
    </div>
    <div class="stat-card">
        <h3>{{ broadcasts_count }}</h3>
        <p>📢 Розсилок</p>
    </div>
</div>

<div class="card">
    <h2>📈 Останні користувачі</h2>
    <table>
        <tr><th>ID</th><th>Ім'я</th><th>Username</th><th>Роль</th><th>Останній візит</th></tr>
        {% for user in recent_users %}
        <tr>
            <td>{{ user.user_id }}</td>
            <td>{{ user.full_name or '-' }}</td>
            <td>@{{ user.username or '-' }}</td>
            <td><span class="badge badge-{{ 'mod' if user.role == 'moderator' else 'user' }}">{{ user.role }}</span></td>
            <td>{{ user.last_seen[:16] if user.last_seen else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="card">
    <h2>📢 Останні розсилки</h2>
    <table>
        <tr><th>Повідомлення</th><th>Отримувачів</th><th>Дата</th></tr>
        {% for b in broadcasts %}
        <tr>
            <td>{{ b.message[:50] }}...</td>
            <td>{{ b.recipients_count }}</td>
            <td>{{ b.sent_at[:16] if b.sent_at else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
""")

USERS_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="card">
    <h2>👥 Користувачі ({{ users|length }})</h2>
    <table>
        <tr><th>ID</th><th>Ім'я</th><th>Username</th><th>Області</th><th>Роль</th><th>Останній візит</th></tr>
        {% for user in users %}
        <tr>
            <td>{{ user.user_id }}</td>
            <td>{{ user.full_name or '-' }}</td>
            <td>@{{ user.username or '-' }}</td>
            <td>{{ user.regions[:30] if user.regions else '-' }}...</td>
            <td><span class="badge badge-{{ 'mod' if user.role == 'moderator' else 'user' }}">{{ user.role }}</span></td>
            <td>{{ user.last_seen[:16] if user.last_seen else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
""")

BROADCAST_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="card">
    <h2>📢 Розсилка повідомлень</h2>
    <form method="POST">
        <textarea name="message" rows="4" placeholder="Текст повідомлення для всіх користувачів..." required></textarea>
        <button type="submit" class="btn">📤 Надіслати всім ({{ users_count }} користувачів)</button>
    </form>
    <p style="margin-top: 1rem; color: #71767b;">⚠️ Повідомлення буде надіслано всім користувачам бота</p>
</div>

<div class="card">
    <h2>📜 Історія розсилок</h2>
    <table>
        <tr><th>Повідомлення</th><th>Отримувачів</th><th>Дата</th></tr>
        {% for b in broadcasts %}
        <tr>
            <td>{{ b.message[:80] }}...</td>
            <td>{{ b.recipients_count }}</td>
            <td>{{ b.sent_at if b.sent_at else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
""")

SHELTERS_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="card">
    <h2>🛡 Додати укриття</h2>
    <form method="POST">
        <input type="text" name="region" placeholder="Область (напр. Київська область)" required>
        <input type="text" name="city" placeholder="Місто" required>
        <input type="text" name="address" placeholder="Адреса" required>
        <input type="text" name="shelter_type" placeholder="Тип (метро, підвал, бункер)" value="укриття">
        <input type="number" name="capacity" placeholder="Місткість (осіб)" value="0">
        <button type="submit" class="btn">➕ Додати укриття</button>
    </form>
</div>

<div class="card">
    <h2>📍 Укриття ({{ shelters|length }})</h2>
    <table>
        <tr><th>Область</th><th>Місто</th><th>Адреса</th><th>Тип</th><th>Місткість</th></tr>
        {% for s in shelters %}
        <tr>
            <td>{{ s.region }}</td>
            <td>{{ s.city }}</td>
            <td>{{ s.address }}</td>
            <td>{{ s.shelter_type }}</td>
            <td>{{ s.capacity }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
""")

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Успішний вхід!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Невірний логін або пароль', 'error')
    
    return render_template_string(LOGIN_TEMPLATE, title="Вхід")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db.init_db()
    users = db.get_all_users()
    regions = db.get_all_regions()
    broadcasts = db.get_broadcast_history()
    
    from database import get_db
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM shelters")
        shelters_count = cur.fetchone()["count"]
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        title="Дашборд",
        users_count=len(users),
        regions_count=len(regions),
        shelters_count=shelters_count,
        broadcasts_count=len(broadcasts),
        recent_users=users[:10],
        broadcasts=broadcasts[:5]
    )

@app.route('/users')
@login_required
def users():
    db.init_db()
    all_users = db.get_all_users()
    return render_template_string(USERS_TEMPLATE, title="Користувачі", users=all_users)

@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    db.init_db()
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            users = db.get_all_users()
            db.add_broadcast(message, session.get('username', 'admin'), len(users))
            flash(f'Розсилка запланована для {len(users)} користувачів! Використайте /broadcast в боті.', 'success')
        return redirect(url_for('broadcast'))
    
    users_count = db.get_users_count()
    broadcasts = db.get_broadcast_history()
    return render_template_string(
        BROADCAST_TEMPLATE,
        title="Розсилка",
        users_count=users_count,
        broadcasts=broadcasts
    )

@app.route('/shelters', methods=['GET', 'POST'])
@login_required
def shelters():
    db.init_db()
    
    if request.method == 'POST':
        region = request.form.get('region')
        city = request.form.get('city')
        address = request.form.get('address')
        shelter_type = request.form.get('shelter_type', 'укриття')
        capacity = int(request.form.get('capacity', 0))
        
        if region and city and address:
            db.add_shelter(region, city, address, shelter_type, capacity)
            flash('Укриття додано!', 'success')
        return redirect(url_for('shelters'))
    
    from database import get_db
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM shelters ORDER BY region, city")
        all_shelters = [dict(row) for row in cur.fetchall()]
    
    return render_template_string(SHELTERS_TEMPLATE, title="Укриття", shelters=all_shelters)

@app.route('/api/stats')
@login_required
def api_stats():
    db.init_db()
    return jsonify({
        'users': db.get_users_count(),
        'regions': len(db.get_all_regions()),
        'broadcasts': len(db.get_broadcast_history())
    })

if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
