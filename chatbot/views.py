import os
import json
import requests
import re
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from gtts import gTTS
from io import BytesIO
from insurance.models import InsuranceProduct

# ==========================================
# 1. CONFIGURATIONS
# ==========================================

LANGUAGES = {
    'en': 'English', 
    'hi': 'Hindi', 
    'mr': 'Marathi', 
    'gu': 'Gujarati', 
    'bn': 'Bengali', 
    'ta': 'Tamil',
    'te': 'Telugu', 
    'kn': 'Kannada', 
    'ml': 'Malayalam', 
    'pa': 'Punjabi'
}

# The Keys for saving data
SURVEY_STEPS = ["occupation", "age", "income", "vehicle"]

# The Scripts (Questions) - NOW INCLUDES ALL LANGUAGES
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
    'mr': [
        "योग्य योजना शोधण्यासाठी, मला काही तपशील हवे आहेत. प्रथम, तुमचा **मुख्य व्यवसाय** काय आहे?",
        "समजले. तुमचे सध्याचे **वय** काय आहे?",
        "साधारणपणे, तुमचे **वार्षिक कौटुंबिक उत्पन्न** किती आहे?",
        "तुमच्याकडे **वाहन** (कार, बाईक, ट्रॅक्टर) आहे का?"
    ],
    'gu': [
        "યોગ્ય પ્લાન શોધવા માટે, મારે થોડી વિગતો જોઈએ છે. પ્રથમ, તમારો **મુખ્ય વ્યવસાય** શું છે?",
        "સમજાયું. તમારી વર્તમાન **ઉંમર** શું છે?",
        "આશરે, તમારી **વાર્ષિક કૌટુંબિક આવક** કેટલી છે?",
        "શું તમારી પાસે **વાહન** (કાર, બાઈક, ટ્રેક્ટર) છે?"
    ],
    'bn': [
        "সঠিক পরিকল্পনা খুঁজে পেতে, আমার কিছু বিবরণ প্রয়োজন। প্রথমত, আপনার **প্রধান পেশা** কী?",
        "বুঝলাম। আপনার বর্তমান **বয়স** কত?",
        "মোটামুটিভাবে, আপনার **বার্ষিক পারিবারিক আয়** কত?",
        "আপনার কি কোনো **যানবাহন** (গাড়ি, বাইক, ট্রাক্টর) আছে?"
    ],
    'ta': [
        "சரியான திட்டத்தைக் கண்டறிய, எனக்கு சில விவரங்கள் தேவை. முதலில், உங்கள் **முக்கிய தொழில்** என்ன?",
        "புரிந்தது. உங்கள் தற்போதைய **வயது** என்ன?",
        "தோராயமாக, உங்கள் **ஆண்டு குடும்ப வருமானம்** என்ன?",
        "உங்களிடம் **வாகனம்** (கார், பைக், டிராக்டர்) உள்ளதா?"
    ],
    'te': [
        "సరైన పాలసీని కనుగొనడానికి, నాకు కొన్ని వివరాలు కావాలి. ముందుగా, మీ **ప్రధాన వృత్తి** ఏమిటి?",
        "అర్థమైంది. మీ ప్రస్తుత **వయస్సు** ఎంత?",
        "సుమారుగా, మీ **కుటుంబ వార్షిక ఆదాయం** ఎంత?",
        "మీకు ఏదైనా **వాహనం** (కారు, బైక్, ట్రాక్టర్) ఉందా?"
    ],
    'kn': [
        "ಸೂಕ್ತವಾದ ಯೋಜನೆಯನ್ನು ಹುಡುಕಲು, ನನಗೆ ಕೆಲವು ವಿವರಗಳು ಬೇಕು. ಮೊದಲನೆಯದಾಗಿ, ನಿಮ್ಮ **ಮುಖ್ಯ ಉದ್ಯೋಗ** ಯಾವುದು?",
        "ಅರ್ಥವಾಯಿತು. ನಿಮ್ಮ ಪ್ರಸ್ತುತ **ವಯಸ್ಸು** ಎಷ್ಟು?",
        "ಅಂದಾಜು, ನಿಮ್ಮ **ವಾರ್ಷಿಕ ಕುಟುಂಬ ಆದಾಯ** ಎಷ್ಟು?",
        "ನಿಮ್ಮ ಬಳಿ **ವಾಹನ** (ಕಾರು, ಬೈಕ್, ಟ್ರ್ಯಾಕ್ಟರ್) ಇದೆಯೇ?"
    ],
    'ml': [
        "ശരിയായ പ്ലാൻ കണ്ടെത്തുന്നതിന്, എനിക്ക് ചില വിവരങ്ങൾ ആവശ്യമാണ്. ആദ്യം, നിങ്ങളുടെ **പ്രധാന ജോലി** എന്താണ്?",
        "മനസ്സിലായി. നിങ്ങളുടെ ഇപ്പോഴത്തെ **പ്രായം** എത്രയാണ്?",
        "ഏകദേശം, നിങ്ങളുടെ **വാർഷിക കുടുംബ വരുമാനം** എത്രയാണ്?",
        "നിങ്ങൾക്ക് സ്വന്തമായി **വാഹനം** (കാർ, ബൈക്ക്, ട്രാക്ടർ) ഉണ്ടോ?"
    ],
    'pa': [
        "ਸਹੀ ਯੋਜਨਾ ਲੱਭਣ ਲਈ, ਮੈਨੂੰ ਕੁਝ ਵੇਰਵਿਆਂ ਦੀ ਲੋੜ ਹੈ। ਪਹਿਲਾਂ, ਤੁਹਾਡਾ **ਮੁੱਖ ਕਿੱਤਾ** ਕੀ ਹੈ?",
        "ਸਮਝ ਗਿਆ। ਤੁਹਾਡੀ ਮੌਜੂਦਾ **ਉਮਰ** ਕੀ ਹੈ?",
        "ਮੋਟੇ ਤੌਰ 'ਤੇ, ਤੁਹਾਡੀ **ਸਾਲਾਨਾ ਪਰਿਵਾਰਕ ਆਮਦਨ** ਕਿੰਨੀ ਹੈ?",
        "ਕੀ ਤੁਹਾਡੇ ਕੋਲ ਕੋਈ **ਵਾਹਨ** (ਕਾਰ, ਬਾਈਕ, ਟਰੈਕਟਰ) ਹੈ?"
    ]
}

# ==========================================
# 2. CORE VIEWS
# ==========================================

def chat_view(request):
    # Reset survey if page is refreshed to start fresh interaction
    if 'survey_step' in request.session: 
        del request.session['survey_step']
    return render(request, 'chatbot/chat.html')

def get_response(request):
    user_msg = request.GET.get('userMessage', '').strip()
    lang_code = request.session.get('language', 'en')
    
    # Initialize Session if not present
    if 'survey_step' not in request.session:
        request.session['survey_step'] = -1
        request.session['survey_data'] = {}

    step = request.session['survey_step']

    # --- ROUTE 1: IN SURVEY? ---
    if step >= 0:
        return handle_survey_logic(request, user_msg, lang_code)

    # --- ROUTE 2: INTENT DETECTION ---
    buy_keywords = ['buy', 'plan', 'suggest', 'recommend', 'policy', 'best', 'insurance for me', 'start', 'find', 'help']
    if any(k in user_msg.lower() for k in buy_keywords):
        # Start Survey
        request.session['survey_step'] = 0
        request.session['survey_data'] = {} # Clear old data
        
        # Get script for selected language, fallback to English if somehow missing
        scripts = SURVEY_SCRIPTS.get(lang_code, SURVEY_SCRIPTS['en'])
        
        # Localized Intro
        intros = {
            'en': "Sure! I can help you find the best policy. ",
            'hi': "ज़रूर! मैं आपको सबसे अच्छी पॉलिसी खोजने में मदद कर सकती हूँ। ",
            'mr': "नक्कीच! मी तुम्हाला सर्वोत्तम पॉलिसी शोधण्यात मदत करू शकते. ",
            'te': "తప్పకుండా! మీకు ఉత్తమమైన పాలసీని కనుగొనడంలో నేను సహాయపడగలను. "
        }
        intro = intros.get(lang_code, intros['en'])
        
        return JsonResponse({"botResponse": intro + scripts[0]})

    # --- ROUTE 3: GENERAL CHAT ---
    return handle_general_chat(user_msg, lang_code)


# ==========================================
# 3. HELPER: SURVEY LOGIC
# ==========================================
def handle_survey_logic(request, user_msg, lang_code):
    step = request.session['survey_step']
    survey_data = request.session['survey_data']
    
    # 1. Identify current question key
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

        # Check if we have a next question
        if next_step < len(SURVEY_STEPS):
            request.session['survey_step'] = next_step
            return JsonResponse({"botResponse": scripts[next_step]})
    
    # 5. SURVEY COMPLETE -> RAG (Recommendation)
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
    AVAILABLE POLICIES: {context_text}
    
    Task: Recommend ONE best policy from the list based on the profile.
    Explain why in {language_name}.
    
    HTML FORMAT:
    <div class="policy-card">
       <div class="policy-header">🏆 Best Match: [Product Name]</div>
       <div class="policy-body">
           <p><b>Why:</b> [Reasoning in {language_name}]</p>
           <p class="price">₹[Premium] / year</p>
       </div>
       <a href="/products/product/[ID]/" class="buy-btn">View Details</a>
    </div>
    """
    
    request.session['survey_step'] = -1  # Reset survey
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
        # Relaxed validation to allow "5 lakhs", "50000", etc.
        if not any(c.isdigit() for c in text): return False, "Please enter income amount."
    return True, ""


# ==========================================
# 5. UTILS & AI CALL
# ==========================================
def handle_general_chat(user_msg, lang_code):
    language_name = LANGUAGES.get(lang_code, 'English')
    prompt = f"""
    You are BimaSakhi (Insurance Agent).
    User: "{user_msg}"
    Answer in {language_name}. Be helpful, empathetic, and concise.
    If the user seems interested in buying, ask: "Shall I suggest a plan for you?"
    """
    return call_gemini(prompt, os.getenv("GEMINI_API_KEY"))

def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        response.raise_for_status()
        reply = response.json()['candidates'][0]['content']['parts'][0]['text']
        return JsonResponse({"botResponse": reply})
    except Exception as e:
        print(f"Gemini Error: {e}")
        return JsonResponse({"botResponse": "I am having trouble connecting. Please try again."})

# ==========================================
# 6. AUDIO & LANGUAGE (GTTS Implementation)
# ==========================================

def speak_text(request):
    """
    Generates audio using Google Text-to-Speech (gTTS).
    """
    text = request.GET.get('text', '')
    # Get lang code (e.g., 'hi' from 'hi-IN')
    lang = request.GET.get('lang', 'en').split('-')[0] 
    
    if not text: 
        return HttpResponse(status=400)
    
    try:
        # Generate Audio using gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to memory buffer instead of disk
        audio_file = BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        
        return HttpResponse(audio_file, content_type='audio/mpeg')
    except Exception as e:
        print(f"TTS Error: {e}")
        return HttpResponse(status=500)

@csrf_exempt
def set_language(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lang_code = data.get('language', 'en')
            if lang_code in LANGUAGES:
                request.session['language'] = lang_code
                return JsonResponse({'status': 'success', 'language': LANGUAGES[lang_code]})
        except:
            pass
    return JsonResponse({'status': 'error'}, status=400)
