from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import InsuranceProduct, ProductTranslation, AgentRequest, Policy
from gtts import gTTS
import io
from django.utils import timezone
from datetime import timedelta

# 1. SEARCH & FILTER VIEW
def product_list(request):
    """
    Displays all products with optional filtering by category.
    """
    category = request.GET.get('category') # e.g., ?category=HEALTH
    products = InsuranceProduct.objects.filter(is_active=True)

    if category:
        products = products.filter(product_type=category)

    context = {
        'products': products,
        'selected_category': category,
        'categories': InsuranceProduct.POLICY_TYPE_CHOICES,
    }
    return render(request, 'insurance/product_list.html', context)

# 2. PRODUCT DETAIL VIEW (Multilingual)
def product_detail(request, pk):
    product = get_object_or_404(InsuranceProduct, pk=pk)
    selected_lang = request.GET.get('lang', 'en') # Default to English
    
    # Default content
    description = product.description
    features = product.key_features

    # Fetch translation if not English
    if selected_lang != 'en':
        translation = ProductTranslation.objects.filter(product=product, language=selected_lang).first()
        if translation:
            description = translation.translated_description
            features = translation.translated_key_features

    context = {
        'product': product,
        'selected_lang': selected_lang,
        'description': description,
        'features': features,
        'languages': ProductTranslation.LANGUAGE_CHOICES,
    }
    return render(request, 'insurance/product_detail.html', context)

# 3. VOICE ASSISTANCE API (gTTS)
from googletrans import Translator 

def get_audio_description(request, pk):
    """
    1. Fetches English text from DB.
    2. Translates it to the selected language (e.g., Hindi).
    3. Converts that translated text to Audio.
    """
    product = get_object_or_404(InsuranceProduct, pk=pk)
    target_lang = request.GET.get('lang', 'en')
    
    # 1. Get original English Text
    text_to_speak = product.description
    
    # 2. Translate if not English
    if target_lang != 'en':
        try:
            translator = Translator()
            # Translate English -> Target Language
            translation = translator.translate(text_to_speak, dest=target_lang)
            text_to_speak = translation.text
            print(f"DEBUG: Translated to {target_lang}: {text_to_speak[:50]}...")
        except Exception as e:
            print(f"Translation Failed: {e}")
            # Fallback: Speak English if translation fails (prevents crash)
            target_lang = 'en' 

    # Clean up text (remove Markdown symbols that sound weird)
    text_to_speak = text_to_speak.replace('*', '').replace('#', '').replace('-', '')

    try:
        # 3. Generate Audio using gTTS with the TRANSLATED text
        tts = gTTS(text=text_to_speak, lang=target_lang, slow=False)
        
        # Save to memory buffer
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        
        response = HttpResponse(audio_file, content_type='audio/mpeg')
        response['Content-Disposition'] = f'inline; filename="desc_{pk}_{target_lang}.mp3"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# 4. AGENT REQUEST ACTION
@login_required
def talk_to_agent(request, pk):
    product = get_object_or_404(InsuranceProduct, pk=pk)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        lang = request.POST.get('language')
        
        AgentRequest.objects.create(
            user=request.user,
            product=product,
            phone_number=phone,
            preferred_language=lang
        )
        messages.success(request, "Request submitted! An agent will call you shortly.")
    
    return redirect('product_detail', pk=pk)

# 5. BUY POLICY ACTION
@login_required
def buy_policy(request, pk):
    product = get_object_or_404(InsuranceProduct, pk=pk)
    
    # In a real app, integrate Payment Gateway here.
    # For now, we create a PENDING policy.
    import uuid
    Policy.objects.create(
        user=request.user,
        product=product,
        policy_number=str(uuid.uuid4())[:10].upper(),
        status='PENDING_APPROVAL',
        start_date=timezone.now().date(),
        expiry_date=timezone.now().date() + timedelta(days=365),
        premium_amount=product.base_premium,
        sum_assured=500000 
    )
    messages.success(request, f"Application for {product.name} submitted successfully!")
    return redirect('product_detail', pk=pk)