#!/usr/bin/env python3
"""Cut the boot splash and the installer banner out of the CROATOAN artwork.

Both images used to carry the upstream #!++ wordmark, which is the first and
the last thing anyone sees of this image - the boot menu background and the
banner across the top of the installer. Rather than redraw the name in some
approximation of the artwork's typeface, this crops the wordmark straight out
of the wallpaper, so all three agree by construction.

The boot splash is not a PNG. live-build renders config/bootloaders/*/splash.svg
at build time - 640x480 for syslinux, 800x600 for grub - and only skips that
when a splash.png is already sitting next to it. Since the BIOS bootloader here
is syslinux and there was no isolinux/splash.png, replacing a PNG under
grub-pc/ fixed the EFI boot menu and left the BIOS one showing #!++. So the
wordmark goes into the SVG itself, where it reaches every bootloader at once,
and the PNGs stay out of the way.

Run by hand after changing the wallpaper or the version; the results are
committed, because the build must not need Pillow:

    python3 assets/make-branding.py
"""
import base64
import io
import pathlib
import re
import sys

from PIL import Image

SRC = "config/includes.chroot_after_packages/usr/share/backgrounds/croatoan-wallpaper.png"
BANNER = "config/includes.installer/usr/share/graphics/logo_debian.png"
SPLASHES = sorted(pathlib.Path("config/bootloaders").glob("*/splash.svg"))

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

    splash(mark)

    # Installer banner: wordmark left, release right, on the same charcoal the
    # installer's gtkrc uses for its header.
    out = Image.new("RGBA", (800, 75), BANNER_BG)
    art = fit(mark, 330, 61)
    out.paste(art.convert("RGBA"), (18, (75 - art.height) // 2))

    version = version_text()
    out.paste(version, (800 - 24 - version.width, (75 - version.height) // 2), version)
    out.save(BANNER)
    print(f"wrote {BANNER} {out.size}, artwork {art.size}")


def splash(mark):
    """Put the wordmark into every bootloader's splash.svg.

    The old logo is a single <image> element carrying a base64 PNG, so this
    swaps the payload rather than touching the drawing. Two other changes go
    with it: the backdrop goes from #333333 to black, because the artwork's own
    background is black and anything else turns the crop into a visible
    rectangle, and the product line stops naming the old project.
    """
    art = fit(mark, 646, 190)
    buf = io.BytesIO()
    art.save(buf, format="PNG", optimize=True)
    payload = base64.b64encode(buf.getvalue()).decode("ascii")

    version = read_version()

    for path in SPLASHES:
        t = path.read_text()

        t, n = re.subn(
            r'(xlink:href="data:image/png;base64,)[^"]*(")',
            lambda m: m.group(1) + payload + m.group(2),
            t,
        )
        if n != 1:
            sys.exit(f"make-branding: {path}: expected one embedded image, found {n}")

        # The slot the old logo filled is 323x195, a different shape to the
        # wordmark; without this the artwork is stretched to fit it.
        t = t.replace('preserveAspectRatio="none"', 'preserveAspectRatio="xMinYMid meet"')

        t = t.replace(
            ">CrunchBang Plus Plus<", f">Croatoan {version}<"
        ).replace(
            ">Version: 13 @ARCHITECTURE@<", f">Version: {version} @ARCHITECTURE@<"
        )

        t = t.replace('style="fill:#333333;fill-opacity:1;stroke:none"',
                      'style="fill:#000000;fill-opacity:1;stroke:none"')

        if "CrunchBang" in t:
            sys.exit(f"make-branding: {path}: the old name survived the rewrite")

        path.write_text(t)
        print(f"wrote {path}")


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
