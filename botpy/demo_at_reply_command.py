# -*- coding: utf-8 -*-
import os

import botpy
from botpy import logging, BotAPI

from botpy.ext.command_util import Commands
from botpy.message import Message
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference

test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()

help_list = """帮助文档
            指令说明-消息测试
            """
@Commands("帮助")
async def help(api: BotAPI, message: Message, params=None):
    _log.info("发送帮助文档")
    # 第一种用reply发送消息
    '''
    await message.reply(content=help_list)
    # 第二种用api.post_message发送消息
    '''
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=help_list,
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True



class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令handler
        handlers = [
            help,
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    # 通过预设置的类型，设置需要监听的事件通道
    # intents = botpy.Intents.none()
    # intents.public_guild_messages=True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
