from __future__ import annotations

import argparse
import csv
from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation
from pptx.util import Inches, Pt

from lead_contract import update_run_manifest


def parse_slides(path: Path) -> list[tuple[str, list[str]]]:
    slides: list[tuple[str, list[str]]] = []
    title = ""
    bullets: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            if title:
                slides.append((title, bullets))
            title = line[2:].strip()
            bullets = []
        elif line.startswith("- "):
            bullets.append(line[2:].strip())
    if title:
        slides.append((title, bullets))
    return slides


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, default=Path("evidence/run_manifest_2026-11-09.json"))
    args = parser.parse_args()
    slides = parse_slides(args.content)
    if len(slides) != 5:
        raise SystemExit(f"expected exactly five slides, found {len(slides)}")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    for title, bullets in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = __import__("pptx").dml.color.RGBColor(245, 248, 252)
        title_box = slide.shapes.add_textbox(Inches(0.65), Inches(0.45), Inches(12), Inches(0.8))
        title_frame = title_box.text_frame
        title_frame.text = title
        title_frame.paragraphs[0].font.size = Pt(28)
        title_frame.paragraphs[0].font.bold = True
        title_frame.paragraphs[0].font.color.rgb = __import__("pptx").dml.color.RGBColor(31, 78, 121)
        body = slide.shapes.add_textbox(Inches(0.85), Inches(1.45), Inches(11.7), Inches(5.4))
        frame = body.text_frame
        frame.word_wrap = True
        for index, bullet in enumerate(bullets):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0
            paragraph.font.size = Pt(19 if len(bullets) <= 6 else 15)
            paragraph.space_after = Pt(13)
            paragraph.font.color.rgb = __import__("pptx").dml.color.RGBColor(45, 45, 45)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(args.output)
    if args.run_manifest.exists():
        update_run_manifest(args.run_manifest, outputs={"deck": args.output})
    print(f"created {args.output} with {len(prs.slides)} slides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
