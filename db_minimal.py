import json
import os
from datetime import datetime

# File path for our simple JSON database
DB_FILE = 'minimal_db.json'

def init_db():
    """Initialize the database if it doesn't exist"""
    if not os.path.exists(DB_FILE):
        default_data = {
            'students': {},
            'sessions': {},
            'attendance': {},
            'attendance_lists': {}
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    # If DB exists, load it
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    """Save data to the database"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_student(student_id):
    """Get a student by ID"""
    db = init_db()
    return db['students'].get(student_id, {
        'student_id': student_id,
        'name': f'Student {student_id}',
        'email': f'{student_id}@example.com',
        'department': 'Computer Science',
        'branch': 'Computer',
        'semester': '3rd',
        'phone': '',
        'address': '',
        'bio': '',
        'created_at': datetime.now().isoformat()
    })

def update_student(student_id, data):
    """Update a student's profile"""
    db = init_db()
    
    # If student doesn't exist, create a default profile
    if student_id not in db['students']:
        db['students'][student_id] = {
            'student_id': student_id,
            'name': f'Student {student_id}',
            'email': f'{student_id}@example.com',
            'department': 'Computer Science',
            'branch': 'Computer',
            'semester': '3rd',
            'phone': '',
            'address': '',
            'bio': '',
            'created_at': datetime.now().isoformat()
        }
    
    # Update with new data
    for key, value in data.items():
        if key != 'student_id' and key != 'created_at':  # Don't allow changing ID or creation date
            db['students'][student_id][key] = value
    
    # Add last updated timestamp
    db['students'][student_id]['updated_at'] = datetime.now().isoformat()
    
    # Save to database
    save_db(db)
    
    return db['students'][student_id]

def get_all_students():
    """Get all students"""
    db = init_db()
    return db['students']

def get_session(session_id):
    """Get a session by ID"""
    db = init_db()
    return db['sessions'].get(session_id, None)

def create_session(session_data):
    """Create a new session"""
    db = init_db()
    session_id = session_data.get('id', f'session-{len(db["sessions"]) + 1}')
    
    db['sessions'][session_id] = {
        'id': session_id,
        'subject': session_data.get('subject', 'Unknown Subject'),
        'faculty': session_data.get('faculty', 'Unknown Faculty'),
        'branch': session_data.get('branch', 'Unknown Branch'),
        'semester': session_data.get('semester', 'Unknown Semester'),
        'date': session_data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'time': session_data.get('time', datetime.now().strftime('%H:%M')),
        'status': session_data.get('status', 'active'),
        'description': session_data.get('description', ''),
        'created_at': datetime.now().isoformat()
    }
    
    save_db(db)
    return db['sessions'][session_id]

def get_all_sessions():
    """Get all sessions"""
    db = init_db()
    return db['sessions']

def update_session(session_id, data):
    """Update a session's data"""
    db = init_db()
    
    # Check if session exists
    if session_id not in db['sessions']:
        return None
    
    # Update with new data
    for key, value in data.items():
        if key != 'id' and key != 'created_at':  # Don't allow changing ID or creation date
            db['sessions'][session_id][key] = value
    
    # Add last updated timestamp
    db['sessions'][session_id]['updated_at'] = datetime.now().isoformat()
    
    # Save to database
    save_db(db)
    
    return db['sessions'][session_id]

def delete_session(session_id):
    """Delete a session from the database"""
    db = init_db()
    
    # Check if session exists
    if session_id not in db['sessions']:
        return False
    
    # Remove the session
    deleted_session = db['sessions'].pop(session_id)
    
    # Save to database
    save_db(db)
    
    return True

def mark_attendance(student_id, session_id, status='present'):
    """Mark attendance for a student in a session"""
    db = init_db()
    
    # Check if student and session exist
    if student_id not in db['students'] or session_id not in db['sessions']:
        return False
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create attendance record
    attendance_id = str(uuid.uuid4())
    db['attendance'][attendance_id] = {
        'id': attendance_id,
        'student_id': student_id,
        'session_id': session_id,
        'status': status,
        'timestamp': timestamp
    }
    
    # Save to database
    save_db(db)
    
    return db['attendance'][attendance_id]

def get_student_attendance(student_id):
    """Get attendance records for a student"""
    db = init_db()
    
    student_attendance = []
    for key, attendance in db['attendance'].items():
        if attendance['student_id'] == student_id:
            student_attendance.append(attendance)
    
    return student_attendance

def get_all_attendance_lists():
    """Get all attendance lists from the database"""
    db = init_db()
    return db.get('attendance_lists', {})

def get_attendance_list(list_id):
    """Get a specific attendance list from the database"""
    db = init_db()
    attendance_lists = db.get('attendance_lists', {})
    return attendance_lists.get(list_id)

def save_attendance_lists(attendance_lists):
    """Save attendance lists to the database"""
    db = init_db()
    db['attendance_lists'] = attendance_lists
    save_db(db)
    return True

def get_student(student_id):
    """Get a student from the database"""
    db = init_db()
    return db['students'].get(student_id)

def get_session_attendance(session_id):
    """Get attendance records for a session"""
    db = init_db()
    
    session_attendance = []
    for key, attendance in db['attendance'].items():
        if attendance['session_id'] == session_id:
            session_attendance.append(attendance)
    
    return session_attendance

def create_attendance_list(list_data):
    """Create a new attendance list"""
    db = init_db()
    
    # Initialize attendance_lists if it doesn't exist
    if 'attendance_lists' not in db:
        db['attendance_lists'] = {}
    
    list_id = list_data.get('id', f"list_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    db['attendance_lists'][list_id] = {
        'id': list_id,
        'session_id': list_data.get('session_id', ''),
        'session_name': list_data.get('session_name', ''),
        'date': list_data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'notes': list_data.get('notes', ''),
        'total_students': list_data.get('total_students', 0),
        'present': list_data.get('present', 0),
        'absent': list_data.get('absent', 0),
        'created_at': datetime.now().isoformat()
    }
    
    save_db(db)
    return db['attendance_lists'][list_id]

def get_all_attendance_lists():
    """Get all attendance lists"""
    db = init_db()
    # Initialize attendance_lists if it doesn't exist
    if 'attendance_lists' not in db:
        db['attendance_lists'] = {}
        save_db(db)
    return db['attendance_lists']

def get_attendance_list(list_id):
    """Get a specific attendance list by ID"""
    db = init_db()
    # Initialize attendance_lists if it doesn't exist
    if 'attendance_lists' not in db:
        db['attendance_lists'] = {}
        save_db(db)
    return db['attendance_lists'].get(list_id)

# Initialize the database when the module is imported
init_db()
