from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB = 'myungga.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        cat TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS exp_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        ctype TEXT NOT NULL,
        guest TEXT,
        tour TEXT,
        guide TEXT,
        payment TEXT NOT NULL,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        cat TEXT NOT NULL,
        vendor TEXT,
        amount REAL NOT NULL,
        payment TEXT NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Seed default menu if empty
    if c.execute('SELECT COUNT(*) FROM menu').fetchone()[0] == 0:
        default_menu = [
            ('Tour Samgyeopsal Set','TOUR','Food',350),
            ('Tour Hanjeongsik Set','TOUR','Food',300),
            ('Tour Bibimbap Set','TOUR','Food',250),
            ('Tour Soju','TOUR','Beverage',350),
            ('Tour Sangsom','TOUR','Beverage',350),
            ('Tour Coke','TOUR','Beverage',50),
            ('Tour Sprite','TOUR','Beverage',50),
            ('Myungga Samgyeopsal Unlimited','WALK-IN','Food',359),
            ('Myungga Hanjeongsik Set (4 persons)','WALK-IN','Food',1199),
            ('Promotion Samgyeopsal Unlimited','WALK-IN','Food',219),
            ('Jeyuk Dupbap Set','WALK-IN','Food',189),
            ('Flower Bibimbap Set','WALK-IN','Food',169),
            ('Kimchi Stew Set','WALK-IN','Food',219),
            ('Soybean Paste Stew Set','WALK-IN','Food',219),
            ('Grilled Mackerel Set','WALK-IN','Food',259),
            ('Tteokbokki Set','WALK-IN','Food',189),
            ('Korean Pancake (Pajeon)','WALK-IN','Food',199),
            ('Bossam','WALK-IN','Food',349),
            ('Jeyuk Bokkeum','WALK-IN','Food',249),
            ('Gamjatang (2 persons)','WALK-IN','Food',549),
            ('Kimchi Cold Noodles','WALK-IN','Food',159),
            ('Ramen Set','WALK-IN','Food',149),
            ('Japchae','WALK-IN','Food',129),
            ('Flat Dumplings','WALK-IN','Food',189),
            ('Seaweed Roll (4 pcs)','WALK-IN','Food',50),
            ('Fried Dumplings (4 pcs)','WALK-IN','Food',50),
            ('Ramen Add-on','WALK-IN','Food',25),
            ('Cheese','WALK-IN','Food',100),
            ('Rice','WALK-IN','Food',10),
            ('Soju + Beer Set (Somek)','WALK-IN','Beverage',350),
            ('Soju','WALK-IN','Beverage',250),
            ('Sangsom 330ml','WALK-IN','Beverage',250),
            ('Coke','WALK-IN','Beverage',40),
            ('Sprite','WALK-IN','Beverage',40),
            ('Water','COMMON','Beverage',10),
            ('Chang Beer 630ml','COMMON','Beverage',150),
            ('Singha Beer 630ml','COMMON','Beverage',150),
            ('Regency 350ml','COMMON','Beverage',700),
            ('Watermelon Smoothie','COMMON','Beverage',60),
            ('Mango Smoothie','COMMON','Beverage',60),
            ('Iced Coffee','COMMON','Beverage',50),
            ('Hot Coffee','COMMON','Beverage',50),
            ('Iced Latte','COMMON','Beverage',60),
            ('Hot Latte','COMMON','Beverage',60),
            ('Honey Cinnamon Tea','COMMON','Beverage',60),
            ('Flower Tea','COMMON','Beverage',60),
        ]
        c.executemany('INSERT INTO menu (name,type,cat,price) VALUES (?,?,?,?)', default_menu)

    # Seed default expense categories if empty
    if c.execute('SELECT COUNT(*) FROM exp_categories').fetchone()[0] == 0:
        default_cats = [
            ('Food Ingredient',), ('Beverage Stock',), ('Supplies',),
            ('Utilities (Water/Electric/Gas)',), ('Salary',), ('Rent',),
            ('Marketing',), ('Equipment / Repair',), ('Other',)
        ]
        c.executemany('INSERT INTO exp_categories (name) VALUES (?)', default_cats)

    conn.commit()
    conn.close()

# ─── MENU ───────────────────────────────────────────────────
@app.route('/api/menu', methods=['GET'])
def get_menu():
    conn = get_db()
    rows = conn.execute('SELECT * FROM menu WHERE active=1 ORDER BY type,cat,name').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/menu', methods=['POST'])
def add_menu():
    d = request.json
    conn = get_db()
    conn.execute('INSERT INTO menu (name,type,cat,price) VALUES (?,?,?,?)',
                 (d['name'], d['type'], d['cat'], d['price']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/menu/<int:id>', methods=['PUT'])
def update_menu(id):
    d = request.json
    conn = get_db()
    conn.execute('UPDATE menu SET name=?,type=?,cat=?,price=? WHERE id=?',
                 (d['name'], d['type'], d['cat'], d['price'], id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/menu/<int:id>', methods=['DELETE'])
def delete_menu(id):
    conn = get_db()
    conn.execute('UPDATE menu SET active=0 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── EXPENSE CATEGORIES ────────────────────────────────────
@app.route('/api/exp_categories', methods=['GET'])
def get_exp_cats():
    conn = get_db()
    rows = conn.execute('SELECT * FROM exp_categories ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/exp_categories', methods=['POST'])
def add_exp_cat():
    d = request.json
    conn = get_db()
    try:
        conn.execute('INSERT INTO exp_categories (name) VALUES (?)', (d['name'],))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'ok': False, 'error': 'Already exists'}), 400
    finally:
        conn.close()
    return jsonify({'ok': True})

@app.route('/api/exp_categories/<int:id>', methods=['PUT'])
def update_exp_cat(id):
    d = request.json
    conn = get_db()
    conn.execute('UPDATE exp_categories SET name=? WHERE id=?', (d['name'], id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/exp_categories/<int:id>', methods=['DELETE'])
def delete_exp_cat(id):
    conn = get_db()
    conn.execute('DELETE FROM exp_categories WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── SALES ─────────────────────────────────────────────────
@app.route('/api/sales', methods=['GET'])
def get_sales():
    date_from = request.args.get('from')
    date_to   = request.args.get('to')
    date      = request.args.get('date')
    conn = get_db()
    if date:
        rows = conn.execute('SELECT * FROM sales WHERE date=? ORDER BY id DESC', (date,)).fetchall()
    elif date_from and date_to:
        rows = conn.execute('SELECT * FROM sales WHERE date>=? AND date<=? ORDER BY date DESC,id DESC',
                            (date_from, date_to)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM sales ORDER BY date DESC,id DESC LIMIT 100').fetchall()
    conn.close()
    result = []
    for r in rows:
        row = dict(r)
        row['items'] = json.loads(row['items'])
        result.append(row)
    return jsonify(result)

@app.route('/api/sales', methods=['POST'])
def add_sale():
    d = request.json
    conn = get_db()
    conn.execute('INSERT INTO sales (date,ctype,guest,tour,guide,payment,items,total) VALUES (?,?,?,?,?,?,?,?)',
                 (d['date'], d['ctype'], d.get('guest',''), d.get('tour',''), d.get('guide',''),
                  d['payment'], json.dumps(d['items']), d['total']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    conn = get_db()
    conn.execute('DELETE FROM sales WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── EXPENSES ──────────────────────────────────────────────
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    date_from = request.args.get('from')
    date_to   = request.args.get('to')
    date      = request.args.get('date')
    conn = get_db()
    if date:
        rows = conn.execute('SELECT * FROM expenses WHERE date=? ORDER BY id DESC', (date,)).fetchall()
    elif date_from and date_to:
        rows = conn.execute('SELECT * FROM expenses WHERE date>=? AND date<=? ORDER BY date DESC,id DESC',
                            (date_from, date_to)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM expenses ORDER BY date DESC,id DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    d = request.json
    conn = get_db()
    conn.execute('INSERT INTO expenses (date,cat,vendor,amount,payment,note) VALUES (?,?,?,?,?,?)',
                 (d['date'], d['cat'], d.get('vendor',''), d['amount'], d['payment'], d.get('note','')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    conn = get_db()
    conn.execute('DELETE FROM expenses WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── MAIN ──────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
