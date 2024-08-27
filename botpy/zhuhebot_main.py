# -*- coding: utf-8 -*-
import os
import yaml
import botpy
from botpy import logging, BotAPI
from botpy.ext.command_util import Commands
from botpy.message import Message
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference


def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data


config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
text = load_yaml('text.yaml')
help_list = text["help_list"]
child_stiitings_error = text["child_stiitings_error"]
not_complete = text["not_complete"]

_log = logging.get_logger()


@Commands("帮助")
async def help(api: BotAPI, message: Message, params=None):
    _log.info("发送帮助文档")
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=help_list,
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True


@Commands("设置")
async def sittings(api: BotAPI, message: Message, params=None):
    _log.info("返回：未完成")
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=not_complete,
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True


@Commands("禁言")
async def mute(api: BotAPI, message: Message, params=None):
    _log.info("执行禁言操作")
    admin = ["2", "4", "5"]
    # 确保 message.mentions 至少有一个用户
    if any(item in message.member.roles for item in admin):
        if message.mentions and len(message.mentions) > 1:
            user = message.mentions[1]  # 获取第一个提到的用户
            message_reference = Reference(message_id=message.id)
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
                    msg_id=message.id,
                    message_reference=message_reference,
                )
                _log.info("用户试图禁言自己，操作已阻止")
                return False
            # 正确获取用户的用户名，并显示禁言时间
            await api.post_message(
                channel_id=message.channel_id,
                content=f"{user.username} 被禁言 {mute_seconds} 秒",
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
            message_reference = Reference(message_id=message.id)
            _log.warning("没有提到用户，无法执行禁言操作!")
            await api.post_message(
                channel_id=message.channel_id,
                content="请提到要禁言的用户!",
                msg_id=message.id,
                message_reference=message_reference,
            )
    else:
        message_reference = Reference(message_id=message.id)
        _log.warning("用户无权限")
        await api.post_message(
            channel_id=message.channel_id,
            content="你没有权限使用此指令！",
            msg_id=message.id,
            message_reference=message_reference,
        )
        return False
    return True


@Commands("封禁")
async def ban(api: BotAPI, message: Message, params=None):
    _log.info("返回：未完成")
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=not_complete,
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True


@Commands("子频道设置")
async def child_settings(api: BotAPI, message: Message, params=None):
    _log.info("子频道设置回复")
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=child_stiitings_error,
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True


@Commands("举报")
async def report(api: BotAPI, message: Message, params=None):
    _log.info("收到举报" + message.content)
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content="收到举报,请等待管理员处理或在源消息下@小智管家/举报 进行快速处理",
        msg_id=message.id,
        message_reference=message_reference,
    )
    return True


class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令handler
        handlers = [
            help,
            child_settings,
            report,
            sittings,
            mute,
            ban,
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])
