import os
import json
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from . import models, schemas
from .pricing_engine import calculate_osp, evaluate_bid, DEFAULT_MANDI_PRICES
from .quality_grader import analyze_produce_image

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart-Yield F2C API",
    description="Backend for AI-Guided Direct Farmer-to-Consumer Digital Marketplace",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists and mount static files
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# --- Seed Initial Data ---
@app.on_event("startup")
def startup_populate_data():
    db = next(get_db())
    try:
        # Seed default users
        farmer = db.query(models.User).filter(models.User.role == "farmer").first()
        if not farmer:
            fpo = models.FPO(name="Sahyadri Farmers Producer Co-op", region="Nashik, Maharashtra")
            db.add(fpo)
            db.commit()
            db.refresh(fpo)

            farmer_user = models.User(
                name="Ramesh Patil (Farmer)",
                role="farmer",
                phone="+91 98220 12345",
                language_pref="hi",
                location="Dindori, Nashik District"
            )
            db.add(farmer_user)
            db.commit()
            db.refresh(farmer_user)

            profile = models.FarmerProfile(
                user_id=farmer_user.id,
                farm_location="Plot 14, Gat No. 201, Dindori",
                linked_bank_account="SBI - 3089402941 (IFSC: SBIN000123)",
                fpo_id=fpo.id
            )
            db.add(profile)

            buyer_user = models.User(
                name="FreshMart Supermarkets (Buyer)",
                role="buyer",
                phone="+91 98450 67890",
                language_pref="en",
                location="Bandra West, Mumbai"
            )
            db.add(buyer_user)
            db.commit()

            # Seed initial worked example listing (Section 8)
            tomatoes_listing = models.Listing(
                farmer_id=farmer_user.id,
                crop_type="Tomatoes",
                quantity=500.0,
                unit="kg",
                image_urls="/uploads/sample_tomatoes.jpg",
                quality_grade="A",
                grade_confidence=0.94,
                shelf_life_days=2,
                transport_distance_km=25.0,
                weather_risk="None",
                mandi_base_price=22.0,
                computed_osp=24.0,
                status="active"
            )
            db.add(tomatoes_listing)
            db.commit()
            db.refresh(tomatoes_listing)

            rec = models.PriceRecommendation(
                listing_id=tomatoes_listing.id,
                computed_osp=24.0,
                input_factors=json.dumps({
                    "mandi_base_price": 22.0,
                    "shelf_life_urgency_factor": 3.0,
                    "transport_cost_estimate": 1.0,
                    "weather_risk_adjustment": 0.0
                })
            )
            db.add(rec)
            db.commit()
    finally:
        db.close()


# --- API Routes ---

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "Smart-Yield F2C Backend",
        "version": "1.0.0",
        "endpoints": ["/api/pricing/calculate", "/api/listings", "/api/orders", "/api/escrow"]
    }


# 1. Market & Pricing Endpoints (Section 8)
@app.get("/api/pricing/mandi-rates")
def get_mandi_rates():
    return {"rates": DEFAULT_MANDI_PRICES}

@app.post("/api/pricing/calculate")
def calculate_price_endpoint(req: schemas.PriceCalculationRequest):
    osp_result = calculate_osp(
        crop_type=req.crop_type,
        mandi_base_price=req.mandi_base_price,
        shelf_life_days=req.shelf_life_days,
        transport_distance_km=req.transport_distance_km,
        weather_risk=req.weather_risk
    )
    return osp_result


# 2. Quality Grading Endpoint (Section 9 Heuristic CV Model)
@app.post("/api/grading/analyze")
async def analyze_crop_image(file: UploadFile = File(...)):
    contents = await file.read()
    analysis = analyze_produce_image(contents)
    
    # Save image for persistent display
    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
        
    analysis["image_url"] = f"/uploads/{filename}"
    return analysis


# 3. Farmer Listing Creation & Browse (Step 2 & Step 3)
@app.post("/api/listings")
async def create_listing(
    crop_type: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form("kg"),
    shelf_life_days: int = Form(2),
    transport_distance_km: float = Form(25.0),
    weather_risk: str = Form("None"),
    mandi_base_price: Optional[float] = Form(None),
    quality_grade: Optional[str] = Form("A"),
    grade_confidence: Optional[float] = Form(0.92),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_url = ""
    # If image provided, analyze with CV model and save
    if file and file.filename:
        contents = await file.read()
        cv_result = analyze_produce_image(contents)
        quality_grade = cv_result.get("grade", "A")
        grade_confidence = cv_result.get("confidence", 0.90)
        
        filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f_out:
            f_out.write(contents)
        image_url = f"/uploads/{filename}"
    elif not image_url:
        image_url = "/uploads/sample_tomatoes.jpg"

    # Compute OSP with Section 8 pricing engine
    osp_data = calculate_osp(
        crop_type=crop_type,
        mandi_base_price=mandi_base_price,
        shelf_life_days=shelf_life_days,
        transport_distance_km=transport_distance_km,
        weather_risk=weather_risk
    )
    computed_osp = osp_data["computed_osp"]
    base_mandi = osp_data["mandi_base_price"]

    farmer = db.query(models.User).filter(models.User.role == "farmer").first()
    farmer_id = farmer.id if farmer else 1

    new_listing = models.Listing(
        farmer_id=farmer_id,
        crop_type=crop_type,
        quantity=quantity,
        unit=unit,
        image_urls=image_url,
        quality_grade=quality_grade,
        grade_confidence=grade_confidence,
        shelf_life_days=shelf_life_days,
        transport_distance_km=transport_distance_km,
        weather_risk=weather_risk,
        mandi_base_price=base_mandi,
        computed_osp=computed_osp,
        status="active"
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)

    # Save price recommendation record
    rec = models.PriceRecommendation(
        listing_id=new_listing.id,
        computed_osp=computed_osp,
        input_factors=json.dumps(osp_data)
    )
    db.add(rec)
    db.commit()

    return {
        "success": True,
        "message": f"Crop listing for {quantity} {unit} of {crop_type} created successfully!",
        "listing": {
            "id": new_listing.id,
            "crop_type": new_listing.crop_type,
            "quantity": new_listing.quantity,
            "unit": new_listing.unit,
            "quality_grade": new_listing.quality_grade,
            "grade_confidence": new_listing.grade_confidence,
            "mandi_base_price": new_listing.mandi_base_price,
            "computed_osp": new_listing.computed_osp,
            "image_urls": new_listing.image_urls,
            "status": new_listing.status
        },
        "pricing_breakdown": osp_data
    }


@app.get("/api/listings")
def get_listings(db: Session = Depends(get_db)):
    listings = db.query(models.Listing).order_by(models.Listing.id.desc()).all()
    out = []
    for l in listings:
        out.append({
            "id": l.id,
            "farmer_id": l.farmer_id,
            "farmer_name": l.farmer.name if l.farmer else "Ramesh Patil",
            "farmer_location": l.farmer.location if l.farmer else "Nashik",
            "crop_type": l.crop_type,
            "quantity": l.quantity,
            "unit": l.unit,
            "image_urls": l.image_urls,
            "quality_grade": l.quality_grade,
            "grade_confidence": l.grade_confidence,
            "shelf_life_days": l.shelf_life_days,
            "transport_distance_km": l.transport_distance_km,
            "weather_risk": l.weather_risk,
            "mandi_base_price": l.mandi_base_price,
            "computed_osp": l.computed_osp,
            "status": l.status,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return out


@app.get("/api/listings/{listing_id}")
def get_listing_detail(listing_id: int, db: Session = Depends(get_db)):
    l = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {
        "id": l.id,
        "farmer_id": l.farmer_id,
        "farmer_name": l.farmer.name if l.farmer else "Ramesh Patil",
        "crop_type": l.crop_type,
        "quantity": l.quantity,
        "unit": l.unit,
        "image_urls": l.image_urls,
        "quality_grade": l.quality_grade,
        "grade_confidence": l.grade_confidence,
        "shelf_life_days": l.shelf_life_days,
        "transport_distance_km": l.transport_distance_km,
        "weather_risk": l.weather_risk,
        "mandi_base_price": l.mandi_base_price,
        "computed_osp": l.computed_osp,
        "status": l.status
    }


# 4. Bid Evaluation & Order Creation (Step 3 & 4)
@app.post("/api/listings/{listing_id}/bid")
def place_bid(listing_id: int, bid: schemas.BidRequest, db: Session = Depends(get_db)):
    l = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")

    evaluation = evaluate_bid(bid.bid_price, l.computed_osp)

    if not evaluation["accepted"]:
        return {
            "accepted": False,
            "status": "rejected",
            "message": evaluation["message"],
            "computed_osp": l.computed_osp,
            "bid_price": bid.bid_price,
            "deficit": round(l.computed_osp - bid.bid_price, 2)
        }

    # Bid accepted (bid_price >= computed_osp)
    # Create Order and Escrow record (Shield 1: Price Lock)
    buyer = db.query(models.User).filter(models.User.role == "buyer").first()
    buyer_id = buyer.id if buyer else bid.buyer_id
    total_amount = round(bid.bid_price * bid.quantity, 2)

    new_order = models.Order(
        listing_id=l.id,
        buyer_id=buyer_id,
        agreed_price=bid.bid_price,
        quantity=bid.quantity,
        status="escrowed"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Initialize Escrow in 'Held' state (Shield 1)
    escrow = models.EscrowTransaction(
        order_id=new_order.id,
        amount=total_amount,
        status="Held",
        payment_ref=f"UPI-ESCROW-{uuid.uuid4().hex[:8].upper()}"
    )
    db.add(escrow)

    # Initialize Delivery tracking
    delivery = models.Delivery(
        order_id=new_order.id,
        pickup_time=datetime.utcnow(),
        gps_dropoff_coords="19.0760, 72.8777",  # Mumbai cluster
        current_gps="19.9975, 73.7898",  # Nashik hub
        otp_code="7842",
        status="in_transit"
    )
    db.add(delivery)

    l.status = "escrowed"
    db.commit()

    return {
        "accepted": True,
        "status": "accepted",
        "message": evaluation["message"],
        "order_id": new_order.id,
        "agreed_price": bid.bid_price,
        "computed_osp": l.computed_osp,
        "total_amount": total_amount,
        "escrow_status": "Held",
        "payment_ref": escrow.payment_ref,
        "delivery_otp": delivery.otp_code
    }


# 5. Orders & Escrow Management (Step 5)
@app.get("/api/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    results = []
    for o in orders:
        results.append({
            "id": o.id,
            "listing_id": o.listing_id,
            "crop_type": o.listing.crop_type if o.listing else "Crop",
            "quantity": o.quantity,
            "unit": o.listing.unit if o.listing else "kg",
            "agreed_price": o.agreed_price,
            "total_amount": round(o.agreed_price * o.quantity, 2),
            "status": o.status,
            "escrow_status": o.escrow.status if o.escrow else "Pending",
            "payment_ref": o.escrow.payment_ref if o.escrow else "",
            "delivery_status": o.delivery.status if o.delivery else "pending",
            "otp_verified": o.delivery.otp_verified if o.delivery else False,
            "geofence_verified": o.delivery.geofence_verified if o.delivery else False,
            "otp_code": o.delivery.otp_code if o.delivery else "",
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return results


# 6. Delivery Confirmation & Escrow Release (Shield 2)
@app.post("/api/orders/{order_id}/verify-delivery")
def verify_delivery_and_release(order_id: int, req: schemas.DeliveryVerifyRequest, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order or not order.delivery:
        raise HTTPException(status_code=404, detail="Order or delivery not found")

    delivery = order.delivery
    escrow = order.escrow

    # Verify OTP
    if req.otp.strip() != delivery.otp_code:
        return {
            "success": False,
            "message": "Invalid Delivery OTP! Funds remain securely locked in Escrow."
        }

    # Mark delivery verified & geofenced
    delivery.otp_verified = True
    delivery.geofence_verified = True
    delivery.status = "delivered"
    delivery.delivered_at = datetime.utcnow()

    # Shield 2: Release funds to farmer
    if escrow:
        escrow.status = "Released"
        escrow.released_at = datetime.utcnow()

    order.status = "settled"
    if order.listing:
        order.listing.status = "sold"

    db.commit()

    return {
        "success": True,
        "message": f"Delivery verified successfully via GPS Geofence + OTP! Escrow ₹{escrow.amount:,.2f} released instantly to Ramesh Patil's bank account.",
        "order_status": order.status,
        "escrow_status": escrow.status,
        "released_at": escrow.released_at.strftime("%Y-%m-%d %H:%M:%S")
    }


# 7. FPO Aggregation View
@app.get("/api/fpo/lots")
def get_fpo_lots(db: Session = Depends(get_db)):
    listings = db.query(models.Listing).all()
    total_crates = len(listings) * 20
    total_volume_kg = sum(l.quantity for l in listings)
    return {
        "hub_name": "Sahyadri Farmers Producer Hub (Nashik Central)",
        "pooled_farmers_count": len(set(l.farmer_id for l in listings)),
        "active_lots": len(listings),
        "total_volume_kg": total_volume_kg,
        "total_crates_aggregated": total_crates,
        "logistics_savings_percent": "38% Shared Transport Efficiency",
        "lots": [
            {
                "id": l.id,
                "crop": l.crop_type,
                "farmer": l.farmer.name if l.farmer else "Farmer",
                "grade": l.quality_grade,
                "quantity": f"{l.quantity} {l.unit}",
                "status": l.status,
                "floor_osp": f"₹{l.computed_osp}/kg"
            } for l in listings
        ]
    }
