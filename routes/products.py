from flask import Blueprint, render_template, request
from utils.database import get_db_connection
from utils.auth_helpers import get_user_info
import math

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
def products():
    # Lấy số trang từ query parameter
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Số sản phẩm mỗi trang
    
    # Tính offset
    offset = (page - 1) * per_page
    
    with get_db_connection() as conn:
        # Đếm tổng số sản phẩm
        total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        
        # Lấy sản phẩm cho trang hiện tại
        products = conn.execute('''
            SELECT productId, name, price, description, image, stock, categoryId 
            FROM products 
            WHERE stock > 0
            ORDER BY productId DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset)).fetchall()
    
    # Tính số trang
    total_pages = math.ceil(total_products / per_page)
    
    # Lấy thông tin user
    loggedIn, firstName, noOfItems, userId = get_user_info()
    
    return render_template('products.html', 
                         products=products,
                         current_page=page,
                         total_pages=total_pages,
                         total_products=total_products,
                         loggedIn=loggedIn,
                         firstName=firstName,
                         noOfItems=noOfItems)
