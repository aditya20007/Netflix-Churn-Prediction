"""
Netflix Churn Prediction - Model Training Script
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style('darkgrid')

def load_data(filepath='data/netflix_customers_sample.csv'):
    """Load customer data"""
    print(f"📊 Loading data from {filepath}")
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} customers")
    return df

def preprocess_data(df):
    """Preprocess and feature engineering"""
    print("\n🔧 Preprocessing data...")
    
    # Create copy
    data = df.copy()
    
    # Feature engineering
    data['tenure_months'] = data['tenure']
    data['avg_monthly_charge'] = data['total_charges'] / (data['tenure'] + 1)
    data['contract_value'] = data['monthly_charges'] * data['tenure']
    
    # Create interaction features
    data['services_count'] = (
        data['streaming_tv'] + 
        data['streaming_movies'] + 
        data['tech_support'] + 
        data['online_security']
    )
    
    # Encode categorical variables
    le_contract = LabelEncoder()
    le_payment = LabelEncoder()
    le_internet = LabelEncoder()
    
    data['contract_encoded'] = le_contract.fit_transform(data['contract_type'])
    data['payment_encoded'] = le_payment.fit_transform(data['payment_method'])
    data['internet_encoded'] = le_internet.fit_transform(data['internet_service'])
    
    # Select features
    feature_cols = [
        'tenure', 'monthly_charges', 'total_charges',
        'contract_encoded', 'payment_encoded', 'internet_encoded',
        'streaming_tv', 'streaming_movies', 'tech_support', 'online_security',
        'avg_monthly_charge', 'contract_value', 'services_count'
    ]
    
    X = data[feature_cols]
    y = data['churn']
    
    print(f"✅ Features prepared: {X.shape[1]} features")
    print(f"   Class distribution: {y.value_counts().to_dict()}")
    
    return X, y, feature_cols

def create_pipeline():
    """Create ML pipeline"""
    print("\n🏗️  Creating ML pipeline...")
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    return pipeline

def train_model(X, y):
    """Train the model"""
    print("\n🚀 Training model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    # Create and train pipeline
    pipeline = create_pipeline()
    
    # Train
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    print("\n📈 Evaluating model...")
    train_score = pipeline.score(X_train, y_train)
    test_score = pipeline.score(X_test, y_test)
    
    print(f"   Training accuracy: {train_score:.4f}")
    print(f"   Test accuracy: {test_score:.4f}")
    
    # Predictions
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    
    # Detailed metrics
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # ROC AUC
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\n🎯 ROC AUC Score: {roc_auc:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': pipeline.named_steps['classifier'].feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔍 Top 10 Most Important Features:")
    print(feature_importance.head(10))
    
    return pipeline, X_test, y_test, y_pred, y_pred_proba

def save_model(pipeline, filepath='models/netflix_churn_model.pkl'):
    """Save trained model"""
    print(f"\n💾 Saving model to {filepath}")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save model
    joblib.dump(pipeline, filepath)
    
    # Verify
    file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
    print(f"✅ Model saved successfully ({file_size:.2f} MB)")

def plot_results(y_test, y_pred, y_pred_proba):
    """Plot evaluation results"""
    print("\n📊 Generating plots...")
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 1. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0])
    axes[0].set_title('Confusion Matrix')
    axes[0].set_xlabel('Predicted')
    axes[0].set_ylabel('Actual')
    
    # 2. ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    axes[1].plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.2f})')
    axes[1].plot([0, 1], [0, 1], 'k--', label='Random')
    axes[1].set_xlabel('False Positive Rate')
    axes[1].set_ylabel('True Positive Rate')
    axes[1].set_title('ROC Curve')
    axes[1].legend()
    axes[1].grid(True)
    
    # 3. Prediction Distribution
    axes[2].hist(y_pred_proba, bins=30, edgecolor='black', alpha=0.7)
    axes[2].set_xlabel('Churn Probability')
    axes[2].set_ylabel('Frequency')
    axes[2].set_title('Prediction Distribution')
    axes[2].axvline(0.5, color='red', linestyle='--', label='Threshold')
    axes[2].legend()
    
    plt.tight_layout()
    
    # Save plot
    os.makedirs('models', exist_ok=True)
    plt.savefig('models/model_evaluation.png', dpi=300, bbox_inches='tight')
    print("✅ Plots saved to models/model_evaluation.png")

def main():
    """Main training pipeline"""
    print("="*60)
    print("🎬 NETFLIX CHURN PREDICTION - MODEL TRAINING")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Preprocess
    X, y, feature_cols = preprocess_data(df)
    
    # Train
    pipeline, X_test, y_test, y_pred, y_pred_proba = train_model(X, y)
    
    # Save
    save_model(pipeline)
    
    # Plot results
    plot_results(y_test, y_pred, y_pred_proba)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print("\n📝 Next steps:")
    print("   1. Review model_evaluation.png")
    print("   2. Run the Flask app: ./start_api.sh")
    print("   3. Test predictions at http://localhost:5000")

if __name__ == '__main__':
    main()