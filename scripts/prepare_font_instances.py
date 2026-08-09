#!/usr/bin/env python3
"""Create deterministic static Traditional Chinese font weights from the bundled variable font."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT=Path(__file__).resolve().parents[1]
FONT_DIR=ROOT/"assets"/"fonts"
SOURCE=FONT_DIR/"NotoSansTC-Variable.ttf"
TARGETS=((600,FONT_DIR/"NotoSansTC-SemiBold.ttf"),(750,FONT_DIR/"NotoSansTC-Bold.ttf"))

def main():
    if not SOURCE.is_file(): raise SystemExit(f"FONT_SOURCE_MISSING:{SOURCE}")
    for weight,target in TARGETS:
        if target.is_file() and target.stat().st_size>1_000_000: continue
        font=TTFont(str(SOURCE))
        instance=instantiateVariableFont(font,{"wght":weight},inplace=True)
        instance.save(str(target))
        print(f"FONT_WEIGHT_READY weight={weight} path={target}")
    return 0

if __name__=="__main__": raise SystemExit(main())
