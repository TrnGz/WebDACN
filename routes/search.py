from flask import Blueprint, render_template, request, flash
from utils.database import get_db_connection
from utils.helpers import getLoginDetails
import sqlite3

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
    search_query = request.args.get('searchQuery', '').strip()
    loggedIn, firstName, noOfItems = getLoginDetails()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Fetch categories ordered by name for sidebar/filter navigation
            cursor.execute("SELECT categoryId, name FROM categories ORDER BY name")
            category_data = cursor.fetchall()

            if search_query:
                category_filter = request.args.get('category', '').strip()
                
                if category_filter:
                    # Search within specific category
                    cursor.execute("""
                        SELECT productId, name, price, description, image, stock
                        FROM products
                        WHERE (name LIKE ? OR description LIKE ?) 
                        AND stock > 0 
                        AND categoryId = ?
                        ORDER BY name ASC
                    """, (f'%{search_query}%', f'%{search_query}%', category_filter))
                else:
                    # Search all products
                    cursor.execute("""
                        SELECT productId, name, price, description, image, stock
                        FROM products
                        WHERE (name LIKE ? OR description LIKE ?) AND stock > 0
                        ORDER BY name ASC
                    """, (f'%{search_query}%', f'%{search_query}%'))

                products = cursor.fetchall()

                if not products:
                    flash(f'Không tìm thấy sản phẩm nào phù hợp với "{search_query}".', 'info')
            else:
                products = []
                flash("Vui lòng nhập từ khóa tìm kiếm!", "warning")

    except sqlite3.Error as e:
        print(f"Database error during search: {e}")
        flash("Lỗi cơ sở dữ liệu khi tìm kiếm. Vui lòng thử lại.", "error")
        products = []
        category_data = []

    # Render search results page with data and UI variables for elegant, minimal presentation
    return render_template(
        'search_results.html',
        itemData=products,
        loggedIn=loggedIn,
        firstName=firstName,
        noOfItems=noOfItems,
        categoryData=category_data,
        searchQuery=search_query,
        totalResults=len(products)
    )

@search_bp.route('/search_by_category')
def search_by_category():
    category_id = request.args.get('categoryId', '').strip()
    loggedIn, firstName, noOfItems = getLoginDetails()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch categories for navigation
            cursor.execute("SELECT categoryId, name FROM categories ORDER BY name")
            category_data = cursor.fetchall()
            
            if category_id:
                # Get products in specific category
                cursor.execute("""
                    SELECT p.productId, p.name, p.price, p.description, p.image, p.stock, c.name as categoryName
                    FROM products p
                    JOIN categories c ON p.categoryId = c.categoryId
                    WHERE p.categoryId = ? AND p.stock > 0
                    ORDER BY p.name ASC
                """, (category_id,))
                
                products = cursor.fetchall()
                category_name = products[0][6] if products else "Danh mục không xác định"
                
                # Convert to format expected by template
                products = [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in products]
                
                return render_template(
                    'displayCategory.html',
                    data=products,
                    loggedIn=loggedIn,
                    firstName=firstName,
                    noOfItems=noOfItems,
                    categoryName=category_name,
                    categoryData=category_data
                )
            else:
                flash("Danh mục không tồn tại!", "error")
                return render_template(
                    'search_results.html',
                    itemData=[],
                    loggedIn=loggedIn,
                    firstName=firstName,
                    noOfItems=noOfItems,
                    categoryData=category_data,
                    searchQuery="",
                    totalResults=0
                )
                
    except sqlite3.Error as e:
        print(f"Database error during category search: {e}")
        flash("Lỗi cơ sở dữ liệu khi tìm kiếm danh mục.", "error")
        return render_template(
            'search_results.html',
            itemData=[],
            loggedIn=loggedIn,
            firstName=firstName,
            noOfItems=noOfItems,
            categoryData=[],
            searchQuery="",
            totalResults=0
        )
