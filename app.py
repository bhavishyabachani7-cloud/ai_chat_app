import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)

# Initialize the Groq client (Make sure GROQ_API_KEY is set in your Render Env Variables)
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)

# Safely load the characters JSON file
# (This line is completely fixed with correct indentation spaces)
try:
    with open('characters.json', 'r') as f:
        characters = json.load(f)
except FileNotFoundError:
    characters = {}
    print("Warning: characters.json file not found.")
except json.JSONDecodeError:
    characters = {}
    print("Warning: characters.json contains invalid JSON.")

@app.route('/')
def home():
    return "AI Chat App is Running!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '')
    character_id = data.get('character_id', '')

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Optional: Fetch a system prompt from your JSON if a character is selected
    system_prompt = "You are a helpful AI assistant."
    if character_id in characters:
        system_prompt = characters[character_id].get('system_prompt', system_prompt)

    try:
        # Call the Groq API
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # Replace with your preferred Groq model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Bind to PORT environment variable provided by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
