import os
import json
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

from .forms import UserRegistrationForm, OnboardingForm
from .models import Profile, Agent
from insurance.models import Policy

def agent_list(request):
    # Base Query
    agents = Agent.objects.filter(is_verified=True)

    # 1. Search Filters
    city_query = request.GET.get('city', '')
    state_query = request.GET.get('state', '')
    lang_query = request.GET.get('lang', '')
    
    if city_query:
        agents = agents.filter(location__icontains=city_query)
    if state_query and state_query != 'All':
        agents = agents.filter(state__iexact=state_query)
    if lang_query:
        agents = agents.filter(languages__icontains=lang_query)

    # 2. Sorting Logic
    sort_by = request.GET.get('sort', 'rating') # Default sort by rating
    if sort_by == 'experience':
        agents = agents.order_by('-experience_years')
    elif sort_by == 'rating':
        agents = agents.order_by('-rating')

    # 3. Get Unique States for the Dropdown filter
    # This automatically finds all states currently in your database
    available_states = Agent.objects.values_list('state', flat=True).distinct()

    context = {
        'agents': agents,
        'available_states': available_states,
        'current_filters': {
            'city': city_query,
            'state': state_query,
            'lang': lang_query,
            'sort': sort_by
        }
    }
    return render(request, 'accounts/agent_list.html', context)
# ==========================================
# 1. REGISTER VIEW (New Users - Manual)
# ==========================================
def register_view(request):
    """
    Handles manual sign-up with Username/Password.
    Google Sign-up is handled automatically by Allauth.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Note: Profile is created automatically by signals.py
            
            # Log the user in immediately
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, "Account created! Let's set up your profile.")
            return redirect('onboarding') # DIRECT TO INTERACTIVE FORM
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


# ==========================================
# 2. LOGIN VIEW (Old Users - Manual)
# ==========================================
def login_view(request):
    """
    Handles manual login. 
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # The dashboard will handle the check if they need to fill details
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


# ==========================================
# 3. LOGOUT VIEW
# ==========================================
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ==========================================
# 4. ONBOARDING VIEW (The Wizard)
# ==========================================
# ... (keep existing imports) ...

@login_required
def onboarding_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    
    # Multilingual Questions with Images and Validation Rules
    questions_data = [
        {
            'field': 'phone_number',
            'icon': 'phone',
            'image': 'https://cdn-icons-png.flaticon.com/512/3616/3616215.png',
            'regex': '^[0-9]{10}$', # Validates 10 digit number
            'questions': {
                'en-IN': "Please tell me your 10-digit mobile number.",
                'hi-IN': "कृपया अपना 10 अंकों का मोबाइल नंबर बताएं।",
                'mr-IN': "कृपया तुमचा 10 अंकी मोबाईल नंबर सांगा."
            },
            'error_msg': {'en-IN': "That doesn't look like a 10-digit number.", 'hi-IN': "यह 10 अंकों का नंबर नहीं लग रहा है।"}
        },
        {
            'field': 'city',
            'icon': 'map-pin',
            'image': 'https://cdn-icons-png.flaticon.com/512/1149/1149576.png',
            'regex': '.{3,}', # At least 3 characters
            'questions': {
                'en-IN': "In which city do you currently live?",
                'hi-IN': "आप अभी किस शहर में रहते हैं?",
                'mr-IN': "तुम्ही सध्या कोणत्या शहरात राहता?"
            },
            'error_msg': {'en-IN': "Please tell me a valid city name.", 'hi-IN': "कृपया शहर का सही नाम बताएं।"}
        },
        # Add more questions following this same structure...
    ]

    return render(request, 'accounts/onboarding.html', {
        'form': OnboardingForm(instance=profile),
        'questions_json': json.dumps(questions_data)
    })
# ==========================================
# 5. DASHBOARD (The Gatekeeper)
# ==========================================
@login_required
def dashboard_view(request):
    user = request.user
    
    # --- GATEKEEPER LOGIC ---
    try:
        if not hasattr(user, 'profile'):
             Profile.objects.create(user=user)

        if not user.profile.phone_number:
            messages.info(request, "Please complete your profile to continue.")
            return redirect('onboarding')
    except Exception:
        return redirect('onboarding')
    # ------------------------

    # Fetch User Policies
    policies = Policy.objects.filter(user=user)
    
    # Fetch Local Agents based on the User's City
    user_city = user.profile.city or ""
    
    # FIXED LINE: Changed 'city' to 'location' to match your Agent model
    agents = Agent.objects.filter(location__icontains=user_city, is_active=True)
    
    # Fallback if no agents found in that location
    if not agents.exists():
        agents = Agent.objects.filter(is_active=True)[:3]

    context = {
        'user': user,
        'policies': policies,
        'agents': agents,
        'active_count': policies.filter(status='ACTIVE').count()
    }
    return render(request, 'accounts/dashboard.html', context)

# ==========================================
# AUDIO API: SPEAK ONLY (TTS)
# ==========================================
def speak_text_view(request):
    """
    Generates MP3 audio from text using gTTS.
    """
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'en-IN')
    
    # Map full lang code to gTTS code
    lang_map = {
        'en-IN': 'en',
        'hi-IN': 'hi',
        'mr-IN': 'mr'
    }
    lang_code = lang_map.get(lang, 'en')

    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_data = BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        
        response = HttpResponse(audio_data, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)