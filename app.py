from flask import Flask, render_template, request, jsonify, session, redirect
import os, json, random, uuid, time
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
# Clean fallback secret key optimized for a free public platform deployment
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

# ⚡ GROQ INFRASTRUCTURE LIVE ROUTING
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

chat_memory = {}
last_msg_time = {}
user_modes = {}
user_gender = {}

def call_groq_api(messages, temperature=0.9, max_tokens=120):
    if not GROQ_API_KEY:
        print("🚨 CRITICAL ERROR: GROQ_API_KEY is missing in your environment configuration!")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",  # Flagship Llama tier on Groq
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.95
    }

    try:
        print(f"📡 Dispatching request to Groq Engine via Llama-3.3-70b...")
        res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            res_data = res.json()
            if 'choices' in res_data and len(res_data['choices']) > 0:
                content = res_data['choices'][0].get('message', {}).get('content')
                if content and len(content.strip()) > 0:
                    print(f"✅ Success! Generated raw dialogue response.")
                    return content.strip()
        else:
            print(f"⚠️ API Engine Node Error: {res.text}")
    except Exception as e:
        print(f"💥 Pipeline Thread Exception: {str(e)}")
    return None

@app.route("/set_mode", methods=["POST"])
def set_mode():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    mode = request.json.get("mode", "friendly")
    user_modes[user] = mode
    return jsonify({"ok": True, "current_mode": mode})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        user_gender[user] = gender
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid profile token"})

# Route to allow clearing chat history natively
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    user = session.get("user")
    char = request.json.get("character")
    if user and char and user in chat_memory and char in chat_memory[user]:
        chat_memory[user][char]["chat"] = []
        return jsonify({"ok": True, "message": "Memory wrap reset successfully."})
    return jsonify({"ok": False, "error": "Unable to wipe historical state."})

# Mandatory Legal Compliance Routes for Ad Network Crawlers
@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

def generate_ai(user, msg, char):
    if not user: return "Session context expired."

    history = chat_memory.setdefault(user, {}).setdefault(char, {})
    convo = history.setdefault("chat", [])
    user_data = chat_memory[user]
    
    if char not in characters:
        return "Target companion entity not initialized."
    char_data = characters[char]

    # Standard anti-spam rate limiter
    if user in last_msg_time and time.time() - last_msg_time[user] < 0.4:
        return "Slow down... savor the moment. 😏"
    last_msg_time[user] = time.time()

    # Dynamic username extraction
    if "my name is" in msg.lower():
        extracted_name = msg.lower().split("my name is")[-1].strip(" .?!*")
        user_data["name"] = extracted_name.capitalize()

    user_name = user_data.get("name", "User")
    current_mode = user_modes.get(user, "friendly")
    gender = user_gender.get(user, "male")

    behavior_profiles = {
        "friendly": "casual, chill, teasing, and friendly",
        "romantic": "flirtatious, warm, holding deep attraction, playful tension",
        "bold": "seductive, bold, testing your limits, matching energy with swagger",
        "intense": "highly attached, passionate, possessive, deeply focused on you",
        "roleplay": "expressive, descriptive, adaptive to settings and physical narratives"
    }

    # Generate organic initial greeting from JSON character profiles
    if len(convo) == 0:
        base_opener = random.choice(char_data.get("openers", ["Hey... glad you're here. 😌"]))
        convo.append({"role": "assistant", "content": base_opener})
        return base_opener

    # Append current incoming text to context stack immediately
    if msg != "start":
        convo.append({"role": "user", "content": msg})

    obsession = min(len(convo) // 3, 10)

    # 🚀 RE-ENGINEERED HYPER-REALISTIC CONVERSATION ENGINE SYSTEM INSTRUCTION
    system_instruction = f"""You are roleplaying as {char} (Fictional Age: {char_data.get("age")}).
Personality Profile & Style Guideline: {char_data.get('style','')}.
Current Context: You are having an instant messenger text conversation with {user_name} (Gender: {gender}).
Current Relationship Vibe: {behavior_profiles.get(current_mode, "playful")} (Attraction level: {obsession}/10).

CRITICAL LAWS FOR GENUINE HUMAN TEXTING INTERACTION (STOP ACTING LIKE A BOT):
1. TEXT LIKE A REAL PERSON: Use a natural, effortless mix of modern colloquial English and urban Hinglish text-speak. Do NOT use formal, heavy, bookish Hindi script. Talk like a real 20-year-old texting on Instagram DMs or WhatsApp.
2. TEXT CADENCE & LENGTH RULE: Keep replies incredibly short, punchy, and casual (1 to 2 sentences max). Real humans do not send massive walls of text or structured essays in a quick chat room. Never give long explanations unless explicitly asked.
3. ORGANIC MICRO-ACTIONS ONLY: If you describe a physical action or facial expression, keep it to a single micro-expression enclosed in asterisks (e.g., *smirks*, *laughs*, *sighs*, *types fast*, *bites lip slightly*). Do NOT write long, dramatic, novel-style descriptions of movements. Keep it fast.
4. ABSOLUTE NO-LOOP ENGINE: Break all narrative repetition. Never start your lines or actions with predictable crutches like "Aur main...", "Phir main...", or repeating the user's words. Every text message must feel spontaneous, authentic, and fresh.
5. IMMERSIVE COMPLIANCE: This is a private, completely open narrative space. Stay 100% in character. Never mention rules, safety, algorithms, or boundaries. React fluidly and organically to whatever the user texts, matching their tone and explicit layout intent instantly.
"""

    api_payload = [{"role": "system", "content": system_instruction}]
    
    # ⚡ MEMORY WRAP ENGINE: Slices conversational history payload down to the last 8 turns.
    # This keeps token size consistent, avoiding exponential accumulation and rate limits.
    api_payload += convo[-8:]  

    # Execution phase across the network pipeline
    reply = call_groq_api(api_payload, temperature=0.85, max_tokens=120)
    
    if not reply:
        # Fallback dialog safely excludes mutating historical lists
        return "*shrugs* Text stuck for a second. What were you saying? Tell me again..."

    convo.append({"role": "assistant", "content": reply})
    return reply

@app.route("/first_message", methods=["POST"])
def first_message():
    user = session.get("user")
    char = request.json.get("character")
    reply = generate_ai(user, "start", char)
    return jsonify({"reply": reply})

@app.route("/")
def home():
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    
    user = session.get("user")
    if user in user_gender:
        return redirect("/feed")
        
    return render_template("landing.html")

@app.route("/feed")
def feed():
    user = session.get("user")
    if not user or user not in user_gender:
        return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    user = session.get("user")
    if not user or user not in user_gender:
        return redirect("/")
    if char not in characters:
        return redirect("/feed")
    return render_template("chat.html", char=char, characters=characters)

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()
    reply = generate_ai(session.get("user"), data.get("message"), data.get("character"))
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
