import os
import json
import requests
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from gtts import gTTS
from io import BytesIO
from insurance.models import InsuranceProduct

# ==========================================
# 1. CONFIGURATIONS
# ==========================================

LANGUAGES = {
    'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 
    'gu': 'Gujarati', 'bn': 'Bengali', 'ta': 'Tamil'
}

# The Keys for saving data
SURVEY_STEPS = ["occupation", "age", "income", "vehicle"]

# The Scripts (Questions) - MUST MATCH THE LENGTH OF SURVEY_STEPS
# ==========================================
# 1. CONFIGURATIONS
# ==========================================

LANGUAGES = {
    'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 
    'gu': 'Gujarati', 'bn': 'Bengali', 'ta': 'Tamil',
    'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam', 'pa': 'Punjabi'
}

SURVEY_STEPS = ["occupation", "age", "income", "vehicle"]

# ADD THE MISSING TRANSLATIONS HERE
SURVEY_SCRIPTS = {
    'en': [
        "To find the perfect match, I need a few details. First, what is your **main occupation**?",
        "Got it. What is your current **age**?",
        "Roughly, what is your **annual family income**?",
        "Do you own a **vehicle** (Car, Bike, Tractor)?"
    ],
    'hi': [
        "सही प्लान खोजने के लिए, मुझे कुछ जानकारी चाहिए। सबसे पहले, आपका **मुख्य व्यवसाय** क्या है?",
        "समझ गयी। आपकी **उम्र** क्या है?",
        "मोटे तौर पर, आपकी **वार्षिक पारिवारिक आय** कितनी है?",
        "क्या आपके पास कोई **वाहन** (कार, बाइक, ट्रैक्टर) है?"
    ],
    'te': [ # TELUGU (Telugu)
        "సరైన పాలసీని కనుగొనడానికి, నాకు కొన్ని వివరాలు కావాలి. ముందుగా, మీ **ప్రధాన వృత్తి** ఏమిటి?",
        "అర్థమైంది. మీ ప్రస్తుత **వయస్సు** ఎంత?",
        "సుమారుగా, మీ **కుటుంబ వార్షిక ఆదాయం** ఎంత?",
        "మీకు ఏదైనా **వాహనం** (కారు, బైక్, ట్రాక్టర్) ఉందా?"
    ],
    'ta': [ # TAMIL (Tamil)
        "சரியான திட்டத்தைக் கண்டறிய, எனக்கு சில விவரங்கள் தேவை. முதலில், உங்கள் **முக்கிய தொழில்** என்ன?",
        "புரிந்தது. உங்கள் தற்போதைய **வயது** என்ன?",
        "தோராயமாக, உங்கள் **ஆண்டு குடும்ப வருமானம்** என்ன?",
        "உங்களிடம் **வாகனம்** (கார், பைக், டிராக்டர்) உள்ளதா?"
    ],
    'mr': [ # MARATHI (Marathi)
        "योग्य योजना शोधण्यासाठी, मला काही तपशील हवे आहेत. प्रथम, तुमचा **मुख्य व्यवसाय** काय आहे?",
        "समजले. तुमचे सध्याचे **वय** काय आहे?",
        "साधारणपणे, तुमचे **वार्षिक कौटुंबिक उत्पन्न** किती आहे?",
        "तुमच्याकडे **वाहन** (कार, बाईक, ट्रॅक्टर) आहे का?"
    ],
    'bn': [ # BENGALI (Bengali)
        "சரியான பாலிசியைக் கண்டறிய, எனக்கு சில விவரங்கள் தேவை. முதலில், உங்கள் **முக்கிய தொழில்** என்ன?", # (Note: This looks like Tamil text in user source, replacing with Bengali below)
        "სঠিক পরিকল্পনা খুঁজে পেতে, আমার কিছু বিবরণ প্রয়োজন। প্রথমত, আপনার **প্রধান পেশা** কী?",
        "বুঝলাম। আপনার বর্তমান **বয়স** কত?",
        "মোটামুটিভাবে, আপনার **বার্ষিক পারিবারিক আয়** কত?",
        "আপনার কি কোনো **যানবাহন** (গাড়ি, বাইক, ট্রাক্টর) আছে?"
    ],
    'gu': [ # GUJARATI
        "યોગ્ય પ્લાન શોધવા માટે, મારે થોડી વિગતો જોઈએ છે. પ્રથમ, તમારો **મુખ્ય વ્યવસાય** શું છે?",
        "સમજાયું. તમારી વર્તમાન **ઉંમર** શું છે?",
        "આશરે, તમારી **વાર્ષિક કૌટુંબિક આવક** કેટલી છે?",
        "શું તમારી પાસે **વાહન** (કાર, બાઈક, ટ્રેક્ટર) છે?"
    ]
}
# ==========================================
# 2. CORE VIEWS
# ==========================================

def chat_view(request):
    if 'survey_step' in request.session: 
        del request.session['survey_step']
    return render(request, 'chatbot/chat.html')

def get_response(request):
    user_msg = request.GET.get('userMessage', '').strip()
    lang_code = request.session.get('language', 'en')
    
    # Initialize Session
    if 'survey_step' not in request.session:
        request.session['survey_step'] = -1
        request.session['survey_data'] = {}

    step = request.session['survey_step']

    # --- ROUTE 1: IN SURVEY? ---
    if step >= 0:
        return handle_survey_logic(request, user_msg, lang_code)

    # --- ROUTE 2: INTENT DETECTION ---
    buy_keywords = ['buy', 'plan', 'suggest', 'recommend', 'policy', 'best', 'insurance for me', 'start']
    if any(k in user_msg.lower() for k in buy_keywords):
        # Start Survey
        request.session['survey_step'] = 0
        scripts = SURVEY_SCRIPTS.get(lang_code, SURVEY_SCRIPTS['en'])
        
        intro = "Sure! I can help you find the best policy. " if lang_code == 'en' else "ज़रूर! मैं आपको सबसे अच्छी पॉलिसी खोजने में मदद कर सकती हूँ। "
        return JsonResponse({"botResponse": intro + scripts[0]})

    # --- ROUTE 3: GENERAL CHAT ---
    return handle_general_chat(user_msg, lang_code)


# ==========================================
# 3. HELPER: SURVEY LOGIC (THE FIX)
# ==========================================
def handle_survey_logic(request, user_msg, lang_code):
    step = request.session['survey_step']
    survey_data = request.session['survey_data']
    
    # 1. Identify current question
    if step < len(SURVEY_STEPS):
        current_key = SURVEY_STEPS[step]

        # 2. Validate Input
        is_valid, error_msg = validate_input(current_key, user_msg)
        if not is_valid:
            return JsonResponse({"botResponse": error_msg})

        # 3. Save Answer
        survey_data[current_key] = user_msg
        request.session['survey_data'] = survey_data
        
        # 4. Determine Next Step
        next_step = step + 1
        scripts = SURVEY_SCRIPTS.get(lang_code, SURVEY_SCRIPTS['en'])

        # --- CRITICAL FIX HERE ---
        # Ensure next_step is within bounds for BOTH keys and scripts
        if next_step < len(SURVEY_STEPS) and next_step < len(scripts):
            request.session['survey_step'] = next_step
            return JsonResponse({"botResponse": scripts[next_step]})
    
    # 5. SURVEY COMPLETE -> RAG
    relevant_products = InsuranceProduct.objects.filter(is_active=True).values('id', 'name', 'base_premium', 'description')
    
    context_text = "\n".join([
        f"- ID {p['id']}: {p['name']} ({p['description']}) @ ₹{p['base_premium']}/yr" 
        for p in relevant_products
    ])
    
    user_profile = ", ".join([f"{k}: {v}" for k,v in survey_data.items()])
    language_name = LANGUAGES.get(lang_code, 'English')
    
    prompt = f"""
    You are BimaSakhi, an expert insurance advisor.
    USER PROFILE: {user_profile}
    POLICIES: {context_text}
    Recommend ONE policy. Explain why.
    Answer in {language_name}.
    
    HTML FORMAT:
    <div class="policy-card">
       <div class="policy-header"> Best Match: [Product Name]</div>
       <div class="policy-body">
           <p><b>Why:</b> [Reasoning]</p>
           <p class="price">₹[Premium] / year</p>
       </div>
       
       <a href="/products/product/[ID]/" class="buy-btn">View Details</a>
       
    </div>
    """
    
    request.session['survey_step'] = -1 
    return call_gemini(prompt, os.getenv("GEMINI_API_KEY"))


# ==========================================
# 4. HELPER: VALIDATION
# ==========================================
def validate_input(key, text):
    text = text.strip().lower()
    if key == "age":
        numbers = re.findall(r'\d+', text)
        if not numbers: return False, "Please enter a valid number for your age (e.g., 35)."
        if int(numbers[0]) < 18: return False, "You must be 18+ for insurance."
    elif key == "income":
        if not any(c.isdigit() for c in text): return False, "Please enter income in numbers."
    return True, ""


# ==========================================
# 5. UTILS
# ==========================================
def handle_general_chat(user_msg, lang_code):
    language_name = LANGUAGES.get(lang_code, 'English')
    prompt = f"""
    You are BimaSakhi (Insurance Agent).
    User: "{user_msg}"
    Answer in {language_name}. Be helpful and short.
    At the end ask: "Shall I suggest a plan for you?"
    """
    return call_gemini(prompt, os.getenv("GEMINI_API_KEY"))

def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        response.raise_for_status()
        reply = response.json()['candidates'][0]['content']['parts'][0]['text']
        return JsonResponse({"botResponse": reply})
    except:
        return JsonResponse({"botResponse": "Connection error. Please try again."})

def speak_text(request):
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'en').split('-')[0]
    if not text: return HttpResponse(status=400)
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_file = BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        return HttpResponse(audio_file, content_type='audio/mpeg')
    except: return HttpResponse(status=500)

@csrf_exempt
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.session['language'] = data.get('language', 'en')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
