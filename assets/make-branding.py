#!/usr/bin/env python3
"""Cut the boot splash and the installer banner out of the CROATOAN artwork.

Both images used to carry the upstream #!++ wordmark, which is the first and
the last thing anyone sees of this image - the boot menu background and the
banner across the top of the installer. Rather than redraw the name in some
approximation of the artwork's typeface, this crops the wordmark straight out
of the wallpaper, so all three agree by construction.

Run by hand after changing the wallpaper; the results are committed, because
the build must not need Pillow:

    python3 assets/make-branding.py
"""
import sys

from PIL import Image

SRC = "config/includes.chroot_after_packages/usr/share/backgrounds/croatoan-wallpaper.png"
SPLASH = "config/bootloaders/grub-pc/splash.png"
BANNER = "config/includes.installer/usr/share/graphics/logo_debian.png"

# Backdrop of the installer banner. Black rather than the charcoal it replaces,
# because the artwork's own background is black and any other colour turns the
# crop into a visible pasted rectangle.
BANNER_BG = (0, 0, 0, 255)


def wordmark(src):
    """Tightest crop that still contains the whole glow."""
    grey = src.convert("L")
    # 12/255 keeps the halo, which is most of what makes the artwork read as
    # itself; a tighter threshold cuts the letters out of their own light.
    mask = grey.point(lambda v: 255 if v > 12 else 0)
    box = mask.getbbox()
    if box is None:
        sys.exit("make-branding: the artwork is uniformly black")
    return src.crop(box), box


def fit(img, w, h):
    """Scale to fit inside w x h without distorting."""
    scale = min(w / img.width, h / img.height)
    return img.resize(
        (max(1, round(img.width * scale)), max(1, round(img.height * scale))),
        Image.LANCZOS,
    )


def main():
    src = Image.open(SRC).convert("RGB")
    mark, box = wordmark(src)
    print(f"wordmark: {box} -> {mark.size}")

    # Boot splash. The grub theme starts its menu at 52% of the height and the
    # help bar sits 50px off the bottom, so the artwork gets the top half.
    out = Image.new("RGBA", (640, 386), (0, 0, 0, 255))
    art = fit(mark, 560, 150)
    out.paste(art.convert("RGBA"), ((640 - art.width) // 2, (193 - art.height) // 2))
    out.save(SPLASH)
    print(f"wrote {SPLASH} {out.size}, artwork {art.size}")

    # Installer banner: wordmark left, release right, on the same charcoal the
    # installer's gtkrc uses for its header.
    out = Image.new("RGBA", (800, 75), BANNER_BG)
    art = fit(mark, 330, 61)
    out.paste(art.convert("RGBA"), (18, (75 - art.height) // 2))

    version = version_text()
    out.paste(version, (800 - 24 - version.width, (75 - version.height) // 2), version)
    out.save(BANNER)
    print(f"wrote {BANNER} {out.size}, artwork {art.size}")


def version_text():
    """The release number, in the grey the old banner used."""
    from PIL import ImageDraw, ImageFont

    text = read_version()
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34
    )
    box = font.getbbox(text)
    img = Image.new("RGBA", (box[2] - box[0] + 2, box[3] - box[1] + 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-box[0], -box[1]), text, font=font, fill=(216, 216, 216, 255))
    return img


def read_version():
    with open("cbpp.conf") as fh:
        for line in fh:
            if line.startswith("CBPP_VERSION="):
                return line.split("=", 1)[1].strip().strip('"')
    sys.exit("make-branding: CBPP_VERSION not found in cbpp.conf")


main()
