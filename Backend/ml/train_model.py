import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


DATASET = "ml/data/training_dataset.csv"
MODEL_PATH = "ml/models/random_forest_model.pkl"


os.makedirs("ml/models", exist_ok=True)


# Load dataset
df = pd.read_csv(DATASET)


# Features used by ML model
FEATURES = [
    "road_length",
    "lanes",
    "max_speed",
    "road_width",
    "curvature"
]


X = df[FEATURES]
y = df["label"]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# Random Forest
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)


print("Training Random Forest model...")

model.fit(X_train, y_train)


# Prediction
predictions = model.predict(X_test)


# Accuracy
accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy:")
print(round(accuracy * 100, 2), "%")


print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions
    )
)


print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        predictions
    )
)


# Save model
joblib.dump(
    {
        "model": model,
        "features": FEATURES
    },
    MODEL_PATH
)


print("\nModel saved successfully!")
print(MODEL_PATH)