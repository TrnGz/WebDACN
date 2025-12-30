import re
import hashlib
import sqlite3
from utils.database import get_db_connection

def validate_email(email):
    """Validate email format"""
    if not email or len(email) > 254:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if '..' in email or email.startswith('.') or email.endswith('.'):
        return False
    
    return re.match(email_pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True
    clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return clean_phone.isdigit() and len(clean_phone) >= 10

def is_valid(email, password):
    """Validate user credentials"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cur.execute('SELECT userId FROM users WHERE email = ? AND password = ?', 
                       (email, hashed_password))
            result = cur.fetchone()
            return result is not None
    except sqlite3.Error as e:
        print(f"Database error in is_valid: {e}")
        return False

def is_admin(email):
    """Check if user is admin"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT role FROM users WHERE email = ?", (email,))
            result = cur.fetchone()
            return result and result[0] == 'admin'
    except sqlite3.Error as e:
        print(f"Database error in is_admin: {e}")
        return False
