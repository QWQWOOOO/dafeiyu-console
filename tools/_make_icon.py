"""Generate a new app icon for 大肥鱼控制台: fat fish + console caret."""
from PIL import Image, ImageDraw, ImageFilter

S = 1024          # supersampled canvas
PAD = 0           # tile fills canvas
R = 232           # tile corner radius


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def tile() -> Image.Image:
    """Rounded square with a soft blue gradient."""
    grad = Image.new("RGB", (S, S))
    top = (58, 110, 246)
    bot = (18, 156, 200)
    px = grad.load()
    for y in range(S):
        c = lerp(top, bot, y / (S - 1))
        for x in range(S):
            px[x, y] = c
    # 左上角一层柔光
    glow = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-S * 0.25, -S * 0.5, S * 0.75, S * 0.45], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.12))
    white = Image.new("RGB", (S, S), (255, 255, 255))
    grad = Image.composite(white, grad, glow.point(lambda v: int(v * 0.55)))
    return grad.convert("RGBA")


def rounded_mask() -> Image.Image:
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=R, fill=255)
    return mask


def fish(draw: ImageDraw.ImageDraw) -> None:
    """一只圆滚滚的白色小鱼，朝左。"""
    body = (255, 255, 255, 255)
    # 尾巴
    draw.polygon([(640, 452), (884, 330), (858, 520), (884, 712), (640, 592)],
                 fill=body)
    # 身体
    draw.ellipse([160, 316, 720, 724], fill=body)
    # 背鳍
    draw.polygon([(372, 356), (450, 258), (528, 360)], fill=body)
    # 腹鳍
    draw.polygon([(396, 696), (462, 792), (534, 700)], fill=body)
    # 眼睛
    draw.ellipse([290, 436, 374, 520], fill=(20, 30, 60, 255))
    draw.ellipse([314, 458, 344, 488], fill=(255, 255, 255, 255))


def caret(draw: ImageDraw.ImageDraw) -> None:
    """>_ 控制台提示符，压在小鱼身上。"""
    cx, cy = 552, 520
    draw.line([(cx - 62, cy - 74), (cx + 16, cy), (cx - 62, cy + 74)],
              fill=(58, 110, 246, 255), width=44, joint="curve")


def build() -> Image.Image:
    base = tile()
    mask = rounded_mask()
    art = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fish(d)
    caret(d)
    # 鱼身阴影
    shadow = layer.filter(ImageFilter.GaussianBlur(26))
    shadow.putalpha(shadow.getchannel("A").point(lambda v: int(v * 0.35)))
    art.paste((0, 0, 0, 60), (0, 22), shadow)
    art = Image.alpha_composite(art, layer)
    # 顶部高光
    hilite = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hilite).ellipse([120, -260, 940, 260], fill=(255, 255, 255, 26))
    art = Image.alpha_composite(art, hilite)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(base, (0, 0))
    out = Image.alpha_composite(out, art)
    out.putalpha(mask)
    return out


icon = build()
icon.resize((512, 512), Image.LANCZOS).save("icon_512.png")
sizes = [16, 24, 32, 48, 64, 128, 256]
icon.save("bot_new.ico", format="ICO",
          sizes=[(s, s) for s in sizes])
strip = Image.new("RGBA", (64 * 3 + 80 + 210, 120), (245, 246, 248, 255))
x = 20
for s in (16, 32, 48):
    strip.paste(icon.resize((s, s), Image.LANCZOS), (x, (120 - s) // 2), icon.resize((s, s), Image.LANCZOS))
    x += s + 20
strip.paste(icon.resize((96, 96), Image.LANCZOS), (x, 12), icon.resize((96, 96), Image.LANCZOS))
strip.save("icon_sizes.png")
print("ok")
