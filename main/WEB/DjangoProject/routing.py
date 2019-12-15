from channels import include

channel_routing = [
	include("app.routing.websocket_routing",path=r'^/ws'),
]
