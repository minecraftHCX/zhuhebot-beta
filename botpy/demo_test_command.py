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

# 消息内容前缀
colls = "尝试禁言："


@Commands("禁言")
async def mute(api: BotAPI, message: Message, params=None):
    _log.info("执行禁言操作")

    # 确保 message.mentions 至少有一个用户
    if message.mentions and len(message.mentions) > 1:
        user = message.mentions[1]  # 获取第一个提到的用户

        # 从消息内容中解析禁言时间
        try:
            # 假设格式为: @机器人 /禁言 @禁言者 时间
            parts = message.content.split()
            mute_seconds = int(parts[-1])  # 假设时间是最后一个部分
        except (IndexError, ValueError):
            _log.warning("无法解析禁言时间，默认禁言20秒")
            mute_seconds = 20  # 设置默认禁言时间

        # 检查是否试图禁言自己
        if user.id == message.author.id:
            await api.post_message(
                channel_id=message.channel_id,
                content="你不能禁言自己！",
                msg_id=message.id
            )
            _log.info("用户试图禁言自己，操作已阻止")
            return False

        message_reference = Reference(message_id=message.id)

        # 正确获取用户的用户名，并显示禁言时间
        await api.post_message(
            channel_id=message.channel_id,
            content=f"{colls} {user.username} 被禁言 {mute_seconds} 秒",
            msg_id=message.id,
            message_reference=message_reference,
        )

        # 禁言成员
        await api.mute_member(
            guild_id=message.guild_id,
            user_id=user.id,
            mute_seconds=mute_seconds
        )
    else:
        _log.warning("没有提到的用户，无法执行禁言操作")
        await api.post_message(
            channel_id=message.channel_id,
            content="请提到要禁言的用户。",
            msg_id=message.id
        )

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
