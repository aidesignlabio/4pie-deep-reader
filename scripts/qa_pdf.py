#!/usr/bin/env python3
"""Render and validate every PDF page without requiring system Poppler."""
import argparse, json
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageStat
from pypdf import PdfReader

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pdf',type=Path); ap.add_argument('--output-dir',type=Path)
    a=ap.parse_args(); out=a.output_dir or a.pdf.with_name(a.pdf.stem+'-qa'); out.mkdir(parents=True,exist_ok=True)
    doc=fitz.open(a.pdf); reader=PdfReader(str(a.pdf)); images=[]; low=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False)
        path=out/f'page-{i+1:03d}.png'; pix.save(path); image=Image.open(path).convert('RGB'); images.append(image)
        if ImageStat.Stat(image.convert('L')).stddev[0]<3: low.append(i+1)
    cols=5; tw,th=220,311; rows=(len(images)+cols-1)//cols
    sheet=Image.new('RGB',(cols*240,rows*345),'#D7D7D7'); draw=ImageDraw.Draw(sheet)
    for i,image in enumerate(images):
        thumb=image.copy(); thumb.thumbnail((tw,th)); x=(i%cols)*240+10; y=(i//cols)*345+22
        sheet.paste(thumb,(x,y)); draw.text((x,y-17),f'Page {i+1}',fill='black')
    sheet.save(out/'contact-sheet.png')
    texts=[p.extract_text() or '' for p in reader.pages]
    result={'pdf':a.pdf.name,'page_count':len(reader.pages),'rendered_page_count':len(images),'extractable_characters':sum(map(len,texts)),'replacement_characters':sum(x.count('\ufffd') for x in texts),'low_content_pages':low,'qa_ok':len(reader.pages)==len(images) and not low and all(len(x.strip())>=20 for x in texts)}
    (out/'pdf_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False)); raise SystemExit(0 if result['qa_ok'] else 2)

if __name__=='__main__': main()
