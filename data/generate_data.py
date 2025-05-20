from db import get_db
from datetime import datetime
import random

def generate_data():
    db = get_db()
    # Only drop collections that we will repopulate
    db.restaurants.drop()
    db.menu.drop()

    locations = ["Downtown", "Suburb", "Midtown", "Uptown", "Riverside"]
    cuisines = ["Italian", "Mexican", "Chinese", "Indian", "American", "French", "Japanese", "Thai", "Mediterranean", "BBQ"]
    menu_items = {
        "Italian": [("Pizza", "main", 15.99, True), ("Pasta", "main", 12.99, True), ("Tiramisu", "dessert", 6.99, True)],
        "Mexican": [("Tacos", "main", 10.99, True), ("Guacamole", "starter", 7.99, False), ("Churros", "dessert", 5.99, True)],
        "Chinese": [("Dumplings", "starter", 8.99, True), ("Kung Pao Chicken", "main", 14.99, True), ("Mango Pudding", "dessert", 5.99, True)],
        "Indian": [("Butter Chicken", "main", 13.99, True), ("Naan", "side", 3.99, False), ("Gulab Jamun", "dessert", 4.99, True)],
        "American": [("Burger", "main", 11.99, True), ("Fries", "side", 4.99, False), ("Milkshake", "dessert", 6.99, True)],
        "French": [("Croissant", "starter", 4.99, False), ("Coq au Vin", "main", 16.99, True), ("Creme Brulee", "dessert", 7.99, True)],
        "Japanese": [("Sushi", "main", 18.99, True), ("Miso Soup", "starter", 3.99, False), ("Mochi", "dessert", 5.99, True)],
        "Thai": [("Pad Thai", "main", 12.99, True), ("Spring Rolls", "starter", 6.99, True), ("Mango Sticky Rice", "dessert", 6.99, True)],
        "Mediterranean": [("Hummus", "starter", 7.99, True), ("Falafel", "main", 10.99, True), ("Baklava", "dessert", 5.99, True)],
        "BBQ": [("Ribs", "main", 19.99, True), ("Coleslaw", "side", 4.99, False), ("Brownie", "dessert", 5.99, True)]
    }

    for i in range(50):
        cuisine = random.choice(cuisines)
        location = random.choice(locations)
        restaurant_id = f"R{i+1}"
        tables = [
            {
                "table_id": f"T{j+1}",
                "capacity": random.choice([2, 4, 6, 8]),
                "price": random.choice([2, 4, 6, 8]) * 2.0,  # $2 per person
                "availability": [{"date_time": "2025-05-20T19:00:00Z", "status": "available"}]
            } for j in range(random.randint(5, 15))
        ]
        db.restaurants.insert_one({
            "restaurant_id": restaurant_id,
            "name": f"FoodieSpot {location} {cuisine}",
            "location": location,
            "cuisine": cuisine,
            "seating_capacity": sum(t["capacity"] for t in tables),
            "tables": tables
        })
        for name, category, price, prebook in menu_items.get(cuisine, [("Generic Dish", "main", 10.99, True)]):
            db.menu.insert_one({
                "meal_id": f"M{restaurant_id}{name}",
                "restaurant_id": restaurant_id,
                "name": name,
                "category": category,
                "price": price,
                "prebook_allowed": prebook
            })

if __name__ == "__main__":
    generate_data()