from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.helpers import getLoginDetails
from utils.database import get_db_connection
from datetime import datetime
import sqlite3

cart_bp = Blueprint('cart', __name__)

@cart_bp.route("/addToCart")
def addToCart():
    if 'email' not in session:
        flash("Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!")
        return redirect(url_for('auth.loginForm'))
    
    productId = request.args.get('productId')
    if not productId:
        flash("Sản phẩm không hợp lệ!")
        return redirect(url_for('main.root'))
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Get user ID
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            user = cur.fetchone()
            if not user:
                flash("Người dùng không tồn tại!")
                return redirect(url_for('auth.loginForm'))
            
            userId = user[0]
            
            # Check if product exists and has stock
            cur.execute("SELECT name, stock FROM products WHERE productId = ?", (productId,))
            product = cur.fetchone()
            if not product:
                flash("Sản phẩm không tồn tại!")
                return redirect(url_for('main.root'))
            
            if product[1] <= 0:
                flash("Sản phẩm đã hết hàng!")
                return redirect(url_for('main.productDescription', productId=productId))
            
            # Check if product already in cart
            cur.execute("SELECT COUNT(*) FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
            if cur.fetchone()[0] > 0:
                flash("Sản phẩm đã có trong giỏ hàng!")
                return redirect(url_for('cart.cart'))
            
            # Add to cart
            cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
            conn.commit()
            flash(f"Đã thêm '{product[0]}' vào giỏ hàng!")
            
    except sqlite3.Error as e:
        print(f"Database error in addToCart: {e}")
        flash("Lỗi khi thêm sản phẩm vào giỏ hàng!")
    
    return redirect(url_for('main.root'))

@cart_bp.route("/cart")
def cart():
    if 'email' not in session:
        flash("Vui lòng đăng nhập để xem giỏ hàng!")
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
            cur.execute("""
                SELECT products.productId, products.name, products.price, products.image 
                FROM products 
                JOIN kart ON products.productId = kart.productId 
                WHERE kart.userId = ?
            """, (userId,))
            products = cur.fetchall()
            
    except sqlite3.Error as e:
        print(f"Database error in cart: {e}")
        products = []
        flash("Lỗi khi tải giỏ hàng!")
    
    totalPrice = sum(p[2] for p in products) if products else 0
    return render_template("cart.html", 
                         products=products, 
                         totalPrice=totalPrice, 
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems)

@cart_bp.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    productId = request.args.get('productId')
    if not productId:
        flash("Sản phẩm không hợp lệ!")
        return redirect(url_for('cart.cart'))
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            user = cur.fetchone()
            if not user:
                flash("Người dùng không tồn tại!")
                return redirect(url_for('auth.loginForm'))
            
            userId = user[0]
            cur.execute("DELETE FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
            
            if cur.rowcount > 0:
                conn.commit()
                flash("Đã xóa sản phẩm khỏi giỏ hàng!")
            else:
                flash("Không tìm thấy sản phẩm trong giỏ hàng!")
                
    except sqlite3.Error as e:
        print(f"Database error in removeFromCart: {e}")
        flash("Lỗi khi xóa sản phẩm!")
    
    return redirect(url_for('cart.cart'))

@cart_bp.route("/checkout")
def checkout():
    if 'email' not in session:
        flash("Vui lòng đăng nhập để thanh toán!")
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
            cur.execute("""
                SELECT products.productId, products.name, products.price, products.image 
                FROM products 
                JOIN kart ON products.productId = kart.productId 
                WHERE kart.userId = ?
            """, (userId,))
            products = cur.fetchall()
            
            cur.execute("""
                SELECT userId, email, firstName, lastName, address1, address2, 
                       zipcode, city, state, country, phone 
                FROM users WHERE email = ?
            """, (session['email'],))
            profileData = cur.fetchone()
            
    except sqlite3.Error as e:
        print(f"Database error in checkout: {e}")
        products = []
        profileData = None
        flash("Lỗi khi tải thông tin!")
    
    if not products:
        flash("Giỏ hàng trống!")
        return redirect(url_for('cart.cart'))
    
    totalPrice = sum(p[2] for p in products)
    return render_template("checkout.html", 
                         products=products, 
                         totalPrice=totalPrice,
                         profileData=profileData,
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems)

@cart_bp.route("/placeOrder", methods=["POST"])
def placeOrder():
    if 'email' not in session:
        flash("Vui lòng đăng nhập!")
        return redirect(url_for('auth.loginForm'))
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            user = cur.fetchone()
            if not user:
                flash("Người dùng không tồn tại!")
                return redirect(url_for('auth.loginForm'))
            
            userId = user[0]
            
            # Get cart items
            cur.execute("""
                SELECT products.productId, products.name, products.price 
                FROM products 
                JOIN kart ON products.productId = kart.productId 
                WHERE kart.userId = ?
            """, (userId,))
            cart_items = cur.fetchall()
            
            if not cart_items:
                flash("Giỏ hàng trống!")
                return redirect(url_for('cart.cart'))
            
            # Get form data
            firstName = request.form.get('firstName', '').strip()
            lastName = request.form.get('lastName', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address1 = request.form.get('address1', '').strip()
            address2 = request.form.get('address2', '').strip()
            city = request.form.get('city', '').strip()
            zipcode = request.form.get('zipcode', '').strip()
            paymentMethod = request.form.get('paymentMethod', 'cod')
            
            if not all([firstName, lastName, email, phone, address1, city]):
                flash("Vui lòng điền đầy đủ thông tin!")
                return redirect(url_for('cart.checkout'))
            
            # Calculate total
            totalPrice = sum(item[2] for item in cart_items) + 30000  # +30k shipping
            
            # Create shipping address
            shippingAddress = f"{firstName} {lastName}, {address1}"
            if address2:
                shippingAddress += f", {address2}"
            shippingAddress += f", {city}, {zipcode}, {phone}"
            
            # Create order
            orderDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cur.execute("""
                INSERT INTO orders (userId, orderDate, status, totalPrice, shippingAddress, paymentMethod)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (userId, orderDate, 'Đang xử lý', totalPrice, shippingAddress, paymentMethod))
            
            orderId = cur.lastrowid
            
            # Add order items and subtract stock by 1 safely
            for item in cart_items:
                productId, name, price = item
                
                # Insert order item with quantity 1
                cur.execute("""
                    INSERT INTO order_items (orderId, productId, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (orderId, productId, 1, price))
                
                # Decrement stock by 1
                cur.execute("""
                    UPDATE products
                    SET stock = stock - 1
                    WHERE productId = ? AND stock > 0
                """, (productId,))
                
                # Optional: Check if stock reached zero (no action here, but could log)
            
            # Clear cart
            cur.execute("DELETE FROM kart WHERE userId = ?", (userId,))
            
            conn.commit()
            flash(f"Đặt hàng thành công! Mã đơn hàng: #{orderId}")
            return redirect(url_for('profile.orders'))
            
    except sqlite3.Error as e:
        print(f"Database error in placeOrder: {e}")
        flash("Lỗi khi đặt hàng!")
        return redirect(url_for('cart.checkout'))
