import os
import json
import time
import random
import requests
import datetime
from io import BytesIO
from gtts import gTTS

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

# Import models
from insurance.models import Policy, InsuranceProduct
from .constants import SURVEY_QUESTIONS, LANGUAGES

# --- CORE VIEWS ---

@login_required
def chat_view(request):
    """
    Renders the main chat interface.
    Clears old session data to start fresh.
    """
    if 'history' in request.session: del request.session['history']
    if 'survey_state' in request.session: del request.session['survey_state']
    return render(request, 'chatbot/chat.html')

@login_required
def get_response(request):
    user_message = request.GET.get('userMessage', '').strip()
    api_key = os.getenv("GEMINI_API_KEY")
    user = request.user
    lang_code = request.session.get('language', 'en')
    language_name = LANGUAGES.get(lang_code, 'English')
    
    questions = SURVEY_QUESTIONS.get(lang_code, SURVEY_QUESTIONS['en'])
    start_survey_keywords = ['find a policy', 'recommend', 'suggest', 'help me choose', 'पॉलिसी ढूंढो', 'पॉलिसी शोधा', 'शिफारस']
    
    # Load History
    history = request.session.get('history', [])
    if not isinstance(history, list): history = []
    
    # --- LOAD INVENTORY (Context for the AI) ---
    active_products = InsuranceProduct.objects.filter(is_active=True)
    product_inventory = ""
    
    if active_products.exists():
        for prod in active_products:
            product_inventory += (
                f"ID: {prod.id} | NAME: {prod.name}\n"
                f"TYPE: {prod.product_type} | PREMIUM: ₹{prod.base_premium}/yr\n"
                f"BEST FOR: {prod.description}\n"
                f"KEY FEATURES: {prod.key_features}\n"
                f"-----------------------------------\n"
            )
    else:
        product_inventory = "No active policies available right now."

    prompt = ""

    # ====================================================
    # SCENARIO 1: SURVEY & CONSULTATION FLOW
    # ====================================================
    if any(keyword in user_message.lower() for keyword in start_survey_keywords) and 'survey_state' not in request.session:
        request.session['survey_state'] = {'step': 1, 'answers': {}}
        return JsonResponse({"botResponse": questions[1]})

    if 'survey_state' in request.session:
        state = request.session['survey_state']
        current_step = state['step']
        state['answers'][f'q{current_step}'] = user_message 
        
        # IF SURVEY COMPLETE -> PITCH THE PRODUCT
        if current_step >= len(questions) - 1:
            prompt = f"""
            **ACT AS:** A senior, empathetic human insurance agent named BimaSakhi.
            **LANGUAGE:** {language_name} ONLY.
            
            **THE USER'S NEEDS (Survey Results):**
            {json.dumps(state['answers'])}

            **YOUR INVENTORY:**
            {product_inventory}

            **YOUR GOAL:** Don't just list products. **SELL** the solution. explain WHY these specific plans fit their age, income, and family status.

            **RESPONSE FORMAT (Strict HTML):**
            1. **The Hook:** "Thank you for sharing details. Based on your family size/income, I highly recommend these 2 plans to secure your future:"
            
            2. **The Pitch (Repeat for top 2 recommendations):**
               <div class="product-card">
                  <h3>[Product Name]</h3>
                  <ul>
                      <li><b>Why I chose this for you:</b> [Connect to their specific survey answer]</li>
                      <li><b>Real Benefit:</b> [e.g., "If you get sick, we pay the hospital directly."]</li>
                      <li><b>Cost:</b> Just ₹[Premium] per year.</li>
                  </ul>
                  <br>
                  <a href="/purchase/?product_id=ID" class="cta-button">View Plan & Buy</a>
               </div>
               <br>
            
            3. **The Close:** "Shall we proceed with the first one? It offers the best value for your family."
            """
            del request.session['survey_state']
            history = [] 
        else:
            next_step = current_step + 1
            state['step'] = next_step
            request.session['survey_state'] = state
            return JsonResponse({"botResponse": questions[next_step]})
    
    # ====================================================
    # SCENARIO 2: GENERAL CONVERSATION & OBJECTION HANDLING
    # ====================================================
    else:
        user_policies = Policy.objects.filter(user=user)
        user_context = "User's Policies: " + (", ".join([p.product.name for p in user_policies]) if user_policies else "None")
        
        prompt = f"""
        **SYSTEM INSTRUCTION:** You are BimaSakhi, the best insurance agent in the village. You are talking to a rural customer in {language_name}.
        
        **KNOWLEDGE BASE:** {product_inventory}
        **USER CONTEXT:** {user_context}
        **USER SAYS:** "{user_message}"
        
        **YOUR BEHAVIOR GUIDELINES:**
        1. **BE A HUMAN AGENT:** - Use simple analogies. "Insurance is like a spare tyre for your life."
           - If they say "It's too expensive", say: "I understand. But think of it as buying seeds. A small cost now saves your entire land later."
           
        2. **VISUAL AIDS (CRITICAL):**
           - If explaining a complex process (e.g., Claims, Coverage Types), you MUST insert a diagram tag.
           - Example: "Here is how the claim process works: " or "See the difference here: ".
           - Place this tag immediately after the explanation.

        3. **ALWAYS BE CLOSING (ABC):**
           - Never just give information. Always follow up with a specific product recommendation.
           - "We have the **[Product Name]** that solves exactly this."
           - <a href="/purchase/?product_id=ID" class="cta-button">Check Premium</a>

        4. **FORMAT:** Use <b>bold</b> for key terms. Use bullet points.
        """

    # ====================================================
    # API CALL (Fixed: gemini-1.5-flash & Retry Logic)
    # ====================================================
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Prepare History
    api_contents = []
    for entry in history:
        if isinstance(entry, dict) and 'role' in entry and 'parts' in entry:
            api_contents.append(entry)

    # Add Prompt
    api_contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Config: Higher token limit for detailed selling
    payload = {
        "contents": api_contents,
        "generationConfig": {
            "temperature": 0.4, 
            "maxOutputTokens": 2000, 
        }
    }

    # --- ROBUST RETRY LOOP ---
    max_retries = 3
    bot_message = "Network error. Please try again."

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if 'candidates' in data and data['candidates']:
                bot_message = data['candidates'][0]['content']['parts'][0]['text']
                
                # Update Session History
                api_contents.pop() # Remove system prompt
                api_contents.append({"role": "user", "parts": [{"text": user_message}]})
                api_contents.append({"role": "model", "parts": [{"text": bot_message}]})
                request.session['history'] = api_contents[-6:]
                break 
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Exponential Backoff for Rate Limits
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit hit. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                print(f"API Error: {e}")
                bot_message = "My connection is weak right now. Please ask again in a moment."
                break
        except Exception as e:
            print(f"Server Error: {e}")
            break

    return JsonResponse({"botResponse": bot_message})

@csrf_exempt
@login_required
def set_language(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.session['language'] = data.get('language', 'en')
        if 'history' in request.session: del request.session['history']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def speak_text(request):
    """
    Converts text to speech using Google's TTS API server-side 
    and streams the audio buffer (Vercel Safe).
    """
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'en')

    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    lang_code = lang.split('-')[0] 

    try:
        # Generate Speech
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to memory buffer (No file system access needed)
        audio_data = BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)

        # Return as audio response
        response = HttpResponse(audio_data, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- AUTH VIEWS ---

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
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')