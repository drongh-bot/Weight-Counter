from pathlib import Path

from PIL import Image

icons_dir = Path(__file__).resolve().parent.parent / "app" / "resources" / "icons"

sizes = [
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]

for png_path in icons_dir.glob("*.png"):
    img = Image.open(png_path)
    ico_path = png_path.with_suffix(".ico")
    img.save(ico_path, sizes=sizes)
    print(f"ICO: {ico_path.name}")
