import os
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

# 1. Production training dataset representing messy bank statement strings
X_train = [
    "AWS_RECURR_883921_SEATTLE",
    "AMZN_MKTPL_CLOUD_COMPUTE",
    "GITHUB_INV_99204_SAN_FRAN",
    "CURSOR_SH_SUBSCRIPTION",
    "UBER_RIDE_GATEWAY_X",
    "LYFT_TRIP_DISPATCH_SF",
    "VNDR_SUPPLY_CHAI_HYD_99",
    "LOCAL_GROCERY_STORES_OFC",
    "STRIPE_PAYMENT_CHG_882"
]

# Parallel labels mapped to matching multi-output matrices: [Clean Name, Category]
y_train = [
    ["Amazon Web Services", "Cloud Infrastructure"],
    ["Amazon Web Services", "Cloud Infrastructure"],
    ["Developer Tooling Suite", "Software Subscriptions"],
    ["Developer Tooling Suite", "Software Subscriptions"],
    ["Rideshare Transport", "Travel & Logistics"],
    ["Rideshare Transport", "Travel & Logistics"],
    ["Local Grocery & Supplies", "Office Operations"],
    ["Local Grocery & Supplies", "Office Operations"],
    ["Stripe Gateway Financials", "Payment Processing"]
]

print("[TRAINING] Initializing Machine Learning Multi-Output Classifier Pipeline...")

# 2. Define a robust vector machine learning text pipeline architecture
model_pipeline = Pipeline([
    # Character-level analyzer handles random bank numbers and typos smoothly
    ('tfidf', TfidfVectorizer(ngram_range=(1, 3), analyzer='char_wb')), 
    ('classifier', RandomForestClassifier(n_estimators=150, random_state=42))
])

# 3. Train the machine learning pipeline patterns
model_pipeline.fit(X_train, y_train)
print("[TRAINING SUCCESS] ML Model trained completely with primary feature metrics.")

# 4. FIX: Use absolute file path calculations based on script location to prevent directory errors
current_dir = os.path.dirname(os.path.abspath(__file__))
destination_path = os.path.join(current_dir, "model.joblib")

print(f"[EXPORT] Serializing pipeline matrices directly to binary: {destination_path}")
joblib.dump(model_pipeline, destination_path)
print("[COMPLETED] model.joblib artifact compiled and saved successfully.")