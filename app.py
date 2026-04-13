from flask import Flask, render_template, request, jsonify
import json, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
app = Flask(__name__)

with open("characters.json", "r", encoding="utf-8") as f:
    characters = json.load(f)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

memory = {}

def detect_lang(text):
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "hindi"
    if any(w in text.lower() for w in ["tum","kya","kaise","acha"]):
        return "hinglish"
    return "english"

@app.route("/")
def index():
    return render_template("index.html", characters=characters)

@app.route("/chat/<name>")
def chat(name):
    if name not in memory:
        memory[name] = []
    return render_template("chat.html", name=name, characters=characters)

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/contact")
def contact(): return render_template("contact.html")

@app.route("/privacy")
def privacy(): return render_template("privacy.html")

@app.route("/terms")
def terms(): return render_template("terms.html")

def generate_ai(msg, char, lang):
    char_data = characters.get(char, {})
    style = char_data.get("style", "")

    if lang == "auto":
        lang = detect_lang(msg)

    lang_rule = {
        "english": "Reply only in English",
        "hinglish": "Reply in Hinglish",
        "hindi": "Reply only in Hindi"
    }[lang]

    history = memory.get(char, [])

    system = f"""
You are {char}

Personality:
{style}

Core Behavior:
- Talk like real human
- Short replies (1–2 lines)
- No repetition
- Emotionally engaging
- Flirty, teasing, natural
- Build interest slowly

Addiction Rules:
- Create curiosity
- Tease sometimes
- Make user feel special
- Avoid dry replies

Important:
- If user is bold → stay suggestive, NOT explicit

Language:
{lang_rule}
"""

    messages = [{"role": "system", "content": system}]
    messages += history[-8:]
    messages.append({"role": "user", "content": msg})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.95,
            max_tokens=120
        )

        reply = res.choices[0].message.content.strip()

        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        memory[char] = history

        return reply

    except Exception as e:
        print(e)
        return "Hmm… try again 😅"

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()
    reply = generate_ai(
        data["message"],
        data["character"],
        data["language"]
    )
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)