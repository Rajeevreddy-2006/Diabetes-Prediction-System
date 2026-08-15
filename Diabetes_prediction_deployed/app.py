import os
import pickle
import numpy as np
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, Response

app = Flask(__name__)

# Initialize database if it doesn't exist
if not os.path.exists("database.db"):
    import init_db

# Load model and scaler
model = pickle.load(open("diabetes_model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():

    pregnancies = float(request.form["Pregnancies"])
    glucose = float(request.form["Glucose"])
    bloodpressure = float(request.form["BloodPressure"])
    skinthickness = float(request.form["SkinThickness"])
    insulin = float(request.form["Insulin"])
    bmi = float(request.form["BMI"])
    dpf = float(request.form["DiabetesPedigreeFunction"])
    age = float(request.form["Age"])

    data = np.array([[
        pregnancies,
        glucose,
        bloodpressure,
        skinthickness,
        insulin,
        bmi,
        dpf,
        age
    ]])

    # Scale input
    data = scaler.transform(data)

    # Prediction
    prediction = model.predict(data)

    if prediction[0] == 1:
        result = "Diabetic"
        color_class = "diabetic"
    else:
        result = "Not Diabetic"
        color_class = "non-diabetic"

    # Save prediction
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO predictions(
            pregnancies,
            glucose,
            bloodpressure,
            skinthickness,
            insulin,
            bmi,
            dpf,
            age,
            result
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pregnancies,
            glucose,
            bloodpressure,
            skinthickness,
            insulin,
            bmi,
            dpf,
            age,
            result
        )
    )

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        prediction=result,
        color_class=color_class
    )


@app.route("/history")
def history():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pregnancies,
            glucose,
            bloodpressure,
            skinthickness,
            insulin,
            bmi,
            dpf,
            age,
            result,
            created_at
        FROM predictions
        ORDER BY created_at DESC
        """
    )

    predictions = cursor.fetchall()
    conn.close()

    return render_template(
        "history.html",
        predictions=predictions
    )


@app.route("/clear_history")
def clear_history():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM predictions")

    conn.commit()
    conn.close()

    return redirect(url_for("history"))


@app.route("/download_history")
def download_history():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pregnancies,
            glucose,
            bloodpressure,
            skinthickness,
            insulin,
            bmi,
            dpf,
            age,
            result
        FROM predictions
        """
    )

    rows = cursor.fetchall()
    conn.close()

    def generate():
        yield "Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DPF,Age,Result\n"

        for row in rows:
            yield ",".join(map(str, row)) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=prediction_history.csv"
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )