import os
import uuid

import yaml
import json
import random
import websocket
import botpy
from botpy import logging, BotAPI
from botpy.ext.command_util import Commands
from botpy.message import Message
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference
from datetime import datetime


# 加载配置文件
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data


config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
text = read(os.path.join(os.path.dirname(__file__), "text.yaml"))
help_list = text["help_list"]
child_stiitings_error = text["child_stiitings_error"]
not_complete = text["not_complete"]
server_address = "https://266941a8.r37.cpolar.top/"
client_id = str(uuid.uuid4())
_log = logging.get_logger()


# ConfyUI 图片生成相关代码
def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    print('prompt')
    print(prompt)
    print('prompt_id:{}'.format(prompt_id))
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    print('执行完成')
                    break  # 执行完成
        else:
            continue  # 预览为二进制数据

    history = get_history(prompt_id)[prompt_id]
    print(history)
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            # 图片分支
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output
            # 视频分支
            if 'videos' in node_output:
                videos_output = []
                for video in node_output['videos']:
                    video_data = get_image(video['filename'], video['subfolder'], video['type'])
                    videos_output.append(video_data)
                output_images[node_id] = videos_output

    print('获取图片完成')
    print(output_images)
    return output_images


def generate_clip(prompt, seed, workflowfile, idx):
    print('seed:' + str(seed))
    ws = websocket.WebSocket()
    ws.connect("wss://{}/ws?clientId={}".format(server_address, client_id))
    images = parse_workflow(ws, prompt, seed, workflowfile, idx)

    for node_id in images:
        for image_data in images[node_id]:
            # 获取当前时间，并格式化为 YYYYMMDDHHMMSS 的格式
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # 使用格式化的时间戳在文件名中
            GIF_LOCATION = "{}/{}_{}_{}.png".format(SageMaker_ComfyUI, idx, seed, timestamp)

            with open(GIF_LOCATION, "wb") as binary_file:
                # 写入二进制文件
                binary_file.write(image_data)

            show_gif(GIF_LOCATION)
            print("{} DONE!!!".format(GIF_LOCATION))

    return GIF_LOCATION  # 返回生成的图像路径


# 读取工作流配置文件并将提示词传入
def parse_workflow(ws, prompt, seed, workflowfile, idx):
    with open(workflowfile, 'r', encoding="utf-8") as workflow_api_txt2gif_file:
        prompt_data = json.load(workflow_api_txt2gif_file)

        # 填充正面提示词
        prompt_data["3"]["inputs"]["text"] = prompt  # 第3节点为正面提示词

        return get_images(ws, prompt_data)


# 帮助指令
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


# 生成指令
@Commands("生成")
async def generate(api: BotAPI, message: Message, params=None):
    _log.info("开始生成图片")
    message_reference = Reference(message_id=message.id)

    # 提取指令中的提示词
    prompt = message.content.strip().split("生成")[1].strip()  # 获取指令后的提示词
    if not prompt:
        await api.post_message(
            channel_id=message.channel_id,
            content="请提供生成图片所需的提示词！",
            msg_id=message.id,
            message_reference=message_reference,
        )
        return False

    # 给出任务开始的反馈
    await api.post_message(
        channel_id=message.channel_id,
        content=f"生成任务已开始，任务编号: {message.id}，请稍等...",
        msg_id=message.id,
        message_reference=message_reference,
    )

    # 设置生成图片的工作流文件
    workflowfile = 'workflow_api.json'  # 根据需要设置工作流文件路径
    seed = random.randint(1, 1000000)  # 随机生成一个种子值
    idx = message.id  # 用消息ID作为任务编号

    # 生成图像
    GIF_LOCATION = generate_clip(prompt, seed, workflowfile, idx)

    # 发送生成后的图片给用户
    await api.post_message(
        channel_id=message.channel_id,
        content=f"任务完成！这是您请求的图像：",
        msg_id=message.id,
        message_reference=message_reference,
    )

    # 发送图片
    await api.upload_file(
        channel_id=message.channel_id,
        file=GIF_LOCATION,
        msg_id=message.id,
        message_reference=message_reference,
    )

    # 通知用户任务完成
    await api.post_message(
        channel_id=message.channel_id,
        content=f"生成任务完成！请查看：{GIF_LOCATION}",
        msg_id=message.id,
        message_reference=message_reference,
    )

    return True


# 其他现有指令（禁言、封禁、解封等）保留不变
@Commands("禁言")
async def mute(api: BotAPI, message: Message, params=None):
    _log.info("执行禁言操作")
    admin = ["2", "4", "5"]
    if any(item in message.member.roles for item in admin):
        # 检测用户权限
        if message.mentions and len(message.mentions) > 1:
            user = message.mentions[1]  # 获取提到的用户（设置成1是因为机器人吧自己也算在里面的）
            message_reference = Reference(message_id=message.id)
            # 从消息内容中解析禁言时间
            try:
                # 预定格式为: @机器人 /禁言 @禁言者 时间
                parts = message.content.split()
                mute_seconds = int(parts[-1])
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
            # 输出用户的用户名、禁言时间
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


# 其它指令代码（解封、封禁、子频道设置等）保持不变
class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令handler
        handlers = [
            help,
            mute,
            generate,  # 添加生成指令处理
            # 其它指令
        ]
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return


if __name__ == "__main__":
    intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])
