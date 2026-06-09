import pickle
import numpy as np
import sqlite3
from flask_bcrypt import Bcrypt
import csv
from flask import Response
from flask import (Flask,render_template,request,session,redirect,url_for,flash)

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "diabetes_prediction_secret"

# Load model and scaler
model = pickle.load(open('diabetes_model.pkl', 'rb'))
scaler = pickle.load(open('scaler.pkl', 'rb'))


@app.route('/')
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html",username=session["username"])


@app.route('/predict', methods=['POST'])
def predict():
    pregnancies = float(request.form['Pregnancies'])
    glucose = float(request.form['Glucose'])
    bloodpressure = float(request.form['BloodPressure'])
    skinthickness = float(request.form['SkinThickness'])
    insulin = float(request.form['Insulin'])
    bmi = float(request.form['BMI'])
    dpf = float(request.form['DiabetesPedigreeFunction'])
    age = float(request.form['Age'])

    data = np.array([[pregnancies, glucose, bloodpressure,skinthickness, insulin, bmi, dpf, age]])

    data = scaler.transform(data)
    prediction = model.predict(data)

    if prediction[0] == 1:
        result = "Diabetic"
        color_class = "diabetic"
    else:
        result = "Not Diabetic"
        color_class = "non-diabetic"

    # Save prediction to database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
    """
    INSERT INTO predictions(
        username,
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
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        session["username"],
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
    session["prediction"] = result
    session["color_class"] = color_class
    return redirect(url_for("result"))

@app.route('/result')
def result():
    prediction = session.get("prediction")
    color_class = session.get("color_class")
    return render_template('result.html',prediction=prediction,color_class=color_class)

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users(username, password)
                VALUES (?, ?)
                """,
                (username, hashed_password)
            )
            conn.commit()
            flash(
                "Registration successful! Please login.",
                "success"
            )
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash(
                "Username already exists!",
                "error"
            )
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(
            user[2],
            password
        ):
            session["username"] = username
            flash(
                f"Welcome back, {username}!",
                "success"
            )
            return redirect(url_for('home'))
        flash(
            "Invalid username or password!",
            "error"
        )
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/history')
def history():
    if "username" not in session:
        return redirect(url_for("login"))
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
        WHERE username = ?
        ORDER BY created_at DESC
        """,
        (session["username"],)
    )
    predictions = cursor.fetchall()
    conn.close()
    return render_template("history.html",predictions=predictions)

@app.route('/clear_history')
def clear_history():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM predictions
        WHERE username = ?
        """,
        (session["username"],)
    )
    conn.commit()
    conn.close()
    flash("History cleared successfully!", "success")
    return redirect(url_for("history"))

@app.route('/download_history')
def download_history():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pregnancies,
               glucose,
               bloodpressure,
               skinthickness,
               insulin,
               bmi,
               dpf,
               age,
               result
        FROM predictions
        WHERE username = ?
    """, (session["username"],))
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

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)