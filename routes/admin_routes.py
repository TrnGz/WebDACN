from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
import sqlite3, os
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from utils.database import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin(email):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT role FROM users WHERE email = ?", (email,))
            result = cur.fetchone()
            return result and result[0] == 'admin'
    except:
        return False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Vui lòng đăng nhập để truy cập trang này.")
            return redirect(url_for('auth.loginForm'))
        
        if not is_admin(session['email']):
            flash("Bạn không có quyền truy cập trang này!")
            return redirect(url_for('main.root'))
        return f(*args, **kwargs)
    return decorated_function

# Dashboard
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Thống kê tổng quan
            cur.execute("SELECT COUNT(*) FROM products")
            total_products = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
            total_users = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM orders")
            total_orders = cur.fetchone()[0]
            
            cur.execute("SELECT COALESCE(SUM(totalPrice), 0) FROM orders WHERE status != 'Đã hủy'")
            total_revenue = cur.fetchone()[0]
            
            # Sản phẩm sắp hết hàng
            cur.execute("SELECT name, stock FROM products WHERE stock < 5 ORDER BY stock ASC LIMIT 5")
            low_stock_products = cur.fetchall()
            
            # Đơn hàng gần đây
            cur.execute("""
                SELECT o.orderId, u.firstName, u.lastName, o.orderDate, o.status, o.totalPrice
                FROM orders o
                JOIN users u ON o.userId = u.userId
                ORDER BY o.orderId DESC
                LIMIT 5
            """)
            recent_orders = cur.fetchall()
            
            stats = {
                'total_products': total_products,
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'low_stock_products': low_stock_products,
                'recent_orders': recent_orders
            }
            
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        flash(f"Lỗi khi tải dashboard: {str(e)}")
        return render_template('admin/dashboard.html', stats={})

# Product Management
@admin_bp.route('/products')
@admin_required
def list_products():
    category_filter = request.args.get('category_filter', type=int, default=None)
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Load categories for dropdown
            cur.execute("SELECT categoryId, name FROM categories ORDER BY name")
            categories = cur.fetchall()
            # Select products with optional category filtering
            if category_filter:
                cur.execute('''SELECT p.productId, p.name, p.price, p.description, p.image, p.stock, c.name as categoryName
                               FROM products p
                               LEFT JOIN categories c ON p.categoryId = c.categoryId
                               WHERE p.categoryId = ?
                               ORDER BY p.productId DESC''', (category_filter,))
            else:
                cur.execute('''SELECT p.productId, p.name, p.price, p.description, p.image, p.stock, c.name as categoryName
                               FROM products p
                               LEFT JOIN categories c ON p.categoryId = c.categoryId
                               ORDER BY p.productId DESC''')
            products = cur.fetchall()
        return render_template('admin/list_products.html', products=products, categories=categories)
    except Exception as e:
        flash(f"Lỗi khi tải danh sách sản phẩm: {str(e)}")
        return render_template('admin/list_products.html', products=[], categories=[])

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT categoryId, name FROM categories ORDER BY name")
            categories = cur.fetchall()
    except Exception as e:
        flash(f"Lỗi khi tải danh mục: {str(e)}")
        categories = []

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            price_str = request.form.get('price', '').strip()
            description = request.form.get('description', '').strip()
            stock_str = request.form.get('stock', '').strip()
            category_str = request.form.get('category', '').strip()

            # Validate required fields
            if not all([name, price_str, stock_str, category_str]):
                flash("Vui lòng điền đầy đủ thông tin!", "error")
                return render_template('admin/add_product.html', categories=categories, form=request.form)

            price = float(price_str)
            stock = int(stock_str)
            categoryId = int(category_str)

            if price < 0 or stock < 0:
                flash("Giá và số lượng phải lớn hơn hoặc bằng 0!", "error")
                return render_template('admin/add_product.html', categories=categories, form=request.form)

            filename = ''
            image = request.files.get('image')
            if image and image.filename:
                if allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    import time
                    timestamp = str(int(time.time()))
                    name_part, ext = os.path.splitext(filename)
                    filename = f"{name_part}_{timestamp}{ext}"

                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    image.save(os.path.join(upload_folder, filename))
                else:
                    flash("Định dạng file không hợp lệ!", "error")
                    return render_template('admin/add_product.html', categories=categories, form=request.form)

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('''INSERT INTO products (name, price, description, image, stock, categoryId)
                               VALUES (?, ?, ?, ?, ?, ?)''',
                            (name, price, description, filename, stock, categoryId))
                conn.commit()

            flash("Thêm sản phẩm thành công!", "success")
            return redirect(url_for('admin.list_products'))

        except ValueError:
            flash("Giá và số lượng phải là số hợp lệ!", "error")
        except Exception as e:
            flash(f"Lỗi khi thêm sản phẩm: {str(e)}", "error")

        # On failure, render with form values preserved
        return render_template('admin/add_product.html', categories=categories, form=request.form)

    return render_template('admin/add_product.html', categories=categories, form={})

@admin_bp.route('/products/edit/<int:productId>', methods=['GET', 'POST'])
@admin_required
def edit_product(productId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT categoryId, name FROM categories ORDER BY name")
            categories = cur.fetchall()

            cur.execute("SELECT productId, name, price, description, image, stock, categoryId FROM products WHERE productId = ?", (productId,))
            product = cur.fetchone()
    except Exception as e:
        flash(f"Lỗi khi tải dữ liệu: {str(e)}")
        return redirect(url_for('admin.list_products'))

    if not product:
        flash("Sản phẩm không tồn tại!")
        return redirect(url_for('admin.list_products'))

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            price_str = request.form.get('price', '').strip()
            description = request.form.get('description', '').strip()
            stock_str = request.form.get('stock', '').strip()
            category_str = request.form.get('category', '').strip()
            
            if not all([name, price_str, stock_str, category_str]):
                flash("Vui lòng điền đầy đủ thông tin!")
                return render_template('admin/edit_product.html', product=product, categories=categories)
            
            price = float(price_str)
            stock = int(stock_str)
            categoryId = int(category_str)

            filename = product[4]
            image = request.files.get('image')
            if image and image.filename:
                if allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    import time
                    timestamp = str(int(time.time()))
                    name_part, ext = os.path.splitext(filename)
                    filename = f"{name_part}_{timestamp}{ext}"
                    
                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    if product[4] and os.path.exists(os.path.join(upload_folder, product[4])):
                        try:
                            os.remove(os.path.join(upload_folder, product[4]))
                        except:
                            pass
                    
                    image.save(os.path.join(upload_folder, filename))
                else:
                    flash("Định dạng file không hợp lệ!")
                    return render_template('admin/edit_product.html', product=product, categories=categories)

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('''UPDATE products SET name=?, price=?, description=?, image=?, stock=?, categoryId=? 
                              WHERE productId=?''',
                            (name, price, description, filename, stock, categoryId, productId))
                conn.commit()
                
                flash("Cập nhật sản phẩm thành công!")
                return redirect(url_for('admin.list_products'))
                
        except Exception as e:
            flash(f"Lỗi khi cập nhật sản phẩm: {str(e)}")

    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin_bp.route('/products/delete/<int:productId>', methods=['POST'])
@admin_required
def delete_product(productId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT image FROM products WHERE productId = ?", (productId,))
            product = cur.fetchone()
            
            if not product:
                flash("Sản phẩm không tồn tại!")
                return redirect(url_for('admin.list_products'))
            
            cur.execute("SELECT COUNT(*) FROM kart WHERE productId = ?", (productId,))
            cart_count = cur.fetchone()[0]
            
            if cart_count > 0:
                cur.execute("DELETE FROM kart WHERE productId = ?", (productId,))
            
            cur.execute("DELETE FROM products WHERE productId = ?", (productId,))
            conn.commit()
            
            if product[0]:
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                image_path = os.path.join(upload_folder, product[0])
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except:
                        pass
            
            flash("Xóa sản phẩm thành công!")
            
    except Exception as e:
        flash(f"Lỗi khi xóa sản phẩm: {str(e)}")
        
    return redirect(url_for('admin.list_products'))

@admin_bp.route('/users')
@admin_required
def list_users():
    search_name = request.args.get('search_name', '').strip()
    
    sql = '''SELECT userId, email, firstName, lastName, phone, city, country, role 
             FROM users'''
    params = []
    
    if search_name:
        sql += ' WHERE firstName LIKE ? OR lastName LIKE ?'
        like_pattern = f'%{search_name}%'
        params.extend([like_pattern, like_pattern])
    
    sql += ' ORDER BY userId DESC'
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            users = cur.fetchall()
        return render_template('admin/list_users.html', users=users, search_name=search_name)
    except Exception as e:
        flash(f"Lỗi khi tải danh sách người dùng: {str(e)}")
        return render_template('admin/list_users.html', users=[], search_name=search_name)


@admin_bp.route('/users/edit/<int:userId>', methods=['GET', 'POST'])
@admin_required
def edit_user(userId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT userId, email, firstName, lastName, address1, address2, 
                          zipcode, city, state, country, phone, role 
                          FROM users WHERE userId = ?''', (userId,))
            user = cur.fetchone()
    except Exception as e:
        flash(f"Lỗi khi tải thông tin người dùng: {str(e)}")
        return redirect(url_for('admin.list_users'))

    if not user:
        flash("Người dùng không tồn tại!")
        return redirect(url_for('admin.list_users'))

    if request.method == 'POST':
        try:
            firstName = request.form.get('firstName', '').strip()
            lastName = request.form.get('lastName', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address1 = request.form.get('address1', '').strip()
            address2 = request.form.get('address2', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            country = request.form.get('country', '').strip()
            zipcode = request.form.get('zipcode', '').strip()
            role = request.form.get('role', 'user')
            
            if not all([firstName, lastName, email]):
                flash("Vui lòng điền đầy đủ thông tin bắt buộc!")
                return render_template('admin/edit_user.html', user=user)

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('''UPDATE users SET firstName=?, lastName=?, email=?, phone=?, 
                              address1=?, address2=?, city=?, state=?, country=?, zipcode=?, role=?
                              WHERE userId=?''',
                            (firstName, lastName, email, phone, address1, address2, 
                             city, state, country, zipcode, role, userId))
                conn.commit()
                
                flash("Cập nhật thông tin người dùng thành công!")
                return redirect(url_for('admin.list_users'))
                
        except Exception as e:
            flash(f"Lỗi khi cập nhật: {str(e)}")

    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/delete/<int:userId>', methods=['POST'])
@admin_required
def delete_user(userId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Kiểm tra xem có đơn hàng nào không
            cur.execute("SELECT COUNT(*) FROM orders WHERE userId = ?", (userId,))
            order_count = cur.fetchone()[0]
            
            if order_count > 0:
                flash("Không thể xóa người dùng có đơn hàng!")
                return redirect(url_for('admin.list_users'))
            
            # Xóa giỏ hàng trước
            cur.execute("DELETE FROM kart WHERE userId = ?", (userId,))
            
            # Xóa người dùng
            cur.execute("DELETE FROM users WHERE userId = ?", (userId,))
            conn.commit()
            
            flash("Xóa người dùng thành công!")
            
    except Exception as e:
        flash(f"Lỗi khi xóa người dùng: {str(e)}")
        
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/orders')
@admin_required
def list_orders():
    search_name = request.args.get('search_name', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    sql = '''
        SELECT o.orderId, u.firstName, u.lastName, u.email, o.orderDate, 
               o.status, o.totalPrice, o.paymentMethod
        FROM orders o
        JOIN users u ON o.userId = u.userId
        WHERE 1=1
    '''
    params = []
    
    if search_name:
        sql += " AND (u.firstName LIKE ? OR u.lastName LIKE ?)"
        like_pattern = f'%{search_name}%'
        params.extend([like_pattern, like_pattern])
    
    if start_date:
        sql += " AND o.orderDate >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND o.orderDate <= ?"
        params.append(end_date)
    
    sql += " ORDER BY o.orderId DESC"
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            orders = cur.fetchall()
        return render_template('admin/list_orders.html', orders=orders,
                               search_name=search_name, start_date=start_date, end_date=end_date)
    except Exception as e:
        flash(f"Lỗi khi tải danh sách đơn hàng: {str(e)}")
        return render_template('admin/list_orders.html', orders=[])


@admin_bp.route('/orders/view/<int:orderId>')
@admin_required
def view_order(orderId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Lấy thông tin đơn hàng
            cur.execute('''SELECT o.orderId, u.firstName, u.lastName, u.email, u.phone,
                          o.orderDate, o.status, o.totalPrice, o.shippingAddress, o.paymentMethod
                          FROM orders o
                          JOIN users u ON o.userId = u.userId
                          WHERE o.orderId = ?''', (orderId,))
            order = cur.fetchone()
            
            if not order:
                flash("Đơn hàng không tồn tại!")
                return redirect(url_for('admin.list_orders'))
            
            # Lấy chi tiết sản phẩm
            cur.execute('''SELECT p.name, p.image, oi.price, oi.quantity
                          FROM order_items oi
                          JOIN products p ON oi.productId = p.productId
                          WHERE oi.orderId = ?''', (orderId,))
            order_items = cur.fetchall()
            
        return render_template('admin/view_order.html', order=order, order_items=order_items)
    except Exception as e:
        flash(f"Lỗi khi tải chi tiết đơn hàng: {str(e)}")
        return redirect(url_for('admin.list_orders'))

@admin_bp.route('/orders/update_status/<int:orderId>', methods=['POST'])
@admin_required
def update_order_status(orderId):
    try:
        status = request.form.get('status')
        if not status:
            flash("Vui lòng chọn trạng thái!")
            return redirect(url_for('admin.view_order', orderId=orderId))
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status = ? WHERE orderId = ?", (status, orderId))
            conn.commit()
            
            flash("Cập nhật trạng thái đơn hàng thành công!")
            
    except Exception as e:
        flash(f"Lỗi khi cập nhật trạng thái: {str(e)}")
        
    return redirect(url_for('admin.view_order', orderId=orderId))

# Order Attachments Management
@admin_bp.route('/order-attachments')
@admin_required
def list_order_attachments():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Tạo bảng nếu chưa có
            cur.execute('''CREATE TABLE IF NOT EXISTS order_attachments (
                attachmentId INTEGER PRIMARY KEY AUTOINCREMENT,
                orderId INTEGER,
                fileName TEXT NOT NULL,
                originalName TEXT NOT NULL,
                fileSize INTEGER,
                uploadDate TEXT,
                description TEXT,
                FOREIGN KEY (orderId) REFERENCES orders(orderId)
            )''')
            
            cur.execute('''SELECT oa.attachmentId, oa.orderId, oa.fileName, oa.originalName,
                          oa.fileSize, oa.uploadDate, oa.description, u.firstName, u.lastName
                          FROM order_attachments oa
                          LEFT JOIN orders o ON oa.orderId = o.orderId
                          LEFT JOIN users u ON o.userId = u.userId
                          ORDER BY oa.attachmentId DESC''')
            attachments = cur.fetchall()
            
        return render_template('admin/list_order_attachments.html', attachments=attachments)
    except Exception as e:
        flash(f"Lỗi khi tải danh sách file đính kèm: {str(e)}")
        return render_template('admin/list_order_attachments.html', attachments=[])

@admin_bp.route('/order-attachments/upload', methods=['GET', 'POST'])
@admin_required
def upload_order_attachment():
    if request.method == 'POST':
        try:
            orderId = request.form.get('orderId')
            description = request.form.get('description', '').strip()
            file = request.files.get('file')
            
            if not orderId or not file or not file.filename:
                flash("Vui lòng điền đầy đủ thông tin và chọn file!")
                return render_template('admin/upload_order_attachment.html')
            
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                name_part, ext = os.path.splitext(filename)
                new_filename = f"order_{orderId}_{timestamp}{ext}"
                
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, new_filename)
                file.save(file_path)
                
                file_size = os.path.getsize(file_path)
                upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('''INSERT INTO order_attachments 
                                  (orderId, fileName, originalName, fileSize, uploadDate, description)
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                                (orderId, new_filename, filename, file_size, upload_date, description))
                    conn.commit()
                
                flash("Upload file thành công!")
                return redirect(url_for('admin.list_order_attachments'))
            else:
                flash("Định dạng file không được hỗ trợ!")
                
        except Exception as e:
            flash(f"Lỗi khi upload file: {str(e)}")

    # Lấy danh sách đơn hàng cho dropdown
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT o.orderId, u.firstName, u.lastName 
                          FROM orders o
                          JOIN users u ON o.userId = u.userId
                          ORDER BY o.orderId DESC''')
            orders = cur.fetchall()
    except:
        orders = []

    return render_template('admin/upload_order_attachment.html', orders=orders)

@admin_bp.route('/order-attachments/delete/<int:attachmentId>', methods=['POST'])
@admin_required
def delete_order_attachment(attachmentId):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT fileName FROM order_attachments WHERE attachmentId = ?", (attachmentId,))
            attachment = cur.fetchone()
            
            if not attachment:
                flash("File không tồn tại!")
                return redirect(url_for('admin.list_order_attachments'))
            
            # Xóa file
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            file_path = os.path.join(upload_folder, attachment[0])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            # Xóa record
            cur.execute("DELETE FROM order_attachments WHERE attachmentId = ?", (attachmentId,))
            conn.commit()
            
            flash("Xóa file thành công!")
            
    except Exception as e:
        flash(f"Lỗi khi xóa file: {str(e)}")
        
    return redirect(url_for('admin.list_order_attachments'))
