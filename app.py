import streamlit as st
import aiohttp
import json
import asyncio
import uuid
from datetime import datetime
from tools import reserve_table, cancel_reservation, update_reservation, prebook_meal, get_menu, recommend_restaurant
from data.db import init_db
import os
from dotenv import load_dotenv
import logging

# Configure logging to write to both file and console
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_file = "foodiebot.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
logger.info(f"GROQ_API_KEY loaded: {'Set' if groq_api_key else 'Not set'}")

# Define a list of 20 restaurants with varying cuisines, locations, and seating capacities
RESTAURANTS = [
    {"id": "R1", "name": "FoodieSpot Downtown French", "cuisine": "french", "location": "Downtown", "seating_capacity": 50},
    {"id": "R2", "name": "FoodieSpot Downtown American", "cuisine": "american", "location": "Downtown", "seating_capacity": 60},
    {"id": "R3", "name": "FoodieSpot Downtown BBQ", "cuisine": "bbq", "location": "Downtown", "seating_capacity": 40},
    {"id": "R4", "name": "FoodieSpot Midtown Italian", "cuisine": "italian", "location": "Midtown", "seating_capacity": 55},
    {"id": "R5", "name": "FoodieSpot Midtown Mexican", "cuisine": "mexican", "location": "Midtown", "seating_capacity": 45},
    {"id": "R6", "name": "FoodieSpot Uptown Chinese", "cuisine": "chinese", "location": "Uptown", "seating_capacity": 70},
    {"id": "R7", "name": "FoodieSpot Uptown Indian", "cuisine": "indian", "location": "Uptown", "seating_capacity": 50},
    {"id": "R8", "name": "FoodieSpot Riverside Japanese", "cuisine": "japanese", "location": "Riverside", "seating_capacity": 30},
    {"id": "R9", "name": "FoodieSpot Riverside Thai", "cuisine": "thai", "location": "Riverside", "seating_capacity": 35},
    {"id": "R10", "name": "FoodieSpot Suburb Mediterranean", "cuisine": "mediterranean", "location": "Suburb", "seating_capacity": 40},
    {"id": "R11", "name": "FoodieSpot Downtown Vegan", "cuisine": "vegan", "location": "Downtown", "seating_capacity": 25},
    {"id": "R12", "name": "FoodieSpot Midtown Spanish", "cuisine": "spanish", "location": "Midtown", "seating_capacity": 50},
    {"id": "R13", "name": "FoodieSpot Uptown Korean", "cuisine": "korean", "location": "Uptown", "seating_capacity": 45},
    {"id": "R14", "name": "FoodieSpot Riverside German", "cuisine": "german", "location": "Riverside", "seating_capacity": 40},
    {"id": "R15", "name": "FoodieSpot Suburb Greek", "cuisine": "greek", "location": "Suburb", "seating_capacity": 35},
    {"id": "R16", "name": "FoodieSpot Downtown Seafood", "cuisine": "seafood", "location": "Downtown", "seating_capacity": 60},
    {"id": "R17", "name": "FoodieSpot Midtown Steakhouse", "cuisine": "steakhouse", "location": "Midtown", "seating_capacity": 50},
    {"id": "R18", "name": "FoodieSpot Uptown Fusion", "cuisine": "fusion", "location": "Uptown", "seating_capacity": 40},
    {"id": "R19", "name": "FoodieSpot Riverside Vietnamese", "cuisine": "vietnamese", "location": "Riverside", "seating_capacity": 30},
    {"id": "R20", "name": "FoodieSpot Suburb Ethiopian", "cuisine": "ethiopian", "location": "Suburb", "seating_capacity": 35},
]

# Define available tools for the LLM to call
TOOLS = [
    {
        "name": "reserve_table",
        "description": "Reserves a table at a specified restaurant. Requires restaurant_id, date_time, party_size, name, phone, and user_id.",
        "parameters": {
            "restaurant_id": "string",
            "date_time": "string (ISO format, e.g., 2025-05-20T19:00:00Z)",
            "party_size": "integer",
            "name": "string",
            "phone": "string",
            "user_id": "string"
        }
    },
    {
        "name": "cancel_reservation",
        "description": "Cancels an existing reservation. Requires reservation_id.",
        "parameters": {"reservation_id": "string"}
    },
    {
        "name": "update_reservation",
        "description": "Updates an existing reservation. Requires reservation_id, and optionally date_time, party_size, user_id.",
        "parameters": {
            "reservation_id": "string",
            "date_time": "string (optional)",
            "party_size": "integer (optional)",
            "user_id": "string"
        }
    },
    {
        "name": "prebook_meal",
        "description": "Prebooks a meal for a reservation. Requires reservation_id, meal_name, and user_id.",
        "parameters": {
            "reservation_id": "string",
            "meal_name": "string",
            "user_id": "string"
        }
    },
    {
        "name": "get_menu",
        "description": "Retrieves the menu for a specified restaurant. Requires restaurant_id.",
        "parameters": {"restaurant_id": "string"}
    },
    {
        "name": "recommend_restaurant",
        "description": "Recommends restaurants based on cuisine, location, and party_size. All parameters are optional.",
        "parameters": {
            "cuisine": "string (optional)",
            "location": "string (optional)",
            "party_size": "integer (optional)"
        }
    }
]

async def call_groq_llama(prompt, request_id):
    if not groq_api_key:
        logger.error("GROQ_API_KEY is not set. Cannot call Groq API.")
        return ""
    
    logger.info(f"[{request_id}] Calling Groq API for LLaMA inference with prompt: {prompt[:50]}...")
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                status = response.status
                logger.info(f"[{request_id}] API response status: {status}")
                if status != 200:
                    logger.error(f"[{request_id}] API call failed with status {status}")
                    return ""
                data = await response.json()
                logger.info(f"[{request_id}] Groq API response data: {data}")
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Groq API: {str(e)}")
        return ""

async def detect_intent(user_input, conversation_history, request_id):
    # Construct the conversation history for context
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    prompt = f"""
You are a conversational AI for FoodieSpot, a restaurant reservation system. Your task is to analyze the user's input and determine their intent and parameters based on the conversation history.

Conversation History:
{history_text}

Current User Input: "{user_input}"

Available Intents:
- reserve_table
- cancel_reservation
- update_reservation
- prebook_meal
- get_menu
- recommend_restaurant

Return the result in the following JSON format:
{{
  "intent": "<intent>",
  "parameters": {{ "key": "value", ... }}
}}

If parameters are missing, provide default values where appropriate (e.g., party_size=2, date_time="2025-05-20T19:00:00Z", name="Guest", phone="+1234567890"). Use the conversation history to fill in missing details if possible.

Respond with JSON only, no additional text or explanation.
"""
    intent_json = await call_groq_llama(prompt, request_id)
    try:
        return json.loads(intent_json)
    except json.JSONDecodeError as e:
        logger.error(f"[{request_id}] JSON decode error in intent detection: {str(e)}")
        return {"intent": "unknown", "parameters": {}}

async def select_tool(intent_data, conversation_history, request_id):
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    prompt = f"""
You are a conversational AI for FoodieSpot. Based on the detected intent and conversation history, select the appropriate tool to call and provide the parameters.

Conversation History:
{history_text}

Detected Intent and Parameters:
{json.dumps(intent_data, indent=2)}

Available Tools:
{json.dumps(TOOLS, indent=2)}

Select the appropriate tool and provide the parameters to call it. If the intent is "unknown" or parameters are insufficient, you may choose "recommend_restaurant" to suggest restaurants or respond with an error message.

Return the result in the following JSON format:
{{
  "tool": "<tool_name>",
  "parameters": {{ "key": "value", ... }},
  "error": "<error_message>" (optional)
}}

Respond with JSON only, no additional text or explanation.
"""
    tool_json = await call_groq_llama(prompt, request_id)
    try:
        return json.loads(tool_json)
    except json.JSONDecodeError as e:
        logger.error(f"[{request_id}] JSON decode error in tool selection: {str(e)}")
        return {"tool": "recommend_restaurant", "parameters": {}, "error": "Failed to select tool due to invalid response format."}

async def execute_tool(tool_data, request_id):
    tool_name = tool_data.get("tool")
    params = tool_data.get("parameters", {})
    logger.info(f"[{request_id}] Executing tool: {tool_name} with parameters: {params}")

    try:
        if tool_name == "reserve_table":
            return await reserve_table(
                params.get("restaurant_id"),
                params.get("date_time"),
                params.get("party_size"),
                params.get("name"),
                params.get("phone"),
                params.get("user_id")
            )
        elif tool_name == "cancel_reservation":
            return await cancel_reservation(params.get("reservation_id"))
        elif tool_name == "update_reservation":
            return await update_reservation(
                params.get("reservation_id"),
                params.get("date_time"),
                params.get("party_size"),
                params.get("user_id")
            )
        elif tool_name == "prebook_meal":
            return await prebook_meal(
                params.get("reservation_id"),
                params.get("meal_name"),
                params.get("user_id")
            )
        elif tool_name == "get_menu":
            return await get_menu(params.get("restaurant_id"))
        elif tool_name == "recommend_restaurant":
            return await recommend_restaurant(
                params.get("cuisine"),
                params.get("location"),
                params.get("party_size")
            )
        else:
            return "Error: Unknown tool selected."
    except Exception as e:
        logger.error(f"[{request_id}] Error executing tool {tool_name}: {str(e)}")
        return f"Error: {str(e)}"

async def generate_response(user_input, conversation_history, tool_result, request_id):
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    prompt = f"""
You are a conversational AI for FoodieSpot, a restaurant reservation system. Based on the conversation history, user input, and the result of a tool execution, generate a natural language response for the user.

Conversation History:
{history_text}

Current User Input: "{user_input}"

Tool Execution Result:
{tool_result}

Restaurant List (for reference):
{json.dumps(RESTAURANTS, indent=2)}

Generate a concise, natural language response to the user. If the tool result contains an error, explain the issue and suggest next steps. If the result is a recommendation, format it nicely and prompt the user to proceed (e.g., "Would you like to reserve a table at one of these?"). Use the conversation history to maintain context and make the response conversational.

Respond with the text response only, no JSON or additional formatting.
"""
    response = await call_groq_llama(prompt, request_id)
    return response.strip()

async def process_input(user_input, request_id):
    try:
        # Access conversation history from session state
        conversation_history = st.session_state.messages

        # Step 1: Detect intent using LLaMA
        intent_data = await detect_intent(user_input, conversation_history, request_id)
        logger.info(f"[{request_id}] Detected intent: {intent_data}")

        # Step 2: Select the appropriate tool using LLaMA
        tool_data = await select_tool(intent_data, conversation_history, request_id)
        logger.info(f"[{request_id}] Selected tool: {tool_data}")

        # Handle errors from tool selection
        if "error" in tool_data:
            return f"Sorry, I encountered an issue: {tool_data['error']}. Please try rephrasing your request or ask for recommendations."

        # Step 3: Execute the selected tool
        tool_result = await execute_tool(tool_data, request_id)
        logger.info(f"[{request_id}] Tool result: {tool_result}")

        # Step 4: Generate a natural language response using LLaMA
        response = await generate_response(user_input, conversation_history, tool_result, request_id)
        logger.info(f"[{request_id}] Generated response: {response}")

        return response
    except Exception as e:
        logger.error(f"[{request_id}] Error processing input: {str(e)}")
        return f"Sorry, an error occurred: {str(e)}. Please try again."

# Helper function to run async tasks in Streamlit
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result

def main():
    st.title("FoodieSpot Reservation Bot")
    st.write("Chat with our AI to book tables, view menus, or get recommendations!")

    # Initialize MongoDB
    init_db()

    # Assign a user ID for the session
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"U{len(st.session_state.get('messages', [])) + 1}"

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! Welcome to FoodieSpot. How can I help you today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Use a more robust check to prevent duplicate processing
    if "last_processed_input" not in st.session_state:
        st.session_state.last_processed_input = None
    if "last_processed_time" not in st.session_state:
        st.session_state.last_processed_time = 0
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "processed_requests" not in st.session_state:
        st.session_state.processed_requests = set()

    user_input = st.chat_input("Type your message...")
    current_time = datetime.now().timestamp()
    request_id = str(uuid.uuid4())
    if user_input and not st.session_state.is_processing and (user_input != st.session_state.last_processed_input or (current_time - st.session_state.last_processed_time > 2)) and request_id not in st.session_state.processed_requests:
        st.session_state.is_processing = True
        st.session_state.last_processed_input = user_input
        st.session_state.last_processed_time = current_time
        st.session_state.processed_requests.add(request_id)
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            response = run_async(process_input(user_input, request_id))
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.is_processing = False

if __name__ == "__main__":
    main()