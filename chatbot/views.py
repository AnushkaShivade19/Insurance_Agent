# chatbot/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import json
import datetime
# Import the Policy model from your 'insurance' app
from insurance.models import Policy

# This dictionary maps the short language code to the full name for the AI
LANGUAGES = {
    'en': 'English', 'as': 'Assamese', 'bn': 'Bengali', 'brx': 'Bodo', 'doi': 'Dogri',
    'gu': 'Gujarati', 'hi': 'Hindi', 'kn': 'Kannada', 'ks': 'Kashmiri', 'kok': 'Konkani',
    'mai': 'Maithili', 'ml': 'Malayalam', 'mni': 'Manipuri', 'mr': 'Marathi', 'ne': 'Nepali',
    'or': 'Odia', 'pa': 'Punjabi', 'sa': 'Sanskrit', 'sat': 'Santali', 'sd': 'Sindhi',
    'ta': 'Tamil', 'te': 'Telugu', 'ur': 'Urdu'
}

@login_required
def chat_view(request):
    """Render the main chat page. Requires user to be logged in."""
    # Set default language and clear history for a new session
    request.session['language'] = 'en'
    if 'history' in request.session:
        del request.session['history']
    return render(request, 'chatbot/chat.html')

@csrf_exempt
@login_required
def set_language(request):
    """Sets the user's chosen language in the session."""
    if request.method == 'POST':
        data = json.loads(request.body)
        lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session:
            del request.session['history'] # Reset history on language change
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_response(request):
    """
    The main chatbot logic: fetches user data, constructs a prompt,
    and gets a response from the Gemini API.
    """
    user_message = request.GET.get('userMessage', '')
    api_key = os.getenv("GEMINI_API_KEY")

    # --- 1. Fetch Personalized Data from Database ---
    user = request.user
    user_policies = Policy.objects.filter(user=user)
    policy_context = ""
    if user_policies.exists():
        policy_context += "Here is the logged-in user's personal insurance policy information:\n"
        for policy in user_policies:
            days_until_expiry = (policy.expiry_date - datetime.date.today()).days
            policy_context += f"- Policy #{policy.policy_number} ({policy.product.name}): Status is {policy.get_status_display()}, Premium is ₹{policy.premium_amount}, Expires on {policy.expiry_date.strftime('%d-%b-%Y')} ({days_until_expiry} days from now).\n"
    else:
        policy_context = "This user currently has no active insurance policies."

    # --- 2. Prepare for API Call ---
    lang_code = request.session.get('language', 'en')
    language_name = LANGUAGES.get(lang_code, 'English')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    history = request.session.get('history', [])

    # --- 3. Construct the AI Prompt with User Data and Rules ---
    prompt_instructions = f"""
    You are 'Gramin Suraksha Mitra', a helpful insurance assistant.

    USER'S PERSONAL DATA (CONTEXT):
    {policy_context}

    YOUR TASK & RULES:
    1.  First, determine if the user is asking a general question OR a question about their own policies (e.g., "when does my policy expire?", "what is my premium?").
    2.  If it is a personal question, you MUST use the information from the CONTEXT section to answer.
    3.  If it is a general question, IGNORE the context and answer it from your general knowledge.
    4.  You MUST respond ONLY in the **{language_name}** language.
    5.  Keep all answers very concise and simple (2-4 sentences max). Do NOT use lists.
    """

    contents = [
        {"parts": [{"text": prompt_instructions}]},
        *history,
        {"parts": [{"text": f"User's Question: {user_message}"}]}
    ]
    data = {"contents": contents}

    # --- 4. Call API and Handle Response ---
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


# --- AUTHENTICATION VIEWS ---

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat')
    else:
        form = UserCreationForm()
    return render(request, 'chatbot/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('chat')
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')