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

    # --- SCENARIO 1: START OR CONTINUE SURVEY ---
    if any(keyword in user_message.lower() for keyword in start_survey_keywords) and 'survey_state' not in request.session:
        request.session['survey_state'] = {'step': 1, 'answers': {}}
        return JsonResponse({"botResponse": questions[1]})

    if 'survey_state' in request.session:
        state = request.session['survey_state']
        current_step = state['step']
        state['answers'][f'q{current_step-1}'] = user_message
        
        if current_step >= len(questions):
            # RECOMMENDATION LOGIC (Existing code)
            recommended_types = generate_recommendations(state['answers'])
            matching_products = InsuranceProduct.objects.filter(product_type__in=recommended_types, is_active=True)
            
            product_info_for_ai = "Based on the user's answers, the following products are suitable:\n"
            if matching_products.exists():
                for product in matching_products:
                    product_info_for_ai += f"- Product Name: {product.name}, Product ID: {product.id}, Description: {product.description}\n"
            else:
                product_info_for_ai = "Based on the user's answers, Health Insurance is a good starting point. No specific products match perfectly."

            language_name = LANGUAGES.get(lang_code, 'English')
            
            prompt = f"""
            You are presenting insurance recommendations.
            PRODUCT DATA: {product_info_for_ai}
            YOUR TASK & RULES:
            1. Explain WHY these products are a good choice.
            2. For EACH recommended product, provide this link format: `<a href="/purchase/?product_id=PRODUCT_ID" class="cta-button">Enroll in [Product Name]</a>`.
            3. Respond ONLY in **{language_name}**.
            4. Explain using simple terms.
            5. Format response in HTML.
            """
            
            del request.session['survey_state']
            history = [] 

        else:
            next_step = current_step + 1; state['step'] = next_step; request.session['survey_state'] = state
            return JsonResponse({"botResponse": questions[next_step]})
    
    # --- SCENARIO 2: GENERAL Q&A (UPDATED RESTRICTION LOGIC) ---
    else:
        user_policies = Policy.objects.filter(user=user)
        policy_context = "User's policy info:\n" if user_policies else "This user has no policies."
        for p in user_policies: policy_context += f"- Policy #{p.policy_number} ({p.product.name}): Status is {p.get_status_display()}, Expires on {p.expiry_date.strftime('%d-%b-%Y')}.\n"
        
        language_name = LANGUAGES.get(lang_code, 'English')
        
        # --- HERE IS THE CRITICAL CHANGE ---
        prompt = f"""
        You are BimaSakhi, an AI assistant dedicated EXCLUSIVELY to the insurance domain.
        
        CONTEXT:
        {policy_context}
        
        STRICT GUIDELINES:
        1. **SCOPE RESTRICTION:** You must ONLY answer questions related to:
           - Insurance concepts (Life, Health, Vehicle, etc.)
           - The user's specific policies (from the CONTEXT above).
           - Claims, premiums, coverage, and financial safety.
           
        2. **REFUSAL PROTOCOL:** If the user asks about ANY topic outside of insurance (e.g., coding, sports, cooking, history, math, general chit-chat, or politics), you MUST politely refuse.
           - Say exactly: "I apologize, but I am an insurance assistant. I can only help you with insurance-related queries." (Translate this refusal to {language_name}).
           
        3. **PERSONAL DATA:** If the user asks about their specific details, use the CONTEXT provided.
        
        4. **LANGUAGE:** Respond ONLY in **{language_name}**.
        
        User's Question: {user_message}
        """

    # 1. API Call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"            
    headers = {"Content-Type": "application/json"}
    
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

@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body); lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session: del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ... (rest of your auth views: register_view, login_view, logout_view remain unchanged) ...
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
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request); return redirect('login')