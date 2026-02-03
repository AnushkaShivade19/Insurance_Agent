from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='homepage'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agents_view, name='agents'),

    path('adminpanel/', views.admin_analytics_view, name='admin_analytics'),
    path('profile/', views.profile_view, name='profile'),
    path('learn/', views.knowledge_hub_view, name='knowledge_hub'),
]