from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import plain_deep_design as design

def main():
    font_dir=ROOT/"assets"/"fonts"
    for name in ("NotoSansTC-SemiBold.ttf","NotoSansTC-Bold.ttf"):
        path=font_dir/name
        assert path.is_file() and path.stat().st_size>1_000_000,name
    assert design.S["body"].fontName=="TCS"
    assert design.S["h1"].fontName=="TCB"
    print("font_weights_ok")

if __name__=="__main__": main()
