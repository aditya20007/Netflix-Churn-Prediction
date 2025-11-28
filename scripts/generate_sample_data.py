"""
Generate Sample Netflix Customer Data for Churn Prediction
"""
import pandas as pd
import numpy as np
import os

np.random.seed(42)

def generate_customer_data(n_samples=5000):
    """Generate realistic Netflix customer data"""
    
    print(f"🎬 Generating {n_samples} sample customers...")
    
    # Customer IDs
    customer_ids = [f'CUST_{i:06d}' for i in range(1, n_samples + 1)]
    
    # Tenure (months with service)
    tenure = np.random.exponential(scale=20, size=n_samples).astype(int)
    tenure = np.clip(tenure, 1, 72)  # 1 to 72 months
    
    # Contract types
    contract_types = np.random.choice(
        ['Month-to-Month', 'One year', 'Two year'],
        size=n_samples,
        p=[0.55, 0.25, 0.20]
    )
    
    # Monthly charges based on contract type
    base_charges = {
        'Month-to-Month': (15, 30),
        'One year': (12, 25),
        'Two year': (10, 20)
    }
    
    monthly_charges = []
    for contract in contract_types:
        min_charge, max_charge = base_charges[contract]
        charge = np.random.uniform(min_charge, max_charge)
        monthly_charges.append(round(charge, 2))
    
    monthly_charges = np.array(monthly_charges)
    
    # Total charges
    total_charges = monthly_charges * tenure
    total_charges = total_charges + np.random.normal(0, 50, n_samples)
    total_charges = np.maximum(total_charges, monthly_charges)
    
    # Payment methods
    payment_methods = np.random.choice(
        ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'],
        size=n_samples,
        p=[0.35, 0.15, 0.25, 0.25]
    )
    
    # Internet service
    internet_services = np.random.choice(
        ['DSL', 'Fiber optic', 'No'],
        size=n_samples,
        p=[0.35, 0.45, 0.20]
    )
    
    # Additional services (influenced by internet service)
    streaming_tv = []
    streaming_movies = []
    tech_support = []
    online_security = []
    
    for internet in internet_services:
        if internet == 'No':
            streaming_tv.append(0)
            streaming_movies.append(0)
            tech_support.append(0)
            online_security.append(0)
        else:
            streaming_tv.append(np.random.choice([0, 1], p=[0.4, 0.6]))
            streaming_movies.append(np.random.choice([0, 1], p=[0.4, 0.6]))
            tech_support.append(np.random.choice([0, 1], p=[0.5, 0.5]))
            online_security.append(np.random.choice([0, 1], p=[0.5, 0.5]))
    
    # Churn (target variable)
    # Higher churn probability for:
    # - Month-to-month contracts
    # - Higher monthly charges
    # - Lower tenure
    # - Electronic check payment
    # - Fewer services
    
    churn_prob = np.zeros(n_samples)
    
    for i in range(n_samples):
        prob = 0.3  # Base probability
        
        # Contract type influence
        if contract_types[i] == 'Month-to-Month':
            prob += 0.25
        elif contract_types[i] == 'Two year':
            prob -= 0.15
        
        # Tenure influence (inverse relationship)
        if tenure[i] < 6:
            prob += 0.20
        elif tenure[i] > 24:
            prob -= 0.15
        
        # Monthly charges influence
        if monthly_charges[i] > 25:
            prob += 0.15
        
        # Payment method influence
        if payment_methods[i] == 'Electronic check':
            prob += 0.10
        
        # Services influence (more services = less churn)
        services_count = (streaming_tv[i] + streaming_movies[i] + 
                         tech_support[i] + online_security[i])
        prob -= services_count * 0.05
        
        churn_prob[i] = np.clip(prob, 0.1, 0.9)
    
    # Generate actual churn based on probability
    churn = (np.random.random(n_samples) < churn_prob).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'customer_id': customer_ids,
        'tenure': tenure,
        'monthly_charges': monthly_charges,
        'total_charges': np.round(total_charges, 2),
        'contract_type': contract_types,
        'payment_method': payment_methods,
        'internet_service': internet_services,
        'streaming_tv': streaming_tv,
        'streaming_movies': streaming_movies,
        'tech_support': tech_support,
        'online_security': online_security,
        'churn': churn
    })
    
    return df

def save_data(df, filepath='data/netflix_customers_sample.csv'):
    """Save data to CSV"""
    
    # Create directory if needed
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save
    df.to_csv(filepath, index=False)
    
    file_size = os.path.getsize(filepath) / 1024  # KB
    print(f"✅ Data saved to {filepath} ({file_size:.2f} KB)")

def print_summary(df):
    """Print data summary"""
    print("\n📊 DATA SUMMARY")
    print("=" * 60)
    print(f"\nTotal Customers: {len(df)}")
    print(f"\nChurn Distribution:")
    print(df['churn'].value_counts(normalize=True))
    
    print(f"\nContract Type Distribution:")
    print(df['contract_type'].value_counts())
    
    print(f"\nInternet Service Distribution:")
    print(df['internet_service'].value_counts())
    
    print(f"\nTenure Statistics:")
    print(df['tenure'].describe())
    
    print(f"\nMonthly Charges Statistics:")
    print(df['monthly_charges'].describe())
    
    print(f"\nAverage Services per Customer:")
    avg_services = (df['streaming_tv'] + df['streaming_movies'] + 
                    df['tech_support'] + df['online_security']).mean()
    print(f"{avg_services:.2f}")
    
    print("\n" + "=" * 60)

def main():
    """Main data generation pipeline"""
    print("=" * 60)
    print("🎬 NETFLIX CHURN PREDICTION - DATA GENERATION")
    print("=" * 60 + "\n")
    
    # Generate data
    df = generate_customer_data(n_samples=5000)
    
    # Save
    save_data(df)
    
    # Summary
    print_summary(df)
    
    print("\n✅ Sample data generation complete!")
    print("\n📝 Next steps:")
    print("   1. Train model: python src/models/train.py")
    print("   2. Start API: ./start_api.sh")

if __name__ == '__main__':
    main()