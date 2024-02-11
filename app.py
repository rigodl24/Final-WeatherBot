import os
from flask import Flask, render_template, request, jsonify
from utils import load_spacy_model, initialize_chatbot, get_location_from_user_input, get_weather_info, \
    generate_clothing_recommendation

# Create a Flask app instance
app = Flask(__name__)

# Load spaCy English language model
nlp = load_spacy_model()

# Create a new chatbot instance
weather_bot, trainer = initialize_chatbot()

# Retrieve API key from environment variable
api_key = os.environ.get('api_key')

# OpenWeatherMap API endpoint
api_endpoint = "http://api.openweathermap.org/data/2.5/weather"

# Last known location
last_location = None

# Greeting message
greeting_message = "Hi! I'm WeatherBot. Ask me about the weather."

# Define the / route to handle both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def handle_request():
    global last_location

    if request.method == 'POST':
        try:
            # Get the user input from the POST request
            user_input = request.form['user_input']

            # Get the location from user input
            current_location = get_location_from_user_input(user_input, nlp)

            if current_location:
                # Update last_location with the current location
                last_location = current_location

                # Fetch weather information
                weather_info = get_weather_info(current_location, api_key, api_endpoint)

                # Check if the user asked about clothing
                if any(intent in user_input.lower() for intent in ['wear', 'dress']):
                    # Generate clothing recommendations
                    clothing_recommendation = generate_clothing_recommendation(weather_info)
                    return jsonify({'response': clothing_recommendation})
                else:
                    # Return general weather information
                    return jsonify({'response': weather_info})

            elif last_location:
                # Check for follow-up questions
                if any(intent in user_input.lower() for intent in ['wear', 'dress']):
                    # If the user explicitly asks about clothing without specifying a location, use the last known location
                    weather_info = get_weather_info(last_location, api_key, api_endpoint)
                    clothing_recommendation = generate_clothing_recommendation(weather_info)
                    return jsonify({'response': clothing_recommendation})
                else:
                    # If no specific question detected, ask how the bot can further assist
                    return jsonify({'response': "How can I assist you further?"})

            else:
                # Ask the user to specify the location
                return jsonify({'response': "Please specify the location."})

        except Exception as e:
            # Handle exceptions
            return jsonify({'response': f"An error occurred: {str(e)}"}), 500

    else:
        # Render the HTML template with the greeting message for GET requests
        return render_template('index.html', weather_response=greeting_message)

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
