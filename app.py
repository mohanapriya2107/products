from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import psycopg2
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploaded_images')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# PostgreSQL connection using DATABASE_URL
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

# Static product list
products = [
    {
        'name': 'Aflat Cap',
        'original_price': '899.00',
        'discounted_price': '449.00',
        'image': 'aflat_cap.png'
    },
    {
        'name': 'Derby Cap',
        'original_price': '899.00',
        'discounted_price': '299.00',
        'image': 'derby.png'
    },
    {
        'name': 'Fedora',
        'original_price': '899.00',
        'discounted_price': '349.00',
        'image': 'fedora.png'
    }
]

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('signup_page'))
    return render_template('admin.html')

@app.route('/upload_product', methods=['POST'])
def upload_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('signup_page'))

    name = request.form['name_of_product']
    original_price = request.form['price_of_product_without_discount']
    discounted_price = request.form['price_of_product_with_discount']
    image_file = request.files['fileupload']

    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        products.append({
            'name': name,
            'original_price': original_price,
            'discounted_price': discounted_price,
            'image': f'uploaded_images/{filename}'
        })

    return redirect(url_for('index'))

@app.route('/signup_page', methods=['GET'])
def signup_page():
    return render_template('signup_page.html')

@app.route('/check_admin_email', methods=['POST'])
def check_admin_email():
    email = request.form['email']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return render_template('signup_page.html', email=email, mode="login")
    else:
        return render_template('signup_page.html', email=email, mode="signup")

@app.route('/admin_login', methods=['POST'])
def admin_login():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        session['admin_logged_in'] = True
        flash("Successfully logged in!", "success")
        return redirect(url_for('admin'))
    else:
        flash("Invalid credentials. Try again.", "error")
        return redirect(url_for('signup_page'))

@app.route('/admin_signup', methods=['POST'])
def admin_signup():
    name = request.form['admin_name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        session['admin_logged_in'] = True
        flash("Signup successful. You are now logged in.", "success")
        return redirect(url_for('admin'))
    except Exception as e:
        conn.rollback()
        flash("Signup failed: " + str(e), "error")
        return redirect(url_for('signup_page'))
    finally:
        cur.close()
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
