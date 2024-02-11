# utils.py
import spacy
from spacy.matcher import Matcher
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
import requests
import json
import time

def load_spacy_model():
    return spacy.load("en_core_web_sm")

def initialize_chatbot():
    weather_bot = ChatBot("WeatherBot")
    trainer = ListTrainer(weather_bot)
    corpus_trainer = ChatterBotCorpusTrainer(weather_bot)
    corpus_trainer.train("chatterbot.corpus.english")
    return weather_bot, trainer

def get_location_from_user_input(user_input, nlp):
    doc = nlp(user_input)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return locations[0] if locations else None

def get_weather_info(location, api_key, api_endpoint):
    location = ' '.join(word.capitalize() for word in location.split())
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(api_endpoint, params=params)
        data = response.json()

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
            return None

    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None

def generate_clothing_recommendation(weather_data):
    try:
        if weather_data is not None:
            temperature = weather_data.get("temperature")
            humidity = weather_data.get("humidity")
            weather_description = weather_data.get("weather_description")

            clothing_recommendation = []

            if temperature is not None:
                if temperature < 10:
                    clothing_recommendation.append("a warm jacket")
                elif 10 <= temperature <= 20:
                    clothing_recommendation.append("a sweater or light jacket")
                else:
                    clothing_recommendation.append("light clothing")

            if humidity is not None and humidity > 70:
                clothing_recommendation.append("and bring an umbrella")

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
