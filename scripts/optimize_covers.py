"""
Optimize book covers: resize to max 400px width + convert to WebP (quality 75).
Updates data.json cover paths to .webp.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image

# Config
MAX_WIDTH = 400
WEBP_QUALITY = 75
SITE_DIR = Path(__file__).resolve().parent.parent / "site"
COVERS_DIR = SITE_DIR / "assets" / "covers"
DATA_JSON = SITE_DIR / "data.json"


def optimize_covers():
    if not COVERS_DIR.exists():
        print(f"❌ Covers directory not found: {COVERS_DIR}")
        sys.exit(1)

    # Get all image files (jpg, jpeg, png)
    image_exts = {".jpg", ".jpeg", ".png"}
    images = [f for f in COVERS_DIR.iterdir() if f.suffix.lower() in image_exts]
    
    if not images:
        print("⚠️  No JPG/PNG images found to convert.")
        return

    print(f"📸 Found {len(images)} images to optimize")
    print(f"   Max width: {MAX_WIDTH}px | WebP quality: {WEBP_QUALITY}%")
    print("=" * 60)

    total_before = 0
    total_after = 0
    converted = 0

    for img_path in sorted(images):
        try:
            original_size = img_path.stat().st_size
            total_before += original_size

            # Open and resize
            with Image.open(img_path) as img:
                # Convert RGBA to RGB (WebP supports both, but smaller with RGB)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if wider than MAX_WIDTH
                if img.width > MAX_WIDTH:
                    ratio = MAX_WIDTH / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

                # Save as WebP
                webp_path = img_path.with_suffix(".webp")
                img.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)

            new_size = webp_path.stat().st_size
            total_after += new_size

            # Delete original
            img_path.unlink()
            converted += 1

            reduction = (1 - new_size / original_size) * 100
            print(f"  ✅ {img_path.name}")
            print(f"     {original_size/1024:.0f}KB → {new_size/1024:.0f}KB ({reduction:.0f}% smaller)")

        except Exception as e:
            print(f"  ❌ {img_path.name}: {e}")

    print("=" * 60)
    print(f"📊 Converted: {converted}/{len(images)} images")
    print(f"💾 Before: {total_before/1024:.0f}KB ({total_before/1024/1024:.1f}MB)")
    print(f"💾 After:  {total_after/1024:.0f}KB ({total_after/1024/1024:.1f}MB)")
    print(f"🎉 Saved:  {(total_before-total_after)/1024:.0f}KB ({(1-total_after/total_before)*100:.0f}% reduction)")

    # Update data.json
    update_data_json()


def update_data_json():
    """Update cover paths in data.json from .jpg/.png to .webp"""
    if not DATA_JSON.exists():
        print(f"\n❌ data.json not found: {DATA_JSON}")
        return

    with open(DATA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for book in data:
        cover = book.get("cover", "")
        if cover:
            # Replace .jpg, .jpeg, .png with .webp
            for ext in [".jpg", ".jpeg", ".png"]:
                if cover.lower().endswith(ext):
                    book["cover"] = cover[:cover.rfind(".")] + ".webp"
                    updated += 1
                    break

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n📝 Updated {updated} cover paths in data.json (.jpg/.png → .webp)")


if __name__ == "__main__":
    optimize_covers()
