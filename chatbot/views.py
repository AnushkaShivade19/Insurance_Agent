from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests, os, json, datetime
from django.http import HttpResponse, JsonResponse
from gtts import gTTS
from io import BytesIO
# Import models and recommendation logic
from insurance.models import Policy, InsuranceProduct
from .recommendation_logic import generate_recommendations
import random
import time
# --- DICTIONARIES FOR LANGUAGE AND SURVEY ---

LANGUAGES = {
    'en': 'English', 'as': 'Assamese', 'bn': 'Bengali', 'brx': 'Bodo', 'doi': 'Dogri', 'gu': 'Gujarati', 'hi': 'Hindi',
    'kn': 'Kannada', 'ks': 'Kashmiri', 'kok': 'Konkani', 'mai': 'Maithili', 'ml': 'Malayalam', 'mni': 'Manipuri',
    'mr': 'Marathi', 'ne': 'Nepali', 'or': 'Odia', 'pa': 'Punjabi', 'sa': 'Sanskrit', 'sat': 'Santali', 'sd': 'Sindhi',
    'ta': 'Tamil', 'te': 'Telugu', 'ur': 'Urdu'
}

SURVEY_QUESTIONS = {
    'en': { 1: "Who are you looking to insure?", 2: "What is your main occupation?", 3: "Which age group do you belong to?", 4: "Do you own a vehicle (like a tractor, bike, or car)?", },
    'hi': { 1: "आप किसका बीमा कराना चाहते हैं?", 2: "आपका मुख्य व्यवसाय क्या है?", 3: "आप किस आयु वर्ग के हैं?", 4: "क्या आपके पास कोई वाहन है?", },
    'mr': { 1: "तुम्ही कोणाचा विमा काढू इच्छिता?", 2: "तुमचा मुख्य व्यवसाय काय आहे?", 3: "तुम्ही कोणत्या वयोगटातील आहात?", 4: "तुमच्याकडे वाहन आहे का?", },
}

# --- CORE VIEWS ---

@login_required
def chat_view(request):
    if 'history' in request.session: del request.session['history']
    if 'survey_state' in request.session: del request.session['survey_state']
    return render(request, 'chatbot/chat.html')


import os
import json
import time
import random
import requests
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from insurance.models import InsuranceProduct, Policy 
from gtts import gTTS
from io import BytesIO

# --- LANGUAGE MAP ---
LANGUAGES = {
    'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 
    'gu': 'Gujarati', 'bn': 'Bengali', 'ta': 'Tamil'
}

def get_response(request):
    user_message = request.GET.get('userMessage', '').strip()
    context = request.GET.get('context', '').strip()
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. GET LANGUAGE (Default to English)
    lang_code = request.session.get('language', 'en')
    language_name = LANGUAGES.get(lang_code, 'English')

    # 2. STRICT SYSTEM PROMPT
    SYSTEM_PROMPT = f"""
    You are 'BimaSakhi', a trusted insurance advisor.
    
    **CRITICAL LANGUAGE RULE:** You MUST reply ONLY in **{language_name}**. Do not mix languages.
    If the user speaks a different language, politely answer in **{language_name}**.

    **Goal:** Educate simply, build trust, and sell policies.

    **FORMATTING RULES:**
    1. Use **bold** for key terms (e.g., **Premium**, **Coverage**).
    2. Keep answers short (under 60 words) for better audio reading.
    3. When recommending a policy, use this HTML format EXACTLY:
    
    <div class="policy-card">
       <div class="policy-header">🏆 Recommended: [Product Name]</div>
       <div class="policy-body">
           <p><b>Why:</b> [1-sentence reason]</p>
           <p class="price">₹[Premium] / year</p>
       </div>
       <a href="/purchase/?product_id=[ID]" class="buy-btn">View & Buy Now</a>
    </div>
    """

    # 3. FETCH INVENTORY
    active_products = InsuranceProduct.objects.filter(is_active=True).values('id', 'name', 'base_premium', 'description')
    inventory_text = "\n".join([f"ID {p['id']}: {p['name']} @ ₹{p['base_premium']}" for p in active_products])

    # 4. FINAL PROMPT CONSTRUCTION
    final_prompt = f"""
    {SYSTEM_PROMPT}
    
    **INVENTORY:**
    {inventory_text}
    
    **USER CONTEXT:** Looking at '{context}' (if any).
    **USER SAYS:** "{user_message}"
    """

    # 5. API CALL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": final_prompt}]}]})
        response.raise_for_status()
        bot_reply = response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        bot_reply = "I am having trouble connecting. Please try again."

    return JsonResponse({"botResponse": bot_reply})

# TTS View (Unchanged but ensuring it works)
def speak_text(request):
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'en')
    
    # Map 'en-IN' to 'en' for gTTS compatibility
    lang = lang.split('-')[0] 
    
    if not text: return HttpResponse(status=400)
    try:
        tts = gTTS(text=text, lang=lang, tld='co.in', slow=False)
        audio_file = BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        return HttpResponse(audio_file, content_type='audio/mpeg')
    except: return HttpResponse(status=500)
    return JsonResponse({"botResponse": bot_reply})

@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body); lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session: del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body); lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session: del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def speak_text(request):
    """
    Converts text to speech using Google's TTS API server-side 
    and returns an audio file.
    """
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'en')

    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    # Clean the language code (e.g., 'en-IN' -> 'en')
    # gTTS supports some regional codes, but 'en', 'hi', 'mr', etc. are safest.
    # You might need a mapping dictionary if exact codes don't match.
    lang_code = lang.split('-')[0] 

    try:
        # Generate Speech
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to memory buffer
        audio_data = BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)

        # Return as audio response
        response = HttpResponse(audio_data, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)