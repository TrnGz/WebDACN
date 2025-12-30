#!/usr/bin/env python3
"""
Database initialization script
Run this to set up the database with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import init_db, fix_database

def main():
    print("Flask E-commerce Database Setup")
    print("=" * 40)
    print("Choose an option:")
    print("1. Initialize new database")
    print("2. Fix existing database")
    print("3. Recreate database from scratch")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        print("Initializing database...")
        init_db()
        print("Database initialization completed!")
        
    elif choice == '2':
        print("Fixing existing database...")
        fix_database()
        print("Database fix completed!")
        
    elif choice == '3':
        print("Recreating database from scratch...")
        # Delete existing database file
        if os.path.exists('database.db'):
            os.remove('database.db')
            print("Deleted existing database")
        init_db()
        print("Database recreation completed!")
        
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == '__main__':
    main()
