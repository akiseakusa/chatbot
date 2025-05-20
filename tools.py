from data.db import get_db
from datetime import datetime

async def reserve_table(restaurant_id, date_time, party_size, name, phone, user_id):
    db = get_db()
    try:
        restaurant = db.restaurants.find_one({"restaurant_id": restaurant_id})
        if not restaurant:
            return "Restaurant not found."

        # Find available table
        selected_table = None
        for table in restaurant["tables"]:
            for avail in table["availability"]:
                if avail["date_time"] == date_time and avail["status"] == "available" and table["capacity"] >= int(party_size):
                    selected_table = table
                    break
            if selected_table:
                break

        if not selected_table:
            other_restaurants = db.restaurants.find({"location": {"$ne": restaurant["location"]}, "tables.capacity": {"$gte": int(party_size)}})
            other_restaurants_list = list(other_restaurants)
            if len(other_restaurants_list) > 0:
                alt = other_restaurants_list[0]
                return f"No tables available at {restaurant['location']}. Try {alt['name']} at {alt['location']}?"
            return "No tables available. Try another time or location."

        table_price = selected_table["price"]
        reservation_id = f"RES{int(datetime.now().timestamp())}"

        # Check if user exists; if not, create a new user
        user = db.users.find_one({"user_id": user_id})
        if not user:
            db.users.insert_one({
                "user_id": user_id,
                "phone_number": phone,
                "email_id": f"{user_id.lower()}@example.com",
                "reservations": []
            })

        # Add reservation details to the user's reservations array
        reservation_details = {
            "reservation_id": reservation_id,
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant["name"],
            "table_id": selected_table["table_id"],
            "table_price": table_price,
            "party_size": int(party_size),
            "date_time": date_time,
            "prebooked_meals": []
        }
        db.users.update_one(
            {"user_id": user_id},
            {"$push": {"reservations": reservation_details}}
        )

        # Add minimal reservation data to reservations collection
        db.reservations.insert_one({
            "reservation_id": reservation_id,
            "user_id": user_id,
            "status": "confirmed"
        })

        # Update table availability
        db.restaurants.update_one(
            {"restaurant_id": restaurant_id, "tables.table_id": selected_table["table_id"]},
            {"$set": {"tables.$.availability.$[avail].status": "booked"}},
            array_filters=[{"avail.date_time": date_time}]
        )

        return f"Table reserved at {restaurant['name']}! Reservation ID: {reservation_id}. Table price: ${table_price:.2f}"

    except Exception as e:
        return f"Error: {str(e)}"

async def cancel_reservation(reservation_id):
    db = get_db()
    try:
        reservation = db.reservations.find_one({"reservation_id": reservation_id})
        if not reservation:
            return "Reservation not found."

        user_id = reservation["user_id"]
        user = db.users.find_one({"user_id": user_id})
        if not user:
            return "User not found."

        # Find the reservation in the user's reservations array
        reservation_details = next((r for r in user["reservations"] if r["reservation_id"] == reservation_id), None)
        if not reservation_details:
            return "Reservation details not found in user profile."

        # Update reservation status in reservations collection
        db.reservations.update_one(
            {"reservation_id": reservation_id},
            {"$set": {"status": "canceled"}}
        )

        # Update table availability in restaurants collection
        db.restaurants.update_one(
            {"restaurant_id": reservation_details["restaurant_id"], "tables.table_id": reservation_details["table_id"]},
            {"$set": {"tables.$.availability.$[avail].status": "available"}},
            array_filters=[{"avail.date_time": reservation_details["date_time"]}]
        )

        return "Reservation canceled."
    except Exception as e:
        return f"Error: {str(e)}"

async def update_reservation(reservation_id, date_time, party_size, user_id):
    db = get_db()
    try:
        user = db.users.find_one({"user_id": user_id})
        if not user:
            return "User not found."

        reservation_details = next((r for r in user["reservations"] if r["reservation_id"] == reservation_id), None)
        if not reservation_details:
            return "Reservation not found in user profile."

        # Cancel old reservation
        await cancel_reservation(reservation_id)
        # Reserve new table
        result = await reserve_table(
            reservation_details["restaurant_id"], date_time, party_size,
            user["phone_number"], user["phone_number"], user_id
        )
        return result
    except Exception as e:
        return f"Error: {str(e)}"

async def prebook_meal(reservation_id, meal_name, user_id):
    db = get_db()
    try:
        user = db.users.find_one({"user_id": user_id})
        if not user:
            return "User not found."

        reservation_details = next((r for r in user["reservations"] if r["reservation_id"] == reservation_id), None)
        if not reservation_details:
            return "Reservation not found in user profile."

        meal = db.menu.find_one({"name": {"$regex": meal_name, "$options": "i"}, "restaurant_id": reservation_details["restaurant_id"]})
        if not meal:
            return "Meal not found."
        if not meal["prebook_allowed"]:
            return f"{meal['name']} cannot be pre-booked."

        # Update the user's reservations array with the prebooked meal
        db.users.update_one(
            {"user_id": user_id, "reservations.reservation_id": reservation_id},
            {"$push": {"reservations.$.prebooked_meals": meal["name"]}}
        )

        return f"{meal['name']} added to your reservation."
    except Exception as e:
        return f"Error: {str(e)}"

async def get_menu(restaurant_id):
    db = get_db()
    try:
        restaurant = db.restaurants.find_one({"restaurant_id": restaurant_id})
        if not restaurant:
            return "Restaurant not found."
        menu_items = db.menu.find({"restaurant_id": restaurant_id})
        menu_text = ", ".join(
            f"{item['name']} ({item['category']}) - ${item['price']}"
            f"{' (Pre-bookable)' if item['prebook_allowed'] else ''}"
            for item in menu_items
        )
        return f"Menu for {restaurant['name']}: {menu_text}"
    except Exception as e:
        return f"Error: {str(e)}"

async def recommend_restaurant(cuisine, location, party_size):
    db = get_db()
    try:
        restaurants = db.restaurants.find({
            "cuisine": {"$regex": cuisine or "", "$options": "i"},
            "location": {"$regex": location or "", "$options": "i"},
            "tables.capacity": {"$gte": int(party_size)}
        }).limit(3)
        restaurants_list = list(restaurants)
        if len(restaurants_list) == 0:
            return "No restaurants match your preferences. Try another cuisine or location."
        recs = [f"{r['name']} ({r['cuisine']}) at {r['location']}" for r in restaurants_list]
        return "Recommended restaurants: " + ", ".join(recs)
    except Exception as e:
        return f"Error: {str(e)}"