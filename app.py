from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploaded_images')

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    category = request.args.get('category')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    rating = request.args.get('rating')

    query = "SELECT name, original_price, discounted_price, image, category, rating FROM products WHERE 1=1"
    params = []

    if price_min and price_min.isdigit():
        query += " AND discounted_price >= %s"
        params.append(int(price_min))

    if price_max and price_max.isdigit():
        query += " AND discounted_price <= %s"
        params.append(int(price_max))

    if category:
        query += " AND category = %s"
        params.append(category)

    if rating and rating.isdigit():
        query += " AND rating >= %s"
        params.append(int(rating))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    products = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('products.html', products=products)


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
    category = request.form['category']
    rating = request.form['rating']
    image_file = request.files['fileupload']

    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO products (name, original_price, discounted_price, image, category, rating) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, original_price, discounted_price, f'uploaded_images/{filename}', category, rating))
        conn.commit()
        cur.close()
        conn.close()

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

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
