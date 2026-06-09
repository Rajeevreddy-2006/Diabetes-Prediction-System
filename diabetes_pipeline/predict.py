import pickle
import numpy as np
from diabetes_pipeline.config import MODEL_PATH, SCALER_PATH

model = pickle.load(
    open(MODEL_PATH, "rb")
)

scaler = pickle.load(
    open(SCALER_PATH, "rb")
)

sample = np.array([
    [2, 140, 80, 35, 100, 32.5, 0.5, 45]
])

sample = scaler.transform(sample)

prediction = model.predict(sample)

if prediction[0] == 1:
    print("Diabetic")
else:
    print("Not Diabetic")