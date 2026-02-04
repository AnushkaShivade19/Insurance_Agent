from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.home_view, name='homepage'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agents_view, name='agents'),
    

    path('offline/', views.offline_view, name='offline'),
    path('profile/', views.profile_view, name='profile'),
    path('learn/', views.knowledge_hub_view, name='knowledge_hub'),

    # PWA CRITICAL PATHS (Serve from Root)
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='pwa_manifest'),
    path('serviceworker.js', TemplateView.as_view(template_name='serviceworker.js', content_type='application/javascript'), name='pwa_serviceworker'),
    path('offline/', views.offline_view, name='offline'),

]