"""
E-Ink BLE Display - Claude Code Interface v2.1
支持中文显示
"""

import asyncio
from bleak import BleakClient
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

DEVICE_ADDRESS = "45881F54-7750-ECE7-0E3E-3D62CC0BF2ED"
WRITE_CHAR_UUID = "62750002-d828-918d-fb46-b6c11c675aec"
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 300

CMD_INIT = bytes([0x01])
CMD_CLEAR = bytes([0x02])
CMD_WRITE_IMAGE = bytes([0x30])
CMD_REFRESH = bytes([0x05])
MTU = 244

WHITE, BLACK = 1, 0


# 当前模型名称 (当前session使用的模型)
CURRENT_MODEL_NAME = "MiniMax-M2.7"


def get_font(size):
    """获取支持中文的字体"""
    # 优先使用 Noto Sans CJK 字体
    font_paths = [
        "/Users/yangxiansen/Library/Fonts/NotoSansCJKsc-Regular.otf",
        "/Users/yangxiansen/Library/Fonts/NotoSansCJKsc-Medium.otf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def get_artistic_font(size):
    """获取加粗斜体艺术字体用于四个角的文字"""
    # 加粗斜体艺术字体路径
    bold_italic_fonts = [
        "/Users/yangxiansen/Library/Fonts/Meslo LG L Bold Italic for Powerline.ttf",
        "/Users/yangxiansen/Library/Fonts/Meslo LG L DZ Bold Italic for Powerline.ttf",
        "/Users/yangxiansen/Library/Fonts/Hack-BoldItalic.ttf",
    ]
    for path in bold_italic_fonts:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return get_font(size)


def to_bw_bytes(img):
    img = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT)).convert('1')
    pixels = list(img.getdata())
    result = []
    for i in range(0, 15000):
        byte = 0
        for j in range(8):
            idx = i * 8 + j
            if idx < len(pixels) and pixels[idx] == 1:
                byte |= 1 << (7 - j)
        result.append(byte)
    return bytes(result)


def to_red_bytes(img):
    img = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT)).convert('1')
    pixels = list(img.getdata())
    result = []
    for i in range(0, 15000):
        byte = 0
        for j in range(8):
            idx = i * 8 + j
            if idx < len(pixels) and pixels[idx] == 1:
                byte |= 1 << (7 - j)
        result.append(byte)
    return bytes(result)


async def send(client, data, flag):
    for i in range(0, len(data), MTU - 3):
        chunk = data[i:i + MTU - 3]
        cmd = CMD_WRITE_IMAGE + bytes([flag | (0x00 if i == 0 else 0xF0)]) + chunk
        await client.write_gatt_char(WRITE_CHAR_UUID, cmd)
        await asyncio.sleep(0.02)


class EInkDisplay:
    def __init__(self, address=DEVICE_ADDRESS):
        self.address = address
        self.client = None

    async def connect(self):
        self.client = BleakClient(self.address)
        await self.client.connect()
        print("已连接墨水屏")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()

    async def clear(self):
        await self.client.write_gatt_char(WRITE_CHAR_UUID, CMD_INIT)
        await asyncio.sleep(0.3)
        await self.client.write_gatt_char(WRITE_CHAR_UUID, CMD_CLEAR)
        await asyncio.sleep(0.2)
        await self.client.write_gatt_char(WRITE_CHAR_UUID, CMD_REFRESH)
        await asyncio.sleep(1)

    async def show(self, bg_img, red_img=None):
        await self.client.write_gatt_char(WRITE_CHAR_UUID, CMD_INIT)
        await asyncio.sleep(0.3)
        await send(self.client, to_bw_bytes(bg_img), 0x0F)
        if red_img:
            await send(self.client, to_red_bytes(red_img), 0x00)
        await self.client.write_gatt_char(WRITE_CHAR_UUID, CMD_REFRESH)
        await asyncio.sleep(1)


def draw_message(message, task_name="Claude Code", model_name=None):
    """绘制消息界面

    Args:
        message: 要显示的核心内容
        task_name: 右上角显示的任务名称
        model_name: footer右下角显示的模型名称，默认使用当前session模型
    """
    if model_name is None:
        model_name = CURRENT_MODEL_NAME

    bg = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), WHITE)
    bg_draw = ImageDraw.Draw(bg)

    red = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), WHITE)
    red_draw = ImageDraw.Draw(red)

    # 艺术字体用于四个角的文字
    font_artistic = get_artistic_font(16)
    # 内容区域使用常规字体
    font_large = get_font(32)

    now = datetime.now()

    # ========== Header ==========
    # 左上角：当前时间 (斜体艺术字体) - 格式 HH:MM
    time_str = now.strftime("%H:%M")
    bg_draw.text((20, 10), time_str, font=font_artistic, fill=BLACK)

    # 右上角：任务名称 (斜体艺术字体)
    bbox = bg_draw.textbbox((0, 0), task_name, font=font_artistic)
    task_width = bbox[2] - bbox[0]
    bg_draw.text((SCREEN_WIDTH - task_width - 20, 10), task_name, font=font_artistic, fill=BLACK)

    # header 底部红色实线 (两边留20像素空间，加粗到4)
    red_draw.line([(20, 35), (SCREEN_WIDTH-20, 35)], fill=BLACK, width=4)

    # ========== Content Area ==========
    # 计算内容区域 (在两条红线之间)
    content_top = 50
    content_bottom = SCREEN_HEIGHT - 50
    content_height = content_bottom - content_top
    content_width = SCREEN_WIDTH - 40  # 左右各留20像素

    # 根据内容长度选择合适的字体大小
    max_chars_per_line = 20
    if len(message) > 100:
        font_size = 20
    elif len(message) > 50:
        font_size = 24
    else:
        font_size = 32

    font_content = get_font(font_size)

    # 自动换行处理
    def wrap_text(text, font, max_width):
        """将文本自动换行"""
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = bg_draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    # 消息内容居中对齐
    lines = message.split('\n')
    wrapped_lines = []
    for line in lines:
        if line.strip():
            wrapped = wrap_text(line, font_content, content_width)
            wrapped_lines.extend(wrapped)

    line_height = font_size + 8
    total_text_height = len(wrapped_lines) * line_height
    start_y = content_top + (content_height - total_text_height) // 2

    y = start_y
    for line in wrapped_lines:
        if line.strip():
            bbox = bg_draw.textbbox((0, 0), line, font=font_content)
            line_width = bbox[2] - bbox[0]
            x = (SCREEN_WIDTH - line_width) // 2
            bg_draw.text((x, y), line, font=font_content, fill=BLACK)
            y += line_height

    # ========== Footer ==========
    # footer 顶部红色实线 (两边留20像素空间，加粗到4)
    red_draw.line([(20, SCREEN_HEIGHT-45), (SCREEN_WIDTH-20, SCREEN_HEIGHT-45)], fill=BLACK, width=4)

    # 左下角：日期 (Month Day, Year) - 斜体艺术字体
    date_str = now.strftime("%B %-d, %Y")  # April 4, 2026
    bg_draw.text((20, SCREEN_HEIGHT-30), date_str, font=font_artistic, fill=BLACK)

    # 右下角：模型名称 - 红色显示 (绘制在红色层上，用黑色填充)
    bbox = red_draw.textbbox((0, 0), model_name, font=font_artistic)
    model_width = bbox[2] - bbox[0]
    red_draw.text((SCREEN_WIDTH - model_width - 20, SCREEN_HEIGHT-30), model_name, font=font_artistic, fill=BLACK)

    return bg, red


# Heartbit 情话列表
HEARTBIT_MESSAGES = [
    "You are my today, and all of my tomorrows. I love you more than words can ever say.",
    "Every moment with you is precious. You make my heart skip a beat every single time.",
    "I am thinking of you right now, and my love for you grows stronger each day.",
    "You are the sunshine in my life, the reason I believe in true love.",
    "My heart is perfect because you are inside. I fall in love with you every day.",
    "You are my favorite hello and my hardest goodbye. Forever isn't long enough with you.",
    "In all the world, you are my everything. You are my greatest adventure.",
    "Being with you is the best thing that ever happened to me. I cherish you always.",
    "Your smile lights up my world. Every day with you is a gift I treasure.",
    "I didn't know love could be this perfect until I met you, my darling.",
    "You are my rock, my soulmate, my everything. I love you beyond words.",
    "When I look at you, I see my future. Thank you for being mine, forever.",
    "My love for you is deeper than the ocean and stronger than any storm.",
    "You make ordinary moments extraordinary. I am so grateful for your love.",
    "Together with you is where I belong. Your love is my greatest treasure.",
]


async def notify(message, task_name="Claude Code"):
    """在屏幕上显示通知消息

    Args:
        message: 要显示的通知内容
        task_name: 右上角显示的任务名称
    """
    display = EInkDisplay()
    await display.connect()
    bg, red = draw_message(message=message, task_name=task_name)
    await display.show(bg, red)
    await display.disconnect()


async def heartbit():
    """发送情话到墨水屏 (heartbit功能)"""
    import random
    message = random.choice(HEARTBIT_MESSAGES)
    display = EInkDisplay()
    await display.connect()
    bg, red = draw_message(message=message, task_name="Heartbit")
    await display.show(bg, red)
    await display.disconnect()
    print(f"Heartbit sent: {message}")


async def main():
    display = EInkDisplay()
    await display.connect()
    await display.clear()

    # 中文欢迎界面
    bg, red = draw_message(
        message="Claude Code\n墨水屏交互界面\n\n三色显示测试成功！",
        task_name="Claude Code"
    )

    await display.show(bg, red)
    print("显示完成!")

    await display.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
