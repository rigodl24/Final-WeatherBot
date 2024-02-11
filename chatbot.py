import spacy
from spacy.matcher import Matcher
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer
import requests
import streamlit as st
import nltk

# Initialize the chatbot without SQL storage adapter
weather_bot = ChatBot("WeatherBot")

nltk.download('wordnet')

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

# Use the ChatterBotCorpusTrainer for better context training
corpus_trainer = ChatterBotCorpusTrainer(weather_bot)

# Train the chatbot on the English language corpus data
corpus_trainer.train("chatterbot.corpus.english")

# Set OpenWeatherMap API key
api_key = "c0dc9ee92a3b15efbd2b65edb8d99a74"

# OpenWeatherMap API endpoint
api_endpoint = "http://api.openweathermap.org/data/2.5/weather"

# Function to retrieve weather information
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

# Function to generate clothing recommendation based on weather data
def generate_clothing_recommendation(weather_data):
    try:
        if weather_data is not None:
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
        return "Unexpected format in weather data. Please check the weather information and try again."
    except Exception as e:
        return "Unable to generate clothing recommendation. Please check the weather information and try again."

# Function to handle user input
def handle_user_input(user_input):
    session_state = st.session_state

    if user_input.lower() in ['exit', 'quit', 'bye']:
        return "WeatherBot: Goodbye!"

    # Preprocess user input
    user_input_lower = user_input.lower()

    # Get the location from user input if present
    current_location = get_location_from_user_input(user_input)

    if current_location:
        # Update last_location in session state with the current location
        session_state.last_location = current_location

    # Retrieve last_location from session state
    last_location = session_state.get("last_location")

    if current_location or last_location:
        # Use the current location if provided, otherwise use the last location
        location = current_location if current_location else last_location

        # Fetch and display weather information
        weather_info = get_weather_info(location)
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
    else:
        return "WeatherBot: Please specify a location or ask about the weather in a particular location."

# Streamlit app title
st.title("Hi! I'm Weather Bot, ask me about the weather")

# Interaction with the chatbot
user_input = st.text_input("You:", "")

if user_input:
    response = handle_user_input(user_input)
    st.write(response)
