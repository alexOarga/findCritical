from channels import route
from .views import *


websocket_routing = [
	route("websocket.connect", ws_add),
	route("websocket.receive", ws_message),
	route("websocket.disconnect", ws_disconnect),
]