from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.helpers import getLoginDetails, parse
from utils.database import get_db_connection
from utils.auth_helpers import get_user_info
import sqlite3

main_bp = Blueprint('main', __name__)

import random

@main_bp.route('/')
def root():
  
    loggedIn, firstName, noOfItems, userId = get_user_info()
    
    try:
        with get_db_connection() as conn:
            categoryData = conn.execute('SELECT categoryId, name FROM categories').fetchall()

            itemData = []
            selected_product_ids = set()

            def get_top_products(limit):
                products = conn.execute('''
                    SELECT p.productId, p.name, p.price, p.description, p.image, COUNT(oi.productId) AS order_count
                    FROM products p
                    LEFT JOIN order_items oi ON p.productId = oi.productId
                    WHERE p.stock > 0 AND p.productId NOT IN ({})
                    GROUP BY p.productId
                    ORDER BY order_count DESC
                    LIMIT ?
                '''.format(','.join(['?'] * len(selected_product_ids))), (*selected_product_ids, limit)).fetchall()

                new_product_ids = {product[0] for product in products}
                selected_product_ids.update(new_product_ids)
                return products

            def get_random_products(limit):
                products = conn.execute('''
                    SELECT productId, name, price, description, image 
                    FROM products 
                    WHERE stock > 0 AND productId NOT IN ({})
                    ORDER BY RANDOM()
                    LIMIT ?
                '''.format(','.join(['?'] * len(selected_product_ids))), (*selected_product_ids, limit)).fetchall()

                new_product_ids = {product[0] for product in products}
                selected_product_ids.update(new_product_ids)
                return products

            products_row1 = get_top_products(10)
            if products_row1:
                itemData.append(products_row1)

            for i in range(2): 
                products_row = get_random_products(6)
                if products_row:
                    itemData.append(products_row)

            return render_template('index.html',
                                 loggedIn=loggedIn,
                                 firstName=firstName,
                                 noOfItems=noOfItems,
                                 categoryData=categoryData,
                                 itemData=itemData)
    except sqlite3.Error as e:
        print(f"Database error in root: {e}")
        flash("Lỗi khi tải trang chủ!")
        return render_template('index.html',
                                 loggedIn=loggedIn,
                                 firstName=firstName,
                                 noOfItems=noOfItems,
                                 categoryData=[],
                                 itemData=[])
    except Exception as e:
        print(f"General error in root: {e}")
        flash("Lỗi khi tải trang chủ!")
        return render_template('index.html',
                                 loggedIn=loggedIn,
                                 firstName=firstName,
                                 noOfItems=noOfItems,
                                 categoryData=[],
                                 itemData=[])



# @main_bp.route("/search")
# def search():
#     loggedIn, firstName, noOfItems = getLoginDetails()
#     searchQuery = request.args.get('searchQuery', '').strip()
    
#     if not searchQuery:
#         flash("Vui lòng nhập từ khóa tìm kiếm!")
#         return redirect(url_for('main.root'))
    
#     try:
#         with get_db_connection() as conn:
#             cur = conn.cursor()
#             cur.execute("""
#                 SELECT productId, name, price, description, image, stock 
#                 FROM products 
#                 WHERE name LIKE ? OR description LIKE ?
#                 ORDER BY name
#             """, (f'%{searchQuery}%', f'%{searchQuery}%'))
#             itemData = cur.fetchall()
            
#             cur.execute('SELECT categoryId, name FROM categories')
#             categoryData = cur.fetchall()
            
#     except sqlite3.Error as e:
#         print(f"Database error in search: {e}")
#         flash("Lỗi khi tìm kiếm sản phẩm!")
#         return redirect(url_for('main.root'))
    
#     itemData = parse(itemData)
    
#     try:
#         return render_template('search_results.html', 
#                              itemData=itemData, 
#                              loggedIn=loggedIn, 
#                              firstName=firstName, 
#                              noOfItems=noOfItems, 
#                              categoryData=categoryData,
#                              searchQuery=searchQuery)
#     except:
#         return render_template('index.html', 
#                              itemData=itemData, 
#                              loggedIn=loggedIn, 
#                              firstName=firstName, 
#                              noOfItems=noOfItems, 
#                              categoryData=categoryData,
#                              searchQuery=searchQuery)

@main_bp.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    
    if not categoryId:
        flash("Danh mục không tồn tại!")
        return redirect(url_for('main.root'))
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT products.productId, products.name, products.price, products.description, 
                       products.image, products.stock, categories.name 
                FROM products 
                JOIN categories ON products.categoryId = categories.categoryId 
                WHERE categories.categoryId = ?
            """, (categoryId,))
            data = cur.fetchall()
            
            cur.execute('SELECT categoryId, name FROM categories')
            categoryData = cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error in displayCategory: {e}")
        data = []
        categoryData = []
    
    categoryName = data[0][6] if data else "Danh mục không xác định"
    data = parse(data)
    return render_template('displayCategory.html', 
                         data=data, 
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems, 
                         categoryName=categoryName,
                         categoryData=categoryData)

@main_bp.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    
    if not productId:
        flash("Sản phẩm không tồn tại!")
        return redirect(url_for('main.root'))
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?', 
                       (productId,))
            productData = cur.fetchone()
            
            if not productData:
                flash("Sản phẩm không tồn tại!")
                return redirect(url_for('main.root'))
                
    except sqlite3.Error as e:
        print(f"Database error in productDescription: {e}")
        flash("Lỗi khi tải thông tin sản phẩm!")
        return redirect(url_for('main.root'))
    
    return render_template("productDescription.html", 
                         data=productData, 
                         loggedIn=loggedIn, 
                         firstName=firstName, 
                         noOfItems=noOfItems)
