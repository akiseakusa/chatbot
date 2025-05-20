FoodieSpot Reservation Bot

A conversational AI system for FoodieSpot, enabling table reservations, cancellations, updates, meal pre-booking, and restaurant recommendations across 50 locations. Built with Python, Streamlit, Grok 3 (xAI API), and MongoDB, deployed on GCP using Docker.

Setup Instructionsa





Prerequisites:





Docker, gcloud CLI, kubectl.



GCP project with Artifact Registry and GKE.



xAI API key (https://x.ai/api).



MongoDB Atlas or local MongoDB.



Clone Repository:

git clone [repository_url]
cd restaurant_bot



Set Environment Variables:





Create .env with XAI_API_KEY=your_key.



Generate Data:

python data/generate_data.py



Build and Deploy:

docker build -t restaurant-bot .
docker tag restaurant-bot us-central1-docker.pkg.dev/[PROJECT_ID]/restaurant-bot-repo/bot:latest
docker push us-central1-docker.pkg.dev/[PROJECT_ID]/restaurant-bot-repo/bot:latest
gcloud container clusters create restaurant-bot-cluster --region=us-central1 --num-nodes=3
kubectl apply -f k8s/deployment.yml



Access:





Get the external IP: kubectl get services restaurant-bot.



Visit http://[EXTERNAL-IP]:8501.

Prompt Engineering





Intent Detection: Uses a structured prompt (prompt.py) to map user input to intents (e.g., reserve_table, recommend_restaurant) and extract parameters.



Conversation Design:





Clear, concise responses with fallbacks (e.g., alternative locations).



Handles edge cases (e.g., unavailable tables, invalid inputs).



Example Prompt:

User: "Book a table for 4 at 7 PM at Downtown"
Output: {"intent": "reserve_table", "parameters": {"party_size": 4, "date_time": "2025-05-20T19:00:00Z", "location": "Downtown"}}

Example Conversations





Reservation:

User: Book a table for 4 at 7 PM at Downtown
Bot: Table reserved at FoodieSpot Downtown Italian! Reservation ID: RES1234567890



Recommendation:

User: Recommend an Italian restaurant in Suburb for 6
Bot: Recommended: FoodieSpot Suburb Italian, FoodieSpot Suburb Mediterranean



Menu Inquiry:

User: What’s the menu at FoodieSpot Downtown?
Bot: Menu: Pizza (main) - $15.99 (Pre-bookable), Pasta (main) - $12.99 (Pre-bookable), Tiramisu (dessert) - $6.99 (Pre-bookable)



Edge Case:

User: Book a table for 10 at 7 PM at Downtown
Bot: No tables available at Downtown. Try FoodieSpot Suburb Italian?

Business Strategy Summary





Problems Addressed: Manual reservations, poor customer experience, missed revenue.



Solution: AI agent with reservations, recommendations, and dynamic pricing.



Metrics: 50% reduction in processing time, 10% revenue increase, NPS 80+.



Expansion: White-label for other chains, adapt for hospitality/events.



Advantages: Personalized recommendations, scalable tool-calling, dynamic pricing.

Assumptions





50 restaurants with varied cuisines and locations.



Users prefer web-based chat; WhatsApp integration is future work.



MongoDB Atlas for simplicity.

Limitations





No multi-language support (future enhancement).



Limited to Grok 3’s token limits for complex queries.



Dynamic pricing not implemented (requires additional logic).

Future Enhancements





Integrate WhatsApp/Messenger channels.



Add dynamic pricing based on demand.



Implement user authentication for loyalty programs.



Use Grok 3’s DeepSearch for external data (e.g., events).

Repository Structure

restaurant_bot/
├── app.py               # Streamlit app
├── tools.py             # Tool-calling logic
├── db.py                # MongoDB interactions
├── prompt.py            # Prompt engineering
├── data/
│   ├── generate_data.py # Data generation
├── k8s/
│   ├── deployment.yml   # GKE deployment
├── Dockerfile
├── requirements.txt
├── .env
├── README.md