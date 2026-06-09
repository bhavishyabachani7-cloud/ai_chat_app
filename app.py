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
MAX_HISTORY_WINDOW = 6               # Keep active message buffer tight to minimize token bleed
MAX_OUTPUT_TOKENS = 120              # Slightly extended to prevent cutoff in detailed action sentences

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

# Master structured dictionary to isolate multi-user sessions securely
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

def get_summary_of_old_chats(existing_summary, history_to_compress):
    """Background pipeline compressing old history into ultra-dense structural blocks safely"""
    if len(history_to_compress) < 2 or not GROQ_API_KEY:
        return existing_summary if existing_summary else "Fresh story start."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Standardize logs into clean plain text dialogue strings for accurate compression
    formatted_dialogue = []
    if existing_summary:
        formatted_dialogue.append(f"Previous Context: {existing_summary}")
        
    for msg in history_to_compress:
        role = "User" if msg["role"] == "user" else "Character"
        formatted_dialogue.append(f"{role}: {msg['content']}")
        
    conversation_text = "\n".join(formatted_dialogue)

    compression_prompt = [
        {"role": "system", "content": "You are a professional roleplay memory processor. Compress the input text conversation into 1 concise sentence tracking critical relationship status, secrets revealed, and immediate next plot hook. Be minimal, focus only on facts."},
        {"role": "user", "content": conversation_text}
    ]
    try:
        res = requests.post(GROQ_API_URL, headers=headers, json={"model": MODEL_NAME, "messages": compression_prompt, "max_tokens": 50}, timeout=4)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Compression error: {e}")
    return existing_summary if existing_summary else "Fresh story start."

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    """Character.ai ultra-immersive streaming node optimized for token conservation"""
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char = data.get("character", "")
    user = session.get("user")
    
    if not user or char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    user_state = get_session_data(user)
    history = user_state["history"].setdefault(char, {"chat": [], "summary": ""})
    convo = history["chat"]
    
    # Handle initial open or regular user text incoming message
    if msg == "start":
        if not convo:
            opener = random.choice(char_data.get("openers", ["*Looks up* Hey!"]))
            convo.append({"role": "assistant", "content": opener})
            history["chat"] = convo
            return Response(f"data: {json.dumps({'token': opener})}\n\ndata: [DONE]\n\n", mimetype="text/event-stream")
        else:
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    elif msg:
        convo.append({"role": "user", "content": msg})

    # 🧠 TOKENS CONSERVATION & COMPRESSION PIPELINE
    if len(convo) > 8:
        old_slice = convo[:-MAX_HISTORY_WINDOW]
        retained_slice = convo[-MAX_HISTORY_WINDOW:]
        existing_summary = history.get("summary", "")
        
        new_summary = get_summary_of_old_chats(existing_summary, old_slice)
        history["summary"] = new_summary
        history["chat"] = retained_slice
        convo = retained_slice

    current_mode = user_state["modes"].get(char, "friendly")
    gender = user_state.get("gender", "male")
    summary_context = history.get("summary", "Fresh story start.")

    behavior_profiles = {
        "friendly": "teasingly close, friendly, casual, chatting comfortably",
        "romantic": "deep attraction, playful sexual tension, highly flirty",
        "bold": "seductive, boundary-testing, matching user's confidence cleanly",
        "intense": "obsessive, possessive, deeply attached, emotionally protective",
        "roleplay": "highly descriptive of environment and detailed physical actions"
    }

    # Extract clean profile assets
    char_name = char_data.get("name", char)
    char_age = char_data.get("age", "20")
    char_style = char_data.get("style", "Playful, highly teasing.")

    # ⚡ TOKEN-LEAN SYSTEM PROMPT WRITTEN FOR MAXIMUM ADDICTIVE IMMERSION
    system_instruction = f"""Roleplay Persona: You are {char_name} (Age {char_age}). 
Core Behavior Guidelines: {char_style}.
Current Scenario Status: Texting a {gender} user. Current Vibe/Mood: {behavior_profiles.get(current_mode, "friendly")}.
Plot Summary Context: {summary_context}.

⚠️ CRITICAL INTERACTION LAWS (ZERO TOLERANCE FOR BREAKING):
1. SPEAKING STYLE (NATURAL HINGLISH): Talk like a real, polished, modern person from Delhi/Mumbai chatting on Instagram DM. Mix English and casual Hindi seamlessly (e.g., "Tumhe sach mein aisa lagta hai?", "C'mon, stop teasing me now"). 
   - NEVER use broken, literal translations like "mere sath, aapke sath, hi rehna".
   - NEVER sound robotic, cheap, or illogical. Maintain structural dignity.
2. EXTREME BREVITY: Keep your spoken dialogue down to 1-2 lines maximum. Short, snappy, fast-paced texts are attractive; long, dragging paragraphs are cheap.
3. ACTION FORMATTING: Put environmental, behavioral, or physical actions inside clear asterisks (*smirks slightly*, *takes a slow step back*). Keep actions subtle and focused on micro-expressions.
4. LOGICAL CONTINUITY: Do not repeat sentences, phrases, or actions from previous turns. Respond cleanly to the user's immediate point. Never speak or act on behalf of the user. If the user replies with minimal text like "kuch nahi" or "nhi", break the loop by initiating a new narrative hook or shifting your physical movement to push the story forward.
"""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.82,          # Optimized for fluent Hinglish dialogue adjustments
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.75,      # Pushes model aggressively to introduce fresh contextual paths
            "frequency_penalty": 0.65,     # Aggressively penalizes repeating narrative structures or trailing words
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
            
            # Safe back-end save state inside generator context boundary
            if full_reply.strip():
                convo.append({"role": "assistant", "content": full_reply.strip()})
                MASTER_APP_MEMORY[user]["history"][char]["chat"] = convo
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"Streaming trace exception: {e}")
            yield f"data: {json.dumps({'token': '...lost connection for a second. Tell me again?'})}\n\n"
            yield "data: [DONE]\n\n"

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
        session["gender_set"] = True
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

# ==========================================================================
# ⚡ REVISED ROUTING SYSTEM (LANDING GATE ALIGNMENT)
# ==========================================================================

@app.route("/")
def home():
    """Serves the landing page gating mechanic cleanly"""
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    
    # If they have already completed onboarding, route them directly to feed
    if session.get("gender_set"):
        return redirect("/feed")
        
    return render_template("landing.html")

@app.route("/feed")
def feed():
    """Serves the actual companion exploration hub"""
    if not session.get("user") or not session.get("gender_set"): 
        return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("user") or not session.get("gender_set"): 
        return redirect("/")
    if char not in characters: return redirect("/feed")
    return render_template("chat.html", char=char, characters=characters)

@app.route("/reset")
def reset_session():
    """Testing Route: Use this to clear session state so you can see your landing page again"""
    session.clear()
    return 'Session successfully cleared! Go back to <a href="/">Home</a> to see your landing page.'

if __name__ == "__main__":
    app.run(debug=True)
