"""
OmniLab AI - Root WebSocket URL Routing
Combines all application WebSocket URL patterns.
"""
from apps.simulation.routing import websocket_urlpatterns as simulation_ws_patterns

websocket_urlpatterns = [
    *simulation_ws_patterns,
]
