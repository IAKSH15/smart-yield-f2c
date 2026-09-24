from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    role: str = "farmer"
    phone: Optional[str] = None
    language_pref: str = "en"
    location: str = "Nashik, Maharashtra"

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class PriceCalculationRequest(BaseModel):
    crop_type: str
    mandi_base_price: float = 22.0
    shelf_life_days: int = 2
    transport_distance_km: float = 25.0
    weather_risk: str = "None"  # "None", "Low", "Moderate", "High"

class PriceCalculationResponse(BaseModel):
    crop_type: str
    mandi_base_price: float
    shelf_life_urgency_factor: float
    transport_cost_estimate: float
    weather_risk_adjustment: float
    computed_osp: float
    explanation: dict

class ListingCreate(BaseModel):
    farmer_id: int = 1
    crop_type: str
    quantity: float
    unit: str = "kg"
    shelf_life_days: int = 2
    transport_distance_km: float = 25.0
    weather_risk: str = "None"
    mandi_base_price: Optional[float] = None
    image_urls: Optional[str] = ""

class ListingOut(BaseModel):
    id: int
    farmer_id: int
    crop_type: str
    quantity: float
    unit: str
    image_urls: str
    quality_grade: str
    grade_confidence: float
    shelf_life_days: int
    transport_distance_km: float
    weather_risk: str
    mandi_base_price: float
    computed_osp: float
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class BidRequest(BaseModel):
    buyer_id: int = 2
    bid_price: float
    quantity: float

class BidResponse(BaseModel):
    status: str  # accepted or rejected
    message: str
    order_id: Optional[int] = None
    agreed_price: float
    computed_osp: float

class EscrowActionRequest(BaseModel):
    action: str  # lock, release

class DeliveryVerifyRequest(BaseModel):
    otp: str
    current_gps: Optional[str] = None
