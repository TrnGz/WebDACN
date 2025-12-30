import sqlite3
import hashlib
from contextlib import contextmanager
from config import Config

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with correct schema"""
    with get_db_connection() as conn:
        print("Opened database successfully")

        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            firstName TEXT NOT NULL,
            lastName TEXT NOT NULL,
            address1 TEXT,
            address2 TEXT,
            zipcode TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            phone TEXT,
            role TEXT DEFAULT 'user'
        )
        ''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            categoryId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        ''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            productId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER NOT NULL,
            categoryId INTEGER,
            FOREIGN KEY (categoryId) REFERENCES categories(categoryId)
        )
        ''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS kart (
            cartId INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            productId INTEGER,
            FOREIGN KEY (userId) REFERENCES users(userId),
            FOREIGN KEY (productId) REFERENCES products(productId)
        )
        ''')

        conn.execute('''
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

        conn.execute('''
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

        conn.execute('''
        CREATE TABLE IF NOT EXISTS order_attachments (
            attachmentId INTEGER PRIMARY KEY AUTOINCREMENT,
            orderId INTEGER,
            fileName TEXT NOT NULL,
            originalName TEXT NOT NULL,
            fileSize INTEGER,
            uploadDate TEXT,
            description TEXT,
            FOREIGN KEY (orderId) REFERENCES orders(orderId)
        )
        ''')


        hashed_admin_pw = hashlib.md5('admin123'.encode()).hexdigest()
        hashed_user_pw = hashlib.md5('user123'.encode()).hexdigest()

        conn.execute('INSERT OR IGNORE INTO users (password, email, firstName, lastName, role, city, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (hashed_admin_pw, 'admin@example.com', 'Admin', 'User', 'admin', 'Bắc Ninh', 'Việt Nam', '0123456789'))
        conn.execute('INSERT OR IGNORE INTO users (password, email, firstName, lastName, role, city, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (hashed_user_pw, 'user@example.com', 'Nguyễn', 'Văn A', 'user', 'Hải Dương', 'Việt Nam', '0987654321'))


        conn.execute('INSERT OR IGNORE INTO categories (categoryId, name) VALUES (1, "Điện tử")')
        conn.execute('INSERT OR IGNORE INTO categories (categoryId, name) VALUES (2, "Thời trang")')
        conn.execute('INSERT OR IGNORE INTO categories (categoryId, name) VALUES (3, "Sách")')

        conn.commit()
        print("Database initialized successfully")

def fix_database():
    """Fix database schema issues"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        try:
            # Check current table structure
            cur.execute("PRAGMA table_info(kart)")
            columns = cur.fetchall()
            print("Current kart table structure:")
            for col in columns:
                print(f"  {col}")
            
            # Check if cartId exists
            column_names = [col[1] for col in columns]
            if 'cartId' not in column_names:
                print("cartId column is missing! Fixing...")
                

                cur.execute("SELECT userId, productId FROM kart")
                existing_data = cur.fetchall()
                print(f"Found {len(existing_data)} existing cart items")
                

                cur.execute('DROP TABLE IF EXISTS kart')
                

                cur.execute('''
                    CREATE TABLE kart (
                        cartId INTEGER PRIMARY KEY AUTOINCREMENT,
                        userId INTEGER,
                        productId INTEGER,
                        FOREIGN KEY (userId) REFERENCES users(userId),
                        FOREIGN KEY (productId) REFERENCES products(productId)
                    )
                ''')
                

                for user_id, product_id in existing_data:
                    cur.execute('INSERT INTO kart (userId, productId) VALUES (?, ?)', (user_id, product_id))
                
                print("Fixed kart table structure and restored data")
            else:
                print("cartId column exists - no fix needed")
                
            conn.commit()
            print("Database fix completed successfully")
            
        except Exception as e:
            print(f"Error fixing database: {e}")
            conn.rollback()
