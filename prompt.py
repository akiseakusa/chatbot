# INTENT_PROMPT = """
# You are an AI assistant for a restaurant reservation system. Given the user input, identify the intent and extract relevant parameters. Return a JSON object with:
# - intent: one of ["reserve_table", "cancel_reservation", "update_reservation", "prebook_meal", "get_menu", "recommend_restaurant"]
# - parameters: a dictionary with relevant fields (e.g., restaurant_id, date_time, party_size, name, phone, reservation_id, meal_name, cuisine, location)

# User input: "{user_input}"

# Examples:
# Input: "Book a table for 4 at 7 PM at Downtown"
# Output: {"intent": "reserve_table", "parameters": {"party_size": 4, "date_time": "2025-05-20T19:00:00Z", "location": "Downtown"}}

# Input: "What’s the menu at FoodieSpot Downtown?"
# Output: {"intent": "get_menu", "parameters": {"restaurant_id": "R1"}}

# Input: "Recommend an Italian restaurant in Suburb for 6"
# Output: {"intent": "recommend_restaurant", "parameters": {"cuisine": "Italian", "location": "Suburb", "party_size": 6}}

# Provide the JSON output for the given input.
# """

INTENT_PROMPT = """
Analyze the following user input and determine the intent and parameters in JSON format:
User input: "{user_input}"
Return the result in the following format:
{{
  "intent": "<intent>",
  "parameters": {{ "key": "value", ... }}
}}
Possible intents: reserve_table, cancel_reservation, update_reservation, prebook_meal, get_menu, recommend_restaurant

note - result should be in JSON format only, no other text or explanation required.
"""