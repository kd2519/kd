from django.urls import re_path
from brain_start.consumers import EEGDataConsumer

websocket_urlpatterns = [
    re_path(r'^ws/eeg/$', EEGDataConsumer.as_asgi()),
]