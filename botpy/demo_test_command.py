# -*- coding: utf-8 -*-
import os
import botpy
from botpy import logging, BotAPI
from botpy.ext.command_util import Commands
from botpy.message import Message
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference

# 读取配置文件
test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

# 日志配置
_log = logging.get_logger()



@Commands("管理等级")
async def mute(api: BotAPI, message: Message, params=None,):
    among = ["4", "5", "13"]
    member = message.member.roles
    message_reference = Reference(message_id=message.id)
    if any(item in member for item in among):
        await api.post_message(
            channel_id=message.channel_id,
            content="你具有管理员权限"+str(member),
            msg_id=message.id,
            message_reference=message_reference,
        )
        _log.info("true")

    return True


class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令 handler
        handlers = [
            mute,  # 使用 mute 作为处理函数
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    # 通过 kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
