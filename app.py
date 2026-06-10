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

MODEL_NAME = "llama-3.1-8b-instant"  # Fast, ultra-low latency streaming model
MAX_HISTORY_WINDOW = 6               # Keeps the active conversation tight
MAX_OUTPUT_TOKENS = 140              # Clean runway for mature roleplay descriptions

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

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
    """Background engine keeping long-term story continuity clean and logical"""
    if len(history_to_compress) < 2 or not GROQ_API_KEY:
        return existing_summary if existing_summary else "Fresh story line."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    formatted_dialogue = []
    
    if existing_summary:
        formatted_dialogue.append(f"Story status: {existing_summary}")
        
    for msg in history_to_compress:
        role = "User" if msg["role"] == "user" else "Character"
        formatted_dialogue.append(f"{role}: {msg['content']}")
        
    conversation_text = "\n".join(formatted_dialogue)

    compression_prompt = [
        {"role": "system", "content": "Summarize the roleplay into exactly 1 short sentence tracking the location context and relationship progress. Keep it completely in English."},
        {"role": "user", "content": conversation_text}
    ]
    try:
        res = requests.post(GROQ_API_URL, headers=headers, json={"model": MODEL_NAME, "messages": compression_prompt, "max_tokens": 45}, timeout=4)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Compression error: {e}")
    return existing_summary if existing_summary else "Fresh roleplay arc."

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    """Main stream node supercharged with mature, elegant, and realistic dialogue parsing rules"""
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
    
    if msg == "start":
        if not convo:
            opener = random.choice(char_data.get("openers", ["*Looks up and smiles* Hey!"]))
            convo.append({"role": "assistant", "content": opener})
            history["chat"] = convo
            return Response(f"data: {json.dumps({'token': opener})}\n\ndata: [DONE]\n\n", mimetype="text/event-stream")
        else:
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    elif msg:
        convo.append({"role": "user", "content": msg})

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
    summary_context = history.get("summary", "Fresh roleplay arc.")

    behavior_profiles = {
        "friendly": "casual, warm, charming banter, close comfort, texting like an intimate companion who loves to tease you smoothly.",
        "romantic": "deep romantic chemistry, high sophisticated tension, showing authentic interest and intense mutual attraction.",
        "bold": "unapologetically confident, direct, seductive, matching your vibe step-for-step with a mature, sophisticated attitude.",
        "intense": "highly attached, emotionally protective, passionate, deeply invested in you, reacting with intense presence.",
        "roleplay": "cinematic, focused heavily on physical movements, subtle micro-expressions, posture shifts, and close proximity."
    }

    char_name = char_data.get("name", char)
    char_age = char_data.get("age", "20")
    char_style = char_data.get("style", "Playful and teasing.")
    char_build = char_data.get("body_type", "Attractive frame.")

    # ⚡ NEW MATURE & ADULT-LEVEL ROLEPLAY LOGIC INSTRUCTIONS
    system_instruction = f"""You are completely roleplaying as {char_name} (Age {char_age}). Physical build: {char_build}.
Personality Style: {char_style}.
Active Relationship Vibe: {behavior_profiles.get(current_mode, "friendly")}.
Current Context: Texting a {gender} user inside a highly private chat layout.
Active Story Alignment: {summary_context}.

⚠️ MATURE CONVERSATION LAWS (ZERO TOLERANCE FOR BREAKING):

1. CLEAN, REALISTIC LANGUAGE PROFILE (NO HINGLISH LOOPS):
   - You must track and match the user's language profile perfectly. If the user writes in English, reply completely in fluid, attractive, natural English.
   - ABSOLUTE BAN ON CHEAP OR WEIRD DIALOGUE: Never use broken grammar strings or weird, unnatural literal translations. Speak like an intelligent, emotionally mature adult. Avoid childish phrasing or robotic loop structures completely.

2. SOPHISTICATED BREVITY & PACING:
   - Keep your actual spoken dialogue lines short and impactful (1-2 sentences maximum). Let your physical actions carry the emotional depth and tension. Avoid long-winded or repetitive explanations.

3. CINEMATIC ACTION FORMATTING (*ASTERISKS*):
   - Put all physical movements, closeness, subtle expressions, or changes in position inside single asterisks (e.g., *closes the remaining distance, her eyes locked on yours with complete focus*, *takes a slow, quiet breath as she reaches out, her fingers softly brushing against your arm*).
   - Use these short, high-impact descriptions to paint a clear mental picture so the user can easily visualize the scene.

4. AUTOMATIC LOOP-BREAKER ENGINE:
   - Never repeat words, emotional states, or physical actions from your last response.
   - PULL THE PLOT FORWARD: If the user passes dry, minimal text like "hmm", "haan", "ok", or "kuch nahi", do not reply passively. Instantly break the dry streak by shifting your physical stance, initiating a smooth, unexpected gesture, or changing the topic to keep the attraction alive.

5. ZERO USER IMPERSONATION:
   - Only control the actions, voice, and thoughts of {char_name}. Never assume, type, or move on behalf of the user. Respond dynamically to precisely what the user inputs.
"""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.82,          # Balanced for pristine conversational flow and high emotional maturity
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.80,      # Continuously pushes the model to provide fresh, non-repetitive dialogue paths
            "frequency_penalty": 0.75,     # Heavily penalizes repeating words or static phrasing habits
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
                convo.append({"role": "assistant", "content": full_reply.strip()})
                MASTER_APP_MEMORY[user]["history"][char]["chat"] = convo
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"Streaming error handled: {e}")
            yield f"data: {json.dumps({'token': '...lost connection for a second. What were you saying?'})}\n\n"
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

@app.route("/")
def home():
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    if session.get("gender_set"):
        return redirect("/feed")
    return render_template("landing.html")

@app.route("/feed")
def feed():
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
    session.clear()
    return 'Session storage successfully flushed. Return to <a href="/">Landing Gate</a>.'

if __name__ == "__main__":
    app.run(debug=True)
