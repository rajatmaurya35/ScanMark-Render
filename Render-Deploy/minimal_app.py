from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from io import StringIO, BytesIO
import csv
import qrcode
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets
import qrcode
from io import BytesIO
import base64
import logging
import json
import csv
from io import StringIO
from db_minimal import (init_db, get_student, update_student, get_all_students, 
                        get_session, create_session, get_all_sessions, mark_attendance,
                        get_student_attendance, get_session_attendance, 
                        create_attendance_list, get_all_attendance_lists, get_attendance_list,
                        update_session, delete_session, save_attendance_lists)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple admin authentication for demo
        if username == 'admin' and password == 'admin123':
            session['admin'] = username
            session.permanent = True
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin/login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    
    # Get admin username
    admin_username = session.get('admin')
    
    # Get sessions from the database or create demo sessions if none exist
    sessions_data = get_all_sessions()
    
    if not sessions_data:
        # Create demo sessions if none exist
        physics_session = create_session({
            'id': 'physics-session-1',
            'subject': 'Physics',
            'faculty': 'Shilpa Mam',
            'branch': 'IT',
            'semester': '8th sem',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'status': 'active',
            'description': 'Physics lecture for IT department'
        })
        
        oops_session = create_session({
            'id': 'oops-session-1',
            'subject': 'OOPS',
            'faculty': 'Avani Mam',
            'branch': 'Computer',
            'semester': '3rd sem',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'status': 'inactive',
            'description': 'Object-Oriented Programming lecture for Computer students'
        })
        
        # Refresh sessions data after creating demo sessions
        sessions_data = get_all_sessions()
    
    # Format sessions for the template
    sessions = []
    for session_id, session_data in sessions_data.items():
        sessions.append({
            'token': session_data['id'],
            'session': f"{session_data['subject']} - {session_data['faculty']} - {session_data['branch']} - {session_data['semester']}",
            'subject': session_data['subject'],
            'faculty': session_data['faculty'],
            'branch': session_data['branch'],
            'semester': session_data['semester'],
            'status': session_data.get('status', 'active'),  # Default to active if not specified
            'created_at': session_data.get('created_at', '')
        })
    
    # Sort sessions - active sessions first, then by creation date (newest first)
    sessions.sort(key=lambda x: (0 if x['status'] == 'active' else 1, x.get('created_at', '')), reverse=True)
    
    # Calculate attendance statistics
    active_sessions_count = sum(1 for s in sessions if s['status'] == 'active')
    
    attendance_stats = {
        'total_sessions': len(sessions),
        'active_sessions': active_sessions_count,
        'total_students': 25,  # Demo data
        'total_attendance': 120  # Demo data
    }
    
    # Get attendance lists
    attendance_lists_data = get_all_attendance_lists()
    
    # Create demo attendance list if none exist
    if not attendance_lists_data:
        # Create a demo attendance list
        demo_list = create_attendance_list({
            'session_id': 'physics-session-1',
            'session_name': 'Physics - Shilpa Mam - IT - 8th sem',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'notes': 'Demo attendance list',
            'total_students': 25,
            'present': 22,
            'absent': 3
        })
        attendance_lists_data = get_all_attendance_lists()
    
    # Format attendance lists for the template
    attendance_lists = []
    for list_id, list_data in attendance_lists_data.items():
        attendance_lists.append({
            'id': list_data['id'],
            'date': list_data['date'],
            'session': list_data['session_name'],
            'total_students': list_data['total_students'],
            'present': list_data['present'],
            'absent': list_data['absent']
        })
    
    ai_insights = ["Attendance has increased by 15% this week", "3 students have perfect attendance"]
    risk_alerts = ["No attendance issues detected"]
    
    return render_template(
        'admin/dashboard.html',
        sessions=sessions,
        admin=admin_username,
        stats=attendance_stats,
        attendance_lists=attendance_lists,
        ai_insights=ai_insights,
        risk_alerts=risk_alerts,
        now=datetime.now()  # Add current date for attendance list form
    )

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

# Create Attendance List
@app.route('/admin/create-attendance-list', methods=['POST'])
def create_attendance_list_route():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    try:
        data = request.json
        session_token = data.get('session_token')
        list_date = data.get('date')
        notes = data.get('notes', '')
        
        if not session_token or not list_date:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Get session details
        session_data = get_session(session_token)
        if not session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        # Format session name
        session_name = f"{session_data['subject']} - {session_data['faculty']} - {session_data['branch']} - {session_data['semester']}"
        
        # Create the attendance list in the database
        attendance_list = create_attendance_list({
            'session_id': session_token,
            'session_name': session_name,
            'date': list_date,
            'notes': notes,
            'total_students': 25,  # Demo data
            'present': 22,         # Demo data
            'absent': 3            # Demo data
        })
        
        return jsonify({
            'success': True, 
            'message': 'Attendance list created successfully',
            'list_id': attendance_list['id']
        })
    except Exception as e:
        app.logger.error(f"Error creating attendance list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Admin Create Session
@app.route('/admin/create-session', methods=['POST'])
def create_session_route():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    try:
        # Get data from JSON or form data
        data = request.get_json() if request.is_json else request.form
        
        subject = data.get('subject')
        faculty = data.get('faculty')
        branch = data.get('branch')
        semester = data.get('semester')
        date = data.get('date')
        time = data.get('time')
        description = data.get('description', '')
        
        if not subject or not faculty or not branch or not semester:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Generate unique ID
        session_id = f"{subject.lower().replace(' ', '-')}-{faculty.lower().replace(' ', '-')}-{int(datetime.now().timestamp())}"
        
        # Create session in database - always set status to active for new sessions
        session_data = create_session({
            'id': session_id,
            'subject': subject,
            'faculty': faculty,
            'branch': branch,
            'semester': semester,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'time': time or datetime.now().strftime('%H:%M'),
            'status': 'active',  # Always create as active
            'description': description
        })
        
        return jsonify({
            'success': True,
            'message': 'Session created successfully',
            'session': session_data
        })
    except Exception as e:
        app.logger.error(f"Error creating session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# This function is implemented below

# View Attendance List
@app.route('/admin/attendance-list/<list_id>')
def view_attendance_list(list_id):
    if 'admin' not in session:
        flash('Please login to continue', 'warning')
        return redirect(url_for('admin_login'))
    
    attendance_list = get_attendance_list(list_id)
    if not attendance_list:
        flash('Attendance list not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Get session details
    session_data = get_session(attendance_list['session_id'])
    
    # Get student attendance for this list
    # In a real app, we would fetch actual student attendance
    # For demo, we'll create some fake data
    students = []
    for i in range(1, attendance_list['total_students'] + 1):
        present = i <= attendance_list['present']
        students.append({
            'id': f"STUD{i:03d}",
            'name': f"Student {i}",
            'status': 'present' if present else 'absent',
            'timestamp': attendance_list['created_at']
        })
    
    return render_template(
        'admin/attendance_list.html',
        attendance_list=attendance_list,
        session_data=session_data,
        students=students,
        admin=session.get('admin')
    )

# Admin Toggle Session Status
@app.route('/admin/toggle-session/<token>', methods=['POST', 'GET'])
def toggle_session_status(token):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get session data
        session_data = get_session(token)
        if not session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Toggle status
        new_status = 'inactive' if session_data['status'] == 'active' else 'active'
        
        # Update session in database
        updated_session = update_session(token, {'status': new_status})
        
        return jsonify({
            'success': True,
            'message': f"Session status changed to {new_status}",
            'status': new_status
        })
    except Exception as e:
        app.logger.error(f"Error toggling session status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Admin Delete Session
@app.route('/admin/delete-session/<token>', methods=['POST'])
def delete_session_route(token):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get session data first to check if it exists
        session_data = get_session(token)
        if not session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Delete the session
        result = delete_session(token)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Session deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete session'}), 500
    except Exception as e:
        app.logger.error(f"Error deleting session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Get sessions for admin dashboard
@app.route('/admin/get-sessions')
def get_admin_sessions():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    try:
        # Get all sessions
        sessions_data = get_all_sessions()
        
        # Format sessions for the response
        sessions = []
        for session_id, session_data in sessions_data.items():
            sessions.append({
                'token': session_data['id'],
                'session': f"{session_data['subject']} - {session_data['faculty']} - {session_data['branch']} - {session_data['semester']}",
                'subject': session_data['subject'],
                'faculty': session_data['faculty'],
                'branch': session_data['branch'],
                'semester': session_data['semester'],
                'status': session_data['status'],
                'created_at': session_data['created_at']
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        app.logger.error(f"Error getting sessions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Get attendance lists for admin dashboard
@app.route('/admin/get-attendance-lists')
def get_admin_attendance_lists():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    try:
        # Get all attendance lists
        attendance_lists_data = get_all_attendance_lists()
        
        # Format attendance lists for the response
        lists = []
        for list_id, list_data in attendance_lists_data.items():
            lists.append({
                'id': list_data['id'],
                'date': list_data['date'],
                'session': list_data['session_name'],
                'total_students': list_data['total_students'],
                'present': list_data['present'],
                'absent': list_data['absent']
            })
        
        return jsonify({
            'success': True,
            'lists': lists
        })
    except Exception as e:
        app.logger.error(f"Error getting attendance lists: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/view-qr/<token>', methods=['GET'])
def view_qr(token):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    # Get session data
    session_data = get_session(token)
    if not session_data:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # URL for the attendance form
    attendance_url = request.host_url.rstrip('/') + f"/attendance/{token}"
    qr.add_data(attendance_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Format session name
    session_name = f"{session_data['subject']} - {session_data['faculty']} - {session_data['branch']} - {session_data['semester']}"
    
    return jsonify({
        'success': True,
        'qr_code': f"data:image/png;base64,{img_str}",
        'session': session_name
    })

# View attendance list details
@app.route('/admin/view-attendance-list/<list_id>', methods=['GET'])
def view_attendance_list_details(list_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get attendance list data
        attendance_lists = get_all_attendance_lists()
        if list_id not in attendance_lists:
            return jsonify({'success': False, 'error': 'Attendance list not found'}), 404
        
        list_data = attendance_lists[list_id]
        
        # Get student details
        students_data = []
        for student_id, status in list_data['students'].items():
            student = get_student(student_id)
            if student:
                students_data.append({
                    'id': student_id,
                    'name': f"{student['first_name']} {student['last_name']}",
                    'status': status
                })
        
        return jsonify({
            'success': True,
            'list_id': list_id,
            'session_name': list_data['session_name'],
            'date': list_data['date'],
            'total_students': list_data['total_students'],
            'present': list_data['present'],
            'absent': list_data['absent'],
            'students': students_data
        })
    except Exception as e:
        app.logger.error(f"Error viewing attendance list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Update attendance list
@app.route('/admin/update-attendance-list', methods=['POST'])
def update_attendance_list():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        data = request.json
        list_id = data.get('list_id')
        students = data.get('students', [])
        
        if not list_id:
            return jsonify({'success': False, 'error': 'List ID is required'}), 400
        
        # Get attendance list data
        attendance_lists = get_all_attendance_lists()
        if list_id not in attendance_lists:
            return jsonify({'success': False, 'error': 'Attendance list not found'}), 404
        
        list_data = attendance_lists[list_id]
        
        # Update student statuses
        present_count = 0
        for student in students:
            student_id = student.get('id')
            status = student.get('status')
            
            if student_id and status:
                list_data['students'][student_id] = status
                if status == 'present':
                    present_count += 1
        
        # Update attendance counts
        list_data['present'] = present_count
        list_data['absent'] = list_data['total_students'] - present_count
        
        # Save updated attendance list
        attendance_lists[list_id] = list_data
        save_attendance_lists(attendance_lists)
        
        return jsonify({
            'success': True,
            'message': 'Attendance list updated successfully'
        })
    except Exception as e:
        app.logger.error(f"Error updating attendance list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Delete attendance list
@app.route('/admin/delete-attendance-list/<list_id>', methods=['DELETE'])
def delete_attendance_list(list_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get attendance lists
        attendance_lists = get_all_attendance_lists()
        
        # Check if list exists
        if list_id not in attendance_lists:
            return jsonify({'success': False, 'error': 'Attendance list not found'}), 404
        
        # Delete the list
        del attendance_lists[list_id]
        
        # Save updated attendance lists
        save_attendance_lists(attendance_lists)
        
        return jsonify({
            'success': True,
            'message': 'Attendance list deleted successfully'
        })
    except Exception as e:
        app.logger.error(f"Error deleting attendance list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete-session/<token>', methods=['DELETE', 'POST'])
def delete_session_handler(token):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    # Demo implementation
    return jsonify({
        'success': True,
        'message': 'Session deleted successfully'
    })

# Admin Register
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('admin/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('admin/register.html')
        
        # Demo implementation
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('admin_login'))
    
    return render_template('admin/register.html')

# Student Login
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        # Simple student authentication for demo
        if student_id and password:
            # For demo purposes, accept any valid input
            session['student_id'] = student_id
            session.permanent = True
            flash('Login successful', 'success')
            return redirect(url_for('user_dashboard', student_id=student_id))
        else:
            flash('Invalid student ID or password', 'danger')
    
    return render_template('user/login.html')

# Student Dashboard
@app.route('/user/dashboard/<student_id>')
def user_dashboard(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    # Get student data from database
    student_data = get_student(student_id)
    
    # Get attendance records from database
    attendance_records_raw = get_student_attendance(student_id)
    
    # Enhance attendance records with session details
    attendance_records = []
    for record in attendance_records_raw:
        session_data = get_session(record['session_id'])
        if session_data:
            attendance_records.append({
                'session_id': record['session_id'],
                'subject': session_data['subject'],
                'faculty': session_data['faculty'],
                'branch': session_data['branch'],
                'semester': session_data['semester'],
                'date': session_data['date'],
                'time': session_data['time'],
                'timestamp': f"{session_data['date']} {session_data['time']}",
                'status': record['status']
            })
    
    # If no attendance records exist, create some demo data
    if not attendance_records_raw:
        # Create demo sessions if they don't exist
        physics_session = create_session({
            'id': 'physics-session-1',
            'subject': 'Physics',
            'faculty': 'Shilpa Mam',
            'branch': 'IT',
            'semester': '8th sem',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'status': 'active',
            'description': 'Physics lecture for IT department'
        })
        
        oops_session = create_session({
            'id': 'oops-session-1',
            'subject': 'OOPS',
            'faculty': 'Avani mam',
            'branch': 'Diploma',
            'semester': '3rd sem',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'status': 'active',
            'description': 'Object-Oriented Programming lecture for Diploma students'
        })
        
        # Mark attendance for these sessions
        mark_attendance(student_id, 'physics-session-1', 'present')
        mark_attendance(student_id, 'oops-session-1', 'present')
        
        # Refresh attendance records
        attendance_records_raw = get_student_attendance(student_id)
        
        # Enhance attendance records with session details
        attendance_records = []
        for record in attendance_records_raw:
            session_data = get_session(record['session_id'])
            if session_data:
                attendance_records.append({
                    'session_id': record['session_id'],
                    'subject': session_data['subject'],
                    'faculty': session_data['faculty'],
                    'branch': session_data['branch'],
                    'semester': session_data['semester'],
                    'date': session_data['date'],
                    'time': session_data['time'],
                    'timestamp': f"{session_data['date']} {session_data['time']}",
                    'status': record['status']
                })
    
    # Calculate attendance statistics
    total_sessions = len(attendance_records)
    present_count = sum(1 for record in attendance_records if record['status'] == 'present')
    absent_count = total_sessions - present_count
    percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Set attendance stats
    stats = {
        'total_classes': total_sessions,
        'classes_attended': present_count,
        'attendance_percentage': percentage
    }
    
    attendance_stats = {
        'total': total_sessions,
        'present': present_count,
        'absent': absent_count,
        'percentage': percentage
    }
    
    # Get recent sessions for sidebar with full session details
    recent_sessions = []
    for record in attendance_records[:2]:
        session_data = get_session(record['session_id'])
        if session_data:
            recent_sessions.append({
                'subject': session_data['subject'],
                'faculty': session_data['faculty'],
                'branch': session_data['branch'],
                'semester': session_data['semester'],
                'date': session_data['date'],
                'time': session_data['time'],
                'status': record['status']
            })
    
    return render_template(
        'user/dashboard.html',
        student=student_data,
        student_id=student_id,
        attendance_records=attendance_records,
        stats=stats,
        attendance_stats=attendance_stats,
        recent_sessions=recent_sessions
    )

# Student Logout
@app.route('/user/logout')
def user_logout():
    session.pop('student_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('user_login'))

# Student Session View
@app.route('/student-session/<session_id>')
def student_session(session_id):
    if 'student_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    student_id = session['student_id']
    
    # Get session data from database
    session_data = get_session(session_id)
    
    # If session doesn't exist, create a demo session
    if not session_data:
        session_data = create_session({
            'id': session_id,
            'subject': 'Physics' if 'physics' in session_id else 'OOPS',
            'faculty': 'Shilpa Mam' if 'physics' in session_id else 'Avani mam',
            'branch': 'IT' if 'physics' in session_id else 'Diploma',
            'semester': '8th sem' if 'physics' in session_id else '3rd sem',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'status': 'active',
            'description': 'This is a demo session for the ScanMark attendance system.'
        })
    
    # Get student data from database
    student_data = get_student(student_id)
    
    return render_template(
        'student_session.html',
        session=session_data,
        student_id=student_id,
        student=student_data
    )

# Update Profile
@app.route('/user/update-profile', methods=['POST'])
def update_profile():
    if 'student_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'})
    
    try:
        student_id = session['student_id']
        
        # Get data from request
        data = request.json
        
        # Update student profile in database
        updated_student = update_student(student_id, {
            'name': data.get('student_name', ''),
            'branch': data.get('student_branch', ''),
            'semester': data.get('student_semester', ''),
            'email': data.get('student_email', ''),
            'phone': data.get('student_phone', ''),
            'address': data.get('student_address', ''),
            'bio': data.get('student_bio', '')
        })
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'student': updated_student
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Export Attendance
@app.route('/export-attendance/<student_id>')
def export_attendance_csv(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    # Get student data
    student = get_student(student_id)
    
    # Get attendance records
    attendance_records = get_student_attendance(student_id)
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Student ID', 'Name', 'Email', 'Department', 'Branch', 'Semester', 'Phone', 'Subject', 'Faculty', 'Date', 'Status'])
    
    # Write data rows
    for record in attendance_records:
        session_data = get_session(record['session_id'])
        if session_data:
            writer.writerow([
                student_id,
                student.get('name', ''),
                student.get('email', ''),
                student.get('department', ''),
                student.get('branch', ''),
                student.get('semester', ''),
                student.get('phone', ''),
                session_data.get('subject', ''),
                session_data.get('faculty', ''),
                session_data.get('date', ''),
                record.get('status', '')
            ])
    
    # Prepare response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=attendance_{student_id}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

# Scan QR Code Page
@app.route('/user/scan-qr')
def scan_qr_page():
    if 'student_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('user_login'))
    
    student_id = session['student_id']
    
    return render_template(
        'user/scan_qr.html',
        student_id=student_id
    )

# Process QR Code
@app.route('/user/process-qr', methods=['POST'])
def process_qr():
    if 'student_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'})
    
    try:
        student_id = session['student_id']
        data = request.json
        session_token = data.get('session_token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Invalid QR code'})
        
        # Get session data
        session_data = get_session(session_token)
        
        if not session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        if session_data['status'] != 'active':
            return jsonify({'success': False, 'error': 'This session is not active'})
        
        # Mark attendance
        mark_attendance(student_id, session_token, 'present')
        
        return jsonify({
            'success': True,
            'message': 'Attendance marked successfully',
            'session': {
                'subject': session_data['subject'],
                'faculty': session_data['faculty'],
                'date': session_data['date'],
                'time': session_data['time']
            }
        })
    except Exception as e:
        app.logger.error(f"Error processing QR code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Get Student Sessions
@app.route('/user/get-sessions/<student_id>')
def get_student_sessions(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        return jsonify({'success': False, 'error': 'Please login first'})
    
    try:
        # Get attendance records
        attendance_records = get_student_attendance(student_id)
        
        # Format sessions for the response
        sessions = []
        for record in attendance_records:
            session_data = get_session(record['session_id'])
            if session_data:
                sessions.append({
                    'id': session_data['id'],
                    'subject': session_data['subject'],
                    'faculty': session_data['faculty'],
                    'branch': session_data['branch'],
                    'semester': session_data['semester'],
                    'date': session_data['date'],
                    'time': session_data['time'],
                    'status': record['status']
                })
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        app.logger.error(f"Error getting student sessions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Export Attendance
@app.route('/user/export-attendance/<student_id>', methods=['GET'])
def export_attendance(student_id):
    try:
        # Get student data
        student_data = get_student(student_id)
        
        # Get attendance records from database
        attendance_records = get_student_attendance(student_id)
        
        # Create CSV in memory
        si = StringIO()
        csv_writer = csv.writer(si)
        
        # Write student information
        csv_writer.writerow(['Student Information'])
        csv_writer.writerow(['Student ID', student_data['student_id']])
        csv_writer.writerow(['Name', student_data['name']])
        csv_writer.writerow(['Email', student_data['email']])
        csv_writer.writerow(['Department', student_data['department']])
        csv_writer.writerow(['Branch', student_data['branch']])
        csv_writer.writerow(['Semester', student_data['semester']])
        csv_writer.writerow(['Phone', student_data['phone']])
        csv_writer.writerow([])  # Empty row for spacing
        
        # Write attendance header
        csv_writer.writerow(['Attendance Records'])
        csv_writer.writerow(['Subject', 'Faculty', 'Date & Time', 'Status'])
        
        # Write attendance data
        for record in attendance_records:
            csv_writer.writerow([
                record['subject'],
                record['faculty'],
                record['timestamp'],
                record['status'].capitalize()
            ])
        
        # Prepare response
        output = si.getvalue()
        response = app.response_class(
            response=output,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=attendance_history_{student_id}.csv'
            }
        )
        
        return response
    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        flash(f'Error exporting data: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard', student_id=student_id))

# Get students for a session
@app.route('/admin/get-session-students/<session_id>', methods=['GET'])
def get_session_students(session_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get session data
        session_data = get_session(session_id)
        if not session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # For demo purposes, get all students
        students_data = get_all_students()
        
        # Format students for the response
        students = []
        for student_id, student_data in students_data.items():
            students.append({
                'id': student_id,
                'name': f"{student_data['first_name']} {student_data['last_name']}"
            })
        
        return jsonify({
            'success': True,
            'students': students
        })
    except Exception as e:
        app.logger.error(f"Error getting session students: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Create attendance list
@app.route('/admin/create-attendance-list', methods=['POST'])
def create_attendance_list_handler():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        app.logger.info("Received create attendance list request")
        data = request.json
        app.logger.info(f"Request data: {data}")
        
        session_id = data.get('session_id')
        date = data.get('date')
        notes = data.get('notes', '')
        students = data.get('students', {})
        
        app.logger.info(f"Processing attendance for session: {session_id}, date: {date}, students: {len(students)}")
        
        if not session_id or not date:
            app.logger.error("Missing required fields: session_id or date")
            return jsonify({'success': False, 'error': 'Session ID and date are required'}), 400
        
        # Get session data
        session_data = get_session(session_id)
        if not session_data:
            app.logger.error(f"Session not found: {session_id}")
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Create attendance list data
        session_name = f"{session_data['subject']} - {session_data['faculty']} - {session_data['branch']} - {session_data['semester']}"
        app.logger.info(f"Session name: {session_name}")
        
        # Count present and absent students
        present_count = sum(1 for status in students.values() if status == 'present')
        total_students = len(students)
        absent_count = total_students - present_count
        
        app.logger.info(f"Attendance counts - Total: {total_students}, Present: {present_count}, Absent: {absent_count}")
        
        # Create a unique ID with timestamp for easier identification
        list_id = f"list_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        app.logger.info(f"Generated list ID: {list_id}")
        
        # Create attendance list
        attendance_list = {
            'id': list_id,
            'session_id': session_id,
            'session_name': session_name,
            'date': date,
            'notes': notes,
            'students': students,
            'total_students': total_students,
            'present': present_count,
            'absent': absent_count,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Initialize attendance_lists if it doesn't exist
        db = init_db()
        if 'attendance_lists' not in db:
            db['attendance_lists'] = {}
            save_db(db)
            app.logger.info("Initialized attendance_lists in database")
        
        # Save attendance list
        attendance_lists = get_all_attendance_lists()
        attendance_lists[list_id] = attendance_list
        save_attendance_lists(attendance_lists)
        app.logger.info(f"Saved attendance list with ID: {list_id}")
        
        return jsonify({
            'success': True,
            'attendance_list': attendance_list
        })
    except Exception as e:
        app.logger.error(f"Error creating attendance list: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
