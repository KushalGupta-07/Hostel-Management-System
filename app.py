import os
from datetime import datetime, date
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# Custom template filters for dates and currency
@app.template_filter('format_currency')
def format_currency(value):
    if value is None:
        return "₹0.00"
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

@app.template_filter('format_date')
def format_date(value, fmt='%d %b %Y'):
    if not value:
        return "-"
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime(fmt)
    except Exception:
        return str(value)

@app.template_filter('format_datetime')
def format_datetime(value, fmt='%d %b %Y, %I:%M %p'):
    if not value:
        return "-"
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime(fmt)
    except Exception:
        return str(value)

# Auto-sync room occupancy on app startup
try:
    db.sync_room_occupancy()
except Exception as e:
    print(f"Warning on startup sync: {e}")

# =====================================================================
# Dashboard
# =====================================================================
@app.route('/')
def dashboard():
    # 1. Total rooms and capacity
    room_stats = db.query_db("""
        SELECT 
            COUNT(*) as total_rooms,
            COALESCE(SUM(capacity), 0) as total_capacity,
            COALESCE(SUM(current_occupancy), 0) as occupied_beds,
            COALESCE(SUM(CASE WHEN status = 'Available' THEN capacity - current_occupancy ELSE 0 END), 0) as available_beds,
            COALESCE(SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END), 0) as maintenance_rooms
        FROM rooms
    """, one=True) or {}

    # 2. Total active students
    student_stats = db.query_db("""
        SELECT 
            COUNT(*) as total_students,
            COALESCE(SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END), 0) as active_students,
            COALESCE(SUM(CASE WHEN status = 'Checked-Out' THEN 1 ELSE 0 END), 0) as checked_out_students
        FROM students
    """, one=True) or {}

    # 3. Fee summary
    fee_stats = db.query_db("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END), 0) as total_pending,
            COALESCE(SUM(CASE WHEN status = 'Overdue' THEN amount ELSE 0 END), 0) as total_overdue
        FROM fees
    """, one=True) or {}

    # 4. Complaints summary
    complaint_stats = db.query_db("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END), 0) as open_complaints,
            COALESCE(SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END), 0) as in_progress_complaints,
            COALESCE(SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END), 0) as resolved_complaints
        FROM complaints
    """, one=True) or {}

    # 5. Recent complaints
    recent_complaints = db.query_db("""
        SELECT c.*, s.full_name as student_name, r.room_number 
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.id
        LEFT JOIN rooms r ON c.room_id = r.id
        ORDER BY c.created_at DESC
        LIMIT 5
    """)

    # 6. Active notices
    recent_notices = db.query_db("""
        SELECT * FROM notices 
        ORDER BY FIELD(priority, 'Urgent', 'Important', 'Normal'), created_at DESC 
        LIMIT 4
    """)

    # 7. Today's visitors
    visitors_today = db.query_db("""
        SELECT v.*, s.full_name as student_name, r.room_number
        FROM visitors v
        JOIN students s ON v.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        ORDER BY v.in_time DESC
        LIMIT 5
    """)

    # 8. Room occupancy by floor
    floor_stats = db.query_db("""
        SELECT 
            floor,
            COUNT(*) as rooms_count,
            SUM(capacity) as total_capacity,
            SUM(current_occupancy) as occupied
        FROM rooms
        GROUP BY floor
        ORDER BY floor ASC
    """)

    return render_template(
        'dashboard.html',
        room_stats=room_stats,
        student_stats=student_stats,
        fee_stats=fee_stats,
        complaint_stats=complaint_stats,
        recent_complaints=recent_complaints,
        recent_notices=recent_notices,
        visitors_today=visitors_today,
        floor_stats=floor_stats
    )

# =====================================================================
# Rooms Management
# =====================================================================
@app.route('/rooms')
def rooms_list():
    floor_filter = request.args.get('floor')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    search = request.args.get('search', '').strip()

    query = "SELECT * FROM rooms WHERE 1=1"
    params = []

    if floor_filter:
        query += " AND floor = %s"
        params.append(floor_filter)
    if type_filter:
        query += " AND room_type = %s"
        params.append(type_filter)
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    if search:
        query += " AND room_number LIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY floor ASC, room_number ASC"
    rooms = db.query_db(query, params)

    floors = db.query_db("SELECT DISTINCT floor FROM rooms ORDER BY floor ASC")
    
    return render_template('rooms.html', rooms=rooms, floors=floors, 
                           current_floor=floor_filter, current_type=type_filter, 
                           current_status=status_filter, search=search)

@app.route('/rooms/add', methods=['POST'])
def add_room():
    room_number = request.form.get('room_number', '').strip()
    floor = request.form.get('floor', 1, type=int)
    room_type = request.form.get('room_type', 'Double')
    capacity = request.form.get('capacity', 2, type=int)
    fee_per_month = request.form.get('fee_per_month', 6000.0, type=float)
    amenities = request.form.get('amenities', '').strip()

    if not room_number:
        flash("Room number is required!", "danger")
        return redirect(url_for('rooms_list'))

    # Check for duplicate
    existing = db.query_db("SELECT id FROM rooms WHERE room_number = %s", [room_number], one=True)
    if existing:
        flash(f"Room {room_number} already exists!", "danger")
        return redirect(url_for('rooms_list'))

    db.execute_db("""
        INSERT INTO rooms (room_number, floor, room_type, capacity, fee_per_month, amenities, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Available')
    """, [room_number, floor, room_type, capacity, fee_per_month, amenities])

    flash(f"Room {room_number} added successfully!", "success")
    return redirect(url_for('rooms_list'))

@app.route('/rooms/view/<int:room_id>')
def room_detail(room_id):
    room = db.query_db("SELECT * FROM rooms WHERE id = %s", [room_id], one=True)
    if not room:
        flash("Room not found!", "danger")
        return redirect(url_for('rooms_list'))

    occupants = db.query_db("""
        SELECT * FROM students 
        WHERE room_id = %s AND status = 'Active'
        ORDER BY check_in_date ASC
    """, [room_id])

    complaints = db.query_db("""
        SELECT c.*, s.full_name as student_name 
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.id
        WHERE c.room_id = %s
        ORDER BY c.created_at DESC
    """, [room_id])

    return render_template('room_detail.html', room=room, occupants=occupants, complaints=complaints)

@app.route('/rooms/edit/<int:room_id>', methods=['POST'])
def edit_room(room_id):
    room_number = request.form.get('room_number', '').strip()
    floor = request.form.get('floor', 1, type=int)
    room_type = request.form.get('room_type', 'Double')
    capacity = request.form.get('capacity', 2, type=int)
    fee_per_month = request.form.get('fee_per_month', 6000.0, type=float)
    status = request.form.get('status', 'Available')
    amenities = request.form.get('amenities', '').strip()

    db.execute_db("""
        UPDATE rooms 
        SET room_number=%s, floor=%s, room_type=%s, capacity=%s, 
            fee_per_month=%s, status=%s, amenities=%s
        WHERE id = %s
    """, [room_number, floor, room_type, capacity, fee_per_month, status, amenities, room_id])

    db.sync_room_occupancy()
    flash(f"Room {room_number} updated successfully!", "success")
    return redirect(url_for('rooms_list'))

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    # Check if there are active occupants
    occupants = db.query_db("SELECT COUNT(*) as cnt FROM students WHERE room_id = %s AND status = 'Active'", [room_id], one=True)
    if occupants and occupants['cnt'] > 0:
        flash("Cannot delete a room with active residents! Please reallocate or check-out students first.", "danger")
        return redirect(url_for('rooms_list'))

    db.execute_db("DELETE FROM rooms WHERE id = %s", [room_id])
    flash("Room deleted successfully!", "success")
    return redirect(url_for('rooms_list'))

# =====================================================================
# Students Management
# =====================================================================
@app.route('/students')
def students_list():
    status_filter = request.args.get('status', 'Active')
    room_filter = request.args.get('room')
    search = request.args.get('search', '').strip()

    query = """
        SELECT s.*, r.room_number, r.floor, r.fee_per_month
        FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != 'All':
        query += " AND s.status = %s"
        params.append(status_filter)
    if room_filter:
        query += " AND s.room_id = %s"
        params.append(room_filter)
    if search:
        query += " AND (s.full_name LIKE %s OR s.student_id_code LIKE %s OR s.phone LIKE %s OR s.email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY s.id DESC"
    students = db.query_db(query, params)

    # Get available rooms for registration dropdown
    available_rooms = db.query_db("""
        SELECT * FROM rooms 
        WHERE status = 'Available' AND current_occupancy < capacity
        ORDER BY room_number ASC
    """)

    return render_template('students.html', students=students, available_rooms=available_rooms,
                           current_status=status_filter, current_room=room_filter, search=search)

@app.route('/students/add', methods=['POST'])
def add_student():
    student_id_code = request.form.get('student_id_code', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    gender = request.form.get('gender', 'Male')
    dob = request.form.get('dob') or None
    address = request.form.get('address', '').strip()
    guardian_name = request.form.get('guardian_name', '').strip()
    guardian_phone = request.form.get('guardian_phone', '').strip()
    blood_group = request.form.get('blood_group', '').strip()
    room_id = request.form.get('room_id') or None
    check_in_date = request.form.get('check_in_date') or datetime.now().date()

    if not full_name or not phone or not student_id_code:
        flash("Student ID, Name, and Phone are required!", "danger")
        return redirect(url_for('students_list'))

    # Check duplicate ID
    existing = db.query_db("SELECT id FROM students WHERE student_id_code = %s", [student_id_code], one=True)
    if existing:
        flash(f"Student ID {student_id_code} is already registered!", "danger")
        return redirect(url_for('students_list'))

    # Validate room availability if room chosen
    if room_id:
        room = db.query_db("SELECT * FROM rooms WHERE id = %s", [room_id], one=True)
        if not room or room['current_occupancy'] >= room['capacity'] or room['status'] == 'Maintenance':
            flash("Selected room is not available or full!", "danger")
            return redirect(url_for('students_list'))

    student_id = db.execute_db("""
        INSERT INTO students 
        (student_id_code, full_name, email, phone, gender, dob, address, 
         guardian_name, guardian_phone, blood_group, room_id, check_in_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
    """, [student_id_code, full_name, email, phone, gender, dob, address, 
          guardian_name, guardian_phone, blood_group, room_id, check_in_date], return_id=True)

    # Sync room occupancy
    db.sync_room_occupancy()

    # Automatically create the first month rent invoice if assigned to a room
    if room_id:
        room = db.query_db("SELECT fee_per_month FROM rooms WHERE id = %s", [room_id], one=True)
        if room:
            due_date = date.today().replace(day=5)
            db.execute_db("""
                INSERT INTO fees (student_id, fee_type, amount, due_date, status, notes)
                VALUES (%s, 'Hostel Rent', %s, %s, 'Pending', 'Initial Room Allocation Rent')
            """, [student_id, room['fee_per_month'], due_date])

    flash(f"Student {full_name} registered successfully!", "success")
    return redirect(url_for('students_list'))

@app.route('/students/view/<int:student_id>')
def student_detail(student_id):
    student = db.query_db("""
        SELECT s.*, r.room_number, r.floor, r.room_type, r.fee_per_month, r.amenities
        FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE s.id = %s
    """, [student_id], one=True)

    if not student:
        flash("Student record not found!", "danger")
        return redirect(url_for('students_list'))

    fees = db.query_db("SELECT * FROM fees WHERE student_id = %s ORDER BY due_date DESC", [student_id])
    complaints = db.query_db("SELECT * FROM complaints WHERE student_id = %s ORDER BY created_at DESC", [student_id])
    visitors = db.query_db("SELECT * FROM visitors WHERE student_id = %s ORDER BY in_time DESC", [student_id])
    gate_passes = db.query_db("SELECT * FROM gate_passes WHERE student_id = %s ORDER BY created_at DESC", [student_id])
    
    # Available rooms if need to transfer
    available_rooms = db.query_db("""
        SELECT * FROM rooms 
        WHERE (status = 'Available' AND current_occupancy < capacity) OR id = %s
        ORDER BY room_number ASC
    """, [student['room_id'] or 0])

    return render_template('student_detail.html', student=student, fees=fees, 
                           complaints=complaints, visitors=visitors, 
                           gate_passes=gate_passes, available_rooms=available_rooms)

@app.route('/students/edit/<int:student_id>', methods=['POST'])
def edit_student(student_id):
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    gender = request.form.get('gender', 'Male')
    dob = request.form.get('dob') or None
    address = request.form.get('address', '').strip()
    guardian_name = request.form.get('guardian_name', '').strip()
    guardian_phone = request.form.get('guardian_phone', '').strip()
    blood_group = request.form.get('blood_group', '').strip()
    room_id = request.form.get('room_id') or None
    status = request.form.get('status', 'Active')

    db.execute_db("""
        UPDATE students 
        SET full_name=%s, email=%s, phone=%s, gender=%s, dob=%s, 
            address=%s, guardian_name=%s, guardian_phone=%s, blood_group=%s, 
            room_id=%s, status=%s
        WHERE id = %s
    """, [full_name, email, phone, gender, dob, address, guardian_name, guardian_phone, blood_group, room_id, status, student_id])

    db.sync_room_occupancy()
    flash(f"Student details updated successfully!", "success")
    return redirect(url_for('student_detail', student_id=student_id))

@app.route('/students/checkout/<int:student_id>', methods=['POST'])
def checkout_student(student_id):
    student = db.query_db("SELECT * FROM students WHERE id = %s", [student_id], one=True)
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for('students_list'))

    # Check pending fees
    pending_fees = db.query_db("""
        SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total 
        FROM fees 
        WHERE student_id = %s AND status != 'Paid'
    """, [student_id], one=True)

    if pending_fees and pending_fees['cnt'] > 0:
        flash(f"Cannot check out! Student has pending dues totaling ₹{pending_fees['total']:,.2f}. Please clear dues first.", "warning")
        return redirect(url_for('student_detail', student_id=student_id))

    db.execute_db("""
        UPDATE students 
        SET status = 'Checked-Out', check_out_date = CURRENT_DATE, room_id = NULL
        WHERE id = %s
    """, [student_id])

    db.sync_room_occupancy()
    flash(f"{student['full_name']} has been checked out successfully and bed released.", "success")
    return redirect(url_for('students_list'))

@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    db.execute_db("DELETE FROM students WHERE id = %s", [student_id])
    db.sync_room_occupancy()
    flash("Student record removed successfully!", "success")
    return redirect(url_for('students_list'))

# =====================================================================
# Fees Management
# =====================================================================
@app.route('/fees')
def fees_list():
    status_filter = request.args.get('status')
    fee_type_filter = request.args.get('fee_type')
    search = request.args.get('search', '').strip()

    query = """
        SELECT f.*, s.full_name as student_name, s.student_id_code, s.phone, r.room_number
        FROM fees f
        JOIN students s ON f.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != 'All':
        query += " AND f.status = %s"
        params.append(status_filter)
    if fee_type_filter and fee_type_filter != 'All':
        query += " AND f.fee_type = %s"
        params.append(fee_type_filter)
    if search:
        query += " AND (s.full_name LIKE %s OR s.student_id_code LIKE %s OR f.transaction_ref LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY f.due_date DESC, f.id DESC"
    fees = db.query_db(query, params)

    students = db.query_db("SELECT id, student_id_code, full_name FROM students WHERE status = 'Active' ORDER BY full_name ASC")

    # Aggregate stats
    stats = db.query_db("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) as paid_amount,
            COALESCE(SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END), 0) as pending_amount,
            COALESCE(SUM(CASE WHEN status = 'Overdue' THEN amount ELSE 0 END), 0) as overdue_amount
        FROM fees
    """, one=True) or {}

    return render_template('fees.html', fees=fees, students=students, stats=stats,
                           current_status=status_filter, current_fee_type=fee_type_filter, search=search)

@app.route('/fees/add', methods=['POST'])
def add_fee():
    student_id = request.form.get('student_id', type=int)
    fee_type = request.form.get('fee_type', 'Hostel Rent')
    amount = request.form.get('amount', type=float)
    due_date = request.form.get('due_date')
    notes = request.form.get('notes', '').strip()

    if not student_id or not amount or not due_date:
        flash("Student, Amount, and Due Date are required!", "danger")
        return redirect(url_for('fees_list'))

    db.execute_db("""
        INSERT INTO fees (student_id, fee_type, amount, due_date, status, notes)
        VALUES (%s, %s, %s, %s, 'Pending', %s)
    """, [student_id, fee_type, amount, due_date, notes])

    flash("Fee invoice created successfully!", "success")
    return redirect(url_for('fees_list'))

@app.route('/fees/pay/<int:fee_id>', methods=['POST'])
def pay_fee(fee_id):
    payment_mode = request.form.get('payment_mode', 'UPI')
    transaction_ref = request.form.get('transaction_ref', '').strip()
    paid_date = request.form.get('paid_date') or datetime.now().date()

    if not transaction_ref:
        transaction_ref = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    db.execute_db("""
        UPDATE fees 
        SET status = 'Paid', paid_date = %s, payment_mode = %s, transaction_ref = %s
        WHERE id = %s
    """, [paid_date, payment_mode, transaction_ref, fee_id])

    flash("Payment recorded successfully!", "success")
    return redirect(request.referrer or url_for('fees_list'))

@app.route('/fees/receipt/<int:fee_id>')
def fee_receipt(fee_id):
    fee = db.query_db("""
        SELECT f.*, s.full_name as student_name, s.student_id_code, s.phone, s.email,
               r.room_number, r.floor, r.room_type
        FROM fees f
        JOIN students s ON f.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE f.id = %s
    """, [fee_id], one=True)

    if not fee:
        flash("Fee receipt not found!", "danger")
        return redirect(url_for('fees_list'))

    return render_template('receipt.html', fee=fee)

@app.route('/fees/delete/<int:fee_id>', methods=['POST'])
def delete_fee(fee_id):
    db.execute_db("DELETE FROM fees WHERE id = %s", [fee_id])
    flash("Fee record deleted!", "success")
    return redirect(url_for('fees_list'))

# =====================================================================
# Complaints Management
# =====================================================================
@app.route('/complaints')
def complaints_list():
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    category_filter = request.args.get('category')

    query = """
        SELECT c.*, s.full_name as student_name, s.phone, r.room_number 
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.id
        LEFT JOIN rooms r ON c.room_id = r.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != 'All':
        query += " AND c.status = %s"
        params.append(status_filter)
    if priority_filter and priority_filter != 'All':
        query += " AND c.priority = %s"
        params.append(priority_filter)
    if category_filter and category_filter != 'All':
        query += " AND c.category = %s"
        params.append(category_filter)

    query += " ORDER BY FIELD(c.status, 'Open', 'In Progress', 'Resolved'), c.created_at DESC"
    complaints = db.query_db(query, params)

    students = db.query_db("SELECT id, full_name, room_id FROM students WHERE status = 'Active' ORDER BY full_name ASC")
    rooms = db.query_db("SELECT id, room_number FROM rooms ORDER BY room_number ASC")

    return render_template('complaints.html', complaints=complaints, students=students, rooms=rooms,
                           current_status=status_filter, current_priority=priority_filter, current_category=category_filter)

@app.route('/complaints/add', methods=['POST'])
def add_complaint():
    student_id = request.form.get('student_id') or None
    room_id = request.form.get('room_id') or None
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Electrical')
    priority = request.form.get('priority', 'Medium')
    description = request.form.get('description', '').strip()

    # If student is chosen and room is not explicitly set, auto-fill student's room
    if student_id and not room_id:
        student = db.query_db("SELECT room_id FROM students WHERE id = %s", [student_id], one=True)
        if student:
            room_id = student['room_id']

    if not title or not description:
        flash("Title and description are required!", "danger")
        return redirect(url_for('complaints_list'))

    db.execute_db("""
        INSERT INTO complaints (student_id, room_id, title, category, priority, description, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Open')
    """, [student_id, room_id, title, category, priority, description])

    flash("Complaint ticket registered successfully!", "success")
    return redirect(url_for('complaints_list'))

@app.route('/complaints/update-status/<int:complaint_id>', methods=['POST'])
def update_complaint_status(complaint_id):
    status = request.form.get('status', 'Open')
    resolution_notes = request.form.get('resolution_notes', '').strip()
    
    resolved_at = datetime.now() if status == 'Resolved' else None

    db.execute_db("""
        UPDATE complaints 
        SET status = %s, resolution_notes = %s, resolved_at = %s
        WHERE id = %s
    """, [status, resolution_notes, resolved_at, complaint_id])

    flash(f"Complaint updated to '{status}'!", "success")
    return redirect(request.referrer or url_for('complaints_list'))

@app.route('/complaints/delete/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    db.execute_db("DELETE FROM complaints WHERE id = %s", [complaint_id])
    flash("Complaint ticket deleted!", "success")
    return redirect(url_for('complaints_list'))

# =====================================================================
# Visitors & Gate Passes
# =====================================================================
@app.route('/visitors')
def visitors_list():
    visitors = db.query_db("""
        SELECT v.*, s.full_name as student_name, s.student_id_code, r.room_number 
        FROM visitors v
        JOIN students s ON v.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        ORDER BY v.in_time DESC
    """)

    gate_passes = db.query_db("""
        SELECT g.*, s.full_name as student_name, s.phone, r.room_number 
        FROM gate_passes g
        JOIN students s ON g.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        ORDER BY g.created_at DESC
    """)

    students = db.query_db("SELECT id, full_name, student_id_code FROM students WHERE status = 'Active' ORDER BY full_name ASC")

    return render_template('visitors.html', visitors=visitors, gate_passes=gate_passes, students=students)

@app.route('/visitors/add', methods=['POST'])
def add_visitor():
    student_id = request.form.get('student_id', type=int)
    visitor_name = request.form.get('visitor_name', '').strip()
    visitor_phone = request.form.get('visitor_phone', '').strip()
    relation = request.form.get('relation', '').strip()
    id_proof = request.form.get('id_proof', '').strip()
    purpose = request.form.get('purpose', '').strip()

    if not student_id or not visitor_name or not visitor_phone:
        flash("Student, Visitor Name, and Phone are required!", "danger")
        return redirect(url_for('visitors_list'))

    db.execute_db("""
        INSERT INTO visitors (student_id, visitor_name, visitor_phone, relation, id_proof, purpose)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, [student_id, visitor_name, visitor_phone, relation, id_proof, purpose])

    flash("Visitor logged in successfully!", "success")
    return redirect(url_for('visitors_list'))

@app.route('/visitors/exit/<int:visitor_id>', methods=['POST'])
def visitor_exit(visitor_id):
    db.execute_db("UPDATE visitors SET out_time = NOW() WHERE id = %s", [visitor_id])
    flash("Visitor departure recorded!", "success")
    return redirect(url_for('visitors_list'))

@app.route('/gatepasses/add', methods=['POST'])
def add_gatepass():
    student_id = request.form.get('student_id', type=int)
    leave_date = request.form.get('leave_date')
    return_date = request.form.get('return_date')
    destination = request.form.get('destination', '').strip()
    reason = request.form.get('reason', '').strip()

    if not student_id or not leave_date or not return_date or not destination:
        flash("All fields are required to request a gate pass!", "danger")
        return redirect(url_for('visitors_list'))

    db.execute_db("""
        INSERT INTO gate_passes (student_id, leave_date, return_date, destination, reason, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """, [student_id, leave_date, return_date, destination, reason])

    flash("Gate pass request submitted successfully!", "success")
    return redirect(url_for('visitors_list'))

@app.route('/gatepasses/update/<int:pass_id>', methods=['POST'])
def update_gatepass(pass_id):
    status = request.form.get('status', 'Pending')
    approved_by = request.form.get('approved_by', 'Warden Office')

    db.execute_db("""
        UPDATE gate_passes 
        SET status = %s, approved_by = %s
        WHERE id = %s
    """, [status, approved_by, pass_id])

    flash(f"Gate pass status changed to '{status}'!", "success")
    return redirect(url_for('visitors_list'))

# =====================================================================
# Mess & Meal Schedule
# =====================================================================
@app.route('/mess')
def mess_schedule():
    meals = db.query_db("SELECT * FROM meal_menu ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), FIELD(meal_type, 'Breakfast', 'Lunch', 'Snacks', 'Dinner')")
    
    # Structure by Day -> Meal Type
    schedule = {}
    for m in meals:
        day = m['day_of_week']
        if day not in schedule:
            schedule[day] = {}
        schedule[day][m['meal_type']] = m

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meal_types = ['Breakfast', 'Lunch', 'Snacks', 'Dinner']

    return render_template('mess.html', schedule=schedule, days=days, meal_types=meal_types)

@app.route('/mess/update', methods=['POST'])
def update_mess_meal():
    day_of_week = request.form.get('day_of_week')
    meal_type = request.form.get('meal_type')
    menu_items = request.form.get('menu_items', '').strip()

    if not day_of_week or not meal_type or not menu_items:
        flash("Day, Meal Type, and Menu Items cannot be empty!", "danger")
        return redirect(url_for('mess_schedule'))

    db.execute_db("""
        INSERT INTO meal_menu (day_of_week, meal_type, menu_items)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE menu_items = VALUES(menu_items)
    """, [day_of_week, meal_type, menu_items])

    flash(f"Menu for {day_of_week} ({meal_type}) updated successfully!", "success")
    return redirect(url_for('mess_schedule'))

# =====================================================================
# Staff & Notices
# =====================================================================
@app.route('/staff-notices')
def staff_notices():
    staff_members = db.query_db("SELECT * FROM staff ORDER BY FIELD(role, 'Warden', 'Assistant Warden', 'Security Supervisor', 'Chef / Cook', 'Maintenance Electrician', 'Plumber', 'Security Guard', 'Cleaning Staff'), name ASC")
    notices = db.query_db("SELECT * FROM notices ORDER BY created_at DESC")
    return render_template('staff_notices.html', staff=staff_members, notices=notices)

@app.route('/staff/add', methods=['POST'])
def add_staff():
    name = request.form.get('name', '').strip()
    role = request.form.get('role', 'Warden')
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    shift = request.form.get('shift', 'General')
    salary = request.form.get('salary', 18000.0, type=float)

    if not name or not phone:
        flash("Staff Name and Phone are required!", "danger")
        return redirect(url_for('staff_notices'))

    db.execute_db("""
        INSERT INTO staff (name, role, phone, email, shift, salary, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Active')
    """, [name, role, phone, email, shift, salary])

    flash(f"Staff member {name} added!", "success")
    return redirect(url_for('staff_notices'))

@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    db.execute_db("DELETE FROM staff WHERE id = %s", [staff_id])
    flash("Staff record removed!", "success")
    return redirect(url_for('staff_notices'))

@app.route('/notices/add', methods=['POST'])
def add_notice():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'Normal')

    if not title or not content:
        flash("Notice Title and Content are required!", "danger")
        return redirect(url_for('staff_notices'))

    db.execute_db("""
        INSERT INTO notices (title, content, priority)
        VALUES (%s, %s, %s)
    """, [title, content, priority])

    flash("New hostel notice published!", "success")
    return redirect(url_for('staff_notices'))

@app.route('/notices/delete/<int:notice_id>', methods=['POST'])
def delete_notice(notice_id):
    db.execute_db("DELETE FROM notices WHERE id = %s", [notice_id])
    flash("Notice removed!", "success")
    return redirect(url_for('staff_notices'))

# =====================================================================
# Database Status / Diagnostic API
# =====================================================================
@app.route('/api/db-status')
def db_status():
    try:
        tables = db.query_db("SHOW TABLES;")
        return jsonify({
            "status": "connected",
            "database": Config.DB_NAME,
            "host": Config.DB_HOST,
            "user": Config.DB_USER,
            "tables_count": len(tables) if tables else 0
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    # Initialize DB if needed
    try:
        db.init_db()
    except Exception as e:
        print(f"Error during db initialization: {e}")
    app.run(host='0.0.0.0', port=5000, debug=True)
