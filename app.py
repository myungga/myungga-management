from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, json, psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        cat TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS exp_categories (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id SERIAL PRIMARY KEY,
        date TEXT NOT NULL,
        ctype TEXT NOT NULL,
        guest TEXT,
        tour TEXT,
        guide TEXT,
        pax INTEGER DEFAULT 0,
        payment TEXT NOT NULL,
        currency TEXT DEFAULT 'THB',
        items TEXT NOT NULL,
        discount REAL DEFAULT 0,
        total REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # 기존 DB에 pax 컬럼이 없을 경우 추가 (마이그레이션)
    try:
        c.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS pax INTEGER DEFAULT 0")
    except Exception:
        conn.rollback()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        date TEXT NOT NULL,
        cat TEXT NOT NULL,
        vendor TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'THB',
        payment TEXT NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        current_stock REAL DEFAULT 0,
        min_stock REAL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_log (
        id SERIAL PRIMARY KEY,
        item_id INTEGER REFERENCES inventory(id),
        action TEXT NOT NULL,
        quantity REAL NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('SELECT COUNT(*) as cnt FROM menu')
    if c.fetchone()['cnt'] == 0:
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
        c.executemany('INSERT INTO menu (name,type,cat,price) VALUES (%s,%s,%s,%s)', default_menu)
    c.execute('SELECT COUNT(*) as cnt FROM exp_categories')
    if c.fetchone()['cnt'] == 0:
        default_cats = [
            ('Food Ingredient',),('Beverage Stock',),('Supplies',),
            ('Utilities (Water/Electric/Gas)',),('Salary',),('Rent',),
            ('Marketing',),('Equipment / Repair',),('Other',)
        ]
        c.executemany('INSERT INTO exp_categories (name) VALUES (%s)', default_cats)
    c.execute('SELECT COUNT(*) as cnt FROM inventory')
    if c.fetchone()['cnt'] == 0:
        default_inv = [
            ('Chang Beer','Beer','bottle',0,24),
            ('Singha Beer','Beer','bottle',0,24),
            ('Soju','Soju','bottle',0,12),
            ('Sangsom','Spirits','bottle',0,6),
            ('Regency','Spirits','bottle',0,6),
            ('Coke','Soft Drink','can',0,24),
            ('Sprite','Soft Drink','can',0,24),
            ('Water','Soft Drink','bottle',0,24),
        ]
        c.executemany('INSERT INTO inventory (name,category,unit,current_stock,min_stock) VALUES (%s,%s,%s,%s,%s)', default_inv)
    conn.commit()
    conn.close()

# MENU
@app.route('/api/menu', methods=['GET'])
def get_menu():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM menu WHERE active=1 ORDER BY type,cat,name')
    rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/menu', methods=['POST'])
def add_menu():
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('INSERT INTO menu (name,type,cat,price) VALUES (%s,%s,%s,%s)',
              (d['name'],d['type'],d['cat'],d['price']))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/menu/<int:id>', methods=['PUT'])
def update_menu(id):
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('UPDATE menu SET name=%s,type=%s,cat=%s,price=%s WHERE id=%s',
              (d['name'],d['type'],d['cat'],d['price'],id))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/menu/<int:id>', methods=['DELETE'])
def delete_menu(id):
    conn = get_db(); c = conn.cursor()
    c.execute('UPDATE menu SET active=0 WHERE id=%s',(id,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

# EXP CATEGORIES
@app.route('/api/exp_categories', methods=['GET'])
def get_exp_cats():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM exp_categories ORDER BY id')
    rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/exp_categories', methods=['POST'])
def add_exp_cat():
    d = request.json; conn = get_db(); c = conn.cursor()
    try:
        c.execute('INSERT INTO exp_categories (name) VALUES (%s)',(d['name'],))
        conn.commit()
    except Exception:
        conn.rollback(); conn.close()
        return jsonify({'ok':False,'error':'Already exists'}),400
    conn.close()
    return jsonify({'ok':True})

@app.route('/api/exp_categories/<int:id>', methods=['PUT'])
def update_exp_cat(id):
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('UPDATE exp_categories SET name=%s WHERE id=%s',(d['name'],id))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/exp_categories/<int:id>', methods=['DELETE'])
def delete_exp_cat(id):
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM exp_categories WHERE id=%s',(id,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

# SALES
@app.route('/api/sales', methods=['GET'])
def get_sales():
    date_from=request.args.get('from'); date_to=request.args.get('to'); date=request.args.get('date')
    conn = get_db(); c = conn.cursor()
    if date:
        c.execute('SELECT * FROM sales WHERE date=%s ORDER BY id DESC',(date,))
    elif date_from and date_to:
        c.execute('SELECT * FROM sales WHERE date>=%s AND date<=%s ORDER BY date DESC,id DESC',(date_from,date_to))
    else:
        c.execute('SELECT * FROM sales ORDER BY date DESC,id DESC LIMIT 100')
    rows = c.fetchall(); conn.close()
    result = []
    for r in rows:
        row = dict(r)
        row['items'] = json.loads(row['items'])
        result.append(row)
    return jsonify(result)

@app.route('/api/sales', methods=['POST'])
def add_sale():
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('''INSERT INTO sales (date,ctype,guest,tour,guide,pax,payment,currency,items,discount,total)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (d['date'],d['ctype'],d.get('guest',''),d.get('tour',''),d.get('guide',''),
               d.get('pax',0),d['payment'],d.get('currency','THB'),json.dumps(d['items']),
               d.get('discount',0),d['total']))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM sales WHERE id=%s',(id,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

# EXPENSES
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    date_from=request.args.get('from'); date_to=request.args.get('to'); date=request.args.get('date')
    conn = get_db(); c = conn.cursor()
    if date:
        c.execute('SELECT * FROM expenses WHERE date=%s ORDER BY id DESC',(date,))
    elif date_from and date_to:
        c.execute('SELECT * FROM expenses WHERE date>=%s AND date<=%s ORDER BY date DESC,id DESC',(date_from,date_to))
    else:
        c.execute('SELECT * FROM expenses ORDER BY date DESC,id DESC LIMIT 200')
    rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('INSERT INTO expenses (date,cat,vendor,amount,currency,payment,note) VALUES (%s,%s,%s,%s,%s,%s,%s)',
              (d['date'],d['cat'],d.get('vendor',''),d['amount'],
               d.get('currency','THB'),d['payment'],d.get('note','')))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id=%s',(id,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

# INVENTORY
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM inventory ORDER BY category,name')
    rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('INSERT INTO inventory (name,category,unit,current_stock,min_stock) VALUES (%s,%s,%s,%s,%s)',
              (d['name'],d['category'],d['unit'],d.get('current_stock',0),d.get('min_stock',0)))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/inventory/<int:id>', methods=['PUT'])
def update_inventory(id):
    d = request.json; conn = get_db(); c = conn.cursor()
    c.execute('UPDATE inventory SET name=%s,category=%s,unit=%s,min_stock=%s WHERE id=%s',
              (d['name'],d['category'],d['unit'],d.get('min_stock',0),id))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/inventory/<int:id>', methods=['DELETE'])
def delete_inventory(id):
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM inventory_log WHERE item_id=%s',(id,))
    c.execute('DELETE FROM inventory WHERE id=%s',(id,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/inventory/<int:id>/stock', methods=['POST'])
def update_stock(id):
    d = request.json; conn = get_db(); c = conn.cursor()
    action = d['action']; qty = float(d['quantity']); note = d.get('note','')
    if action == 'add':
        c.execute('UPDATE inventory SET current_stock=current_stock+%s,updated_at=NOW() WHERE id=%s',(qty,id))
    else:
        c.execute('UPDATE inventory SET current_stock=GREATEST(0,current_stock-%s),updated_at=NOW() WHERE id=%s',(qty,id))
    c.execute('INSERT INTO inventory_log (item_id,action,quantity,note) VALUES (%s,%s,%s,%s)',(id,action,qty,note))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/inventory/<int:id>/log', methods=['GET'])
def get_inventory_log(id):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM inventory_log WHERE item_id=%s ORDER BY created_at DESC LIMIT 30',(id,))
    rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/')
def index():
    return render_template('index.html')

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug=False)
