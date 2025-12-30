from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.validators import validate_email, validate_phone, is_valid, is_admin
from utils.database import get_db_connection
from datetime import timedelta
import sqlite3
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/registerForm")
def registerForm():
    return render_template("register.html")

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        cpassword = request.form.get('cpassword', '')
        firstName = request.form.get('firstName', '').strip()
        lastName = request.form.get('lastName', '').strip()
        address1 = request.form.get('address1', '').strip()
        address2 = request.form.get('address2', '').strip()
        zipcode = request.form.get('zipcode', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not email or not password or not firstName or not lastName:
            flash("Vui lòng điền đầy đủ thông tin bắt buộc!")
            return redirect(url_for('auth.registerForm'))
        
        if password != cpassword:
            flash("Mật khẩu xác nhận không khớp!")
            return redirect(url_for('auth.registerForm'))
        
        if len(password) < 6:
            flash("Mật khẩu phải có ít nhất 6 ký tự!")
            return redirect(url_for('auth.registerForm'))
        
        if not validate_email(email):
            flash("Email không hợp lệ!")
            return redirect(url_for('auth.registerForm'))
        
        if not validate_phone(phone):
            flash("Số điện thoại không hợp lệ!")
            return redirect(url_for('auth.registerForm'))
        
        # Hash password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Insert into database
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if email already exists
            cur.execute("SELECT email FROM users WHERE email = ?", (email,))
            if cur.fetchone():
                flash("Email đã được sử dụng!")
                return redirect(url_for('auth.registerForm'))
            
            # Insert new user
            cur.execute('''
                INSERT INTO users 
                (email, password, firstName, lastName, address1, address2, 
                 zipcode, city, state, country, phone, role) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email, hashed_password, firstName, lastName, address1, address2,
                  zipcode, city, state, country, phone, 'user'))
            
            conn.commit()
            
        flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for('auth.loginForm'))
        
    except sqlite3.IntegrityError:
        flash("Email đã được sử dụng!")
        return redirect(url_for('auth.registerForm'))
    except sqlite3.Error as e:
        print(f"Database error in register: {e}")
        flash("Lỗi cơ sở dữ liệu khi đăng ký!")
        return redirect(url_for('auth.registerForm'))
    except Exception as e:
        print(f"Registration error: {e}")
        flash("Lỗi khi đăng ký!")
        return redirect(url_for('auth.registerForm'))

@auth_bp.route("/loginForm")
def loginForm():
    if 'email' in session:
        if is_admin(session['email']):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.root'))
    
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')
        
        if not email or not password:
            flash("Vui lòng nhập đầy đủ email và mật khẩu!", "error")
            return redirect(url_for('auth.loginForm'))
        
        if not validate_email(email):
            flash("Định dạng email không hợp lệ!", "error")
            return redirect(url_for('auth.loginForm'))
        
        if len(password) < 6:
            flash("Mật khẩu phải có ít nhất 6 ký tự!", "error")
            return redirect(url_for('auth.loginForm'))
        
        if is_valid(email, password):
            session['email'] = email
            
            if remember:
                session.permanent = True
                from flask import current_app
                current_app.permanent_session_lifetime = timedelta(days=30)
            
            if is_admin(email):
                flash("Chào mừng Admin! Bạn đã đăng nhập thành công.", "success")
                return redirect(url_for('admin.dashboard'))
            else:
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT firstName FROM users WHERE email = ?", (email,))
                        user = cur.fetchone()
                        firstName = user[0] if user and user[0] else "User"
                        flash(f"Chào mừng {firstName}! Đăng nhập thành công.", "success")
                except sqlite3.Error:
                    flash("Đăng nhập thành công!", "success")
                
                return redirect(url_for('main.root'))
        else:
            flash("Email hoặc mật khẩu không đúng! Vui lòng thử lại.", "error")
            return redirect(url_for('auth.loginForm'))
            
    except sqlite3.Error as e:
        print(f"Database error in login: {e}")
        flash("Lỗi cơ sở dữ liệu! Vui lòng thử lại sau.", "error")
        return redirect(url_for('auth.loginForm'))
    except Exception as e:
        print(f"Login error: {e}")
        flash("Có lỗi xảy ra khi đăng nhập! Vui lòng thử lại.", "error")
        return redirect(url_for('auth.loginForm'))

@auth_bp.route("/logout")
def logout():
    if 'email' in session:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT firstName FROM users WHERE email = ?", (session['email'],))
                user = cur.fetchone()
                firstName = user[0] if user and user[0] else "User"
                
            session.clear()
            flash(f"Tạm biệt {firstName}! Bạn đã đăng xuất thành công.", "info")
        except:
            session.clear()
            flash("Đã đăng xuất thành công!", "info")
    else:
        flash("Bạn chưa đăng nhập!", "info")
    
    return redirect(url_for('main.root'))
