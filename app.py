from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask import send_from_directory
import sqlite3
import os
import random
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Initialize Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DB_PATH = os.path.join(os.path.dirname(__file__), 'contacts.db')

# Admin password (better: use env var in production)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "arihantadmin")


# ---------------- DB Initialization ----------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            stars INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        
        # Create default admin user if not exists
        c.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        admin_count = c.fetchone()[0]
        if admin_count == 0:
            admin_password = generate_password_hash(ADMIN_PASSWORD)
            c.execute('INSERT INTO users (username, email, password_hash, full_name, is_admin) VALUES (?, ?, ?, ?, ?)',
                     ('admin', 'admin@arihantgranite.com', admin_password, 'Arihant Admin', True))
        
        conn.commit()


# ---------------- Authentication Functions ----------------
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
            user = c.fetchone()
            if not user or not user[0]:
                flash('Admin access required.', 'error')
                return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# ---------------- Routes ----------------
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    message = ''
    if request.method == 'POST':
        password = request.form.get('password')
        file = request.files.get('file')

        if password != ADMIN_PASSWORD:
            message = '❌ Incorrect admin password.'
        elif not file or file.filename == '':
            message = '⚠️ No file selected.'
        else:
            fname = secure_filename(file.filename)
            save_dir = os.path.join(app.root_path, 'static', 'img', 'Arihant')
            os.makedirs(save_dir, exist_ok=True)
            file.save(os.path.join(save_dir, fname))
            message = f'✅ File {fname} uploaded successfully!'

    return render_template('admin_upload.html', message=message)


@app.route('/why-choose-us')
def why_choose_us():
    return render_template('why_choose_us.html')


@app.route('/')
def home():
    img_dir = os.path.join(app.root_path, 'static', 'img', 'Arihant')
    all_imgs = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))] if os.path.exists(img_dir) else []
    featured_imgs = random.sample(all_imgs, min(6, len(all_imgs))) if all_imgs else []

    # Enhanced product descriptions based on granite names
    granite_descriptions = {
        'Astoria Ivory Pink': 'Elegant pink granite with ivory veining, perfect for modern kitchens and bathrooms.',
        'Canyon Gold': 'Rich golden granite with natural patterns, ideal for luxury interiors.',
        'Colonial Gold': 'Classic gold granite with timeless appeal for traditional and contemporary spaces.',
        'Colonial White': 'Pure white granite with subtle veining, perfect for minimalist designs.',
        'Crystal Gold': 'Crystal-infused gold granite with sparkling finish for premium projects.',
        'Imperial Gold': 'Royal gold granite with imperial patterns, perfect for grand entrances.',
        'Kashmir Gold': 'Exotic Kashmir gold granite with unique veining patterns.',
        'Millenium Ivory Gold': 'Millennium collection ivory gold granite with sophisticated patterns.',
        'Shiva Gold': 'Divine gold granite with spiritual elegance for sacred spaces.',
        'Shiva Ivory Pink': 'Sacred pink granite with ivory accents, perfect for temples and homes.',
        'Vegas Gold': 'Vibrant gold granite with Vegas-style glamour for luxury projects.'
    }

    featured = []
    for fname in featured_imgs:
        base_name = os.path.splitext(fname)[0]
        clean_name = base_name.replace('_', ' ').replace('-', ' ').title()
        description = granite_descriptions.get(clean_name, f'Premium {clean_name} granite from Arihant\'s exclusive collection.')
        
        featured.append({
            'title': clean_name,
            'image': f'/static/img/Arihant/{fname}',
            'category': 'Biege & Creme Collection',
            'description': description,
           
        })

    # Dynamic testimonials with more variety
    testimonials = [
        {"text": "The quality and finish of Arihant's granite is unmatched. Our home looks stunning!", "author": "Priya S., Chennai", "rating": 5},
        {"text": "Professional service and beautiful granite. Highly recommended for any project.", "author": "Ramesh K., Bangalore", "rating": 5},
        {"text": "Arihant Granites team helped us choose the perfect stone for our hotel lobby.", "author": "Hotel Grand, Madurai", "rating": 5},
        {"text": "Excellent quality and timely delivery. The Kashmir Gold looks amazing in our living room!", "author": "Anita M., Delhi", "rating": 5},
        {"text": "Great variety and competitive prices. Very satisfied with our purchase.", "author": "Rajesh P., Mumbai", "rating": 4},
        {"text": "The Imperial Gold granite transformed our office reception area completely.", "author": "Corporate Client, Hyderabad", "rating": 5}
    ]
    
    # Get recent reviews for homepage
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT name, stars, message FROM reviews ORDER BY created_at DESC LIMIT 3')
        recent_reviews = c.fetchall()
    
    return render_template('home.html', featured=featured, testimonials=testimonials, recent_reviews=recent_reviews)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/explore')
def explore():
    img_dir = os.path.join(app.root_path, 'static', 'img', 'Arihant')
    listings = []
    
    # Enhanced product descriptions based on granite names
    granite_descriptions = {
        'Astoria Ivory Pink': 'Elegant pink granite with ivory veining, perfect for modern kitchens and bathrooms.',
        'Canyon Gold': 'Rich golden granite with natural patterns, ideal for luxury interiors.',
        'Colonial Gold': 'Classic gold granite with timeless appeal for traditional and contemporary spaces.',
        'Colonial White': 'Pure white granite with subtle veining, perfect for minimalist designs.',
        'Crystal Gold': 'Crystal-infused gold granite with sparkling finish for premium projects.',
        'Imperial Gold': 'Royal gold granite with imperial patterns, perfect for grand entrances.',
        'Kashmir Gold': 'Exotic Kashmir gold granite with unique veining patterns.',
        'Millenium Ivory Gold': 'Millennium collection ivory gold granite with sophisticated patterns.',
        'Shiva Gold': 'Divine gold granite with spiritual elegance for sacred spaces.',
        'Shiva Ivory Pink': 'Sacred pink granite with ivory accents, perfect for temples and homes.',
        'Vegas Gold': 'Vibrant gold granite with Vegas-style glamour for luxury projects.'
    }
    
    # Granite categories for better organization
    granite_categories = {
        'Astoria Ivory Pink': 'Pink Collection',
        'Canyon Gold': 'Gold Collection',
        'Colonial Gold': 'Gold Collection',
        'Colonial White': 'White Collection',
        'Crystal Gold': 'Gold Collection',
        'Imperial Gold': 'Gold Collection',
        'Kashmir Gold': 'Gold Collection',
        'Millenium Ivory Gold': 'Gold Collection',
        'Shiva Gold': 'Gold Collection',
        'Shiva Ivory Pink': 'Pink Collection',
        'Vegas Gold': 'Gold Collection',
        'Olivia Green': 'Premium Series & Others',
        'Royal Pink':'Pink Collection',
        'Millenium':'White Collection',
        'Mani White':'White Collection',
        'Ghibli Ivory':'White Collection',
        'Flamingo Pink':'Pink Collection',
        'Colombo Jubarna':'Premium Series & Others',
        'Classic Ivory':'Premium Series & Others',
        'Bhama Ivory Pink':'Pink Collection',
        'Astoria Ivory':'White Collection',
        'Astoria': 'Premium Series & Others'

        
    }
    
    if os.path.exists(img_dir):
        for fname in os.listdir(img_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                base_name = os.path.splitext(fname)[0]
                clean_name = base_name.replace('_', ' ').replace('-', ' ').title()
                description = granite_descriptions.get(clean_name, f'Premium {clean_name} granite from Arihant\'s exclusive collection.')
                category = granite_categories.get(clean_name, 'Biege & Creme Collection')
                
                listings.append({
                    'title': clean_name,
                    'image': f'/static/img/Arihant/{fname}',
                    'category': category,
                    'description': description,
                   
                    'availability': 'In Stock' if random.choice([True, True, True, False]) else 'Limited Stock',
                    'thickness': random.choice(['2cm', '3cm', '2-3cm']),
                    'finish': random.choice(['Polished', 'Honed', 'Leathered', 'Brushed'])
                })
    
    listings.sort(key=lambda x: x['title'])
    return render_template('explore.html', listings=listings)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)', (name, email, message))
            conn.commit()
        flash('✅ Thank you for contacting us!')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/admin/contacts')
def admin_contacts():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT id, name, email, message, created_at FROM contacts ORDER BY created_at DESC')
        contacts = c.fetchall()
    return render_template('admin_contacts.html', contacts=contacts)


@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        stars = int(request.form['stars'])
        message = request.form['message']
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO reviews (name, email, phone, stars, message) VALUES (?, ?, ?, ?, ?)',
                      (name, email, phone, stars, message))
            conn.commit()
        flash('✅ Thank you for your review!')
        return redirect(url_for('reviews'))

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT name, stars, message, created_at FROM reviews ORDER BY created_at DESC LIMIT 20')
        reviews = c.fetchall()

    return render_template('reviews.html', reviews=reviews)


# ---------------- Authentication Routes ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT id, password_hash, full_name, is_admin FROM users WHERE username = ? OR email = ?', 
                     (username, username))
            user = c.fetchone()
            
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['username'] = username
                session['full_name'] = user[2]
                session['is_admin'] = bool(user[3])
                
                # Generate session token
                session_token = secrets.token_hex(32)
                c.execute('INSERT INTO user_sessions (user_id, session_token) VALUES (?, ?)', 
                         (user[0], session_token))
                session['session_token'] = session_token
                
                flash('✅ Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('❌ Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form.get('phone', '')
        
        # Validate password strength
        if len(password) < 6:
            flash('❌ Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, email, password_hash, full_name, phone) VALUES (?, ?, ?, ?, ?)',
                         (username, email, password_hash, full_name, phone))
                conn.commit()
            
            flash('✅ Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('❌ Username or email already exists.', 'error')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    if 'session_token' in session:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM user_sessions WHERE session_token = ?', (session['session_token'],))
            conn.commit()
    
    session.clear()
    flash('✅ You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/profile')
@login_required
def profile():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT username, email, full_name, phone, created_at FROM users WHERE id = ?', 
                 (session['user_id'],))
        user = c.fetchone()
    
    return render_template('profile.html', user=user)


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Get statistics
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM contacts')
        total_contacts = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM reviews')
        total_reviews = c.fetchone()[0]
        
        c.execute('SELECT AVG(stars) FROM reviews')
        avg_rating = c.fetchone()[0] or 0
        
        # Get recent activity
        c.execute('SELECT name, email, created_at FROM contacts ORDER BY created_at DESC LIMIT 5')
        recent_contacts = c.fetchall()
        
        c.execute('SELECT name, stars, message, created_at FROM reviews ORDER BY created_at DESC LIMIT 5')
        recent_reviews = c.fetchall()
    
    stats = {
        'total_users': total_users,
        'total_contacts': total_contacts,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1)
    }
    
    return render_template('admin_dashboard.html', stats=stats, recent_contacts=recent_contacts, recent_reviews=recent_reviews)


# ---------------- Run App ----------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
