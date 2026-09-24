"""
Section 8: Dynamic Pricing Engine — Formula & Worked Example

OSP = MandiBasePrice 
      + w1 * ShelfLifeUrgencyFactor 
      - w2 * TransportCostEstimate 
      + w3 * WeatherRiskAdjustment

Exact Worked Example from Section 8:
Crop: Tomatoes
Mandi Base Price: ₹22/kg
Shelf-life urgency (high, 2 days left): +₹3/kg
Transport cost estimate: -₹1/kg
Weather risk (none): +₹0/kg
Computed OSP (protected floor): ₹24/kg

Bids:
Buyer accepted bid: ₹28/kg (accepted, >= floor)
Rejected bid: ₹19/kg (rejected, < floor)
"""

DEFAULT_MANDI_PRICES = {
    "Tomatoes": 22.0,
    "Onions": 18.0,
    "Potatoes": 15.0,
    "Cabbage": 14.0,
    "Cauliflower": 20.0,
    "Green Chillies": 45.0,
    "Wheat": 24.0,
    "Paddy/Rice": 22.0,
    "Soybean": 42.0,
    "Cotton": 65.0
}

def calculate_osp(
    crop_type: str,
    mandi_base_price: float = None,
    shelf_life_days: int = 2,
    transport_distance_km: float = 25.0,
    weather_risk: str = "None"
) -> dict:
    # 1. Base price
    if mandi_base_price is None or mandi_base_price <= 0:
        base_price = DEFAULT_MANDI_PRICES.get(crop_type, 22.0)
    else:
        base_price = float(mandi_base_price)

    # 2. Shelf-life urgency factor (w1 = 0.15 normalized, or exact formula mapping)
    # High urgency (1-2 days left) gives +3 for Tomatoes at base ₹22
    # Standard linear mapping calibrated to match Section 8 exact values
    if shelf_life_days <= 2:
        shelf_life_factor = 3.0
    elif shelf_life_days <= 4:
        shelf_life_factor = 1.5
    elif shelf_life_days <= 7:
        shelf_life_factor = 0.5
    else:
        shelf_life_factor = 0.0

    # 3. Transport cost estimate (w2 = 0.10)
    # For ~25 km, estimate is ₹1.0 / kg to match Section 8
    transport_cost = round(max(0.5, (transport_distance_km / 25.0) * 1.0), 2)

    # 4. Weather risk adjustment (w3 = 0.05)
    # "None" -> 0, "Low" -> +1, "Moderate" -> +2, "High" -> +3.5
    weather_risk_map = {
        "None": 0.0,
        "Low": 1.0,
        "Moderate": 2.0,
        "High": 3.5
    }
    weather_adjustment = weather_risk_map.get(weather_risk, 0.0)

    # Computed OSP (Protected Floor Price)
    computed_osp = round(base_price + shelf_life_factor - transport_cost + weather_adjustment, 2)

    return {
        "crop_type": crop_type,
        "mandi_base_price": base_price,
        "shelf_life_urgency_factor": shelf_life_factor,
        "transport_cost_estimate": transport_cost,
        "weather_risk_adjustment": weather_adjustment,
        "computed_osp": computed_osp,
        "explanation": {
            "formula": "OSP = MandiBasePrice + ShelfLifeUrgency - TransportCost + WeatherRisk",
            "base": f"₹{base_price:.2f}/kg",
            "shelf_life": f"+₹{shelf_life_factor:.2f}/kg ({shelf_life_days} days left)",
            "transport": f"-₹{transport_cost:.2f}/kg ({transport_distance_km:.1f} km distance)",
            "weather": f"+₹{weather_adjustment:.2f}/kg ({weather_risk} risk)",
            "total_osp": f"₹{computed_osp:.2f}/kg (Protected Floor Price)"
        }
    }

def evaluate_bid(bid_price: float, computed_osp: float) -> dict:
    if bid_price >= computed_osp:
        return {
            "accepted": True,
            "status": "accepted",
            "message": f"Bid ₹{bid_price:.2f}/kg accepted! Price meets or exceeds the protected floor price of ₹{computed_osp:.2f}/kg."
        }
    else:
        diff = round(computed_osp - bid_price, 2)
        return {
            "accepted": False,
            "status": "rejected",
            "message": f"Bid ₹{bid_price:.2f}/kg rejected! Below the protected floor price of ₹{computed_osp:.2f}/kg (Deficit: ₹{diff:.2f}/kg)."
        }
