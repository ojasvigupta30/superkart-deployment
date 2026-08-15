
# Import necessary libraries
import os
import numpy as np
import joblib  # For loading the serialized model
import pandas as pd  # For data manipulation
from flask import Flask, request, jsonify  # For creating the Flask API

# Initialize the Flask app with a name
superkart_api = Flask("SuperKart Sales Predictor")

# Load the trained sales-forecasting pipeline (preprocessing + tuned Random Forest).
# The path is resolved relative to this file so the app works both inside the Docker
# container (WORKDIR /app) and when run directly from the repository root.
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "superkart_sales_prediction_model_v1_0.joblib",
)
model = joblib.load(MODEL_PATH)

# The exact feature order the pipeline was trained on
FEATURES = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]


# Define a route for the home page
@superkart_api.get("/")
def home():
    return (
        "Welcome to the SuperKart Sales Prediction API. "
        "POST a JSON record to /v1/predict for a single forecast, "
        "or upload a CSV to /v1/predictbatch for batch forecasts."
    )


# Health-check endpoint, useful for container orchestration
@superkart_api.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": True})


# Endpoint for single-record inference
@superkart_api.post("/v1/predict")
def predict_sales():
    # Get JSON data from the request
    data = request.get_json()

    # Extract the relevant product/store features. The order of the column names matters.
    sample = {
        "Product_Weight": data["Product_Weight"],
        "Product_Sugar_Content": data["Product_Sugar_Content"],
        "Product_Allocated_Area": data["Product_Allocated_Area"],
        "Product_MRP": data["Product_MRP"],
        "Store_Size": data["Store_Size"],
        "Store_Location_City_Type": data["Store_Location_City_Type"],
        "Store_Type": data["Store_Type"],
        "Product_Id_char": data["Product_Id_char"],
        "Store_Age_Years": data["Store_Age_Years"],
        "Product_Type_Category": data["Product_Type_Category"],
    }

    # Convert the extracted data into a DataFrame
    input_data = pd.DataFrame([sample])

    # Make the sales prediction using the trained pipeline
    prediction = model.predict(input_data).tolist()[0]

    # Return the prediction as a JSON response
    return jsonify({"Sales": round(prediction, 2)})


# Endpoint for batch inference from an uploaded CSV file
@superkart_api.post("/v1/predictbatch")
def predict_batch():
    # Read the uploaded CSV file from the request
    file = request.files["file"]
    input_df = pd.read_csv(file)

    # If the raw dataset columns are supplied, engineer the model features on the fly
    if "Product_Id" in input_df.columns:
        input_df["Product_Id_char"] = input_df["Product_Id"].str[:2]
    if "Store_Establishment_Year" in input_df.columns:
        input_df["Store_Age_Years"] = 2025 - input_df["Store_Establishment_Year"]
    if "Product_Type" in input_df.columns:
        perishables = [
            "Dairy",
            "Meat",
            "Fruits and Vegetables",
            "Breakfast",
            "Breads",
            "Seafood",
        ]
        input_df["Product_Type_Category"] = np.where(
            input_df["Product_Type"].isin(perishables), "Perishables", "Non Perishables"
        )
    if "Product_Sugar_Content" in input_df.columns:
        input_df["Product_Sugar_Content"] = input_df["Product_Sugar_Content"].replace(
            "reg", "Regular"
        )

    # Validate that every required feature is present
    missing = [c for c in FEATURES if c not in input_df.columns]
    if missing:
        return jsonify({"error": f"Missing required columns: {missing}"}), 400

    # Predict for every row and append the forecast as a new column
    predictions = model.predict(input_df[FEATURES]).round(2)
    input_df["Predicted_Sales"] = predictions

    # Return the enriched records as JSON
    return jsonify({"predictions": input_df.to_dict(orient="records")})


# Run the Flask app
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
