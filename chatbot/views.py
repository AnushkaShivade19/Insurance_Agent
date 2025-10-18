from django.shortcuts import render
from django.http import JsonResponse
import requests, os

def chat_view(request):
    """Render the chatbot page and clear the history for a new session."""
    if 'history' in request.session:
        del request.session['history']
    return render(request, 'chatbot/chat.html')

def get_response(request):
    user_message = request.GET.get('userMessage', '')
    api_key = os.getenv("GEMINI_API_KEY")

    # This is your working URL and model - we will not change it.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    # --- MEMORY LOGIC START ---

    # 1. Get the conversation history from the user's session.
    #    If it doesn't exist, start with an empty list.
    history = request.session.get('history', [])

    # 2. Create the prompt with your strict rules for conciseness.
    #    The instructions are now part of the history, not the user message.
    prompt_instructions = """
    You are an insurance assistant for rural users named 'Gramin Suraksha Mitra'.
    
    **CRITICAL RULES:**
    1.  Explain the user's term in a maximum of **3-4 simple sentences**.
    2.  Be very **direct and to the point**.
    3.  **Do NOT use lists or bullet points.**
    4.  Use one simple analogy to make it easy to understand.
    """

    # 3. Combine the instructions, past conversation, and the new message.
    #    The API expects a list of "content" objects.
    contents = [
        # The prompt instructions set the persona for the entire conversation
        {"parts": [{"text": prompt_instructions}]},
        # The history provides the context
        *history,
        # The new message is the latest user query
        {"parts": [{"text": f"Explain the following: {user_message}"}]}
    ]
    
    data = {"contents": contents}

    # --- MEMORY LOGIC END ---

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        bot_message = response.json()['candidates'][0]['content']['parts'][0]['text']

        # --- UPDATE HISTORY AFTER A SUCCESSFUL RESPONSE ---
        # Add the user's message and the bot's response to the history
        history.append({"parts": [{"text": user_message}]})
        history.append({"parts": [{"text": bot_message}]})

        # Save the updated history back to the session, keeping only the last 4 exchanges (8 messages)
        request.session['history'] = history[-8:]

    except Exception as e:
        print("HTTP error:", e)
        bot_message = "I'm facing some network issues. Please try again later."

    return JsonResponse({"botResponse": bot_message})