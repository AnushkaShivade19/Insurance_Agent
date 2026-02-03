from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='products'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/audio/', views.get_audio_description, name='product_audio'),
    path('product/<int:pk>/agent/', views.talk_to_agent, name='talk_to_agent'),
    path('product/<int:pk>/buy/', views.buy_policy, name='buy_policy'),
]