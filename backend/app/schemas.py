from pydantic import BaseModel


class VehicleInput(BaseModel):

    oem: str

    model: str

    variant: str

    fuel: str

    transmission: str

    body: str

    owner_type: str

    City: str

    state: str

    km: float

    car_age: int

    premium_brand: int

    damage_description: str | None = None

    transaction_type: str = "selling"  # "selling", "buying_resale", "buying_personal"


class PredictionResponse(BaseModel):

    predicted_price: float

    damage_cost: float

    confidence_score: int

    suggested_price: float

    currency: str

    model_version: str

    status: str

    transaction_type: str

    transaction_price: float

    profit_margin: float | None = None

    price_range_min: float | None = None

    price_range_max: float | None = None
    
    # Market Intelligence fields
    market_data_available: bool = False
    
    ml_prediction: float | None = None
    
    market_average: float | None = None
    
    market_median: float | None = None
    
    market_confidence: str | None = None
    
    market_sample_size: int = 0


class PredictionHistoryItem(BaseModel):

    id: int

    brand: str

    model: str

    variant: str

    fuel: str

    transmission: str

    body: str

    owner_type: str

    City: str

    state: str

    km: float

    car_age: int

    premium_brand: int

    predicted_price: float

    created_at: str


class ImageSlotAnalysis(BaseModel):

    slot: str

    filename: str

    content_type: str

    width: int

    height: int


class ImageAnalysisResponse(BaseModel):

    detected_brand: str | None

    detected_model: str | None

    detected_body_type: str | None

    detected_color: str | None

    estimated_year: int | None

    vehicle_category: str | None

    images: list[ImageSlotAnalysis]


class AppMetadata(BaseModel):

    model_version: str

    brands_count: int

    models_count: int

    total_predictions: int

    dataset_version: str