import pickle
from diabetes_pipeline.data_preprocessing import preprocess_data
from sklearn.metrics import accuracy_score, classification_report
from diabetes_pipeline.config import MODEL_PATH

X_train, X_test, y_train, y_test, scaler = preprocess_data()

model = pickle.load(
    open(MODEL_PATH, "rb")
)

y_pred = model.predict(X_test)

print("Accuracy:")
print(accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))