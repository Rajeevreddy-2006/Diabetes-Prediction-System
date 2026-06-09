from sklearn.ensemble import RandomForestClassifier
from diabetes_pipeline.data_preprocessing import preprocess_data
import pickle

import logging

logging.basicConfig(
    filename="diabetes_pipeline/logs/training.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Training Started")

X_train, X_test, y_train, y_test, scaler = preprocess_data()

rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

rf.fit(X_train, y_train)

pickle.dump(
    rf,
    open("Diabetes_prediction_deployed/diabetes_model.pkl", "wb")
)

pickle.dump(
    scaler,
    open("Diabetes_prediction_deployed/scaler.pkl", "wb")
)

print("Model Saved Successfully")
logging.info("Model Saved Successfully")