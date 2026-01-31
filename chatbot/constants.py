# Mapping of Language Codes (2-letter) to Full Names
LANGUAGES = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'mr': 'मराठी (Marathi)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)',
    'bn': 'বাংলা (Bengali)',
    'gu': 'ગુજરાતી (Gujarati)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'ml': 'മലയാളം (Malayalam)',
    'pa': 'ਪੰਜਾਬੀ (Punjabi)',
    'ur': 'اردو (Urdu)'
}

# Survey Questions for Policy Recommendation
# Index 0 is a placeholder title (since we start steps at 1).
# You can customize these questions based on your insurance logic.

SURVEY_QUESTIONS = {
    'en': [
        "Survey Start",  # Index 0 (Placeholder)
        "Let's find the best policy for you. First, could you tell me your **age**?",
        "Great. What is your approximate **annual income**?",
        "Who are you looking to insure? (e.g., Self, Family, Parents, or Child)",
        "Do you have any existing medical conditions or history of illness? (Yes/No)",
        "Finally, what is your primary goal? (e.g., Tax Saving, Health Protection, Investment, or Life Cover)"
    ],
    'hi': [
        "Survey Start",
        "चलिए आपके लिए सबसे अच्छी पॉलिसी ढूंढते हैं। सबसे पहले, क्या आप मुझे अपनी **उम्र** बता सकते हैं?",
        "बहुत बढ़िया। आपकी अनुमानित **वार्षिक आय** (Annual Income) क्या है?",
        "आप किसका बीमा करवाना चाहते हैं? (जैसे: स्वयं, परिवार, माता-पिता, या बच्चे)",
        "क्या आपको कोई पुरानी बीमारी या मेडिकल हिस्ट्री है? (हाँ / नहीं)",
        "अंत में, आपका मुख्य लक्ष्य क्या है? (जैसे: टैक्स बचत, स्वास्थ्य सुरक्षा, निवेश, या जीवन बीमा)"
    ],
    'mr': [
        "Survey Start",
        "चला, तुमच्यासाठी सर्वोत्तम पॉलिसी शोधूया. प्रथम, तुम्ही मला तुमचे **वय** सांगू शकाल का?",
        "छान. तुमचे अंदाजे **वार्षिक उत्पन्न** (Annual Income) किती आहे?",
        "तुम्ही कोणाचा विमा उतरवू इच्छिता? (उदा. स्वतःचा, कुटुंबाचा, पालकांचा किंवा मुलांचा)",
        "तुम्हाला कोणताही जुना आजार किंवा वैद्यकीय इतिहास आहे का? (होय / नाही)",
        "शेवटी, तुमचे प्राथमिक ध्येय काय आहे? (उदा. कर बचत, आरोग्य संरक्षण, गुंतवणूक किंवा जीवन कवच)"
    ],
    # Add other languages (ta, te, etc.) here if needed
    'ta': [
        "Survey Start",
        "உங்களுக்கான சிறந்த பாலிசியைக் கண்டுபிடிப்போம். முதலில், உங்கள் **வயதை**ச் சொல்ல முடியுமா?",
        "மிக்க நன்று. உங்கள் தோராயமான **ஆண்டு வருமானம்** என்ன?",
        "யாருக்கு காப்பீடு செய்ய விரும்புகிறீர்கள்? (எ.கா., சுய, குடும்பம், பெற்றோர் அல்லது குழந்தை)",
        "உங்களுக்கு ஏதேனும் மருத்துவப் பாதிப்புகள் உள்ளதா? (ஆம் / இல்லை)",
        "இறுதியாக, உங்கள் முதன்மை குறிக்கோள் என்ன? (எ.கா., வரி சேமிப்பு, உடல்நலம், முதலீடு)"
    ],
    'te': [
        "Survey Start",
        "మీ కోసం ఉత్తమ పాలసీని కనుగొందాం. ముందుగా, మీ **వయస్సు** ఎంత?",
        "చాలా బాగుంది. మీ సుమారు **వార్షిక ఆదాయం** ఎంత?",
        "మీరు ఎవరికి బీమా చేయాలనుకుంటున్నారు? (ఉదా. స్వయం, కుటుంబం, తల్లిదండ్రులు లేదా పిల్లలు)",
        "మీకు ఏవైనా ఆరోగ్య సమస్యలు ఉన్నాయా? (అవును / కాదు)",
        "చివరగా, మీ ప్రధాన లక్ష్యం ఏమిటి? (ఉదా. పన్ను ఆదా, ఆరోగ్య రక్షణ, పెట్టుబడి)"
    ]
}