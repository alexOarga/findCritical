import json
import logging
from channels import Channel, Group
from channels.sessions import channel_session


def ws_add(message):
	message.reply_channel.send({"accept": True})
	Group("group_name").add(message.reply_channel)


def ws_message(message):
	try:
		print(data)
		data = json.loads(message['text'])
	except ValueError:
		log.debug("el formato no parece json=%s", message['text'])
		return
	if data:
		reply_channel = message.reply_channel.name
	returnFalse

def ws_disconnect(message):
	Group("group_name").discard(message.reply_channel)