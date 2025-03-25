from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.VoiceChatAPI.as_view(), name='voice_chat'),
]
