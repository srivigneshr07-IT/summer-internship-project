"""
=========================================================

Project : AI Powered Vehicle Valuation System

Module  : FastAPI Backend

Author  : Srivignesh

=========================================================
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from datetime import datetime
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR, MODEL_VERSION
from app.predictor import (
    predict_price,
    estimate_damage_cost,
    calculate_confidence_score,
    compute_suggested_price,
    calculate_transaction_price,
)
from app.schemas import (
    AppMetadata,
    ImageAnalysisResponse,
    PredictionHistoryItem,
    PredictionResponse,
    VehicleInput,
)
from app.utils import (
    init_db,
    list_brands,
    list_models,
    get_vehicle_details,
    record_prediction,
    list_history,
    clear_history,
    search_brands,
    search_models,
    list_vehicles,
    count_brands,
    count_models,
    count_predictions,
)
from app.bedrock_vision import analyze_vehicle_image_with_bedrock, detect_vehicle_damage_with_bedrock

# Import Dynamic Pricing Engine
from pricing import DynamicPricingEngine
from market_intelligence import MarketIntelligence


app = FastAPI(

    title="AI Powered Vehicle Valuation API",

    version="1.0.0",

    description="Predicts used vehicle prices using XGBoost."

)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://orange-funicular-5g4q579x4qqphw9g-5500.app.github.dev",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Initialize the SQLite-based vehicle catalog when the app starts.
db_connection = init_db()

# Initialize Dynamic Pricing Engine
pricing_engine = DynamicPricingEngine(freshness_days=30)
market_intelligence = MarketIntelligence(freshness_days=30)

@app.post("/predict", response_model=PredictionResponse)
def predict(vehicle: VehicleInput):
    payload = vehicle.model_dump()
    payload["myear"] = datetime.utcnow().year - payload["car_age"]
    input_df = pd.DataFrame([payload])
    
    # Get ML prediction
    ml_price = predict_price(input_df)
    
    # Normalize brand name for market intelligence (remove "Suzuki" from "Maruti Suzuki")
    brand_for_market = payload.get("brand", "")
    if "maruti" in brand_for_market.lower():
        brand_for_market = "Maruti"
    
    # Get dynamic price with market intelligence
    try:
        # Check if database is configured
        import os
        db_host = os.getenv('POSTGRES_HOST', '')
        
        if db_host:
            # Database configured, try dynamic pricing
            print(f"🔍 Attempting market intelligence with DB: {db_host[:20]}...")
            
            dynamic_result = pricing_engine.get_dynamic_price(
                ml_prediction=ml_price,
                brand=brand_for_market,
                model=payload.get("model"),
                year=payload["myear"],
                city=payload.get("city", "Chennai"),
                fuel=payload.get("fuel_type"),
                transmission=payload.get("transmission")
            )
            
            print(f"✅ Market intelligence result: {dynamic_result.get('status')}")
            print(f"   Sample size: {dynamic_result.get('market_context', {}).get('sample_size', 0)}")
            
            # Use dynamic price as final price
            price = dynamic_result["final_price"]
            market_data_available = dynamic_result["status"] == "success"
            market_context = dynamic_result.get("market_context", {})
            pricing_breakdown = dynamic_result.get("pricing_breakdown", {})
        else:
            # Database not configured, use ML prediction only
            print("⚠️  No database configured, using ML-only prediction")
            raise Exception("Database not configured")
        
    except Exception as e:
        # Fallback to ML-only if dynamic pricing fails
        error_msg = str(e).lower()
        if "database not configured" not in error_msg:
            print(f"❌ Dynamic pricing failed: {e}. Using ML prediction only.")
        price = ml_price
        market_data_available = False
        market_context = {}
        pricing_breakdown = {"ml_prediction": ml_price}
    
    damage_cost = estimate_damage_cost(payload.get("damage_description"))
    confidence_score = calculate_confidence_score(payload)
    suggested_price = compute_suggested_price(price, damage_cost)
    
    # Calculate transaction-specific pricing
    transaction_type = payload.get("transaction_type", "selling")
    transaction_data = calculate_transaction_price(price, damage_cost, transaction_type, payload)
    
    record_prediction(db_connection, payload, price)

    return {
        "predicted_price": round(price, 2),
        "damage_cost": round(damage_cost, 2),
        "confidence_score": confidence_score,
        "suggested_price": round(suggested_price, 2),
        "currency": "INR",
        "model_version": MODEL_VERSION,
        "status": "success",
        "transaction_type": transaction_type,
        "transaction_price": transaction_data["transaction_price"],
        "profit_margin": transaction_data["profit_margin"],
        "price_range_min": transaction_data["price_range_min"],
        "price_range_max": transaction_data["price_range_max"],
        # Add market intelligence data
        "market_data_available": market_data_available,
        "ml_prediction": round(ml_price, 2),
        "market_average": pricing_breakdown.get("market_average"),
        "market_median": pricing_breakdown.get("market_median"),
        "market_confidence": pricing_breakdown.get("confidence", "none"),
        "market_sample_size": market_context.get("sample_size", 0),
    }

@app.get("/history", response_model=list[PredictionHistoryItem])
def get_history(limit: int = 20):
    return list_history(db_connection, limit)

@app.delete("/history")
def delete_history():
    clear_history(db_connection)
    return {"status": "success", "message": "Prediction history cleared."}

@app.post("/vision/analyze", response_model=ImageAnalysisResponse)
async def analyze_vehicle_images(
    main: UploadFile | None = File(None),
    rear: UploadFile | None = File(None),
    left: UploadFile | None = File(None),
    right: UploadFile | None = File(None),
    interior: UploadFile | None = File(None),
    dashboard: UploadFile | None = File(None),
    tyres: UploadFile | None = File(None),
    engine: UploadFile | None = File(None),
):
    if not main:
        raise HTTPException(status_code=400, detail="Please upload a primary vehicle image for analysis.")

    try:
        # Read and preprocess image
        contents = await main.read()
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image.thumbnail((1024, 1024))
        
        # Analyze with AWS Bedrock Nova Lite
        result = analyze_vehicle_image_with_bedrock(image)
        
        return {
            "detected_brand": result.get("detected_brand"),
            "detected_model": result.get("detected_model"),
            "detected_body_type": result.get("detected_body_type"),
            "detected_color": result.get("detected_color"),
            "estimated_year": None,
            "vehicle_category": result.get("detected_body_type"),
            "images": [
                {
                    "slot": "main",
                    "filename": main.filename,
                    "content_type": main.content_type,
                    "width": image.width,
                    "height": image.height,
                }
            ],
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(error)}")


# DAMAGE DETECTION DISABLED - Feature temporarily disabled
# @app.post("/vision/detect-damage")
# async def detect_damage(image: UploadFile = File(...)):
#     """Detect vehicle damage from uploaded image using AWS Bedrock Nova Lite."""
#     try:
#         contents = await image.read()
#         from PIL import Image
#         import io
#         img = Image.open(io.BytesIO(contents)).convert("RGB")
#         img.thumbnail((1024, 1024))
#         
#         result = detect_vehicle_damage_with_bedrock(img)
#         
#         return {
#             "status": "success",
#             "has_damage": result["has_damage"],
#             "damage_severity": result["damage_severity"],
#             "damage_description": result["damage_description"],
#             "damage_areas": result["damage_areas"],
#             "confidence": result["confidence"]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Damage detection failed: {str(e)}")

@app.get("/vehicles")
def get_vehicles(search: str | None = None, limit: int = 50):
    return list_vehicles(db_connection, search, limit)

@app.get("/brands")
def get_brands(search: str | None = None):
    return search_brands(db_connection, search)

@app.get("/models/{brand}")
def get_models(brand: str, search: str | None = None):
    return search_models(db_connection, brand, search)

@app.get("/metadata", response_model=AppMetadata)
def get_metadata():
    return {
        "model_version": MODEL_VERSION,
        "brands_count": count_brands(db_connection),
        "models_count": count_models(db_connection),
        "total_predictions": count_predictions(db_connection),
        "dataset_version": "v1",
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "model_version": MODEL_VERSION, "database": "available"}

@app.get("/vehicle/{brand}/{model}")
def get_vehicle(brand: str, model: str):
    return get_vehicle_details(db_connection, brand, model)


# ============================================================================
# MARKET INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/market/insights")
def get_market_insights(
    brand: str,
    model: str,
    year: int,
    city: str,
    fuel: str | None = None,
    transmission: str | None = None
):
    """Get market insights for a specific car"""
    try:
        insights = market_intelligence.get_market_insights(
            brand=brand,
            model=model,
            year=year,
            city=city,
            fuel=fuel,
            transmission=transmission
        )
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market insights: {str(e)}")


@app.get("/market/city/{city}")
def get_city_market_overview(city: str):
    """Get overall market overview for a city"""
    try:
        overview = market_intelligence.get_city_market_overview(city)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get city overview: {str(e)}")


@app.get("/market/brand/{brand}")
def get_brand_insights(brand: str, city: str | None = None):
    """Get market insights for a specific brand"""
    try:
        insights = market_intelligence.get_brand_insights(brand, city)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand insights: {str(e)}")


@app.post("/market/compare-cities")
def compare_cities(
    ml_prediction: float,
    brand: str,
    model: str,
    year: int,
    cities: list[str]
):
    """Compare prices across multiple cities"""
    try:
        comparison = pricing_engine.get_price_comparison(
            ml_prediction=ml_prediction,
            brand=brand,
            model=model,
            year=year,
            cities=cities
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare cities: {str(e)}")