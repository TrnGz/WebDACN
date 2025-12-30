from flask import session
from utils.database import get_db_connection

def get_user_info():
    """
    Lấy thông tin user từ session và database
    Returns: (loggedIn, firstName, noOfItems, userId)
    """
    loggedIn = 'email' in session
    firstName = ''
    noOfItems = 0
    userId = None
    
    if loggedIn:
        try:
            with get_db_connection() as conn:
                # Lấy thông tin user từ email
                user_data = conn.execute(
                    'SELECT userId, firstName FROM users WHERE email = ?', 
                    (session['email'],)
                ).fetchone()
                
                if user_data:
                    userId = user_data[0]
                    firstName = user_data[1]
                    
                    # Cập nhật userId vào session nếu chưa có
                    if 'userId' not in session:
                        session['userId'] = userId
                    
                    # Đếm số lượng trong giỏ hàng
                    noOfItems = conn.execute(
                        'SELECT COUNT(*) FROM kart WHERE userId = ?', 
                        (userId,)
                    ).fetchone()[0]
                else:
                    # User không tồn tại, clear session
                    session.clear()
                    loggedIn = False
                    
        except Exception as e:
            print(f"Error getting user info: {e}")
            # Nếu có lỗi, reset session
            session.clear()
            loggedIn = False
    
    return loggedIn, firstName, noOfItems, userId
