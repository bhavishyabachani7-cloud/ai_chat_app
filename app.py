from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid, time
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
# Ensure the session cookie has a secure fallback token key
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

# ⚡ GROQ INFRASTRUCTURE TUNED FOR REAL-TIME STREAMING
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"  # Premium 500,000 daily token workhorse
MAX_HISTORY_WINDOW = 6               # Active back-and-forth buffer size
MAX_OUTPUT_TOKENS = 120              # Slightly increased for clean generation cutoff

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

# Master structured dictionary to isolate multi-user sessions securely
# Structure: { user_uuid: { "gender": "male", "modes": { "char_name": "friendly" }, "history": { "char_name": { "chat": [], "summary": "" } } } }
MASTER_APP_MEMORY = {}

def get_session_data(user_id):
    """Ensures a user has an isolated partition inside master state"""
    if user_id not in MASTER_APP_MEMORY:
        MASTER_APP_MEMORY[user_id] = {
            "gender": "male",
            "modes": {},
            "history": {}
        }
    return MASTER_APP_MEMORY[user_id]

def get_summary_of_old_chats(history_to_compress):
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
    
    # Isolate user state sandbox explicitly
    user_state = get_session_data(user)
    history = user_state["history"].setdefault(char, {"chat": [], "summary": ""})
    convo = history["chat"]
    
    # Handle initial open or regular user text incoming message
    if msg == "start":
        if not convo:  # Only inject opener if history is clean slate
            opener = random.choice(char_data.get("openers", ["*Looks up at you* Hey!"]))
            convo.append({"role": "assistant", "content": opener})
            history["chat"] = convo
            return Response(f"data: {json.dumps({'token': opener})}\n\n", mimetype="text/event-stream")
        else:
            # If conversation already exists, return nothing or let user type
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    elif msg:
        convo.append({"role": "user", "content": msg})

    # 🧠 CHARACTER.AI LONG TERM MEMORY COMPRESSION ENGINE
    if len(convo) > 8:
        old_slice = convo[:-MAX_HISTORY_WINDOW]
        retained_slice = convo[-MAX_HISTORY_WINDOW:]
        existing_summary = history.get("summary", "")
        
        # Background block running structural tracking
        new_summary = get_summary_of_old_chats([existing_summary] + old_slice)
        history["summary"] = new_summary
        history["chat"] = retained_slice
        convo = retained_slice

    current_mode = user_state["modes"].get(char, "friendly")
    gender = user_state.get("gender", "male")
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
Current Context: Texting conversation with User (Gender: {gender}).
Current Relationship Vibe: {behavior_profiles.get(current_mode, "friendly")}.
Long-Term Memory Summary of past actions: {rolling_memory_context}.

CRITICAL LAWS FOR GENUINE HUMAN TEXTING INTERACTION:
1. TEXT LIKE A REAL PERSON: Use a natural mix of colloquial English and urban Hinglish text-speak. Talk like a real 20-year-old on Instagram DMs.
2. TEXT CADENCE & LENGTH RULE: Keep replies incredibly short, punchy, and casual (1 to 2 sentences max). Never send walls of text. Do not break character or switch out of character.
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
            "stream": True
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
            
            if full_reply.strip():
                convo.append({"role": "assistant", "content": full_reply})
                history["chat"] = convo
        except Exception as e:
            yield f"data: {json.dumps({'token': '...lost connection for a second. Tell me again?'})}\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

@app.route("/set_mode", methods=["POST"])
def set_mode():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    
    data = request.json or {}
    mode = data.get("mode", "friendly")
    char = data.get("character")
    
    if not char: return jsonify({"ok": False, "error": "Missing character mapping"})
    
    user_state = get_session_data(user)
    user_state["modes"][char] = mode
    return jsonify({"ok": True, "current_mode": mode})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        user_state = get_session_data(user)
        user_state["gender"] = gender
        session["gender_set"] = True # Set flag explicitly inside session engine
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    user = session.get("user")
    char = request.json.get("character")
    if user:
        user_state = get_session_data(user)
        if char in user_state["history"]:
            user_state["history"][char] = {"chat": [], "summary": ""}
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
    return redirect("/feed") if session.get("gender_set") else render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("user") or not session.get("gender_set"): return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("user") or not session.get("gender_set"): return redirect("/")
    if char not in characters: return redirect("/feed")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    app.run(debug=True)
