# chatbot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Chat-related URLs
    path('', views.chat_view, name='chat'),
    path('get-response', views.get_response, name='get_response'),
    path('set-language', views.set_language, name='set_language'),
    path('speak/', views.speak_text, name='speak_text'),
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]