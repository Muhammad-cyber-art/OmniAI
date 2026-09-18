"""
OmniLab AI - Simulation WebSocket Routing
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/simulations/(?P<session_id>[0-9a-fA-F-]+)/?$",
        consumers.SimulationConsumer.as_asgi(),
    ),
]
