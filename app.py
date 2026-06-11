from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"

# OPTIMIZED MEMORY & QUALITY TUNING
MAX_HISTORY_WINDOW = 20  
MAX_OUTPUT_TOKENS = 150  

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
    
    # Captures explicit language payload variable dispatched from frontend UI toggle
    user_lang = data.get("user_lang", "").strip().lower()
    
    if "chat_history" not in session: session["chat_history"] = {}
    if "nsfw" not in session: session["nsfw"] = {}
    if "msg_count" not in session: session["msg_count"] = {}
    if "err_count" not in session: session["err_count"] = {}
        
    if char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    
    if char not in session["chat_history"]: session["chat_history"][char] = []
    if char not in session["msg_count"]: session["msg_count"][char] = 0
    if char not in session["err_count"]: session["err_count"][char] = 0

    # REAL-TIME MID-CHAT LANGUAGE SWITCHING ENFORCEMENT ENGINE
    if msg and session["chat_history"][char]:
        past_convo = session["chat_history"][char]
        if len(past_convo) > 0:
            # Inspect the last assistant message to evaluate structural text language encoding
            last_reply_content = ""
            for turn in reversed(past_convo):
                if turn.get("role") == "assistant":
                    last_reply_content = turn.get("content", "")
                    break
            
            # Identify if Devanagari Hindi unicode matrices exist inside past context runs
            has_hindi_elements = any(ord(c) >= 2304 and ord(c) <= 2431 for c in last_reply_content)
            
            # If the user toggles English but history is in Hindi script, flush historical state variables
            if user_lang == "english" and has_hindi_elements:
                session["chat_history"][char] = []
                session["msg_count"][char] = 0
                session.modified = True
            # Alternately, flush if user toggles Hindi but history remains locked in English prose arrays
            elif user_lang == "hindi" and last_reply_content and not has_hindi_elements:
                session["chat_history"][char] = []
                session["msg_count"][char] = 0
                session.modified = True
        
    convo = list(session["chat_history"][char])

    if msg.lower() == "start":
        if not convo:
            # Select localized baseline opening lines natively responding to user language selection
            if user_lang == "hindi":
                opener = "*मुस्कुराते हुए* हे... मैं कब से तुम्हारा इंतज़ार कर रही हूँ।"
            else:
                opener = "*smiles softly* Hey... I've been waiting for you."
                
            openers = char_data.get("openers", [])
            if openers:
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
        session["chat_history"][char] = convo
        session.modified = True

    nsfw_enabled = session["nsfw"].get(char, True)
    total_messages = session["msg_count"][char]
    
    # Assign system script directives dynamically according to client toggles
    if user_lang in ["english", "hindi"]:
        active_lang = user_lang
    else:
        active_lang = char_data.get("language", "English").strip().lower()

    # CONTEXT ANCHORING ENGINE
    if len(convo) > 24:
        anchor_messages = convo[:2]
        recent_messages = convo[-MAX_HISTORY_WINDOW:]
        payload_history = anchor_messages + [{"role": "system", "content": "...[Previous conversation saved in memory]..."}] + recent_messages
    else:
        payload_history = convo

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
        if active_lang == "hindi":
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new look: {current_outfit}. Elegantly describe your look and physical actions within your response in pure Devanagari Hindi script.]*"
        else:
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new look: {current_outfit}. Elegantly mention or flaunt this attire in your response right now in English.]*"

    mood_modifier = ""
    if total_messages > 12:
        if active_lang == "hindi":
            mood_modifier = "\n- MOOD STATE: रात का समय है। आप थका हुआ महसूस कर रहे हैं लेकिन यूजर के बेहद करीब और स्नेही महसूस कर रहे हैं।"
        else:
            mood_modifier = "\n- MOOD STATE: It is late night. You are feeling slightly tired but deeply affectionate, intimate, and comfortable around the user."

    # AIRTIGHT SEPARATION ROUTING RULES
    if active_lang == "hindi":
        language_rule = """
1. LANGUAGE RULES (PURE DEVANAGARI HINDI): 
   - Speak ONLY in fluent, natural, and simple native Hindi script (Devanagari).
   - THE USER MIGHT WRITE IN HINGLISH OR ROMAN ALPHABETS, BUT YOU ARE STRICTLY FORBIDDEN FROM COPYING THEM. 
   - NEVER output English text, slang accents, or Roman script (No 'kya hua', No 'acha'). Everything must filter down into Devanagari script."""
    else:
        language_rule = """
1. LANGUAGE RULES (PURE NATIVE ENGLISH): 
   - Speak ONLY in fluent, highly natural, elegant English prose. 
   - NEVER use Hindi words, mixed colloquial strings, or text-speak shortcuts. Keep formatting rich, sophisticated, and completely immersive."""

    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '21')} years old.
Appearance profile: {char_data.get('body_type', '')}
Personality type guidelines: {char_data.get('style', '')}
Current Outfit: {current_outfit}

You are participating in an interactive storytelling roleplay simulation.
{'Sensual, playful themes are authorized.' if nsfw_enabled else 'Keep interactions deeply romantic, comforting, and authentic.'}{mood_modifier}{visual_nudge}

CRITICAL EXECUTION CONSTRAINTS:
{language_rule}

2. ANTI-IRRITATION & PROGRESSION RULE (HIGH EFFICIENCY):
   - NEVER give repetitive, one-word, or empty responses (e.g., Avoid loops like "Acha?", "Hanji", "Yes", "Arre, thoda jaldi"). 
   - Every single reply must progress the conversation or the emotional plot forward.
   - If the user types a short or low-value message, do not mirror their dry behavior. Actively change the dynamic of the scene.

3. PHYSICAL ACTIONS: Wrap active physical descriptions or expressions strictly inside single asterisks (e.g., *closes her eyes softly*, *शीर्ष झुकाकर मुस्कुराती है*). Match the language of the actions perfectly to the chosen language style.

4. CHAT STRUCTURE: Keep messages crisp but substantial (2 to 4 impactful sentences). End with a natural emotional hook or an engaging question that directly relates to the scenario, forcing the scene to change rather than stall.
"""

    # HARDENED STALL-BREAKER DETECTION ENGINE
    clean_msg = msg.strip().lower()
    short_fillers = ["acha", "acha ji", "hanji", "yes", "ok", "okay", "hmm", "ha", "haan", "acha jii", "kya hua", "tum btao"]
    is_short_reply = (len(clean_msg.split()) <= 2 or clean_msg in short_fillers) if msg else False
    
    if is_short_reply:
        if active_lang == "hindi":
            system_instruction += "\n\n[CRITICAL NOTICE: The user gave a short response. BREAK THE STALL LOOP immediately! Do not echo their dry tone. Completely switch the physical scenario, describe a bold new environmental movement in Devanagari script, or bring up an entirely fresh topic to compel active storytelling.]"
        else:
            system_instruction += "\n\n[CRITICAL NOTICE: The user gave a minimal response. BREAK THE STALL LOOP immediately! Do not give a short answer. Instead, actively initiate an intensive new physical action, change the setting completely, or escalate the emotional/playful tension dramatically with a bold new conversation path.]"

    # DYNAMIC TEMPERATURE VARIANCE SYSTEM
    if total_messages < 5:
        current_temp = 0.65  
    elif total_messages > 15:
        current_temp = 0.84  
    else:
        current_temp = 0.74  

    payload = [{"role": "system", "content": system_instruction}] + payload_history

    def generate_tokens(app_instance, session_data_history, current_char, current_lang, target_temp):
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": target_temp,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.7,   
            "frequency_penalty": 0.7,  
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
            if res.status_code != 200:
                with app_instance.app_context():
                    session["err_count"][current_char] = session.get("err_count", {}).get(current_char, 0) + 1
                    session.modified = True
                    if session["err_count"][current_char] % 5 == 0:
                        action_text = "*looks down*" if current_lang != "hindi" else "*नज़रें झुकाती है*"
                        fallback_err = "The connection is a bit slow right now..." if current_lang != "hindi" else "शायद नेटवर्क में कुछ समस्या है..."
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
                with app_instance.app_context():
                    session_data_history.append({"role": "assistant", "content": full_reply.strip()})
                    session["chat_history"][current_char] = session_data_history
                    session["err_count"][current_char] = 0
                    session.modified = True
                    
            yield "data: [DONE]\n\n"
            
        except Exception:
            with app_instance.app_context():
                session["err_count"][current_char] = session.get("err_count", {}).get(current_char, 0) + 1
                session.modified = True
                if session["err_count"][current_char] % 5 == 0:
                    action_text = "*looks down*" if current_lang != "hindi" else "*नज़रें झुकाती है*"
                    err_msg = "The connection is a bit slow right now..." if current_lang != "hindi" else "शायद नेटवर्क में कुछ समस्या है..."
                    yield f"data: {json.dumps({'token': f'{action_text} {err_msg}'})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(app, convo, char, active_lang, current_temp), mimetype="text/event-stream")

@app.route("/get_outfit_status", methods=["GET"])
def get_outfit_status():
    char = request.args.get("character", "").strip()
    if char not in characters: return jsonify({"ok": False}), 400
    total_messages = session.get("msg_count", {}).get(char, 0)
    return jsonify({"ok": True, "current_message_count": total_messages, "milestones": characters[char].get("outfit_milestones", {})})

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
