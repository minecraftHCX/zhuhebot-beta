import os
import random
import time
import yaml
import botpy
from botpy import logging, BotAPI
from botpy.ext.command_util import Commands
from botpy.message import Message
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference
import uuid
import json
import urllib.request
import urllib.parse
import websocket

# 读取配置和文本
config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
text = read(os.path.join(os.path.dirname(__file__), "text.yaml"))
help_list = text["help_list"]
child_stiitings_error = text["child_stiitings_error"]
not_complete = text["not_complete"]

_log = logging.get_logger()

server_address = "2163c43b.r37.cpolar.top"
client_id = str(uuid.uuid4())

# 用于生成图像的函数
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)

    try:
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read())
        _log.info(f"远端服务器响应：{response_data}")
        return response_data
    except urllib.error.HTTPError as e:
        _log.error(f"HTTPError: {e}")
        raise
    except urllib.error.URLError as e:
        _log.error(f"URLError: {e}")
        raise


def get_image_url(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    url = "http://{}/view?{}".format(server_address, url_values)
    _log.info(f"生成图像的 URL: {url}")
    return url


def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        history_data = json.loads(response.read())
        _log.info(f"远端服务器历史记录响应：{history_data}")
        return history_data


def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    _log.info(f"生成任务 ID: {prompt_id}")
    output_images = {}

    # 监听 WebSocket 消息
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            _log.info(f"收到消息：{message}")
            data = message.get('data', {})
            #好吧，这单纯就是坨屎山，只是因为逻辑莫名其妙炸了，后面获取历史记录我添加了机制进行弥补，后面会再次尝试的
            if message['type'] == 'status':
                _log.info(f"状态更新: {data}")
                queue_remaining = data.get('status', {}).get('exec_info', {}).get('queue_remaining', 0)
                if queue_remaining > 0:
                    _log.info(f"队列剩余任务: {queue_remaining}")
                    continue  # 如果队列中有任务，则继续等待
                elif queue_remaining == 0:
                    break
            elif message['type'] == 'executing':
                _log.info(f"图像生成中: {data}")
                continue  # 继续等待
            elif message['type'] == 'executed':
                _log.info(f"图像生成完成: {data}")
                break  # 图像生成完成，退出循环
            else:
                _log.info(f"未处理的消息类型: {message['type']}")
        else:
            _log.warning(f"收到意外的消息格式: {out}")
    _log.info(f"图像生成完成，获取历史记录...")
    #嗯，对这就是补救措施
    matched=False
    while True:
        history_data = get_history(prompt_id)
        if history_data:
            for key in history_data:
                if key == prompt_id:
                    matched=True
            if matched:
                break
        else:
            continue
    history = get_history(prompt_id)[prompt_id]
    _log.info(f"获取图像URL...")

    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_url = get_image_url(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_url)
        output_images[node_id] = images_output

    return output_images


@Commands("生成")
async def generate(api: BotAPI, message: Message, params=None,msg_type: int = 1):
    _log.info("收到生成指令，正在创建任务...")
    #下面这是工作流，目前正在开发和微调，下一版本可能放出更稳定的工作流作为风格选择
    prompt_text = """
{
    "1": {
        "inputs": {
          "ckpt_name": "noobxl.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
          "title": "加载大模型"
        }
    },
    "2": {
        "inputs": {
          "stop_at_clip_layer": -3,
          "clip": [
            "1",
            1
          ]
        },
        "class_type": "CLIPSetLastLayer",
        "_meta": {
          "title": "CLIP Set Last Layer（我也不到这是个啥awa）"
        }
    },
    "3": {
        "inputs": {
          "text": "Masterpiece, of the best quality, very beautiful, with high resolution,\n\n(Artist: Qian Qian Jie: 1), (Artist: Ru Ru Ru Dao: 1), (Artist: Dorino Aquila: 0.4), (Art: momoko（momopoco）：0.7），\n\n(Full body), furry, detailed composition, BREAK anime coloring\n\nCat boy, white hands, soft cushion, white ears, bright eyes, clear pupils\n\nHappy expression, fur stripes, inner ear fuzz, stripes, multicolored body, multicolored fur, multicolored tail, multicolored tufted hair, neck tufted hair\n\nBright environment (bedroom background)",
          "clip": [
            "2",
            0
          ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
          "title": "正面提示词"
        }
    },
    "4": {
        "inputs": {
          "text": "bad anatomy, bad proportions, extra limbs, extra digit, extra legs, extra legs and arms, disfigured, missing arms, too many fingers, fused fingers, missing fingers, unclear eyes,(watermark),username,worst quality, bad quality, low quality, lowres, jpeg artifacts,words",
          "clip": [
            "2",
            0
          ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
          "title": "负面提示词"
        }
    },
    "5": {
        "inputs": {
          "seed": 977266203627725,
          "steps": 35,
          "cfg": 7.5,
          "sampler_name": "euler",
          "scheduler": "normal",
          "denoise": 1,
          "model": [
            "10",
            0
          ],
          "positive": [
            "3",
            0
          ],
          "negative": [
            "4",
            0
          ],
          "latent_image": [
            "6",
            0
          ]
        },
        "class_type": "KSampler",
        "_meta": {
          "title": "操作参数"
        }
    },
    "6": {
        "inputs": {
          "width": 700,
          "height": 700,
          "batch_size": 1
        },
        "class_type": "EmptyLatentImage",
        "_meta": {
          "title": "图片大小"
        }
    },
    "7": {
        "inputs": {
          "samples": [
            "5",
            0
          ],
          "vae": [
            "8",
            0
          ]
        },
        "class_type": "VAEDecode",
        "_meta": {
          "title": "VAE 解码处理"
        }
    },
    "8": {
        "inputs": {
          "vae_name": "sdxl_vae_fp16.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
          "title": "加载VAE模型"
        }
    },
    "9": {
        "inputs": {
          "filename_prefix": "ComfyUI",
          "images": [
            "7",
            0
          ]
        },
        "class_type": "SaveImage",
        "_meta": {
          "title": "图片预览（输出前缀修改）"
        }
    },
    "10": {
        "inputs": {
          "sampling": "v_prediction",
          "zsnr": true,
          "model": [
            "1",
            0
          ]
        },
        "class_type": "ModelSamplingDiscrete",
        "_meta": {
          "title": "ModelSamplingDiscrete（我也不到这是个啥awa）"
        }
    },
    "18": {
        "inputs": {
          "image": "ARDT2KMADQN2045H47QBVYG4P0.jpg",
          "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
          "title": "加载图像"
        }
    },
    "20": {
        "inputs": {
          "pixels": [
            "18",
            0
          ],
          "vae": [
            "1",
            2
          ]
        },
        "class_type": "VAEEncode",
        "_meta": {
          "title": "导入图片的VAE编码"
        }
    }
}
    """
    prompt = json.loads(prompt_text,strict=False)
    # 处理用户输入的提示词
    user_prompt = message.content
    user_prompt_o = user_prompt.replace("\n", "\\n").replace("\r", "\\r").replace("@竹禾bot-测试中 /生成","colorful" )
    prompt["3"]["inputs"]["text"] = user_prompt_o
    prompt["5"]["inputs"]["seed"] = random.randint(1,9999999999)
    _log.info(f"提示词处理完毕")
    # 发送请求到 WebSocket 服务器
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    _log.info(f"WebSocket 连接已建立，开始生成图像...")

    # 回复用户生成任务 ID
    task_id = message.id
    message_reference = Reference(message_id=message.id)
    await api.post_message(
        channel_id=message.channel_id,
        content=f"您的生成任务已创建，任务 ID: {task_id}，请稍等...",
        msg_id=message.id,
        image="https://framerusercontent.com/images/ZdBbq96uSdSV7csYpT0JsoE4.png",
        message_reference=message_reference,
    )
    image_url = get_images(ws, prompt)
    ws.close()  # 关闭连接

    # 任务 ID 与用户消息关联
    _log.info(f"任务 {task_id} 已生成完成，准备返回图像链接。")
    link = image_url['9'][0]
    # 生成完成后，返回图片 URL 并回复用户
    _log.info(f"准备将图像 URL 发送给用户：{image_url}")
    await api.post_message(
                channel_id=message.channel_id,
                content="生成完成！",
                msg_id=message.id,
                image=link,
                message_reference=message_reference,
    )

    return True

class MyClient(botpy.Client):
    async def on_at_message_create(self, message: Message):
        # 注册指令handler
        handlers = [
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