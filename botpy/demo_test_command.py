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


@Commands("封禁")
async def ban(api: BotAPI, message: Message, params=None):
    # 确保有 mentions 列表，并且至少有一个用户提及
    if message.mentions and len(message.mentions) > 1:
        user_to_ban = message.mentions[1]

        try:
            # 确保 guild_id 存在
            if message.guild_id:
                await api.get_delete_member(
                    guild_id=message.guild_id,
                    user_id=user_to_ban.id,  # 仅传递 user_id
                    add_blacklist=False,
                    delete_history_msg_days=0
                )
                _log.info("User successfully banned.")
            else:
                _log.error("Guild ID not found.")
        except Exception as e:
            _log.error(f"Failed to ban user: {e}")
    else:
        _log.error("No users mentioned in the message.")


class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令 handler
        handlers = [
            ban,  # 使用 mute 作为处理函数
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    # 通过 kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
