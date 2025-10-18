from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='homepage'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agents/', views.agents_view, name='agents'),
    path('claims/file/', views.file_claim_view, name='file_claim'),
    path('claims/<int:claim_id>/', views.claim_detail_view, name='claim_detail'),
    path('products/', views.products_view, name='products')
]