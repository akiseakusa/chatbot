import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_db():
    print("db called")
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["restaurant_bot"]

def init_db():
    db = get_db()
    # Create collections if they don't exist
    collections = db.list_collection_names()
    if "restaurants" not in collections:
        db.create_collection("restaurants")
    if "reservations" not in collections:
        db.create_collection("reservations")
    if "menu" not in collections:
        db.create_collection("menu")
    if "users" not in collections:
        db.create_collection("users")

    # Ensure indexes for performance
    db.restaurants.create_index([("restaurant_id", 1)], unique=True)
    db.restaurants.create_index([("location", 1)])
    db.restaurants.create_index([("cuisine", 1)])
    db.reservations.create_index([("reservation_id", 1)], unique=True)
    db.reservations.create_index([("user_id", 1)])
    db.menu.create_index([("meal_id", 1)], unique=True)
    db.menu.create_index([("restaurant_id", 1)])
    db.users.create_index([("user_id", 1)], unique=True)
    db.users.create_index([("reservations.reservation_id", 1)])