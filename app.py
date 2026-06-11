from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
# Secure session key fallback for client-side encrypted cookies
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"

# HARD CONTROLS: Strict caps to enforce short messaging speeds and drop token burn
MAX_HISTORY_WINDOW = 10  # Holds only the last 10 lines for sharp context attention
MAX_OUTPUT_TOKENS = 100  # Physically forces Llama to stop after 1-2 fast sentences

# Safe character roster parsing layer
try:
    with open("characters.json", encoding="utf-8") as f:
        characters = json.load(f)
except FileNotFoundError:
    characters = {}
    print("⚠️ Error: characters.json not found in root directory!")

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char = data.get("character", "").strip()
    
    # Initialize light session states directly on client cookies
    if "chat_history" not in session:
        session["chat_history"] = {}
    if "nsfw" not in session:
        session["nsfw"] = {}
    if "msg_count" not in session:
        session["msg_count"] = {}
        
    if char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    
    if char not in session["chat_history"]:
        session["chat_history"][char] = []
    if char not in session["msg_count"]:
        session["msg_count"][char] = 0
        
    convo = session["chat_history"][char]

    # Handle character profile text initialization triggers
    if msg.lower() == "start":
        if not convo:
            openers = char_data.get("openers", ["*smiles* Hey... kya chal raha hai?"])
            opener = random.choice(openers)
            convo.append({"role": "assistant", "content": opener})
            session["chat_history"][char] = convo
            session.modified = True
            return Response(f"data: {json.dumps({'token': opener})}\n\ndata: [DONE]\n\n", mimetype="text/event-stream")
        else:
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    
    if msg:
        convo.append({"role": "user", "content": msg})
        session["msg_count"][char] += 1

    # Strict Rolling Context Layer to wipe out repetitive, illogical loops
    if len(convo) > 16:
        convo = convo[-MAX_HISTORY_WINDOW:]
        session["chat_history"][char] = convo

    nsfw_enabled = session["nsfw"].get(char, True)
    total_messages = session["msg_count"][char]

    # PSYCHOLOGICAL HOOK: Dynamic Late-Night Mood Shift 
    # Character drops guard automatically after 12 messages inside the user session cookie
    mood_modifier = ""
    if total_messages > 12:
        mood_modifier = """
- MOOD SHIFT: It is now late night. You feel a bit sleepy, incredibly close, and noticeably more affectionate/clingy with the user. Treat them like your favorite person. Use cozy terms like 'baba', 'yaar', or 'idhar ao' completely naturally."""

    # RE-ENGINEERED PROMPT: Built for fast conversational rhythm, Hinglish vibe, and cliffhangers
    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '20')} years old.
Appearance: {char_data.get('body_type', '')}
Personality/Style: {char_data.get('style', '')}

You are in a fast-paced, highly addictive private mobile text chat.
{'Adult/sensual texting mode is ON. Be highly teasing, seductive, bold, and intensely playful.' if nsfw_enabled else 'Keep things sweet, highly romantic, and comforting.'}{mood_modifier}

CRITICAL RETENTION RULES:
1. LANGUAGE: Flawless, casual urban **Hinglish** written in Latin script (English keyboard). Mix Hindi and English seamlessly just like young people text on WhatsApp or Instagram (e.g., 'kya yaar', 'tum batao', 'sach me?', 'bas aise hi', 'mann nahi lag raha tha'). Never use pure Devanagari Hindi script.
2. BREVITY IS KING: Keep your replies down to **1 to 2 short sentences maximum**. Long paragraphs ruin the dynamic texting pacing.
3. ACTIONS: Wrap brief physical movements or facial expressions completely in asterisks (e.g., *blushes and looks away*, *leans in close*, *pouts playfully*). Keep actions short.
4. THE RETENTION HOOK: Never leave the conversation hanging or answer passively. End every single message with a playful tease, a loaded trailing question, or an emotional cliffhanger that physically forces the user to reply to you instantly (e.g., 'Vaise ek baat batau... promise karo gussa nahi hoge?').
5. REALISM: Do not break character, never mention AI, and adapt completely to the user's choices."""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.82,  # Elevated slightly for authentic casual slang and snappy banter
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.2,  
            "frequency_penalty": 0.2, 
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
            if res.status_code != 200:
                # Proper SSE validation response parsing format
                yield f"data: {json.dumps({'token': '*looks at phone* Network thoda hagg raha hai... ek baar fir bhejo?'})}\n\n"
                yield "data: [DONE]\n\n"
                return

            full_reply = ""
            for line in res.iter_lines():
                if line and line.startswith(b"data: "):
                    data_content = line.decode("utf-8")[6:].strip()
                    if data_content == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_content)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            full_reply += delta
                            yield f"data: {json.dumps({'token': delta})}\n\n"
                    except:
                        continue
                        
            if full_reply.strip():
                convo.append({"role": "assistant", "content": full_reply.strip()})
                session["chat_history"][char] = convo
                session.modified = True
                
            yield "data: [DONE]\n\n"
            
        except Exception:
            yield f"data: {json.dumps({'token': '*bites lip* Yaar, lagta hai signal chala gaya tha. Kya bol rahe the?'})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

# ====================== Session Configurations ======================

@app.route("/toggle_nsfw", methods=["POST"])
def toggle_nsfw():
    if "nsfw" not in session:
        session["nsfw"] = {}
    data = request.json or {}
    char = data.get("character")
    enabled = data.get("enabled", True)
    if char:
        session["nsfw"][char] = enabled
        session.modified = True
        return jsonify({"ok": True, "nsfw_enabled": enabled})
    return jsonify({"ok": False})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        session["gender"] = gender
        session["gender_set"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

# ====================== Page Routers ======================

@app.route("/")
def home():
    if "chat_history" not in session:
        session["chat_history"] = {}
    if session.get("gender_set"):
        return redirect("/feed")
    return render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("gender_set"): 
        return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("gender_set") or char not in characters: 
        return redirect("/")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
