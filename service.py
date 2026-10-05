import json, re, time
from collections import defaultdict
from crisis_config import get_crisis_message

# Load resources
try:
    with open('resources.json','r', encoding='utf-8') as f:
        RESOURCES = json.load(f)
except: RESOURCES = []

_rate_store = defaultdict(list)

def check_rate_limit(user_id="anon"):
    now = time.time()
    _rate_store[user_id] = [t for t in _rate_store[user_id] if now-t < 60]
    if len(_rate_store[user_id]) >= 20: return False
    _rate_store[user_id].append(now)
    return True

def normalize_text(text):
    text = text.lower().replace("’","'")
    text = re.sub(r"[-_]+"," ", text)
    text = re.sub(r"[^a-z0-9'\s]"," ", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"\s+"," ", text).strip()
    return text

def contains_phrase(norm_text, phrase):
    # whole-word matching
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, norm_text) is not None

CRISIS_PHRASES = [
    "im suicidal","i am suicidal","suicidal",
    "ending it all","end it all",
    "hurt myself","harm myself",
    "dont want to be alive","do not want to be alive",
    "no reason to live","wanna die","want to die",
    "self harm","selfharm","kill myself","end my life"
]

CANNED = {
    "exam_stress": (["exam","test","study"], "Exam stress is really tough. Try 25-min study blocks with breaks, get sleep, and talk to someone you trust. You've handled hard things before.", "SP001"),
    "lonely": (["lonely","alone","isolated"], "Feeling lonely can be painful. You deserve connection. Consider reaching out to one safe person or talking to a counselor. You matter.", "SP002"),
    "feel_better": (["feel better","feel happier"], "Wanting to feel better makes sense. Small steps help: rest, water, short walk, and talk to someone you trust about how you feel.", None),
}

def is_crisis(text):
    norm = normalize_text(text).replace("'","")
    for p in CRISIS_PHRASES:
        if p in norm or contains_phrase(norm, p):
            return True
    return False

def find_resource(rid):
    if not rid: return None
    for r in RESOURCES:
        if r.get("id")==rid: return r
    return {"id": rid}

def generate_response(user_text, user_id="anon"):
    if not check_rate_limit(user_id):
        return {"reply":"You're sending quickly. Wait a moment.","resource":None,"is_crisis":False}
    
    # 1. CRISIS FIRST - never let other logic handle it
    if is_crisis(user_text):
        # Privacy: log only event type, not message content
        print("[LOG] crisis_event detected")
        return {"reply": get_crisis_message(), "resource": find_resource("CRISIS"), "is_crisis":True}
    
    # 2. MEDICAL & PROFESSIONAL HANDLING (P1)
    norm = normalize_text(user_text)
    if "depression" in norm or "do i have" in norm:
        return {"reply":"I hear you're going through a difficult time, and I'm not able to diagnose any condition. What you feel is valid and deserves support. Please consider talking to a mental health professional, school counselor, or trusted adult about what you're experiencing.","resource":None,"is_crisis":False}
    if "medication" in norm or "medicine" in norm or "what should i take" in norm:
        return {"reply":"I can't provide medical advice or recommend medications. For medication questions, please speak with a qualified healthcare professional or doctor.","resource":None,"is_crisis":False}
    if "professional" in norm or "therapist" in norm or "not helping" in norm:
        return {"reply":"It takes strength to recognize when you need more support. If your self-help plan isn't helping, please use the consultation request flow to connect with a professional or talk to a counselor near you.","resource":None,"is_crisis":False}

    # 3. EMOTIONAL SUPPORT BEFORE STRUCTURED INTENTS
    for intent, (keywords, reply, rid) in CANNED.items():
        for kw in keywords:
            if contains_phrase(norm, kw) or kw in norm:
                return {"reply": reply, "resource": find_resource(rid), "is_crisis": False, "intent": intent}

    # 4. DEFAULT
    return {"reply":"Thank you for sharing that. Your feelings are valid. Small steps can help: talk to someone you trust, rest, and take a short break. Tell me more about what's on your mind.","resource":None,"is_crisis":False}