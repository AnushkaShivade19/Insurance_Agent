from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import json

# Dictionary mapping language codes to their full names for the AI prompt
LANGUAGES = {
    'en': 'English',
    'as': 'Assamese',
    'bn': 'Bengali',
    'brx': 'Bodo',
    'doi': 'Dogri',
    'gu': 'Gujarati',
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ks': 'Kashmiri',
    'kok': 'Konkani',
    'mai': 'Maithili',
    'ml': 'Malayalam',
    'mni': 'Manipuri',
    'mr': 'Marathi',
    'ne': 'Nepali',
    'or': 'Odia',
    'pa': 'Punjabi',
    'sa': 'Sanskrit',
    'sat': 'Santali',
    'sd': 'Sindhi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ur': 'Urdu'
}

# Dictionary for translated welcome messages (can be expanded)
WELCOME_MESSAGES = {
    'en': "Namaste! 🙏 I'm your insurance guide. How can I help you today?",
    'hi': "नमस्ते! 🙏 मैं आपका बीमा गाइड हूँ। मैं आपकी कैसे मदद कर सकता हूँ?",
    'mr': "नमस्कार! 🙏 मी तुमचा विमा मार्गदर्शक आहे. मी तुम्हाला कशी मदत करू शकेन?",
    # Add other welcome messages as needed
}

def chat_view(request):
    """Render the chatbot page and set default language."""
    request.session['language'] = 'en' # Default to English on fresh load
    if 'history' in request.session:
        del request.session['history']
    return render(request, 'chatbot/chat.html')

@csrf_exempt
def set_language(request):
    """Sets the user's chosen language in the session."""
    if request.method == 'POST':
        data = json.loads(request.body)
        lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        
        if 'history' in request.session:
            del request.session['history']
            
        welcome_message = WELCOME_MESSAGES.get(lang_code, WELCOME_MESSAGES['en'])
        return JsonResponse({'status': 'success', 'welcome_message': welcome_message})
    return JsonResponse({'status': 'error'}, status=400)


def get_response(request):
    user_message = request.GET.get('userMessage', '')
    api_key = os.getenv("GEMINI_API_KEY")

    lang_code = request.session.get('language', 'en')
    language_name = LANGUAGES.get(lang_code, 'English')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    history = request.session.get('history', [])

    prompt_instructions = f"""
    You are an insurance assistant for rural users named 'Gramin Suraksha Mitra'.

    **CRITICAL RULES:**
    1.  You **MUST** respond **ONLY** in the **{language_name}** language.
    2.  Explain the user's term in a maximum of 3-4 simple sentences.
    3.  Be very direct and to the point.
    4.  Do NOT use lists or bullet points.
    5.  Use one simple analogy.
    """

    contents = [
        {"parts": [{"text": prompt_instructions}]},
        *history,
        {"parts": [{"text": f"Explain the following: {user_message}"}]}
    ]
    
    data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        bot_message = response.json()['candidates'][0]['content']['parts'][0]['text']

        history.append({"parts": [{"text": user_message}]})
        history.append({"parts": [{"text": bot_message}]})
        request.session['history'] = history[-8:]
    except Exception as e:
        print("HTTP error:", e)
        bot_message = "I'm facing network issues. Please try again later."

    return JsonResponse({"botResponse": bot_message})