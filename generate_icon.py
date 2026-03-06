"""
Generate application icon for Peak Volume Manager.

Creates a multi-resolution .ico file with the "PV" logo in the app's
blue accent color. Run this once before building with PyInstaller.

Usage:
    python generate_icon.py

Requires: Pillow (pip install Pillow)
Output:   assets/icon.ico
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is required: pip install Pillow")
    sys.exit(1)


def create_icon_image(size: int) -> Image.Image:
    """Create a single icon image at the given size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    margin = max(1, size // 32)
    draw.ellipse(
        [margin, margin, size - margin - 1, size - margin - 1],
        fill='#2196F3',
        outline='#FFFFFF',
        width=max(1, size // 32),
    )

    # "PV" text centered in the circle
    font_size = int(size * 0.38)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except (OSError, IOError):
            # Fallback to default bitmap font
            font = ImageFont.load_default()

    text = "PV"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) // 2 - bbox[0]
    text_y = (size - text_h) // 2 - bbox[1]

    draw.text((text_x, text_y), text, fill='#FFFFFF', font=font)

    return img


def main():
    os.makedirs('assets', exist_ok=True)

    # Standard Windows .ico sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon_image(s) for s in sizes]

    ico_path = os.path.join('assets', 'icon.ico')
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icon saved to {ico_path}")

    # Also save a 256px PNG for Inno Setup's wizard image
    png_path = os.path.join('assets', 'icon_256.png')
    images[-1].save(png_path, format='PNG')
    print(f"PNG icon saved to {png_path}")


if __name__ == '__main__':
    main()
