"""Add golden background bands using the matching TeX marker build."""
import argparse
from collections import defaultdict

import fitz

MARKER_INK = 0x8C5B00
GOLD_BACKGROUND = (1, .89, .50)


def lines(page):
    for block in page.get_text("rawdict", flags=fitz.TEXTFLAGS_RAWDICT & ~fitz.TEXT_PRESERVE_IMAGES)["blocks"]:
        yield from block["lines"]


def glyph_positions(page):
    positions = defaultdict(list)
    for line in lines(page):
        for span in line["spans"]:
            for char in span["chars"]:
                # A color change can move punctuation in a bidirectional line.
                if char["c"].isalnum():
                    x, y = char["origin"]
                    positions[char["c"], round(y, 1)].append(x)
    return {key: sorted(values) for key, values in positions.items()}


def matching_layout(base, mask):
    normal = glyph_positions(base)
    marked = glyph_positions(mask)
    if base.rect != mask.rect or normal.keys() != marked.keys():
        return False
    return all(
        len(normal[key]) == len(xs)
        and all(abs(x - y) <= .5 for x, y in zip(normal[key], xs))
        for key, xs in marked.items()
    )


def highlight_bands(page):
    for line in lines(page):
        band = None
        for span in sorted(line["spans"], key=lambda item: item["bbox"][0]):
            if span["color"] != MARKER_INK:
                continue
            x0, _, x1, _ = span["bbox"]
            _, baseline = span["origin"]
            size = span["size"]
            rect = fitz.Rect(x0 - .6, baseline - .86 * size,
                             x1 + .6, baseline + .22 * size) & page.rect
            if band is not None and rect.x0 <= band.x1 + 2:
                band |= rect
            else:
                if band is not None:
                    yield band
                band = rect
        if band is not None:
            yield band


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("normal_pdf")
    parser.add_argument("marker_pdf")
    parser.add_argument("output_pdf")
    args = parser.parse_args()
    with fitz.open(args.normal_pdf) as normal, fitz.open(args.marker_pdf) as marker:
        if len(normal) != len(marker):
            raise ValueError("The normal and marker builds have different page counts.")
        marked_pages = 0
        for number, (base, mask) in enumerate(zip(normal, marker, strict=True), 1):
            bands = list(highlight_bands(mask))
            if not bands:
                continue
            if not matching_layout(base, mask):
                raise ValueError(f"Text layout differs between builds on page {number}.")
            background = base.new_shape()
            for band in bands:
                background.draw_rect(band)
            background.finish(color=None, fill=GOLD_BACKGROUND)
            background.commit(overlay=False)
            marked_pages += 1
        if not marked_pages:
            raise ValueError("The marker build has no marked text.")
        normal.save(args.output_pdf, garbage=3, deflate=True)
        print(f"Added golden highlight backgrounds on {marked_pages} pages.")


if __name__ == "__main__":
    main()
