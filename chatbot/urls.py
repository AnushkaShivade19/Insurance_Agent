from django.urls import path
from . import views

urlpatterns = [
    # This URL will serve our chat interface (the HTML page)
    path('', views.chat_view, name='chat'),
    # This URL will be used by our JavaScript to get the bot's response
    path('get-response', views.get_response, name='get_response'),
]