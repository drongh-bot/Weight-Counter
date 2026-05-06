from PIL import Image

# 输入 PNG 路径
png_path = "../app/resources/icons/app.png"

# 输出 ICO 路径
ico_path = "../app/resources/icons/app.ico"

# ICO 需要的尺寸
sizes = [
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]

img = Image.open(png_path)

# 生成 ICO
img.save(ico_path, sizes=sizes)

print("ICO 已生成:", ico_path)
