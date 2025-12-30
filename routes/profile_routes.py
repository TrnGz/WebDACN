from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.helpers import getLoginDetails, getUserStats, getRecentActivity
from utils.validators import validate_phone
from utils.database import get_db_connection
import sqlite3
import hashlib

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/account/profile")
def profileHome():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT userId, email, firstName, lastName, address1, address2, 
                       zipcode, city, state, country, phone 
                FROM users WHERE email = ?
            """, (session['email'],))
            user_data = cur.fetchone()
            
            if user_data:
                userId = user_data[0]
                stats = getUserStats(userId)
                recent_activities = getRecentActivity(userId)
                
                user_info = {
                    'userId': user_data[0],
                    'email': user_data[1],
                    'firstName': user_data[2] or 'User',
                    'lastName': user_data[3] or 'Name',
                    'fullName': f"{user_data[2] or 'User'} {user_data[3] or 'Name'}",
                    'address1': user_data[4] or '',
                    'address2': user_data[5] or '',
                    'zipcode': user_data[6] or '',
                    'city': user_data[7] or 'Hải Dương',
                    'state': user_data[8] or 'Hải Dương',
                    'country': user_data[9] or 'Việt Nam',
                    'phone': user_data[10] or '',
                    'avatar_letters': f"{(user_data[2] or 'U')[0]}{(user_data[3] or 'N')[0]}",
                    'member_since': '2023'
                }
                
                return render_template("profileHome.html", 
                                     loggedIn=loggedIn, 
                                     firstName=firstName, 
                                     noOfItems=noOfItems,
                                     user_info=user_info,
                                     stats=stats,
                                     recent_activities=recent_activities)
                                     
    except sqlite3.Error as e:
        print(f"Database error in profileHome: {e}")
        flash("Lỗi khi tải thông tin hồ sơ!")
    
    return redirect(url_for('auth.loginForm'))

@profile_bp.route("/account/profile/view")
def viewProfile():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT userId, email, firstName, lastName, address1, address2, 
                                   zipcode, city, state, country, phone 
                            FROM users WHERE email = ?""", (session['email'],))
            profileData = cur.fetchone()
            
            if not profileData:
                flash("Không tìm thấy thông tin người dùng!")
                return redirect(url_for('auth.loginForm'))

            user_info = {
                'userId': profileData[0],
                'email': profileData[1],
                'firstName': profileData[2] or 'User ',
                'lastName': profileData[3] or 'Name',
                'fullName': f"{profileData[2] or 'User '} {profileData[3] or 'Name'}",
                'address1': profileData[4] or '',
                'address2': profileData[5] or '',
                'zipcode': profileData[6] or '',
                'city': profileData[7] or 'Hải Dương',
                'state': profileData[8] or 'Hải Dương',
                'country': profileData[9] or 'Việt Nam',
                'phone': profileData[10] or '',
                'avatar_letters': f"{(profileData[2] or 'U')[0]}{(profileData[3] or 'N')[0]}",
                'member_since': '2023'  # You can replace this with actual member since date if available
            }
            
            return render_template("viewProfile.html", 
                                   loggedIn=loggedIn, 
                                   firstName=firstName, 
                                   noOfItems=noOfItems,
                                   user_info=user_info)  # Pass user_info to the template

    except sqlite3.Error as e:
        print(f"Database error in viewProfile: {e}")
        flash("Lỗi khi tải thông tin hồ sơ!")
    
    return redirect(url_for('auth.loginForm'))


@profile_bp.route("/account/profile/edit", methods=["GET", "POST"])
def editProfile():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    
    if request.method == "POST":
        try:
            # Get form data
            email = session['email']
            firstName = request.form.get('firstName', '').strip()
            lastName = request.form.get('lastName', '').strip()
            address1 = request.form.get('address1', '').strip()
            address2 = request.form.get('address2', '').strip()
            zipcode = request.form.get('zipcode', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            country = request.form.get('country', 'Việt Nam').strip()
            phone = request.form.get('phone', '').strip()
            
            # Validation
            if not firstName or not lastName:
                flash("Họ và tên không được để trống!")
                return redirect(url_for('profile.editProfile'))
            
            if not validate_phone(phone):
                flash("Số điện thoại không hợp lệ!")
                return redirect(url_for('profile.editProfile'))
            
            # Update database
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if user exists
                cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
                user = cur.fetchone()
                if not user:
                    flash("Không tìm thấy thông tin người dùng!")
                    return redirect(url_for('auth.loginForm'))
                
                # Update profile
                cur.execute('''
                    UPDATE users SET 
                    firstName=?, lastName=?, address1=?, address2=?, 
                    zipcode=?, city=?, state=?, country=?, phone=? 
                    WHERE email=?
                ''', (firstName, lastName, address1, address2, 
                      zipcode, city, state, country, phone, email))
                
                if cur.rowcount > 0:
                    conn.commit()
                    flash("Cập nhật thông tin cá nhân thành công!")
                else:
                    flash("Không có thay đổi nào được thực hiện!")
                
        except sqlite3.Error as e:
            print(f"Database error in editProfile: {e}")
            flash("Lỗi cơ sở dữ liệu khi cập nhật!")
        except Exception as e:
            print(f"General error in editProfile: {e}")
            flash("Lỗi khi cập nhật thông tin!")
        
        return redirect(url_for('profile.editProfile'))
    
    # GET request - load current profile data
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT userId, email, firstName, lastName, address1, address2, 
                       zipcode, city, state, country, phone 
                FROM users WHERE email = ?
            """, (session['email'],))
            profileData = cur.fetchone()
            
            if not profileData:
                flash("Không tìm thấy thông tin người dùng!")
                return redirect(url_for('auth.loginForm'))
                
    except sqlite3.Error as e:
        print(f"Database error loading profile: {e}")
        flash("Lỗi khi tải thông tin!")
        profileData = None
    
    return render_template("editProfile.html", 
                         profileData=profileData, 
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems)

@profile_bp.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))

    loggedIn, firstName, noOfItems = getLoginDetails()

    if request.method == "POST":
        oldPassword = request.form.get('oldpassword', '')
        newPassword = request.form.get('newpassword', '')
        confirmPassword = request.form.get('confirmpassword', '')

        # Validation
        if not oldPassword or not newPassword or not confirmPassword:
            flash("Vui lòng điền đầy đủ thông tin!", "error")
            return render_template("changePassword.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

        if newPassword != confirmPassword:
            flash("Mật khẩu mới và xác nhận không khớp!", "error")
            return render_template("changePassword.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

        if len(newPassword) < 6:
            flash("Mật khẩu mới phải có ít nhất 6 ký tự!", "error")
            return render_template("changePassword.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

        try:
            oldPasswordHash = hashlib.md5(oldPassword.encode()).hexdigest()
            newPasswordHash = hashlib.md5(newPassword.encode()).hexdigest()

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'],))
                user = cur.fetchone()

                if not user:
                    flash("Không tìm thấy thông tin người dùng!", "error")
                    return redirect(url_for('auth.loginForm'))

                userId, currentPassword = user
                if currentPassword == oldPasswordHash:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPasswordHash, userId))
                    conn.commit()
                    flash("Đổi mật khẩu thành công!", "success")
                else:
                    flash("Mật khẩu cũ không đúng!", "error")

        except sqlite3.Error as e:
            print(f"Database error in changePassword: {e}")
            flash("Lỗi khi đổi mật khẩu!", "error")

    return render_template("changePassword.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@profile_bp.route("/account/orders")
def orders():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            user = cur.fetchone()
            if not user:
                flash("Người dùng không tồn tại!")
                return redirect(url_for('auth.loginForm'))
            
            userId = user[0]
            
            # Create tables if they don't exist
            cur.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    orderId INTEGER PRIMARY KEY AUTOINCREMENT,
                    userId INTEGER,
                    orderDate TEXT,
                    status TEXT DEFAULT 'Đang xử lý',
                    totalPrice REAL,
                    shippingAddress TEXT,
                    paymentMethod TEXT,
                    FOREIGN KEY (userId) REFERENCES users(userId)
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    orderItemId INTEGER PRIMARY KEY AUTOINCREMENT,
                    orderId INTEGER,
                    productId INTEGER,
                    quantity INTEGER DEFAULT 1,
                    price REAL,
                    FOREIGN KEY (orderId) REFERENCES orders(orderId),
                    FOREIGN KEY (productId) REFERENCES products(productId)
                )
            ''')
            
            # Get orders list
            cur.execute("""
                SELECT orderId, orderDate, status, totalPrice 
                FROM orders 
                WHERE userId = ? 
                ORDER BY orderId DESC
            """, (userId,))
            order_list = cur.fetchall()
            
            orders = []
            for order in order_list:
                orderId, orderDate, status, totalPrice = order
                
                # Get order items
                cur.execute("""
                    SELECT p.name, p.image, oi.price, oi.quantity
                    FROM order_items oi
                    JOIN products p ON oi.productId = p.productId
                    WHERE oi.orderId = ?
                """, (orderId,))
                items_data = cur.fetchall()
                
                order_items = []
                for item in items_data:
                    order_items.append({
                        'name': item[0],
                        'image': item[1],
                        'price': item[2],
                        'quantity': item[3]
                    })
                
                orders.append({
                    'orderId': orderId,
                    'orderDate': orderDate,
                    'status': status,
                    'totalPrice': totalPrice,
                    'order_items': order_items
                })
                
    except sqlite3.Error as e:
        print(f"Database error in orders: {e}")
        orders = []
        flash("Lỗi khi tải đơn hàng!")
    
    return render_template("orders.html", 
                         orders=orders,
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems)
