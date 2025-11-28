"""
Netflix Churn Prediction - Database Utilities
"""
import sqlite3
import os

DATABASE = os.getenv('DATABASE_URL', 'netflix_churn.db').replace('sqlite:///', '')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
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
    
    # Predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_id TEXT,
            features TEXT,
            churn_probability REAL,
            churn_prediction INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Batch jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            total_records INTEGER,
            processed_records INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Customer segments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_name TEXT,
            description TEXT,
            risk_level TEXT,
            customer_count INTEGER,
            avg_churn_probability REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # System metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT,
            metric_value REAL,
            metric_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Database tables initialized")

def clear_database():
    """Clear all data from database (use with caution!)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = ['predictions', 'batch_jobs', 'customer_segments', 'system_metrics']
    
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')
    
    conn.commit()
    conn.close()
    
    print("⚠️  Database cleared")

def get_statistics():
    """Get database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        'total_users': cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_predictions': cursor.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],
        'total_batch_jobs': cursor.execute('SELECT COUNT(*) FROM batch_jobs').fetchone()[0],
        'avg_churn_prob': cursor.execute('SELECT AVG(churn_probability) FROM predictions').fetchone()[0] or 0
    }
    
    conn.close()
    
    return stats

def backup_database(backup_path='backups/'):
    """Create database backup"""
    import shutil
    from datetime import datetime
    
    os.makedirs(backup_path, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_path, f'netflix_churn_{timestamp}.db')
    
    shutil.copy2(DATABASE, backup_file)
    
    print(f"✅ Database backed up to {backup_file}")
    return backup_file

def restore_database(backup_file):
    """Restore database from backup"""
    import shutil
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    shutil.copy2(backup_file, DATABASE)
    
    print(f"✅ Database restored from {backup_file}")
    return True

if __name__ == '__main__':
    # Test database initialization
    init_database()
    stats = get_statistics()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")