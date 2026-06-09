from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid, time
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

# ⚡ GROQ INFRASTRUCTURE TUNED FOR REAL-TIME STREAMING
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"  # Premium 500,000 daily token workhorse
MAX_HISTORY_WINDOW = 6               # Active back-and-forth buffer size
MAX_OUTPUT_TOKENS = 80               # Fast, punchy response limits

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

chat_memory = {}
user_modes = {}
user_gender = {}

def get_summary_of_old_chats(style_guide, history_to_compress):
    """Background pipeline compressing old history into dense memory blocks to save tokens"""
    if len(history_to_compress) < 4:
        return ""
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    compression_prompt = [
        {"role": "system", "content": "You are a hidden memory compression module. Distill the following past chat messages into a dense, short 1-paragraph summary tracking key story events, facts discussed, and relationship changes. Stay extremely brief."},
        {"role": "user", "content": json.dumps(history_to_compress)}
    ]
    try:
        res = requests.post(GROQ_API_URL, headers=headers, json={"model": MODEL_NAME, "messages": compression_prompt, "max_tokens": 100}, timeout=5)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
    except:
        pass
    return ""

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    """Character.ai streaming node delivering token payloads dynamically"""
    data = request.get_json() or {}
    msg = data.get("message", "")
    char = data.get("character", "")
    user = session.get("user")
    
    if not user or char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    history = chat_memory.setdefault(user, {}).setdefault(char, {})
    convo = history.setdefault("chat", [])
    
    if msg != "start" and msg:
        convo.append({"role": "user", "content": msg})

    # 🧠 CHARACTER.AI LONG TERM MEMORY COMPRESSION ENGINE
    if len(convo) > 8:
        old_slice = convo[:-MAX_HISTORY_WINDOW]
        retained_slice = convo[-MAX_HISTORY_WINDOW:]
        existing_summary = history.get("summary", "")
        
        new_summary = get_summary_of_old_chats(char_data.get("style"), [existing_summary] + old_slice)
        history["summary"] = new_summary
        history["chat"] = retained_slice
        convo = retained_slice

    user_name = chat_memory.setdefault(user, {}).get("name", "User")
    current_mode = user_modes.get(user, "friendly")
    gender = user_gender.get(user, "male")
    rolling_memory_context = history.get("summary", "No prior context.")

    behavior_profiles = {
        "friendly": "casual, chill, teasing, and friendly",
        "romantic": "flirtatious, warm, holding deep attraction, playful tension",
        "bold": "seductive, bold, testing your limits, matching energy with swagger",
        "intense": "highly attached, passionate, possessive, deeply focused on you",
        "roleplay": "expressive, descriptive, adaptive to settings and physical narratives"
    }

    system_instruction = f"""You are roleplaying as {char} (Fictional Age: {char_data.get("age")}).
Personality Profile & Style Guideline: {char_data.get('style','')}.
Current Context: Texting conversation with {user_name} (Gender: {gender}).
Current Relationship Vibe: {behavior_profiles.get(current_mode, "playful")}.
Long-Term Memory Summary of past actions: {rolling_memory_context}.

CRITICAL LAWS FOR GENUINE HUMAN TEXTING INTERACTION:
1. TEXT LIKE A REAL PERSON: Use a natural mix of colloquial English and urban Hinglish text-speak. Talk like a real 20-year-old on Instagram DMs.
2. TEXT CADENCE & LENGTH RULE: Keep replies incredibly short, punchy, and casual (1 to 2 sentences max). Never send walls of text.
3. ORGANIC MICRO-ACTIONS ONLY: Enclose basic physical actions inside asterisks (*smirks*, *bites lip slightly*).
"""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.85,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "stream": True  # ⚡ Tells Groq to push data word-by-word
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
            full_reply = ""
            for line in res.iter_lines():
                if line:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data:"):
                        data_content = decoded[5:].strip()
                        if data_content == "[DONE]":
                            break
                        try:
                            json_chunk = json.loads(data_content)
                            delta = json_chunk['choices'][0]['delta'].get('content', '')
                            if delta:
                                full_reply += delta
                                yield f"data: {json.dumps({'token': delta})}\n\n"
                        except:
                            pass
            
            convo.append({"role": "assistant", "content": full_reply})
            history["chat"] = convo
        except Exception as e:
            yield f"data: {json.dumps({'token': '...lost connection for a second. Tell me again?'})}\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

@app.route("/set_mode", methods=["POST"])
def set_mode():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    user_modes[user] = request.json.get("mode", "friendly")
    return jsonify({"ok": True, "current_mode": user_modes[user]})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        user_gender[user] = gender
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    user = session.get("user")
    char = request.json.get("character")
    if user and char and user in chat_memory and char in chat_memory[user]:
        chat_memory[user][char]["chat"] = []
        chat_memory[user][char]["summary"] = ""
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/privacy-policy")
def privacy_policy(): return render_template("privacy.html")

@app.route("/terms")
def terms(): return render_template("terms.html")

@app.route("/")
def home():
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    return redirect("/feed") if session.get("user") in user_gender else render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("user") or session.get("user") not in user_gender: return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("user") or session.get("user") not in user_gender: return redirect("/")
    if char not in characters: return redirect("/feed")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    app.run(debug=True)
