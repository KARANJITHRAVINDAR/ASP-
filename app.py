# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import xgboost as xgb
import shap
import mysql.connector
from mysql.connector import pooling
import os
from textblob import TextBlob
import re

# --- App Initialization ---
app = Flask(__name__, static_folder='static')
CORS(app)

# --- Database Configuration & Connection Pooling ---
# It's more secure to use environment variables for credentials in production.
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="medrisk_pool",
        pool_size=5,
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'Ks@kbd23777'), # Using the password you provided
        database=os.environ.get('MYSQL_DATABASE', 'hospital_ai_dashboard')
    )
    print("Database connection pool created successfully.")
except mysql.connector.Error as e:
    print(f"Error creating connection pool: {e}")
    exit()

# --- Load Model and Explainer on Startup ---
print("Loading XGBoost model...")
model = xgb.XGBRegressor()
model.load_model('xgboost_model.json')
print("Model loaded successfully.")

print("Creating SHAP explainer...")
explainer = shap.TreeExplainer(model)
print("SHAP explainer created.")

# This feature list must be consistent with the model training and database schema.
FEATURE_NAMES = [
    'age', 'admissionType', 'priorAdmissions', 'surgeryMethod', 'albumin',
    'hemoglobin', 'hasSepsis', 'hasDelirium', 'hasMalignancy', 'hasDiabetes',
    'hasCHF', 'hasCKD', 'hasCOPD', 'hasStroke', 'hasLiverDisease'
]

# --- AI Model Prediction Logic ---
def get_prediction_and_explanation(data):
    """Runs the model and returns a formatted prediction and explanation."""
    input_df = pd.DataFrame([data], columns=FEATURE_NAMES)

    # Convert boolean values to integers (0 or 1) for the model
    for col in input_df.select_dtypes(include='bool').columns:
        input_df[col] = input_df[col].astype(int)

    prediction = model.predict(input_df)
    predicted_los = round(float(prediction[0]))

    shap_values = explainer.shap_values(input_df)
    base_value = float(explainer.expected_value)
    shap_dict = dict(zip(FEATURE_NAMES, shap_values[0]))

    # Determine risk category based on predicted Length of Stay (LOS)
    if predicted_los >= 10:
        risk_category = "High"
    elif predicted_los >= 6:
        risk_category = "Moderate"
    else:
        risk_category = "Low"
    
    # Simplified risk score calculation for display purposes
    risk_score = min(int(predicted_los * 7.5 + abs(base_value * 2)), 100)

    return {
        'predicted_los': predicted_los,
        'riskScore': risk_score,
        'riskLevel': risk_category,
        'baseValue': round(base_value, 2),
        'shapValues': {k: round(float(v), 2) for k, v in shap_dict.items()}
    }

# --- AI Feedback Analysis Logic ---
FEEDBACK_CATEGORIES = {
    "Nursing Care": ["nurse", "nurses", "nursing", "care staff"],
    "Doctor's Conduct": ["doctor", "dr", "physician", "consultant"],
    "Cleanliness": ["clean", "hygiene", "dirty", "messy", "housekeeping"],
    "Billing": ["bill", "invoice", "payment", "charge", "insurance"],
    "Food": ["food", "meal", "diet", "canteen"],
    "Facilities": ["room", "bed", "washroom", "ac", "infrastructure", "wifi"]
}

def categorize_feedback(text):
    text_lower = text.lower()
    for category, keywords in FEEDBACK_CATEGORIES.items():
        if any(re.search(r'\b' + keyword + r'\b', text_lower) for keyword in keywords):
            return category
    return "General"

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text.
    Returns the polarity score and a corresponding label (Positive, Negative, Neutral).
    """
    analysis = TextBlob(text)
    score = analysis.sentiment.polarity
    if score > 0.1:
        label = "Positive"
    elif score < -0.1:
        label = "Negative"
    else:
        label = "Neutral"
    return score, label

# --- API Endpoints ---
@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Fetches all stored patient predictions."""
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM predictions ORDER BY admissionDate DESC, id DESC")
        patients = cursor.fetchall()
        # Convert date objects to strings for JSON serialization
        for patient in patients:
            if patient.get('admissionDate'):
                patient['admissionDate'] = patient['admissionDate'].isoformat()
            if patient.get('timestamp'):
                patient['timestamp'] = patient['timestamp'].isoformat()
        return jsonify(patients)
    except mysql.connector.Error as e:
        app.logger.error(f"Database query failed: {e}")
        return jsonify({"error": "Failed to retrieve patient data."}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/assessment', methods=['POST'])
def run_assessment():
    """Receives new patient data, runs prediction, and stores it."""
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        inputs = request.get_json()

        # Prepare data for the model
        model_inputs = {key: inputs.get(key) for key in FEATURE_NAMES}

        # Get prediction from the AI model
        prediction_result = get_prediction_and_explanation(model_inputs)

        # Combine inputs and results for database logging
        db_data = {**inputs, **prediction_result}

        # --- MODIFIED SECTION ---
        # Define the column order explicitly to ensure it matches the query
        column_order = [
            'patientId', 'patientName', 'admissionDate', 'age', 'admissionType', 'priorAdmissions',
            'surgeryMethod', 'albumin', 'hemoglobin', 'hasSepsis', 'hasDelirium', 'hasMalignancy',
            'hasDiabetes', 'hasCHF', 'hasCKD', 'hasCOPD', 'hasStroke', 'hasLiverDisease',
            'predicted_los', 'riskScore', 'riskLevel'
        ]

        # Create a query with standard %s placeholders
        query = f"""
            INSERT INTO predictions ({', '.join(f'`{col}`' for col in column_order)})
            VALUES ({', '.join(['%s'] * len(column_order))})
        """

        # Create a tuple of values in the correct order
        values_tuple = tuple(db_data.get(col) for col in column_order)

        # Execute with the tuple
        cursor.execute(query, values_tuple)
        # --- END OF MODIFIED SECTION ---

        conn.commit()

        return jsonify({"status": "success", "message": "Assessment stored successfully."}), 201

    except mysql.connector.Error as e:
        app.logger.error(f"Database insertion failed: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "An internal error occurred while saving the assessment."}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Calculates and returns key statistics for the dashboard header."""
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Total Patients
        cursor.execute("SELECT COUNT(*) as totalPatients FROM predictions")
        total_patients = cursor.fetchone()['totalPatients']
        
        # Average Risk Score
        cursor.execute("SELECT AVG(riskScore) as avgRisk FROM predictions")
        avg_risk = cursor.fetchone()['avgRisk']
        
        # High Risk Count
        cursor.execute("SELECT COUNT(*) as highRiskCount FROM predictions WHERE riskLevel = 'High'")
        high_risk_count = cursor.fetchone()['highRiskCount']
        
        stats = {
            "totalPatients": total_patients or 0,
            "avgRisk": round(avg_risk) if avg_risk else 0,
            "highRiskCount": high_risk_count or 0
        }
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Dashboard stats error: {e}")
        return jsonify({"error": "Could not calculate dashboard statistics."}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """API endpoint to receive, process, and store patient feedback."""
    if not request.is_json:
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415

    data = request.get_json()
    patient_id = data.get('patient_id')
    feedback_text = data.get('feedback_text')

    if not patient_id or not feedback_text:
        return jsonify({"error": "patient_id and feedback_text are required fields"}), 400

    # --- MODIFIED SECTION: Perform sentiment analysis and categorization ---
    sentiment_score, sentiment_label = analyze_sentiment(feedback_text)
    category = categorize_feedback(feedback_text)
    # --- END OF MODIFIED SECTION ---
    
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    try:
        # Updated query to include sentiment score and label
        query = """
            INSERT INTO feedback (patient_id, feedback_text, sentiment_score, sentiment_label, category)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Updated values for the query execution
        cursor.execute(query, (patient_id, feedback_text, sentiment_score, sentiment_label, category))
        conn.commit()
        
        # Updated response to include both analysis results
        return jsonify({
            "message": "Feedback submitted successfully!",
            "analysis": { "sentiment_label": sentiment_label, "category": category }
        }), 201
    except mysql.connector.Error as e:
        app.logger.error(f"Database insertion failed: {e}")
        return jsonify({"error": "An internal error occurred while saving feedback."}), 500
    finally:
        cursor.close()
        conn.close()

# --- HTML Rendering ---
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/feedback')
def feedback_page():
    return render_template('feedback.html')

# --- Static File Serving ---
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)