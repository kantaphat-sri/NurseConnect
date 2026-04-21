import os
import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'nurseconnect_secret_key'

# === CONFIGURATION ===
CSV_FILES = {
    'users': 'users.csv',
    'nurses': 'nurses.csv',
    'bookings': 'bookings.csv'
}

HEADERS = {
    'users': ['id', 'name', 'email', 'password', 'phone', 'role'],
    'nurses': ['user_id', 'license_number', 'specialization', 'rating', 'is_verified'],
    'bookings': ['id', 'client_id', 'nurse_id', 'service_type', 'date', 'time', 'address', 'notes', 'status', 'duration', 'total_price']
}

SERVICE_RATES = {
    'พาผู้ป่วยไปพบแพทย์': 250,
    'พยาบาลที่บ้าน': 400,
    'ดูแลผู้สูงอายุ': 300,
    'หัตถการที่บ้าน': 500,
    'ฟื้นฟูสมรรถภาพ': 450
}

# === CSV HELPERS ===

def csv_read(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, mode='r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def csv_write(filename, rows):
    fieldnames = HEADERS[filename.split('.')[0]]
    with open(filename, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def csv_insert(filename, row):
    rows = csv_read(filename)
    if 'id' in HEADERS[filename.split('.')[0]]:
        existing_ids = [int(r['id']) for r in rows if r.get('id')]
        row['id'] = max(existing_ids) + 1 if existing_ids else 1
    rows.append(row)
    csv_write(filename, rows)
    return row

def csv_update(filename, row_id, updates, id_col='id'):
    rows = csv_read(filename)
    updated = False
    for row in rows:
        if str(row.get(id_col)) == str(row_id):
            row.update(updates)
            updated = True
            break
    if updated:
        csv_write(filename, rows)
    return updated

def csv_delete(filename, row_id, id_col='id'):
    rows = csv_read(filename)
    new_rows = [row for row in rows if str(row.get(id_col)) != str(row_id)]
    if len(rows) != len(new_rows):
        csv_write(filename, new_rows)
        return True
    return False

# === INITIALIZATION & SEEDING ===

def auto_init_csv():
    for name, filename in CSV_FILES.items():
        if not os.path.exists(filename):
            csv_write(filename, [])

def seed_data():
    if not csv_read(CSV_FILES['users']):
        print(" seeding data...")
        # Nurses
        u1 = csv_insert(CSV_FILES['users'], {'name': 'สมรักษ์ พยาบาลดี', 'email': 'nurse1@test.com', 'password': '1234', 'phone': '0811111111', 'role': 'nurse'})
        u2 = csv_insert(CSV_FILES['users'], {'name': 'จิตรา นักกายภาพ', 'email': 'nurse2@test.com', 'password': '1234', 'phone': '0822222222', 'role': 'nurse'})
        
        csv_insert(CSV_FILES['nurses'], {'user_id': u1['id'], 'license_number': 'RN-001', 'specialization': 'พยาบาลวิชาชีพ RN', 'rating': '5', 'is_verified': 'True'})
        csv_insert(CSV_FILES['nurses'], {'user_id': u2['id'], 'license_number': 'PT-001', 'specialization': 'นักกายภาพ PT', 'rating': '0', 'is_verified': 'False'})
        
        # Clients
        c1 = csv_insert(CSV_FILES['users'], {'name': 'นายสมบัติ ใจดี', 'email': 'client1@test.com', 'password': '1234', 'phone': '0833333333', 'role': 'client'})
        c2 = csv_insert(CSV_FILES['users'], {'name': 'นางมณี รักษาสุข', 'email': 'client2@test.com', 'password': '1234', 'phone': '0844444444', 'role': 'client'})
        
        # Bookings
        csv_insert(CSV_FILES['bookings'], {'client_id': c1['id'], 'nurse_id': '', 'service_type': 'พาผู้ป่วยไปพบแพทย์', 'date': '2026-05-01', 'address': '123 สุขุมวิท กรุงเทพ', 'notes': 'ต้องการรถเข็น', 'status': 'pending'})
        csv_insert(CSV_FILES['bookings'], {'client_id': c2['id'], 'nurse_id': u1['id'], 'service_type': 'พยาบาลที่บ้าน', 'date': '2026-05-02', 'address': '456 ลาดพร้าว กรุงเทพ', 'notes': 'ล้างแผลผ่าตัด', 'status': 'confirmed'})
        csv_insert(CSV_FILES['bookings'], {'client_id': c1['id'], 'nurse_id': u1['id'], 'service_type': 'ดูแลผู้สูงอายุ', 'date': '2026-04-20', 'address': '123 สุขุมวิท กรุงเทพ', 'notes': '', 'status': 'completed'})

# === AUTH DECORATORS ===

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# === ROUTES ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/credit')
def credit():
    return render_template('credit.html')


@app.route('/nurses')
def nurses_directory():
    all_nurses = csv_read(CSV_FILES['nurses'])
    users = csv_read(CSV_FILES['users'])
    user_map = {u['id']: u['name'] for u in users}
    
    nurse_list = []
    for n in all_nurses:
        if n['is_verified'] == 'True':
            n['name'] = user_map.get(n['user_id'], 'Unknown')
            nurse_list.append(n)
            
    return render_template('nurses.html', nurses=nurse_list)

@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Admin check
        if email == 'admin@platform.com' and password == 'admin1234':
            session['user_id'] = 'admin'
            session['role'] = 'admin'
            session['name'] = 'System Admin'
            return redirect(url_for('admin_dashboard'))
            
        users = csv_read(CSV_FILES['users'])
        for u in users:
            if u['email'] == email and u['password'] == password:
                session['user_id'] = u['id']
                session['role'] = u['role']
                session['name'] = u['name']
                
                if u['role'] == 'nurse':
                    return redirect(url_for('nurse_dashboard'))
                return redirect(url_for('client_dashboard'))
        
        flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        role = request.form['role']
        
        existing_users = csv_read(CSV_FILES['users'])
        if any(u['email'] == email for u in existing_users):
            flash('อีเมลนี้ถูกใช้งานแล้ว')
            return redirect(url_for('register'))
            
        new_user = csv_insert(CSV_FILES['users'], {
            'name': name,
            'email': email,
            'password': password,
            'phone': phone,
            'role': role
        })
        
        if role == 'nurse':
            csv_insert(CSV_FILES['nurses'], {
                'user_id': new_user['id'],
                'license_number': request.form.get('license_number'),
                'specialization': request.form.get('specialization'),
                'rating': '0',
                'is_verified': 'False'
            })
            
        flash('ลงทะเบียนสำเร็จ! กรุณาเข้าสู่ระบบ')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# === CLIENT DASHBOARD ===

@app.route('/client/dashboard')
@login_required
@role_required('client')
def client_dashboard():
    all_bookings = csv_read(CSV_FILES['bookings'])
    all_users = csv_read(CSV_FILES['users'])
    user_map = {u['id']: u['name'] for u in all_users}
    
    my_bookings = []
    for b in all_bookings:
        if str(b['client_id']) == str(session['user_id']):
            b['nurse_name'] = user_map.get(b['nurse_id'], '')
            my_bookings.append(b)
            
    return render_template('client_dashboard.html', bookings=my_bookings)

@app.route('/client/book', methods=['POST'])
@login_required
@role_required('client')
def client_book():
    service_type = request.form['service_type']
    duration = int(request.form.get('duration', 1))
    total_price = SERVICE_RATES.get(service_type, 0) * duration

    csv_insert(CSV_FILES['bookings'], {
        'client_id': session['user_id'],
        'nurse_id': '',
        'service_type': service_type,
        'date': request.form['date'],
        'time': request.form['time'],
        'address': request.form['address'],
        'notes': request.form['notes'],
        'status': 'pending',
        'duration': duration,
        'total_price': total_price
    })
    flash('สร้างการจองสำเร็จ!')
    return redirect(url_for('client_dashboard'))

@app.route('/client/cancel/<id>', methods=['POST'])
@login_required
@role_required('client')
def client_cancel(id):
    csv_delete(CSV_FILES['bookings'], id)
    flash('ยกเลิกการจองเรียบร้อยแล้ว')
    return redirect(url_for('client_dashboard'))

# === NURSE DASHBOARD ===

@app.route('/nurse/dashboard')
@login_required
@role_required('nurse')
def nurse_dashboard():
    nurses = csv_read(CSV_FILES['nurses'])
    nurse_info = next((n for n in nurses if str(n['user_id']) == str(session['user_id'])), {})
    
    all_bookings = csv_read(CSV_FILES['bookings'])
    all_users = csv_read(CSV_FILES['users'])
    user_map = {u['id']: u['name'] for u in all_users}
    phone_map = {u['id']: u['phone'] for u in all_users}
    
    pending_bookings = []
    my_bookings = []
    for b in all_bookings:
        b['client_name'] = user_map.get(b['client_id'], 'Unknown')
        b['phone'] = phone_map.get(b['client_id'], '-')
        if b['status'] == 'pending' and not b['nurse_id']:
            pending_bookings.append(b)
        elif str(b['nurse_id']) == str(session['user_id']):
            my_bookings.append(b)
            
    return render_template('nurse_dashboard.html', 
                                 nurse_info=nurse_info, 
                                 pending_bookings=pending_bookings,
                                 my_bookings=my_bookings)

@app.route('/nurse/accept/<id>', methods=['POST'])
@login_required
@role_required('nurse')
def nurse_accept(id):
    csv_update(CSV_FILES['bookings'], id, {'nurse_id': session['user_id'], 'status': 'confirmed'})
    flash('รับงานเรียบร้อย! ขอให้โชคดี')
    return redirect(url_for('nurse_dashboard'))

@app.route('/nurse/complete/<id>', methods=['POST'])
@login_required
@role_required('nurse')
def nurse_complete(id):
    csv_update(CSV_FILES['bookings'], id, {'status': 'completed'})
    flash('งานเสร็จสิ้น! ขอบคุณสำหรับการดูแล')
    return redirect(url_for('nurse_dashboard'))

# === ADMIN DASHBOARD ===

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    users = csv_read(CSV_FILES['users'])
    nurses = csv_read(CSV_FILES['nurses'])
    bookings = csv_read(CSV_FILES['bookings'])
    
    user_map = {u['id']: u['name'] for u in users}
    
    nurse_list = []
    for n in nurses:
        n['name'] = user_map.get(n['user_id'], 'Deleted User')
        nurse_list.append(n)
        
    booking_list = []
    revenue = 0
    for b in bookings:
        b['client_name'] = user_map.get(b['client_id'], 'N/A')
        b['nurse_name'] = user_map.get(b['nurse_id'], '')
        booking_list.append(b)
        if b['status'] == 'completed':
            revenue += int(b.get('total_price', 0))
            
    total_clients = sum(1 for u in users if u['role'] == 'client')
    
    return render_template('admin_dashboard.html', 
                                 nurses=nurse_list,
                                 bookings=booking_list,
                                 total_nurses=len(nurses),
                                 total_clients=total_clients,
                                 total_bookings=len(bookings),
                                 revenue=revenue)

@app.route('/admin/verify/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_verify(user_id):
    csv_update(CSV_FILES['nurses'], user_id, {'is_verified': 'True'}, id_col='user_id')
    flash('ยืนยันตัวตนพยาบาลสำเร็จ')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_nurse/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_nurse(user_id):
    csv_delete(CSV_FILES['nurses'], user_id, id_col='user_id')
    csv_delete(CSV_FILES['users'], user_id)
    flash('ลบข้อมูลพยาบาลสำเร็จ')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_booking/<id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_booking(id):
    csv_delete(CSV_FILES['bookings'], id)
    flash('ลบข้อมูลการจองสำเร็จ')
    return redirect(url_for('admin_dashboard'))

# Jinja filter for currency formatting
@app.template_filter('toLocaleString')
def to_locale_string_filter(s):
    return "{:,}".format(int(s))

if __name__ == '__main__':
    auto_init_csv()
    seed_data()
    print("\\n" + "="*40)
    print("NURSE CONNECT LITE STARTED")
    print("="*40)
    print("Admin: admin@platform.com / admin1234")
    print("Nurse: nurse1@test.com / 1234 (Verified)")
    print("Nurse: nurse2@test.com / 1234 (Not Verified)")
    print("Client: client1@test.com / 1234")
    print("="*40 + "\\n")
    app.run(debug=True, port=3000)
