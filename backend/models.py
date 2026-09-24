from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="farmer")  # farmer, buyer, fpo_admin
    phone = Column(String, nullable=True)
    language_pref = Column(String, default="en")
    location = Column(String, default="Nashik, Maharashtra")
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    listings = relationship("Listing", back_populates="farmer")
    orders = relationship("Order", back_populates="buyer")

class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    farm_location = Column(String, default="Nashik Rural, Block 4")
    linked_bank_account = Column(String, default="HDFC0001234 - ****4321")
    fpo_id = Column(Integer, ForeignKey("fpos.id"), nullable=True)

    user = relationship("User", back_populates="farmer_profile")
    fpo = relationship("FPO", back_populates="members")

class FPO(Base):
    __tablename__ = "fpos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)

    members = relationship("FarmerProfile", back_populates="fpo")

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    crop_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)  # in kg or quintal
    unit = Column(String, default="kg")
    image_urls = Column(Text, default="")  # JSON or comma-separated
    quality_grade = Column(String, default="Pending")  # A, B, C, Pending
    grade_confidence = Column(Float, default=0.0)
    shelf_life_days = Column(Integer, default=5)
    transport_distance_km = Column(Float, default=25.0)
    weather_risk = Column(String, default="None")  # None, Low, Moderate, High
    mandi_base_price = Column(Float, default=22.0)
    computed_osp = Column(Float, default=24.0)
    status = Column(String, default="active")  # active, escrowed, sold, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("User", back_populates="listings")
    price_recommendation = relationship("PriceRecommendation", back_populates="listing", uselist=False)
    orders = relationship("Order", back_populates="listing")

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop_type = Column(String, nullable=False)
    region = Column(String, nullable=False)
    mandi_price = Column(Float, nullable=False)
    date = Column(String, nullable=False)

class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), unique=True)
    computed_osp = Column(Float, nullable=False)
    input_factors = Column(Text, default="{}")  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="price_recommendation")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    agreed_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String, default="placed")  # placed, escrowed, delivered, settled, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="orders")
    buyer = relationship("User", back_populates="orders")
    escrow = relationship("EscrowTransaction", back_populates="order", uselist=False)
    delivery = relationship("Delivery", back_populates="order", uselist=False)

class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    amount = Column(Float, nullable=False)
    status = Column(String, default="Pending")  # Pending, Held, Released, Disputed
    payment_ref = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="escrow")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    pickup_time = Column(DateTime, nullable=True)
    gps_dropoff_coords = Column(String, default="19.9975, 73.7898")
    current_gps = Column(String, default="19.9975, 73.7898")
    otp_code = Column(String, default="7842")
    otp_verified = Column(Boolean, default=False)
    geofence_verified = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, picked_up, in_transit, delivered
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="delivery")
