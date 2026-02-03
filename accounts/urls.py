from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('agents/', views.agent_list, name='agent_list'),
    
    # Only one API needed now
    path('api/speak/', views.speak_text_view, name='speak_text'),
]