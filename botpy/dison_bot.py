# -*- coding: utf-8 -*-
# 这是一个简单的示例，不是开发程序主体！
import os
import time

import botpy
from botpy import logging
from botpy.ext.cog_yaml import read
from botpy.ext.command_util import Commands
from botpy.message import Message

_log = logging.get_logger()

helplist = """使用说明
/报时
    返回服务器时间-24h
    ！！会有一定小误差！！
    示例：/报时
    （返回格式：
                  年-月-日，时-分-秒
  “YYYY-MM-DD,hour-minute-second”）
/问好
    返回一句简单的问好语句
    示例：/问好 
_________下方未开发_____________
/举报 违规详情
    允许举报成员违规行为，需回复源消息（待开发）
    示例：/举报 宣传违规软件

！以下操作均需管理员权限方可执行！

/禁言 @指定成员 时长(以秒为单位)
    管理员审查后即可禁言指定成员（待开发）
    示例：/禁言 @AFK 100

/封禁 @指定成员
    直接踢出成员并拉进黑名单（待开发）
    示例：/封禁 @AFK 

/解封 @指定成员
    解除成员禁言状态（待开发）
    示例：/解封 @AFK

帮助文档版本：a 0.03beta"""


@Commands("/帮助")
async def help_list(message: Message,):
    _log.info('执行了帮助命令')
    await message.reply(
        content=helplist
    )
    return True


@Commands("如何使用")
async def no_thing(message: Message):
    _log.info('无修饰-使用说明')
    await message.reply(
        content=helplist
    )
    return True


@Commands("/报时")
async def now_time(message: Message):
    t = time.strftime("%Y-%m-%d, %H:%M:%S")
    _log.info(f'执行了报时命令,返回的时间为“{t}”')
    await message.reply(
        content=f'''  现在的时间是 “{t} ” 
     注意：
（attention）：
                  时间可能存有一定延迟，仅供参考！
    （Time may have some delay error, for reference only.）
'''
    )
    return True


@Commands("/问好")
async def say_hello(message: Message):
    t = time.strftime("%Y-%m-%d, %H:%M:%S")
    _log.info(f'执行了问好命令,返回了时间“{t}”和简单问好')

    await message.reply(
        content=f'''现在是“{t}”。你好，很高兴认识你!
    It is '{t}'.Hi,nice to meet you!'''
    )


class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令handler
        tasks = [
            help_list,
            no_thing,
            now_time,
            say_hello
        ]
        for handler in tasks:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    # 通过预设置的类型，设置需要监听的事件通道
    # intents = botpy.Intents.none()
    # intents.public_guild_messages=True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid="102268340", secret="quy26AEINSXchmrw28EKQWcjqx4BIPXf")