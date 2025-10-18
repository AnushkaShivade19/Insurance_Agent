from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests, os, json, datetime

# Import models and recommendation logic
from insurance.models import Policy, InsuranceProduct
from .recommendation_logic import generate_recommendations

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
    # Add all other survey question translations here
}

# --- CORE VIEWS ---

@login_required
def chat_view(request):
    if 'history' in request.session: del request.session['history']
    if 'survey_state' in request.session: del request.session['survey_state']
    return render(request, 'chatbot/chat.html')

@login_required
def get_response(request):
    user_message = request.GET.get('userMessage', '').strip()
    api_key = os.getenv("GEMINI_API_KEY")
    user = request.user
    lang_code = request.session.get('language', 'en')
    questions = SURVEY_QUESTIONS.get(lang_code, SURVEY_QUESTIONS['en'])
    
    start_survey_keywords = ['find a policy', 'recommend', 'suggest', 'पॉलिसी ढूंढो', 'पॉलिसी शोधा', 'शिफारस']
    
    history = request.session.get('history', [])
    prompt = ""

    if any(keyword in user_message.lower() for keyword in start_survey_keywords) and 'survey_state' not in request.session:
        request.session['survey_state'] = {'step': 1, 'answers': {}}
        return JsonResponse({"botResponse": questions[1]})

    if 'survey_state' in request.session:
        state = request.session['survey_state']
        current_step = state['step']
        state['answers'][f'q{current_step-1}'] = user_message
        
        if current_step >= len(questions):
            recommended_types = generate_recommendations(state['answers'])
            matching_products = InsuranceProduct.objects.filter(product_type__in=recommended_types, is_active=True)
            
            product_info = "Based on your answers, here are some suitable insurance types:\n"
            if matching_products:
                for product in matching_products: product_info += f"- **{product.name}**: {product.description}\n"
            else: product_info = "Based on your answers, Health Insurance is a good start."
            
            language_name = LANGUAGES.get(lang_code, 'English')
            prompt = f"Present this recommendation conversationally. Explain WHY these are good choices. Respond ONLY in **{language_name}** and be concise.\n\nRecommendation:\n{product_info}"
            del request.session['survey_state']
            history = [] # Use clean history for final recommendation
        else:
            next_step = current_step + 1; state['step'] = next_step; request.session['survey_state'] = state
            return JsonResponse({"botResponse": questions[next_step]})
    else:
        user_policies = Policy.objects.filter(user=user)
        policy_context = "User's policy info:\n" if user_policies else "This user has no policies."
        for p in user_policies: policy_context += f"- Policy #{p.policy_number} ({p.product.name}): Status is {p.get_status_display()}, Expires on {p.expiry_date.strftime('%d-%b-%Y')}.\n"
        
        language_name = LANGUAGES.get(lang_code, 'English')
        prompt = f"You are 'Gramin Suraksha Mitra'. CONTEXT: {policy_context}. RULES: 1. If asked a personal question, answer using ONLY the CONTEXT. 2. If asked a general question, IGNORE context. 3. Respond ONLY in **{language_name}** and be concise. User's Question: {user_message}"

    # --- API CALL FIX ---
    # Using gemini-pro which is compatible with the v1beta endpoint structure we confirmed works.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    contents = history + [{"parts": [{"text": prompt}]}]
    data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        bot_message = response.json()['candidates'][0]['content']['parts'][0]['text']
        
        if history is not None:
             history.append({"parts": [{"text": user_message}]}); history.append({"parts": [{"text": bot_message}]})
             request.session['history'] = history[-8:]
    except Exception as e:
        print("HTTP error:", e); bot_message = "I'm facing network issues. Please try again."
    
    return JsonResponse({"botResponse": bot_message})

# --- HELPER & AUTH VIEWS ---

@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body); lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session: del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid(): user = form.save(); login(request, user); return redirect('dashboard')
    else: form = UserCreationForm()
    return render(request, 'chatbot/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('dashboard') # Redirects to dashboard after successful login
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request); return redirect('login')