from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests, os, json, datetime

# Import models and recommendation logic
# Ensure 'insurance' matches your actual app name
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
    # Clear session data on page load for a fresh start
    if 'history' in request.session:
        del request.session['history']
    if 'survey_state' in request.session:
        del request.session['survey_state']
    return render(request, 'chatbot/chat.html')

@login_required
def get_response(request):
    user_message = request.GET.get('userMessage', '').strip()
    api_key = os.getenv("GEMINI_API_KEY")
    user = request.user
    lang_code = request.session.get('language', 'en')
    language_name = LANGUAGES.get(lang_code, 'English')
    
    # Load Survey Questions based on language
    # Default to English if language not found in dict
    questions = SURVEY_QUESTIONS.get(lang_code, SURVEY_QUESTIONS['en'])
    
    # Keywords to trigger the survey
    start_survey_keywords = ['find a policy', 'recommend', 'suggest', 'पॉलिसी ढूंढो', 'पॉलिसी शोधा', 'शिफारस']
    
    # Load History
    history = request.session.get('history', [])
    
    # --- SCENARIO 1: START OR CONTINUE SURVEY ---
    # Check if user wants to start survey
    if any(keyword in user_message.lower() for keyword in start_survey_keywords) and 'survey_state' not in request.session:
        request.session['survey_state'] = {'step': 1, 'answers': {}}
        return JsonResponse({"botResponse": questions[1]})

    # Handle Active Survey
    if 'survey_state' in request.session:
        state = request.session['survey_state']
        current_step = state['step']
        
        # Save answer (using q0, q1 format for consistency)
        state['answers'][f'q{current_step}'] = user_message
        
        # Check if survey is finished
        if current_step >= len(questions):
            # --- GENERATE RECOMMENDATION ---
            recommended_types = generate_recommendations(state['answers'])
            matching_products = InsuranceProduct.objects.filter(product_type__in=recommended_types, is_active=True)
            
            product_info = "Based on answers, suitable products:\n"
            if matching_products.exists():
                for product in matching_products:
                    product_info += f"- Name: {product.name}, ID: {product.id}, Desc: {product.description}\n"
            else:
                product_info = "Suggest general Health Insurance. No specific matches."

            # Prompt for Recommendation
            prompt = f"""
            You are an insurance expert.
            PRODUCT DATA: {product_info}
            
            TASK:
            1. Recommend these products in **{language_name}**.
            2. Explain WHY briefly.
            3. Use HTML formatting explicitly:
               - Use <ul><li> for bullet points.
               - Use <b> for bold text.
               - Use <br> for new lines.
            4. For every product, add this exact button HTML: 
               <br><a href="/purchase/?product_id=PRODUCT_ID" class="cta-button" style="background:green; color:white; padding:5px; border-radius:5px; text-decoration:none;">Enroll in [Name]</a>
            """
            
            # Reset state
            del request.session['survey_state']
            request.session['history'] = [] # Reset history after survey
            
            # We send this prompt to Gemini below...
            
        else:
            # Move to next question
            next_step = current_step + 1
            state['step'] = next_step
            request.session['survey_state'] = state
            request.session.modified = True
            return JsonResponse({"botResponse": questions[next_step]})
    
    # --- SCENARIO 2: GENERAL Q&A ---
    else:
        # Fetch Policy Context
        user_policies = Policy.objects.filter(user=user)
        policy_context = "User's Policies:\n" if user_policies else "User has no policies."
        for p in user_policies:
            policy_context += f"- Policy #{p.policy_number} ({p.product.name}): Status {p.get_status_display()}, Expires {p.expiry_date.strftime('%d-%b-%Y')}.\n"

        # SYSTEM PROMPT
        prompt = f"""
        You are BimaSakhi, an insurance assistant.
        CONTEXT: {policy_context}
        
        RULES:
        1. Answer ONLY insurance queries (Plans, Claims, User's specific policies).
        2. If asked about non-insurance topics (coding, sports, etc.), refuse politely in {language_name}.
        3. FORMATTING (STRICTLY USE HTML): 
           - Use HTML tags explicitly. 
           - Use <b> for key terms.
           - Use <ul> and <li> for lists.
           - Use <p> for paragraphs.
           - Use <br> for line breaks.
           - DO NOT produce large blocks of plain text.
           - DO NOT use Markdown symbols like ** or *.
        4. Respond in {language_name}.
        
        User Query: {user_message}
        """

    # --- API CALL TO GEMINI ---
    # Correct Model Version: 1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"            
    headers = {"Content-Type": "application/json"}
    
    # Construct Payload with CORRECT Roles
    # History must look like: [{'role': 'user', 'parts': [...]}, {'role': 'model', 'parts': [...]}]
    contents = history + [{"role": "user", "parts": [{"text": prompt}]}]
    data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raises error for 400/500 codes
        
        # Check if response structure is valid
        if 'candidates' in response.json() and len(response.json()['candidates']) > 0:
             bot_message = response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
             bot_message = "I didn't receive a valid response from the server."

        # Update History with ROLES
        history.append({"role": "user", "parts": [{"text": user_message}]})
        history.append({"role": "model", "parts": [{"text": bot_message}]})
        
        # Keep last 10 turns to save token space
        request.session['history'] = history[-10:]
        request.session.modified = True
        
    except requests.exceptions.HTTPError as e:
        print(f"Gemini API Error: {e.response.text}")
        bot_message = "I am currently facing high traffic. Please try again."
    except Exception as e:
        print(f"Server Error: {e}")
        bot_message = "An internal error occurred."
    
    return JsonResponse({"botResponse": bot_message})

@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lang_code = data.get('language', 'en')
        request.session['language'] = lang_code
        if 'history' in request.session:
            del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ... (rest of your auth views: register_view, login_view, logout_view) ...
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
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
                # Redirect to dashboard, or 'chat' if that's your main page
                return redirect('dashboard') 
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')