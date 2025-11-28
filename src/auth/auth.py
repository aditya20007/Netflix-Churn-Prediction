"""
Netflix Churn Prediction - Authentication Module
"""
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import os

DATABASE = os.getenv('DATABASE_URL', 'netflix_churn.db').replace('sqlite:///', '')

class User(UserMixin):
    """User model for authentication"""
    
    def __init__(self, id, username, email, password_hash=None, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get(user_id):
        """Get user by ID"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                is_admin=bool(row['is_admin'])
            )
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'

def init_db():
    """Initialize users database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Users table initialized")

def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            is_admin=bool(row['is_admin'])
        )
    return None

def create_user(username, password, email, is_admin=False):
    """Create new user"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, int(is_admin)))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin
        )
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_all_users():
    """Get all users (admin only)"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [User(
        id=row['id'],
        username=row['username'],
        email=row['email'],
        password_hash=row['password_hash'],
        is_admin=bool(row['is_admin'])
    ) for row in rows]