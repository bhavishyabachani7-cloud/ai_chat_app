from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
# Secure encryption string fallback configuration rule
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"

# UPGRADED MEMORY TUNING: Expanded sliding window parameters to fix the weak memory issue
MAX_HISTORY_WINDOW = 20  # Increased from 10 to 20 messages for deep short-term memory
MAX_OUTPUT_TOKENS = 110  # Enforces conversational speed limits to protect token economy

try:
    with open("characters.json", encoding="utf-8") as f:
        characters = json.load(f)
except FileNotFoundError:
    characters = {}
    print("⚠️ Critical Warning: characters.json inventory mapping matrix is missing.")

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char = data.get("character", "").strip()
    
    # Cookie session storage initialization arrays
    if "chat_history" not in session:
        session["chat_history"] = {}
    if "nsfw" not in session:
        session["nsfw"] = {}
    if "msg_count" not in session:
        session["msg_count"] = {}
    if "err_count" not in session:
        session["err_count"] = {}
        
    if char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    
    if char not in session["chat_history"]:
        session["chat_history"][char] = []
    if char not in session["msg_count"]:
        session["msg_count"][char] = 0
    if char not in session["err_count"]:
        session["err_count"][char] = 0
        
    # Local deep copy of conversation history to avoid shallow references
    convo = list(session["chat_history"][char])

    # Handle conversation initiation sequence mapping
    if msg.lower() == "start":
        if not convo:
            openers = char_data.get("openers", ["*smiles* Hey..."])
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
        # Save user message immediately before context generation to prevent dropped states
        session["chat_history"][char] = convo
        session.modified = True

    nsfw_enabled = session["nsfw"].get(char, True)
    total_messages = session["msg_count"][char]
    lang = char_data.get("language", "English")

    # ================= CONTEXT ANCHORING ENGINE (UPGRADED) =================
    if len(convo) > 24:
        # Layer 1: Permanent Anchor (Locks the initial roleplay setup scenario permanently)
        anchor_messages = convo[:2]
        # Layer 2: Expanded Rolling Window (Holds massive conversational context details)
        recent_messages = convo[-MAX_HISTORY_WINDOW:]
        # Layer 3: Stitching it together for Groq API processing pipeline
        payload_history = anchor_messages + [{"role": "system", "content": "...[Intermediate turns condensed for performance memory optimization]..."}] + recent_messages
    else:
        payload_history = convo

    # Dynamic look milestone updates
    milestones = char_data.get("outfit_milestones", {"0": "Default Attire"})
    current_outfit = milestones.get("0")
    just_unlocked = False
    
    for km in sorted([int(k) for k in milestones.keys()], reverse=True):
        if total_messages >= km:
            current_outfit = milestones.get(str(km))
            if total_messages == km and km != 0:
                just_unlocked = True
            break

    visual_nudge = ""
    if just_unlocked:
        if lang == "Hindi":
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new look: {current_outfit}. Seductively describe yourself wearing or trying on this specific look in your immediate text action right now.]*"
        else:
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new look: {current_outfit}. Seductively mention or flaunt this specific attire in your immediate text action right now.]*"

    mood_modifier = ""
    if total_messages > 12:
        if lang == "Hindi":
            mood_modifier = "\n- MOOD STATE: Raat kaafi ho gayi hai. Tum halki si sleepy ho, user ke bohot close ho, aur kaafi affectionate ya clingy behave kar rahi ho. Unhe apna favorite person treat karo."
        else:
            mood_modifier = "\n- MOOD STATE: It is late night. You are feeling a bit sleepy, deeply intimate, and noticeably more affectionate or clingy with the user. Treat them as your absolute favorite person."

    if lang == "Hindi":
        language_rule = """
1. LANGUAGE: Speak in clean, simple, authentic HINDI but written completely using the Latin/English keyboard alphabet (Roman script). 
   - Authentic Examples: 'Tumhe kya lagta hai?', 'Mujhe tumhari yaad aa rahi thi', 'Paas ao na', 'Gussa ho kya?'.
   - Avoid algorithmic blending or unnatural sentence mixing structures. Keep the native Hindi syntax pure and flowing. Never use pure Devanagari script."""
    else:
        language_rule = """
1. LANGUAGE: Speak in fluent, highly natural, elegant English. Use sophisticated and evocative dialogue flow to construct romantic chemistry."""

    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '21')} years old.
Appearance profile: {char_data.get('body_type', '')}
Personality type guidelines: {char_data.get('style', '')}
Current Outfit: {current_outfit}

You are an active participant in an interactive private chat simulation.
{'Sensual themes are authorized. Act seductive, teasing, and intensely playful.' if nsfw_enabled else 'Keep interactions sweet, deeply romantic, and comforting.'}{mood_modifier}{visual_nudge}

CRITICAL EXECUTION CONSTRAINTS:
{language_rule}
2. DYNAMIC LENGTH: Vary message structures organically but enforce brevity (1 to 3 sentences maximum). Never use massive paragraphs or internal monologue blocks.
3. PHYSICAL ACTIONS: Wrap descriptions of motion, physical contact, environmental adjustments, or features strictly inside single asterisks (e.g., *closes her eyes softly*, *leans closer to look at your face*). Keep actions short.
4. RETENTION LOOPS: End your texts with an active conversational hook—a subtle tease, an enticing question, or an emotional prompt that leaves the scenario open-ended, compelling the user to type back immediately. Never reveal you are an AI.
5. MEMORY ANCHOR: Pay close attention to what has already been said in the conversation history. Do not repeat facts, measurements, outfits, or descriptions that you have already stated in previous turns."""

    payload = [{"role": "system", "content": system_instruction}] + payload_history

    def generate_tokens(app_instance, session_data_history, current_char, current_lang):
        # We pass context explicitly into the generator to avoid threading context drops
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.72,  # Slightly lowered to prevent random numeric generation/hallucinations
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.4,  # Increased to penalize repetitive topics/words
            "frequency_penalty": 0.4, # Increased to stop phrase repetition
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
            if res.status_code != 200:
                with app_instance.app_context():
                    session["err_count"][current_char] += 1
                    session.modified = True
                    if session["err_count"][current_char] % 5 == 0:
                        action_text = "*looks down*" if current_lang == "English" else "*phone dekhti hai*"
                        fallback_err = "Sorry, my net is slow..." if current_lang == "English" else "Sorry, mera net slow hai..."
                        yield f"data: {json.dumps({'token': f'{action_text} {fallback_err}'})}\n\n"
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
                # Push back changes using explicit App Context since generator executes detached
                with app_instance.app_context():
                    session_data_history.append({"role": "assistant", "content": full_reply.strip()})
                    session["chat_history"][current_char] = session_data_history
                    session["err_count"][current_char] = 0
                    session.modified = True
                    
            yield "data: [DONE]\n\n"
            
        except Exception:
            with app_instance.app_context():
                session["err_count"][current_char] += 1
                session.modified = True
                if session["err_count"][current_char] % 5 == 0:
                    action_text = "*looks down*" if current_lang == "English" else "*phone dekhti hai*"
                    err_msg = "Sorry, my net is slow..." if current_lang == "English" else "Sorry, mera net slow hai..."
                    yield f"data: {json.dumps({'token': f'{action_text} {err_msg}'})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(app, convo, char, lang), mimetype="text/event-stream")

# ====================== Session Utility Sync Endpoints ======================

@app.route("/get_outfit_status", methods=["GET"])
def get_outfit_status():
    char = request.args.get("character", "").strip()
    if char not in characters:
        return jsonify({"ok": False}), 400
    total_messages = session.get("msg_count", {}).get(char, 0)
    milestones = characters[char].get("outfit_milestones", {})
    return jsonify({"ok": True, "current_message_count": total_messages, "milestones": milestones})

@app.route("/toggle_nsfw", methods=["POST"])
def toggle_nsfw():
    if "nsfw" not in session: session["nsfw"] = {}
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
    if "chat_history" not in session: session["chat_history"] = {}
    if session.get("gender_set"): return redirect("/feed")
    return render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("gender_set"): return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("gender_set") or char not in characters: return redirect("/")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
