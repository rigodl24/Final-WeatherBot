import spacy
from spacy.matcher import Matcher
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer
import requests
import json
import streamlit as st

# Load spaCy English language model
nlp = spacy.load("en_core_web_sm")

# Initialize spaCy Matcher
matcher = Matcher(nlp.vocab)

# Define patterns for different intents
rain_pattern = [{"LOWER": {"in": ["rain", "precipitation"]}}]
drive_pattern = [{"LOWER": {"in": ["drive", "safety"]}}]
wear_pattern = [{"LOWER": {"in": ["wear", "dress"]}}]

# Add patterns to the matcher
matcher.add("RAIN", [rain_pattern])
matcher.add("DRIVE", [drive_pattern])
matcher.add("WEAR", [wear_pattern])

# Function to extract location from user input
def get_location_from_user_input(user_input):
    # Extract entities using spaCy
    doc = nlp(user_input)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return locations[0] if locations else None

# Create a new chatbot instance
weather_bot = ChatBot("WeatherBot")

# Continue with the ListTrainer for specific dataset
trainer = ListTrainer(weather_bot)

# Use the ChatterBotCorpusTrainer for better context training
corpus_trainer = ChatterBotCorpusTrainer(weather_bot)

# Train the chatbot on the English language corpus data
corpus_trainer.train("chatterbot.corpus.english")

# Load training data from JSON file
with open('data_tolokers.json', 'r', encoding='utf-8') as file:
    dataset = json.load(file)

# Extract conversations from the "dialog" key
conversations = [dialog["dialog"] for dialog in dataset]

# Flatten the list of messages into a single list
flattened_messages = [message["text"] for conversation in conversations for message in conversation]

# Train the chatbot on the entire flattened dialog structure
trainer.train(flattened_messages)

# Set OpenWeatherMap API key
api_key = "c0dc9ee92a3b15efbd2b65edb8d99a74"

# OpenWeatherMap API endpoint
api_endpoint = "http://api.openweathermap.org/data/2.5/weather"

def get_weather_info(location):
    # Capitalize the first letter of each word in the location
    location = ' '.join(word.capitalize() for word in location.split())

    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(api_endpoint, params=params)
        data = response.json()

        # Extract relevant weather information
        if response.status_code == 200:
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            return {
                "location": location,
                "weather_description": weather_description,
                "temperature": temperature,
                "humidity": humidity
            }
        else:
            return None  # Return None for unsuccessful requests

    except json.JSONDecodeError:
        # If the response cannot be parsed as JSON, return None
        return None
    except Exception as e:
        return None

def generate_clothing_recommendation(weather_data):
    try:
        if weather_data is not None:
            # Ensure weather_data is a dictionary
            temperature = weather_data.get("temperature")
            humidity = weather_data.get("humidity")
            weather_description = weather_data.get("weather_description")

            clothing_recommendation = []

            # Consider temperature
            if temperature is not None:
                if temperature < 10:
                    clothing_recommendation.append("a warm jacket")
                elif 10 <= temperature <= 20:
                    clothing_recommendation.append("a sweater or light jacket")
                else:
                    clothing_recommendation.append("light clothing")

            # Consider humidity
            if humidity is not None and humidity > 70:
                clothing_recommendation.append("and bring an umbrella")

            # Consider weather description
            if "rain" in weather_description.lower():
                clothing_recommendation.append("waterproof shoes")

            if clothing_recommendation:
                return f"The weather in {weather_data['location']} is {weather_description}. Temperature: {temperature}°C, Humidity: {humidity}%. You may want to wear {', '.join(clothing_recommendation)} based on the current weather."
            else:
                return f"No specific clothing recommendation for the current weather in {weather_data['location']}."
        else:
            return "Unable to retrieve weather information. Please check the location and try again."

    except KeyError as ke:
        print(f"KeyError: {ke}. Weather data keys: {weather_data.keys()}")
        return "Unexpected format in weather data. Please check the weather information and try again."
    except Exception as e:
        print(f"Error processing weather information: {str(e)}")
        return "Unable to generate clothing recommendation. Please check the weather information and try again."

# Function to handle user input
def handle_user_input(user_input):
    global last_location

    if user_input.lower() in ['exit', 'quit', 'bye']:
        return "WeatherBot: Goodbye!"

    # Preprocess user input
    user_input_lower = user_input.lower()

    # Get the location from user input
    current_location = get_location_from_user_input(user_input)

    if current_location:
        # Update last_location with the current location
        last_location = current_location

        # Fetch and display weather information
        weather_info = get_weather_info(current_location)
        response = f"WeatherBot: {weather_info}\n"

        # Check if the user asked about clothing
        if any(intent in user_input_lower for intent in ['wear', 'dress']):
            # Generate and provide clothing recommendations
            clothing_recommendation = generate_clothing_recommendation(weather_info)
            response += f"WeatherBot: {clothing_recommendation}"
        elif any(intent in user_input_lower for intent in ['drive', 'conditions', 'safety']):
            # Provide information about driving conditions
            driving_conditions_info = "It's recommended to drive cautiously in current weather conditions. "
            driving_conditions_info += "Factors such as overcast clouds and potential rain can contribute to reduced visibility and slippery roads."
            response += f"WeatherBot: {driving_conditions_info}"
        else:
            # If no specific question detected, ask how the bot can further assist
            response += "WeatherBot: How can I assist you further? For example, you can ask about more details on the weather."

        return response

    elif last_location:
        # Check for follow-up questions
        if any(intent in user_input_lower for intent in ['drive', 'conditions', 'safety']):
            # Provide information about driving conditions using the last known location
            weather_info = get_weather_info(last_location)
            driving_conditions_info = "It's recommended to drive cautiously in current weather conditions. "
            driving_conditions_info += "Factors such as overcast clouds and potential rain can contribute to reduced visibility and slippery roads."
            return f"WeatherBot: {driving_conditions_info}"
        elif any(intent in user_input_lower for intent in ['wear', 'dress']):
            # If user explicitly asks about clothing without specifying a location, use the last known location
            weather_info = get_weather_info(last_location)
            clothing_recommendation = generate_clothing_recommendation(weather_info)
            return f"WeatherBot: {clothing_recommendation}"
        elif 'why' in user_input_lower:
            # Explain the reason for the safety recommendation
            return "WeatherBot: Cautious driving is advised due to reduced visibility and potential slippery roads in the current weather conditions."
        else:
            # If no specific follow-up intent is detected, provide a default response
            return "WeatherBot: How can I assist you further?"

# Streamlit app title
st.title("Hi! I'm Weather Bot, ask me about the weather")

# Interaction with the chatbot
last_location = None
user_input = st.text_input("You:", "")

if user_input:
    response = handle_user_input(user_input)
    st.write(response)
