from django.urls import path
from . import views

urlpatterns = [
    path('file/', views.file_claim_view, name='file_claim'),
    path('detail/<int:claim_id>/', views.claim_detail_view, name='claim_detail'),
]