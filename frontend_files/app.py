
import os
import io
import requests
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# The backend URL is read from an environment variable so the same image can point
# at a local container, a Codespaces forwarded URL, or any other host.
DEFAULT_API_URL = "http://localhost:7860"
API_URL = os.environ.get("API_URL", DEFAULT_API_URL)

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon=":shopping_cart:", layout="centered")

st.title("SuperKart Sales Forecasting")
st.write(
    "Predict the total revenue a product will generate in a given store, "
    "using the tuned Random Forest model served by the SuperKart Flask API."
)

api_url = st.sidebar.text_input("Backend API URL", API_URL)
st.sidebar.caption("Point this at your Codespaces forwarded URL, e.g. https://<codespace>-7860.app.github.dev")

tab_single, tab_batch = st.tabs(["Single Prediction", "Batch Prediction"])

# ---------------------------------------------------------------------------
# Single prediction
# ---------------------------------------------------------------------------
with tab_single:
    st.subheader("Single product-store forecast")

    col1, col2 = st.columns(2)

    with col1:
        Product_Weight = st.number_input("Product Weight", min_value=0.0, max_value=50.0, value=12.66, step=0.01)
        Product_Sugar_Content = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
        Product_Allocated_Area = st.number_input("Product Allocated Area (ratio)", min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f")
        Product_MRP = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
        Product_Id_char = st.selectbox("Product Family (Product Id prefix)", ["FD", "DR", "NC"])

    with col2:
        Store_Size = st.selectbox("Store Size", ["High", "Medium", "Small"])
        Store_Location_City_Type = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"])
        Store_Type = st.selectbox("Store Type", ["Departmental Store", "Supermarket Type1", "Supermarket Type2", "Food Mart"])
        Store_Age_Years = st.number_input("Store Age (years)", min_value=0, max_value=100, value=16, step=1)
        Product_Type_Category = st.selectbox("Product Type Category", ["Perishables", "Non Perishables"])

    product_data = {
        "Product_Weight": Product_Weight,
        "Product_Sugar_Content": Product_Sugar_Content,
        "Product_Allocated_Area": Product_Allocated_Area,
        "Product_MRP": Product_MRP,
        "Store_Size": Store_Size,
        "Store_Location_City_Type": Store_Location_City_Type,
        "Store_Type": Store_Type,
        "Product_Id_char": Product_Id_char,
        "Store_Age_Years": Store_Age_Years,
        "Product_Type_Category": Product_Type_Category,
    }

    if st.button("Predict", type="primary"):
        try:
            response = requests.post(f"{api_url.rstrip('/')}/v1/predict", json=product_data, timeout=60)
            if response.status_code == 200:
                predicted_sales = response.json()["Sales"]
                st.success(f"Predicted Product Store Sales Total: Rs. {predicted_sales:,.2f}")
            else:
                st.error(f"Error in API request (status {response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Could not reach the API at {api_url}. Details: {e}")

# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------
with tab_batch:
    st.subheader("Batch forecast from a CSV file")
    st.write(
        "Upload a CSV with the SuperKart columns (Product_Id, Product_Weight, "
        "Product_Sugar_Content, Product_Allocated_Area, Product_Type, Product_MRP, "
        "Store_Id, Store_Establishment_Year, Store_Size, Store_Location_City_Type, Store_Type). "
        "The API engineers the model features automatically."
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        preview = pd.read_csv(uploaded_file)
        st.write("Preview of the uploaded data:")
        st.dataframe(preview.head())
        uploaded_file.seek(0)

        if st.button("Run batch prediction", type="primary"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                response = requests.post(f"{api_url.rstrip('/')}/v1/predictbatch", files=files, timeout=300)
                if response.status_code == 200:
                    results = pd.DataFrame(response.json()["predictions"])
                    st.success(f"Generated {len(results)} forecasts.")
                    st.dataframe(results)
                    st.metric("Total forecasted revenue", f"Rs. {results['Predicted_Sales'].sum():,.2f}")
                    csv_bytes = results.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download predictions as CSV",
                        data=csv_bytes,
                        file_name="superkart_predictions.csv",
                        mime="text/csv",
                    )
                else:
                    st.error(f"Error in API request (status {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Could not reach the API at {api_url}. Details: {e}")
