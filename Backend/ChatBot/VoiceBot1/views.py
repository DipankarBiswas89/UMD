from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .models import Conversation
from .serializers import ConversationSerializer
import os
import speech_recognition as sr
from gtts import gTTS
import numpy as np
from django.conf import settings
from pygame import mixer

class VoiceChatAPI(APIView):
    parser_classes = [MultiPartParser]  # Explicitly set to handle multipart/form-data only

    def __init__(self):
        self.recognizer = sr.Recognizer()
        mixer.init()

    def post(self, request):
        try:
            if 'audio' not in request.FILES:
                return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            audio_file = request.FILES['audio']
            
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                user_text = self.recognizer.recognize_google(audio_data)
            
            bot_response = self.process_input(user_text)
            audio_path = self.text_to_speech(bot_response)
            
            conversation = Conversation.objects.create(
                user_input=user_text,
                bot_response=bot_response,
                audio_response=audio_path.replace(settings.MEDIA_ROOT, '')
            )
            
            serializer = ConversationSerializer(conversation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except sr.UnknownValueError:
            return Response({'error': 'Could not understand audio'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_input(self, text):
        text = text.lower()
        if 'hello' in text:
            return "Hi there! How can I assist you today?"
        elif 'how are you' in text:
            return "I'm doing great, thanks for asking! How about you?"
        elif 'bye' in text:
            return "Goodbye, have a great day!"
        else:
            return "I'm not sure how to respond to that. Can you try asking something else?"
    
    def text_to_speech(self, text):
        tts = gTTS(text=text, lang='en', slow=False)
        output_path = os.path.join(settings.MEDIA_ROOT, 'audio_responses', f'response_{np.random.randint(100000)}.mp3')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tts.save(output_path)
        return output_path
    
    def play_audio(self, audio_path):
        mixer.music.load(audio_path)
        mixer.music.play()
        while mixer.music.get_busy():
            continue