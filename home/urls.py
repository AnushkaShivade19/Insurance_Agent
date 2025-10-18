from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='homepage'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agents_view, name='agents'),
    path('claims/file/', views.file_claim_view, name='file_claim'),
    path('claims/<int:claim_id>/', views.claim_detail_view, name='claim_detail'),
    path('products/', views.products_view, name='products'),
    path('adminpanel/', views.admin_analytics_view, name='admin_analytics'),
    path('purchase/', views.purchase_policy_view, name='purchase_policy'),
    path('profile/', views.profile_view, name='profile'),
    path('learn/', views.knowledge_hub_view, name='knowledge_hub'),
]