#!/usr/bin/env python3
"""
Scikit-learn Anomaly Detection Pipeline
Alternative to PySpark for smaller datasets or local development

Manufacturing Group Manufacturing - OEMPartner Assembly Line MES

This module provides:
1. Isolation Forest for unsupervised anomaly detection
2. Random Forest for supervised classification (using labeled anomalies)
3. Real-time scoring for new telemetry data
"""
import asyncio
import os
import pickle
from datetime import datetime, timedelta
from typing import Optional, Tuple
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score
)

from pymongo import AsyncMongoClient
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings('ignore')

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")

# Feature columns
FEATURE_COLUMNS = [
    "temperature", "vibration", "powerConsumption", "cycleTime",
    "tempMean", "tempStd", "tempZScore",
    "vibMean", "vibStd", "vibZScore",
    "powerMean", "powerStd", "powerZScore",
    "cycleMean", "cycleStd", "cycleZScore",
    "alertCount", "errorRate"
]

# Anomaly type mapping
ANOMALY_TYPES = {
    "normal": 0,
    "temperature_spike": 1,
    "vibration_anomaly": 2,
    "power_surge": 3,
    "cycle_degradation": 4,
    "bearing_failure": 5,
}

REVERSE_ANOMALY_TYPES = {v: k for k, v in ANOMALY_TYPES.items()}


class AnomalyDetector:
    """
    Hybrid anomaly detection using Isolation Forest and Random Forest.

    - Isolation Forest: Unsupervised detection of outliers
    - Random Forest: Supervised classification of anomaly types
    """

    def __init__(self):
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,  # Expected proportion of anomalies
            random_state=42,
            n_jobs=-1
        )
        self.random_forest = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.model_version = "1.0.0"
        self.trained_at = None
        self.metrics = {}

    def preprocess(self, df: pd.DataFrame) -> np.ndarray:
        """
        Preprocess features for model input.
        """
        # Select feature columns
        X = df[FEATURE_COLUMNS].copy()

        # Fill missing values
        X = X.fillna(0)

        return X

    def fit(self, df: pd.DataFrame) -> dict:
        """
        Train both anomaly detection models.

        Args:
            df: DataFrame with features and labels

        Returns:
            Training metrics
        """
        print("=" * 60)
        print("Training Anomaly Detection Models")
        print("=" * 60)

        X = self.preprocess(df)

        # Create labels
        y = df['anomalyType'].map(ANOMALY_TYPES).fillna(0).astype(int)

        # Scale features
        print("\n1. Scaling features...")
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest (unsupervised)
        print("\n2. Training Isolation Forest...")
        self.isolation_forest.fit(X_scaled)

        # Train Random Forest (supervised)
        print("\n3. Training Random Forest classifier...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        self.random_forest.fit(X_train, y_train)

        # Evaluate
        print("\n4. Evaluating models...")
        y_pred = self.random_forest.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')

        print(f"\n   Random Forest Accuracy: {accuracy:.4f}")
        print(f"   Random Forest F1 Score: {f1:.4f}")

        print("\n   Classification Report:")
        print(classification_report(y_test, y_pred, target_names=list(ANOMALY_TYPES.keys())))

        # Isolation Forest evaluation
        if_predictions = self.isolation_forest.predict(X_scaled)
        if_anomalies = (if_predictions == -1).sum()
        print(f"\n   Isolation Forest detected {if_anomalies} anomalies ({if_anomalies/len(X)*100:.2f}%)")

        self.is_fitted = True
        self.trained_at = datetime.now()
        self.metrics = {
            "accuracy": round(accuracy, 4),
            "f1Score": round(f1, 4),
            "trainingSamples": len(X_train),
            "testSamples": len(X_test),
            "isolationForestAnomalies": int(if_anomalies),
            "trainedAt": self.trained_at.isoformat(),
            "modelVersion": self.model_version
        }

        print("\n" + "=" * 60)
        print("Training Complete!")
        print("=" * 60)

        return self.metrics

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomalies on new data.

        Returns DataFrame with predictions and confidence scores.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = self.preprocess(df)
        X_scaled = self.scaler.transform(X)

        # Get predictions from both models
        if_predictions = self.isolation_forest.predict(X_scaled)
        if_scores = self.isolation_forest.decision_function(X_scaled)

        rf_predictions = self.random_forest.predict(X_scaled)
        rf_probabilities = self.random_forest.predict_proba(X_scaled)

        # Combine results
        results = df[['machineId', 'lineId', 'timestamp']].copy()
        results['isAnomalyIF'] = if_predictions == -1
        results['anomalyScoreIF'] = -if_scores  # Negate so higher = more anomalous
        results['predictedType'] = rf_predictions
        results['predictedTypeName'] = results['predictedType'].map(REVERSE_ANOMALY_TYPES)
        results['confidence'] = rf_probabilities.max(axis=1)

        # Combined anomaly flag (either model detects)
        results['isAnomaly'] = (results['isAnomalyIF']) | (results['predictedType'] > 0)

        # Determine severity
        results['severity'] = results['predictedType'].apply(
            lambda x: 'critical' if x in [1, 5] else ('warning' if x in [2, 3] else 'info')
        )

        return results

    def save(self, path: str):
        """Save model to disk."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'isolation_forest': self.isolation_forest,
                'random_forest': self.random_forest,
                'scaler': self.scaler,
                'model_version': self.model_version,
                'trained_at': self.trained_at,
                'metrics': self.metrics,
            }, f)
        print(f"Model saved to {path}")

    @classmethod
    def load(cls, path: str) -> 'AnomalyDetector':
        """Load model from disk."""
        detector = cls()
        with open(path, 'rb') as f:
            data = pickle.load(f)
            detector.isolation_forest = data['isolation_forest']
            detector.random_forest = data['random_forest']
            detector.scaler = data['scaler']
            detector.model_version = data['model_version']
            detector.trained_at = data['trained_at']
            detector.metrics = data['metrics']
            detector.is_fitted = True
        print(f"Model loaded from {path}")
        return detector


async def load_training_data() -> pd.DataFrame:
    """Load feature store data from MongoDB."""
    client = AsyncMongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    try:
        collection = db["feature_store"]
        cursor = collection.find({})
        docs = await cursor.to_list(length=100000)

        if not docs:
            raise ValueError("No data in feature store. Run feature_engineering.py first.")

        df = pd.DataFrame(docs)
        print(f"Loaded {len(df)} records from feature store")

        return df

    finally:
        await client.close()


async def write_predictions_to_mongodb(predictions: pd.DataFrame):
    """Write anomaly predictions to MongoDB."""
    client = AsyncMongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    try:
        collection = db["anomaly_detections"]

        # Filter to actual anomalies
        anomalies = predictions[predictions['isAnomaly']].copy()

        if len(anomalies) == 0:
            print("No anomalies to write")
            return

        # Prepare documents
        docs = []
        for _, row in anomalies.iterrows():
            docs.append({
                "machineId": row['machineId'],
                "lineId": row['lineId'],
                "timestamp": row['timestamp'],
                "detectedAt": datetime.now(),
                "anomalyType": row['predictedTypeName'],
                "confidence": float(row['confidence']),
                "severity": row['severity'],
                "anomalyScore": float(row['anomalyScoreIF']),
                "modelVersion": "1.0.0",
                "acknowledged": False,
            })

        await collection.insert_many(docs)
        print(f"Wrote {len(docs)} anomaly detections to MongoDB")

    finally:
        await client.close()


async def main():
    """Main training and inference pipeline."""
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "train"
    model_path = "models/sklearn_anomaly_detector.pkl"

    if mode == "train":
        # Load data
        print("Loading training data from MongoDB...")
        df = await load_training_data()

        # Train model
        detector = AnomalyDetector()
        metrics = detector.fit(df)

        # Save model
        detector.save(model_path)

        print(f"\nTraining complete. Metrics: {metrics}")

    elif mode == "inference":
        # Load model
        detector = AnomalyDetector.load(model_path)

        # Load latest data
        print("Loading latest data...")
        df = await load_training_data()

        # Predict
        predictions = detector.predict(df)

        # Show summary
        anomaly_counts = predictions['predictedTypeName'].value_counts()
        print("\nAnomaly type counts:")
        print(anomaly_counts)

        # Write to MongoDB
        await write_predictions_to_mongodb(predictions)

    elif mode == "full":
        # Train and inference
        df = await load_training_data()

        detector = AnomalyDetector()
        detector.fit(df)
        detector.save(model_path)

        predictions = detector.predict(df)
        await write_predictions_to_mongodb(predictions)

    else:
        print(f"Unknown mode: {mode}")
        print("Usage: sklearn_anomaly_detection.py [train|inference|full]")


if __name__ == "__main__":
    asyncio.run(main())
