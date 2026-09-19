import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

GOLD = '#D4AF37'
INK = '#090A0C'
PANEL = '#111318'
LINE = '#272B34'
MUTED = '#8B929F'
WHITE = '#F7F7F4'
GREEN = '#55C98A'
RED = '#F05D5E'
AMBER = '#F0A94B'

DATA_DIR = os.environ.get('QALACH_DATA_DIR', os.path.dirname(__file__))
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_FILE = os.path.join(DATA_DIR, 'qalach_darak.db')


def initialize_database():
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                location TEXT NOT NULL,
                start_date TEXT,
                status TEXT NOT NULL,
                area TEXT,
                rooms TEXT,
                salon REAL DEFAULT 0,
                measurements TEXT DEFAULT '{}'
            )
        ''')
        columns = {row[1] for row in connection.execute('PRAGMA table_info(clients)').fetchall()}
        if 'measurements' not in columns:
            connection.execute("ALTER TABLE clients ADD COLUMN measurements TEXT DEFAULT '{}' ")


def get_db():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def get_client_by_id(client_id):
    with get_db() as connection:
        row = connection.execute('''
            SELECT id, name, phone, location, start_date, status, area, rooms, salon, measurements
            FROM clients WHERE id = ?
        ''', (client_id,)).fetchone()
    return dict(row) if row else None


initialize_database()

HTML = '''
<!doctype html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>قلش دارك</title>
  <style>
    body { font-family: Tahoma, sans-serif; margin: 0; background: #0a0b0d; color: #f3f3f1; }
    .topbar { background: #111318; border-bottom: 1px solid #272b34; padding: 18px 30px; }
    .container { max-width: 1100px; margin: 0 auto; padding: 24px 18px 60px; }
    .card { background: #111318; border: 1px solid #272b34; border-radius: 16px; padding: 22px; }
    h1, h2, h3 { color: #fff; }
    .gold { color: #D4AF37; }
    .muted { color: #8B929F; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 18px; }
    .stats { background: #171a21; border-radius: 14px; padding: 20px; border: 1px solid #272b34; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #272b34; padding: 12px; text-align: right; }
    form { display: grid; gap: 12px; }
    input, select, textarea { width: 100%; box-sizing: border-box; padding: 10px 12px; border-radius: 10px; border: 1px solid #272b34; background: #171a21; color: #fff; }
    button { border: none; border-radius: 10px; background: #D4AF37; color: #090A0C; padding: 12px 20px; font-weight: bold; cursor: pointer; }
    .status { display: inline-block; padding: 7px 12px; border-radius: 999px; font-size: 12px; }
    .waiting { background: rgba(240,93,94,0.12); color: #F05D5E; }
    .progress { background: rgba(240,169,75,0.12); color: #F0A94B; }
    .done { background: rgba(85,201,138,0.12); color: #55C98A; }
    @media (max-width: 700px) { .container { padding: 16px 12px 48px; } }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="container" style="padding-top:12px;padding-bottom:12px;">
      <h1 style="margin:0;">قلش دارك <span class="gold">| إدارة الورشة</span></h1>
    </div>
  </div>

  <div class="container">
    <div class="grid" style="margin-bottom: 20px;">
      <div class="stats"><div class="muted">إجمالي الورشات</div><h2>{{ total_clients }}</h2></div>
      <div class="stats"><div class="muted">قيد التنفيذ</div><h2>{{ in_progress }}</h2></div>
      <div class="stats"><div class="muted">بانتظار التحضير</div><h2>{{ waiting }}</h2></div>
      <div class="stats"><div class="muted">مكتملة</div><h2>{{ completed }}</h2></div>
    </div>

    <div class="card">
      <h2>إضافة ورشة جديدة</h2>
      <form method="post" action="{{ url_for('create_client') }}">
        <input name="name" placeholder="اسم الزبون" required>
        <input name="phone" placeholder="رقم الهاتف" required>
        <input name="location" placeholder="الموقع" required>
        <input name="start_date" placeholder="تاريخ بدء الأشغال" value="{{ today }}">
        <select name="status">
          <option value="في الانتظار والتحضير">في الانتظار والتحضير</option>
          <option value="قيد التنفيذ الميداني حالياً">قيد التنفيذ الميداني حالياً</option>
          <option value="تم تسليم المفتاح بنجاح">تم تسليم المفتاح بنجاح</option>
        </select>
        <input name="area" placeholder="المساحة">
        <input name="rooms" placeholder="عدد الغرف">
        <button type="submit">حفظ الورشة</button>
      </form>
    </div>

    <div class="card" style="margin-top:20px;">
      <h2>إضافة ورشة بسرعة</h2>
      <form method="post" action="{{ url_for('quick_add_client') }}">
        <input name="name" placeholder="اسم الزبون" required>
        <input name="phone" placeholder="رقم الهاتف" required>
        <input name="location" placeholder="الموقع" required>
        <button type="submit">إضافة ورشة بسرعة</button>
      </form>
    </div>

    <div class="card" style="margin-top:20px;">
      <h2>جدول الزبائن</h2>
      <table>
        <thead>
          <tr>
            <th>الاسم</th>
            <th>الهاتف</th>
            <th>الموقع</th>
            <th>التاريخ</th>
            <th>الحالة</th>
            <th>المساحة</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {% for client in clients %}
          <tr>
            <td>{{ client['name'] }}</td>
            <td>{{ client['phone'] }}</td>
            <td>{{ client['location'] }}</td>
            <td>{{ client['start_date'] or 'غير محدد' }}</td>
            <td>
              {% if client['status'] == 'في الانتظار والتحضير' %}<span class="status waiting">{{ client['status'] }}</span>
              {% elif client['status'] == 'قيد التنفيذ الميداني حالياً' %}<span class="status progress">{{ client['status'] }}</span>
              {% else %}<span class="status done">{{ client['status'] }}</span>
              {% endif %}
            </td>
            <td>{{ client['area'] or 'غير محدد' }}</td>
            <td>
              <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                <a href="{{ url_for('edit_client', client_id=client['id']) }}" style="color:#D4AF37; text-decoration:none;">تعديل</a>
                <form method="post" action="{{ url_for('delete_client', client_id=client['id']) }}" style="display:inline;">
                  <button type="submit">حذف</button>
                </form>
                <form method="post" action="{{ url_for('update_status', client_id=client['id']) }}" style="display:flex; gap:6px; align-items:center;">
                  <select name="status" style="width:auto; min-width:150px;">
                    <option value="في الانتظار والتحضير" {% if client['status'] == 'في الانتظار والتحضير' %}selected{% endif %}>في الانتظار والتحضير</option>
                    <option value="قيد التنفيذ الميداني حالياً" {% if client['status'] == 'قيد التنفيذ الميداني حالياً' %}selected{% endif %}>قيد التنفيذ الميداني حالياً</option>
                    <option value="تم تسليم المفتاح بنجاح" {% if client['status'] == 'تم تسليم المفتاح بنجاح' %}selected{% endif %}>تم تسليم المفتاح بنجاح</option>
                  </select>
                  <button type="submit">تغيير الحالة</button>
                </form>
              </div>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="7" class="muted">لا توجد ورشات مسجلة.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
'''


@app.route('/', methods=['GET'])
def index():
    with get_db() as connection:
        clients = connection.execute('''
            SELECT name, phone, location, start_date, status, area, rooms, salon, measurements
            FROM clients ORDER BY id DESC
        ''').fetchall()

    total_clients = len(clients)
    waiting = sum(1 for c in clients if c['status'] == 'في الانتظار والتحضير')
    in_progress = sum(1 for c in clients if c['status'] == 'قيد التنفيذ الميداني حالياً')
    completed = sum(1 for c in clients if c['status'] == 'تم تسليم المفتاح بنجاح')

    return render_template_string(HTML, clients=clients, total_clients=total_clients, waiting=waiting, in_progress=in_progress, completed=completed, today=datetime.now().strftime('%d/%m/%Y'))


@app.route('/create', methods=['POST'])
def create_client():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    location = request.form.get('location', '').strip()
    start_date = request.form.get('start_date', '').strip() or datetime.now().strftime('%d/%m/%Y')
    status = request.form.get('status', 'في الانتظار والتحضير')
    area = request.form.get('area', '').strip()
    rooms = request.form.get('rooms', '').strip()

    if not name or not phone or not location:
        return 'الاسم والهاتف والموقع مطلوبان', 400

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute('''
            INSERT INTO clients (name, phone, location, start_date, status, area, rooms, salon, measurements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, location, start_date, status, area, rooms, 0, '{}'))

    return redirect(url_for('index'))


@app.route('/quick-add', methods=['POST'])
def quick_add_client():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    location = request.form.get('location', '').strip()

    if not name or not phone or not location:
        return 'الاسم والهاتف والموقع مطلوبان', 400

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute('''
            INSERT INTO clients (name, phone, location, start_date, status, area, rooms, salon, measurements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, location, datetime.now().strftime('%d/%m/%Y'), 'في الانتظار والتحضير', 'غير محدد', '', 0, '{}'))

    return redirect(url_for('index'))


@app.route('/delete/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    return redirect(url_for('index'))


@app.route('/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    client = get_client_by_id(client_id)
    if client is None:
        return 'الزبون غير موجود', 404

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        start_date = request.form.get('start_date', '').strip() or client.get('start_date', '')
        status = request.form.get('status', client.get('status', 'في الانتظار والتحضير'))
        area = request.form.get('area', '').strip()
        rooms = request.form.get('rooms', '').strip()

        if not name or not phone or not location:
            return 'الاسم والهاتف والموقع مطلوبان', 400

        with sqlite3.connect(DATABASE_FILE) as connection:
            connection.execute('''
                UPDATE clients
                SET name = ?, phone = ?, location = ?, start_date = ?, status = ?, area = ?, rooms = ?
                WHERE id = ?
            ''', (name, phone, location, start_date, status, area, rooms, client_id))
        return redirect(url_for('index'))

    return f'''
        <html dir="rtl" lang="ar">
        <head><meta charset="utf-8"><title>تعديل الزبون</title>
        <style>body{{font-family:Tahoma,sans-serif;background:#0a0b0d;color:#fff;padding:30px}} input,select{{width:100%;padding:10px;margin:10px 0;border-radius:10px;border:1px solid #272b34;background:#171a21;color:#fff}} button{{background:#D4AF37;color:#090A0C;border:none;padding:12px 18px;border-radius:10px;font-weight:bold;cursor:pointer}} a{{color:#D4AF37;text-decoration:none}} .card{{max-width:500px;margin:auto;background:#111318;padding:20px;border-radius:16px;border:1px solid #272b34}}</style>
        </head>
        <body>
        <div class="card">
            <h2>تعديل بيانات الزبون</h2>
            <form method="post">
                <input name="name" value="{client['name']}" required>
                <input name="phone" value="{client['phone']}" required>
                <input name="location" value="{client['location']}" required>
                <input name="start_date" value="{client['start_date'] or ''}">
                <select name="status">
                    <option value="في الانتظار والتحضير" {'selected' if client['status']=='في الانتظار والتحضير' else ''}>في الانتظار والتحضير</option>
                    <option value="قيد التنفيذ الميداني حالياً" {'selected' if client['status']=='قيد التنفيذ الميداني حالياً' else ''}>قيد التنفيذ الميداني حالياً</option>
                    <option value="تم تسليم المفتاح بنجاح" {'selected' if client['status']=='تم تسليم المفتاح بنجاح' else ''}>تم تسليم المفتاح بنجاح</option>
                </select>
                <input name="area" value="{client['area'] or ''}">
                <input name="rooms" value="{client['rooms'] or ''}">
                <button type="submit">حفظ التعديلات</button>
                <p><a href="{url_for('index')}">رجوع</a></p>
            </form>
        </div>
        </body>
        </html>'''


@app.route('/status/<int:client_id>', methods=['POST'])
def update_status(client_id):
    status = request.form.get('status', 'في الانتظار والتحضير')
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute('UPDATE clients SET status = ? WHERE id = ?', (status, client_id))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8550')))
