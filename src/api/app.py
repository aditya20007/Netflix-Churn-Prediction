"""
Netflix Churn Prediction - Main Flask Application
COMPLETE FIXED VERSION with proper feature engineering and error handling
Admin: admin / aditya123
"""
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import json
from sklearn.preprocessing import LabelEncoder

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth import User, init_db, get_user_by_username, create_user
from utils.db import get_db_connection, init_database

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../../templates',
            static_folder='../../static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///netflix_churn.db')

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load ML model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/netflix_churn_model.pkl')
try:
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded successfully from {MODEL_PATH}")
    
    # Check model type
    if hasattr(model, 'named_steps'):
        print(f"   📊 Pipeline detected with steps: {list(model.named_steps.keys())}")
    else:
        print(f"   📊 Direct model type: {type(model).__name__}")
        
except Exception as e:
    print(f"⚠️  Warning: Could not load model - {e}")
    print(f"   💡 Run: python src/models/train.py")
    model = None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ============================================================================
# ROUTES - Authentication
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with validation"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        errors = []
        
        # Check if fields are empty
        if not username:
            errors.append('Username is required')
        if not password:
            errors.append('Password is required')
        if not email:
            errors.append('Email is required')
            
        # Validate username length
        if username and (len(username) < 3 or len(username) > 50):
            errors.append('Username must be between 3 and 50 characters')
            
        # Validate password strength
        if password and len(password) < 8:
            errors.append('Password must be at least 8 characters')
            
        # Validate email format
        if email and '@' not in email:
            errors.append('Invalid email format')
            
        # Check if username already exists
        if username and get_user_by_username(username):
            errors.append('Username already exists')
            
        # Check if email already exists
        if email:
            conn = get_db_connection()
            existing_email = conn.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            ).fetchone()
            conn.close()
            if existing_email:
                errors.append('Email already registered')
        
        # If there are errors, show them
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create user
        user = create_user(username, password, email)
        if user:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

# ============================================================================
# ROUTES - Dashboard & Analytics
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with analytics"""
    conn = get_db_connection()
    
    # Get summary statistics
    stats = {
        'total_predictions': conn.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],
        'high_risk_customers': conn.execute(
            'SELECT COUNT(*) FROM predictions WHERE churn_probability > 0.7'
        ).fetchone()[0],
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
    }
    
    # Get recent predictions
    recent = conn.execute('''
        SELECT * FROM predictions 
        ORDER BY created_at DESC 
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', stats=stats, recent=recent)

@app.route('/predict')
@login_required
def predict_page():
    """Prediction form page"""
    return render_template('predict.html')

@app.route('/admin')
@app.route('/admin')
@app.route('/admin/') 
@login_required
def admin():
    """Admin panel - requires admin privileges"""
    if not current_user.is_admin:
        flash('Access denied - Admin only', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    # Get all users
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    
    # Get system metrics
    metrics = {
        'total_users': len(users),
        'total_predictions': conn.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],
        'avg_churn_probability': conn.execute(
            'SELECT AVG(churn_probability) FROM predictions'
        ).fetchone()[0] or 0,
    }
    
    conn.close()
    
    return render_template('admin.html', users=users, metrics=metrics)

# ============================================================================
# API ENDPOINTS - Predictions (FIXED VERSION)
# ============================================================================

@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    """Single customer churn prediction - FIXED with proper feature engineering"""
    if not model:
        return jsonify({
            'success': False,
            'error': 'Model not loaded. Please run: python src/models/train.py'
        }), 500
    
    try:
        data = request.json
        print(f"\n{'='*60}")
        print(f"📥 PREDICTION REQUEST from user: {current_user.username}")
        print(f"📝 Received data: {json.dumps(data, indent=2)}")
        
        # Extract and validate data
        try:
            tenure = float(data.get('tenure', 0))
            monthly_charges = float(data.get('monthly_charges', 0))
            total_charges = float(data.get('total_charges', 0))
            contract_type = data.get('contract_type', 'Month-to-Month')
            payment_method = data.get('payment_method', 'Electronic check')
            internet_service = data.get('internet_service', 'Fiber optic')
            streaming_tv = int(data.get('streaming_tv', 0))
            streaming_movies = int(data.get('streaming_movies', 0))
            tech_support = int(data.get('tech_support', 0))
            online_security = int(data.get('online_security', 0))
            
            print(f"✅ Data validation passed")
            
        except (ValueError, TypeError) as e:
            print(f"❌ Data validation failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Invalid input data: {str(e)}'
            }), 400
        
        # FEATURE ENGINEERING (Critical - must match training!)
        print(f"\n🔧 Feature Engineering:")
        
        # Calculate derived features
        avg_monthly_charge = total_charges / (tenure + 1)
        contract_value = monthly_charges * tenure
        services_count = streaming_tv + streaming_movies + tech_support + online_security
        
        print(f"   avg_monthly_charge: {avg_monthly_charge:.2f}")
        print(f"   contract_value: {contract_value:.2f}")
        print(f"   services_count: {services_count}")
        
        # Encode categorical variables
        # Contract type encoding
        contract_encoder = LabelEncoder()
        contract_encoder.fit(['Month-to-Month', 'One year', 'Two year'])
        try:
            contract_encoded = contract_encoder.transform([contract_type])[0]
            print(f"   contract_encoded: {contract_type} → {contract_encoded}")
        except ValueError:
            contract_encoded = 0  # Default to Month-to-Month
            print(f"   ⚠️  Unknown contract type, defaulting to Month-to-Month")
        
        # Payment method encoding
        payment_encoder = LabelEncoder()
        payment_encoder.fit(['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'])
        try:
            payment_encoded = payment_encoder.transform([payment_method])[0]
            print(f"   payment_encoded: {payment_method} → {payment_encoded}")
        except ValueError:
            payment_encoded = 0  # Default
            print(f"   ⚠️  Unknown payment method, using default")
        
        # Internet service encoding
        internet_encoder = LabelEncoder()
        internet_encoder.fit(['DSL', 'Fiber optic', 'No'])
        try:
            internet_encoded = internet_encoder.transform([internet_service])[0]
            print(f"   internet_encoded: {internet_service} → {internet_encoded}")
        except ValueError:
            internet_encoded = 1  # Default to Fiber optic
            print(f"   ⚠️  Unknown internet service, using default")
        
        # Create features DataFrame with EXACT order as training
        features = pd.DataFrame([{
            'tenure': tenure,
            'monthly_charges': monthly_charges,
            'total_charges': total_charges,
            'contract_encoded': contract_encoded,
            'payment_encoded': payment_encoded,
            'internet_encoded': internet_encoded,
            'streaming_tv': streaming_tv,
            'streaming_movies': streaming_movies,
            'tech_support': tech_support,
            'online_security': online_security,
            'avg_monthly_charge': avg_monthly_charge,
            'contract_value': contract_value,
            'services_count': services_count
        }])
        
        print(f"\n📊 Features prepared:")
        print(f"   Shape: {features.shape}")
        print(f"   Columns: {features.columns.tolist()}")
        print(f"\n   Values:\n{features.to_string()}")
        
        # Make prediction
        try:
            print(f"\n🔮 Making prediction...")
            churn_prob = model.predict_proba(features)[0][1]
            churn_prediction = int(churn_prob > 0.5)
            
            print(f"   ✅ Prediction successful!")
            print(f"   📈 Churn probability: {churn_prob:.4f} ({churn_prob*100:.2f}%)")
            print(f"   🎯 Churn prediction: {churn_prediction}")
            
        except Exception as pred_error:
            print(f"   ❌ Prediction failed: {str(pred_error)}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            
            return jsonify({
                'success': False,
                'error': f'Model prediction failed: {str(pred_error)}'
            }), 500
        
        # Save to database
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO predictions (user_id, features, churn_probability, churn_prediction)
                VALUES (?, ?, ?, ?)
            ''', (current_user.id, json.dumps(data), float(churn_prob), churn_prediction))
            conn.commit()
            conn.close()
            print(f"   💾 Saved to database")
        except Exception as db_error:
            print(f"   ⚠️  Database save warning: {str(db_error)}")
            # Continue even if DB save fails
        
        # Determine risk level
        if churn_prob < 0.3:
            risk_level = 'Low'
            color = 'green'
            emoji = '🟢'
        elif churn_prob < 0.7:
            risk_level = 'Medium'
            color = 'orange'
            emoji = '🟡'
        else:
            risk_level = 'High'
            color = 'red'
            emoji = '🔴'
        
        print(f"   {emoji} Risk Level: {risk_level}")
        
        # Generate recommendations
        recommendations = get_recommendations(churn_prob, data)
        
        response = {
            'success': True,
            'churn_probability': round(churn_prob, 4),
            'churn_prediction': churn_prediction,
            'risk_level': risk_level,
            'color': color,
            'recommendations': recommendations
        }
        
        print(f"\n📤 Response sent successfully")
        print(f"{'='*60}\n")
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ CRITICAL ERROR in api_predict:")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'details': 'Check server console for detailed error trace'
        }), 400


@app.route('/api/batch_predict', methods=['POST'])
@login_required
def api_batch_predict():
    """Batch prediction from CSV file - FIXED with proper feature engineering"""
    if not model:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"\n{'='*60}")
        print(f"📁 BATCH PREDICTION REQUEST")
        print(f"   File: {file.filename}")
        print(f"   User: {current_user.username}")
        
        # Read CSV
        df = pd.read_csv(file)
        print(f"   📊 Loaded {len(df)} rows")
        print(f"   📋 Columns: {df.columns.tolist()}")
        
        # Feature engineering (same as single prediction)
        print(f"\n🔧 Feature Engineering...")
        df['avg_monthly_charge'] = df['total_charges'] / (df['tenure'] + 1)
        df['contract_value'] = df['monthly_charges'] * df['tenure']
        df['services_count'] = (
            df['streaming_tv'] + df['streaming_movies'] + 
            df['tech_support'] + df['online_security']
        )
        
        # Encode categorical variables
        le_contract = LabelEncoder()
        le_payment = LabelEncoder()
        le_internet = LabelEncoder()
        
        df['contract_encoded'] = le_contract.fit_transform(df['contract_type'])
        df['payment_encoded'] = le_payment.fit_transform(df['payment_method'])
        df['internet_encoded'] = le_internet.fit_transform(df['internet_service'])
        
        print(f"   ✅ Feature engineering complete")
        
        # Select features for prediction (MUST match training order)
        feature_cols = [
            'tenure', 'monthly_charges', 'total_charges',
            'contract_encoded', 'payment_encoded', 'internet_encoded',
            'streaming_tv', 'streaming_movies', 'tech_support', 'online_security',
            'avg_monthly_charge', 'contract_value', 'services_count'
        ]
        
        X = df[feature_cols]
        print(f"   📊 Features shape: {X.shape}")
        
        # Make predictions
        print(f"\n🔮 Making predictions...")
        predictions = model.predict_proba(X)[:, 1]
        df['churn_probability'] = predictions
        df['churn_prediction'] = (predictions > 0.5).astype(int)
        df['risk_level'] = pd.cut(predictions, 
                                    bins=[0, 0.3, 0.7, 1.0],
                                    labels=['Low', 'Medium', 'High'])
        
        # Summary statistics
        summary = {
            'total_customers': len(df),
            'high_risk': int((predictions > 0.7).sum()),
            'medium_risk': int(((predictions >= 0.3) & (predictions <= 0.7)).sum()),
            'low_risk': int((predictions < 0.3).sum()),
            'avg_churn_probability': float(predictions.mean())
        }
        
        print(f"\n✅ Batch prediction complete!")
        print(f"   📊 Summary: {summary}")
        print(f"{'='*60}\n")
        
        # Convert to JSON (exclude encoded columns for cleaner output)
        output_cols = [col for col in df.columns if not col.endswith('_encoded')]
        results = df[output_cols].to_dict('records')
        
        return jsonify({
            'success': True,
            'summary': summary,
            'results': results[:100]  # Limit to first 100 for response
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ BATCH PREDICTION ERROR:")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'details': 'Check server console for detailed error trace'
        }), 400


@app.route('/api/segments', methods=['GET'])
@login_required
def api_segments():
    """Get customer segmentation data"""
    conn = get_db_connection()
    
    # Get predictions grouped by risk level
    segments = conn.execute('''
        SELECT 
            CASE 
                WHEN churn_probability < 0.3 THEN 'Low Risk'
                WHEN churn_probability < 0.7 THEN 'Medium Risk'
                ELSE 'High Risk'
            END as segment,
            COUNT(*) as count,
            AVG(churn_probability) as avg_probability
        FROM predictions
        GROUP BY segment
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'segments': [dict(s) for s in segments]
    })

@app.route('/api/metrics', methods=['GET'])
@login_required
def api_metrics():
    """Get system metrics for charts"""
    conn = get_db_connection()
    
    # Daily predictions count
    daily_predictions = conn.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM predictions
        WHERE created_at >= DATE('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''').fetchall()
    
    # Churn probability distribution
    distribution = conn.execute('''
        SELECT 
            ROUND(churn_probability, 1) as prob,
            COUNT(*) as count
        FROM predictions
        GROUP BY ROUND(churn_probability, 1)
        ORDER BY prob
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'daily_predictions': [dict(d) for d in daily_predictions],
        'distribution': [dict(d) for d in distribution]
    })

# ============================================================================
# Helper Functions
# ============================================================================

def get_recommendations(churn_prob, customer_data):
    """Generate personalized recommendations based on churn probability"""
    recommendations = []
    
    if churn_prob > 0.7:
        recommendations.append("🚨 High churn risk - Immediate intervention required")
        recommendations.append("💰 Offer loyalty discount or premium features")
        recommendations.append("📞 Schedule personal call from retention team")
    elif churn_prob > 0.4:
        recommendations.append("⚠️  Monitor closely for changes in usage patterns")
        recommendations.append("📧 Send targeted re-engagement email campaign")
        recommendations.append("🎁 Offer upgrade incentives or bundled services")
    else:
        recommendations.append("✅ Customer appears satisfied")
        recommendations.append("📊 Continue monitoring engagement metrics")
        recommendations.append("⭐ Consider for referral program")
    
    # Add specific recommendations based on features
    if customer_data.get('contract_type') == 'Month-to-Month':
        recommendations.append("📝 Encourage upgrade to annual contract")
    
    if customer_data.get('tech_support') == 0:
        recommendations.append("🛠️  Promote tech support subscription")
    
    return recommendations

# ============================================================================
# Initialize & Run
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 NETFLIX CHURN PREDICTION - INITIALIZATION")
    print("="*60)
    
    # Initialize database
    print("\n💾 Initializing database...")
    init_database()
    init_db()
    print("   ✅ Database initialized")
    
    # Create default admin user with credentials: admin / aditya123
    print("\n🔐 Setting up users...")
    if not get_user_by_username('admin'):
        create_user('admin', 'aditya123', 'admin@netflix-churn.com', is_admin=True)
        print("   ✅ Admin user created")
    else:
        print("   ℹ️  Admin user already exists")
    
    # Create default regular user
    if not get_user_by_username('user'):
        create_user('user', 'password123', 'user@netflix-churn.com')
        print("   ✅ Regular user created")
    else:
        print("   ℹ️  Regular user already exists")
    
   
    
    # Run app
    port = int(os.getenv('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)