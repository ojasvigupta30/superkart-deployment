# SuperKart Sales Forecasting - Model Deployment

URL - `https://friendly-space-waffle-4vpxpj4j677hqwvv-8501.app.github.dev/`

Forecasts `Product_Store_Sales_Total` for a product in a store, using a tuned Random Forest
pipeline (one-hot encoding + regressor) served as a REST API with a Streamlit front end.

**Model performance (hold-out test set):** RMSE 290.42 | MAE 109.86 | R-squared 0.926 | MAPE 4.98%

## Repository structure

```
backend_files/     Flask API + Dockerfile + serialized model
frontend_files/    Streamlit web app + Dockerfile
superkart_batch_sample.csv   20-row sample file for the batch-inference demo
```

## API endpoints

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/v1/predict` | POST (JSON) | Single product-store forecast |
| `/v1/predictbatch` | POST (multipart CSV) | Batch forecasts for an uploaded CSV |

## Running in GitHub Codespaces

Backend (port 7860):

```bash
cd backend_files
docker build -t superkart-backend .
docker run -d -p 7860:7860 --name superkart-api superkart-backend
```

Frontend (port 8501) - replace the URL with your own forwarded backend address:

```bash
cd frontend_files
docker build -t superkart-frontend .
docker run -d -p 8501:8501 \
  -e API_URL="https://friendly-space-waffle-4vpxpj4j677hqwvv-7860.app.github.dev" \
  --name superkart-ui superkart-frontend
```

Set both ports to **Public** in the Codespaces **PORTS** tab.

## Example request

```bash
curl -X POST https://friendly-space-waffle-4vpxpj4j677hqwvv-7860.app.github.dev/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"Product_Weight":12.66,"Product_Sugar_Content":"Low Sugar","Product_Allocated_Area":0.027,"Product_MRP":117.08,"Store_Size":"Medium","Store_Location_City_Type":"Tier 2","Store_Type":"Supermarket Type2","Product_Id_char":"FD","Store_Age_Years":16,"Product_Type_Category":"Non Perishables"}'
```
