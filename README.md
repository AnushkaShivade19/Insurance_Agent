Virtual Insurance Agent for Rural India
This project is a Django-based virtual assistant designed to improve insurance accessibility in rural India. It provides a digital platform to educate users about insurance products, simplify complex terms, and recommend suitable plans.
Features
Multilingual Support: Integrates with Bhashini API for regional language support.
AI-Powered Assistance: Uses Google Gemini API to answer insurance-related queries.
Voice Assistance: Incorporates the Web Speech API for voice-based interaction.
User-Friendly Interface: A simple chat interface for easy communication.
Project Structure
insurance_agent/
├── insurance_agent/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── assistant/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── templates/
│   └── assistant.html
├── manage.py
└── requirements.txt


Setup and Installation
Clone the repository:
git clone <repository_url>
cd insurance_agent


Create a virtual environment and activate it:
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`


Install the required packages:
pip install -r requirements.txt


Set up environment variables:
Create a .env file in the root directory and add your API keys:
GEMINI_API_KEY=your_google_gemini_api_key
BHASHINI_API_KEY=your_bhashini_api_key


Apply migrations:
python manage.py migrate


Run the development server:
python manage.py runserver


Open your browser and navigate to http://127.0.0.1:8000/ to interact with the virtual assistant.
