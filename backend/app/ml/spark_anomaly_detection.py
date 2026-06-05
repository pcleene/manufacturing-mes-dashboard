#!/usr/bin/env python3
"""
PySpark Anomaly Detection Pipeline
Trains Isolation Forest model on MongoDB Time Series feature store data

Manufacturing Group Manufacturing - OEMPartner Assembly Line MES
MongoDB Time Series -> Feature Store -> Spark ML -> Anomaly Predictions

This script demonstrates how to:
1. Read transformed feature data from MongoDB
2. Use PySpark for distributed ML training
3. Deploy model for real-time anomaly detection
4. Write predictions back to MongoDB
"""
import os
from datetime import datetime
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, current_timestamp,
    udf, struct, array
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    BooleanType, TimestampType, IntegerType
)
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

from dotenv import load_dotenv

load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")

# Feature columns for ML model
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
    "temperature_spike": 1,
    "vibration_anomaly": 2,
    "power_surge": 3,
    "cycle_degradation": 4,
    "bearing_failure": 5,
}


def create_spark_session(app_name: str = "OEMPartnerAnomalyDetection") -> SparkSession:
    """
    Create Spark session with MongoDB connector.

    Note: Requires mongodb-spark-connector package.
    Run with: spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0
    """
    return (SparkSession.builder
            .appName(app_name)
            .config("spark.mongodb.read.connection.uri", MONGODB_URI)
            .config("spark.mongodb.write.connection.uri", MONGODB_URI)
            .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0")
            .getOrCreate())


def load_feature_store(spark: SparkSession) -> 'DataFrame':
    """
    Load feature store data from MongoDB into Spark DataFrame.
    """
    return (spark.read
            .format("mongodb")
            .option("database", MONGODB_DATABASE)
            .option("collection", "feature_store")
            .load())


def prepare_training_data(df: 'DataFrame') -> 'DataFrame':
    """
    Prepare data for ML training.

    - Handle null values
    - Encode categorical labels
    - Create feature vector
    """
    # Fill null values with 0 for numeric columns
    for col_name in FEATURE_COLUMNS:
        df = df.fillna({col_name: 0.0})

    # Create numeric label from anomaly type
    df = df.withColumn(
        "label",
        when(col("isAnomaly") == False, 0)
        .when(col("anomalyType") == "temperature_spike", 1)
        .when(col("anomalyType") == "vibration_anomaly", 2)
        .when(col("anomalyType") == "power_surge", 3)
        .when(col("anomalyType") == "cycle_degradation", 4)
        .when(col("anomalyType") == "bearing_failure", 5)
        .otherwise(6)  # Unknown anomaly type
    )

    return df


def build_anomaly_detection_pipeline() -> Pipeline:
    """
    Build ML pipeline for anomaly detection.

    Uses Random Forest for multi-class classification of anomaly types.
    """
    # Assemble features into vector
    assembler = VectorAssembler(
        inputCols=FEATURE_COLUMNS,
        outputCol="rawFeatures",
        handleInvalid="skip"
    )

    # Scale features
    scaler = StandardScaler(
        inputCol="rawFeatures",
        outputCol="features",
        withMean=True,
        withStd=True
    )

    # Random Forest classifier for anomaly type prediction
    rf = RandomForestClassifier(
        labelCol="label",
        featuresCol="features",
        numTrees=100,
        maxDepth=10,
        seed=42
    )

    # Create pipeline
    pipeline = Pipeline(stages=[assembler, scaler, rf])

    return pipeline


def train_model(
    spark: SparkSession,
    save_path: Optional[str] = None
) -> tuple:
    """
    Train anomaly detection model on feature store data.

    Args:
        spark: Spark session
        save_path: Optional path to save trained model

    Returns:
        Tuple of (trained model, evaluation metrics)
    """
    print("=" * 60)
    print("OEMPartner Assembly Line - Anomaly Detection Training")
    print("=" * 60)

    # Load data
    print("\n1. Loading feature store from MongoDB...")
    df = load_feature_store(spark)
    print(f"   Loaded {df.count()} feature records")

    # Prepare data
    print("\n2. Preparing training data...")
    df = prepare_training_data(df)

    # Show class distribution
    print("\n   Label distribution:")
    df.groupBy("label").count().orderBy("label").show()

    # Split data
    print("\n3. Splitting data (80% train, 20% test)...")
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
    print(f"   Training samples: {train_df.count()}")
    print(f"   Test samples: {test_df.count()}")

    # Build and train pipeline
    print("\n4. Training Random Forest model...")
    pipeline = build_anomaly_detection_pipeline()
    model = pipeline.fit(train_df)

    # Evaluate on test set
    print("\n5. Evaluating model...")
    predictions = model.transform(test_df)

    evaluator = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    )
    accuracy = evaluator.evaluate(predictions)

    evaluator_f1 = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="f1"
    )
    f1_score = evaluator_f1.evaluate(predictions)

    metrics = {
        "accuracy": round(accuracy, 4),
        "f1Score": round(f1_score, 4),
        "trainingSamples": train_df.count(),
        "testSamples": test_df.count(),
        "trainedAt": datetime.now().isoformat(),
        "modelVersion": "1.0.0"
    }

    print(f"\n   Accuracy: {accuracy:.4f}")
    print(f"   F1 Score: {f1_score:.4f}")

    # Show confusion matrix sample
    print("\n   Prediction sample:")
    predictions.select(
        "machineId", "label", "prediction", "probability"
    ).show(10, truncate=False)

    # Save model if path provided
    if save_path:
        print(f"\n6. Saving model to {save_path}...")
        model.write().overwrite().save(save_path)

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)

    return model, metrics


def run_inference(
    spark: SparkSession,
    model: PipelineModel,
    write_to_mongodb: bool = True
) -> 'DataFrame':
    """
    Run inference on latest feature store data and write predictions to MongoDB.

    Args:
        spark: Spark session
        model: Trained ML model
        write_to_mongodb: Whether to write predictions to anomaly_detections collection

    Returns:
        DataFrame with predictions
    """
    print("\nRunning inference on latest data...")

    # Load latest features
    df = load_feature_store(spark)
    df = prepare_training_data(df)

    # Run predictions
    predictions = model.transform(df)

    # Filter to detected anomalies (predicted class > 0)
    anomalies = predictions.filter(col("prediction") > 0)

    print(f"Detected {anomalies.count()} anomalies")

    # Map prediction back to anomaly type
    reverse_mapping = {v: k for k, v in ANOMALY_TYPES.items()}
    reverse_mapping[0] = "normal"
    reverse_mapping[6] = "unknown"

    # Prepare for MongoDB write
    if write_to_mongodb and anomalies.count() > 0:
        # Select and rename columns for anomaly_detections collection
        output = anomalies.select(
            col("machineId"),
            col("lineId"),
            col("timestamp"),
            current_timestamp().alias("detectedAt"),
            when(col("prediction") == 1, "temperature_spike")
            .when(col("prediction") == 2, "vibration_anomaly")
            .when(col("prediction") == 3, "power_surge")
            .when(col("prediction") == 4, "cycle_degradation")
            .when(col("prediction") == 5, "bearing_failure")
            .otherwise("unknown").alias("anomalyType"),
            # Extract max probability as confidence
            col("probability").getItem(col("prediction").cast("int")).alias("confidence"),
            when(col("prediction").isin([1, 5]), "critical")
            .when(col("prediction").isin([2, 3]), "warning")
            .otherwise("info").alias("severity"),
            struct(
                col("temperature"), col("vibration"),
                col("powerConsumption"), col("cycleTime"),
                col("tempZScore"), col("vibZScore"),
                col("powerZScore"), col("cycleZScore")
            ).alias("features"),
            lit("1.0.0").alias("modelVersion"),
            lit(False).alias("acknowledged")
        )

        # Write to MongoDB
        (output.write
         .format("mongodb")
         .option("database", MONGODB_DATABASE)
         .option("collection", "anomaly_detections")
         .mode("append")
         .save())

        print(f"Wrote {output.count()} anomalies to MongoDB")

    return anomalies


def main():
    """Main entry point for training and inference."""
    import sys

    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # Check command line args
        mode = sys.argv[1] if len(sys.argv) > 1 else "train"

        if mode == "train":
            # Train new model
            model_path = "models/anomaly_detector"
            model, metrics = train_model(spark, save_path=model_path)
            print(f"\nModel saved to: {model_path}")
            print(f"Metrics: {metrics}")

        elif mode == "inference":
            # Load existing model and run inference
            model_path = sys.argv[2] if len(sys.argv) > 2 else "models/anomaly_detector"
            print(f"Loading model from: {model_path}")
            model = PipelineModel.load(model_path)
            anomalies = run_inference(spark, model, write_to_mongodb=True)
            anomalies.show(20)

        elif mode == "full":
            # Train and run inference
            model, metrics = train_model(spark)
            anomalies = run_inference(spark, model, write_to_mongodb=True)
            print(f"\nDetected {anomalies.count()} anomalies")

        else:
            print(f"Unknown mode: {mode}")
            print("Usage: spark_anomaly_detection.py [train|inference|full]")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
