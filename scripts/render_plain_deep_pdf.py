#!/usr/bin/env python3
"""Render the exact reusable 4PIE Plain Deep Report v1 format."""
import argparse, html, json, re
from datetime import date
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, HRFlowable, PageTemplate, Paragraph, Spacer, Table, TableStyle
import plain_deep_design as d

NAVY=d.NAVY; BODY=d.BODY; MUTED=d.MUTED; LINE=d.LINE; SOFT=d.SOFT; GREEN=d.GREEN; AMBER=d.AMBER; PURPLE=d.PURPLE; WHITE=d.WHITE; BG=d.BG
ST={
 'h1':ParagraphStyle('body_h1',fontName='TCB',fontSize=20,leading=27,textColor=NAVY,spaceBefore=4,spaceAfter=12),
 'h2':ParagraphStyle('body_h2',fontName='TCB',fontSize=14.2,leading=20,textColor=NAVY,spaceBefore=12,spaceAfter=7),
 'h3':ParagraphStyle('body_h3',fontName='TCB',fontSize=11.2,leading=16,textColor=NAVY,spaceBefore=8,spaceAfter=5),
 'body':ParagraphStyle('body_text',fontName='TC',fontSize=10.15,leading=17.2,textColor=BODY,spaceAfter=8,allowWidows=0,allowOrphans=0),
 'bullet':ParagraphStyle('body_bullet',fontName='TC',fontSize=9.8,leading=16.2,textColor=BODY,leftIndent=12,firstLineIndent=-8,spaceAfter=4),
 'quote':ParagraphStyle('body_quote',fontName='TCB',fontSize=11.2,leading=18,textColor=NAVY,leftIndent=5,rightIndent=5),
 'small':ParagraphStyle('body_small',fontName='TC',fontSize=8.4,leading=12.5,textColor=MUTED),
}

def inline(text):
    placeholders=[]
    def keep(match): placeholders.append((match.group(1),match.group(2))); return f'\x00{len(placeholders)-1}\x00'
    text=re.sub(r'(\*\*|`)(.+?)\1',keep,text); text=html.escape(text)
    for index,(marker,value) in enumerate(placeholders):
        replacement=f'<b>{html.escape(value)}</b>' if marker=='**' else f"<font name='TC'>{html.escape(value)}</font>"
        text=text.replace(f'\x00{index}\x00',replacement)
    return text

def markdown_story(md):
    story=[]; buf=[]
    def flush():
        if buf:
            text=' '.join(x.strip() for x in buf).strip(); buf.clear()
            if text: story.append(Paragraph(inline(text),ST['body']))
    for raw in md.splitlines():
        line=raw.strip()
        if not line: flush(); continue
        if line.startswith('# '):
            flush(); title=line[2:].strip(); table=Table([[Paragraph(inline(title),ST['h1']),Paragraph('裁決、候選版本、四派證據與修正條件同頁呈現',ST['small'])]],colWidths=[102*mm,56*mm]); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SOFT),('BOX',(0,0),(-1,-1),.6,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)])); story.extend([Spacer(1,12),table,Spacer(1,10)])
        elif line.startswith('## '): flush(); story.extend([Paragraph(inline(line[3:]),ST['h2']),HRFlowable(width='100%',thickness=.45,color=LINE,spaceAfter=5)])
        elif line.startswith('### '): flush(); story.append(Paragraph(inline(line[4:]),ST['h3']))
        elif line.startswith('>'):
            flush(); box=Table([[Paragraph(inline(line.lstrip('> ')),ST['quote'])]],colWidths=[158*mm]); box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GREEN),('BOX',(0,0),(-1,-1),.6,LINE),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)])); story.extend([box,Spacer(1,7)])
        elif re.match(r'^[-*] ',line): flush(); story.append(Paragraph('• '+inline(line[2:]),ST['bullet']))
        elif re.match(r'^\d+\. ',line): flush(); story.append(Paragraph(inline(line),ST['bullet']))
        elif not line.startswith('```'): buf.append(line)
    flush(); return story

def body_pdf(md,path,label):
    def chrome(c,doc):
        c.saveState(); c.setFillColor(BG); c.rect(0,0,A4[0],A4[1],0,1); c.setStrokeColor(LINE); c.line(18*mm,15*mm,A4[0]-18*mm,15*mm); c.setFont('TC',7.6); c.setFillColor(MUTED); c.drawString(18*mm,8.5*mm,label); c.drawRightString(A4[0]-18*mm,8.5*mm,f'{doc.page+4:02d}'); c.restoreState()
    frame=Frame(18*mm,20*mm,A4[0]-36*mm,A4[1]-37*mm,id='main',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0); doc=BaseDocTemplate(str(path),pagesize=A4); doc.addPageTemplates(PageTemplate('editorial',[frame],onPage=chrome)); doc.build(markdown_story(md))

def chapter_titles(md):
    h1=[x[2:].strip() for x in md.splitlines() if x.startswith('# ')]
    return h1[1:] if len(h1)>1 else [x[3:].strip() for x in md.splitlines() if x.startswith('## ')][:12]

def page_map(body,titles):
    texts=[(p.extract_text() or '').replace(' ','') for p in PdfReader(str(body)).pages]; result={}
    for title in titles:
        key=title.replace('｜','').replace('：','').replace(' ','')[:6]; result[title]=next((i+5 for i,text in enumerate(texts) if key in text.replace('｜','').replace('：','')),'—')
    return result

def front_pdf(path,titles,pages,scores,packet,title,subject,generated,start_year):
    c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1); thesis=(packet or {}).get('core_thesis') or '四派先獨立推演，再比較人生版本與成立條件。'; d.cover(c,title,subject,thesis,generated)
    d.header(c,2,'CONTENTS','目錄與閱讀路線','先讀結論及評分，再按人生領域進入深讀正文。')
    if not titles or len(titles)>14: raise ValueError(f'contents requires 1-14 chapters, got {len(titles)}')
    missing=[name for name in titles if pages.get(name)=='—']
    if missing: raise ValueError(f'contents page mapping failed: {missing}')
    step=15.5 if len(titles)>11 else 16.5
    for i,name in enumerate(titles[:14]):
        y=(220-i*step)*mm; d.card(c,18*mm,y,174*mm,13*mm,SOFT if i%2==0 else WHITE,shadow=False,r=4); d.para(c,f'{i:02d}',23*mm,y+3*mm,13*mm,7*mm,'small'); d.para(c,name,40*mm,y+3*mm,125*mm,7*mm,'body'); d.para(c,str(pages[name]),173*mm,y+3*mm,12*mm,7*mm,'h3')
    d.end(c)
    d.header(c,3,'DOMAIN SCOREBOARD','八領域評分 Dashboard','四項分數回答不同問題；分數是閱讀索引，不是命運保證或人格價值。')
    rows=((scores or {}).get('domains') or (scores or {}).get('natal_dimensions') or [])[:8]
    if len(rows)!=8: raise ValueError(f'exactly 8 scored domains required, got {len(rows)}')
    for i,item in enumerate(rows):
        col=i%2; row=i//2; x=(18+col*90)*mm; y=(197-row*43)*mm; d.card(c,x,y,83*mm,38*mm,WHITE); d.para(c,str(item.get('label') or item.get('domain')),x+5*mm,y+26*mm,35*mm,8*mm,'h3')
        for j,(key,name,color) in enumerate((('flow_score','順勢',d.BLUE),('potential_score','潛力',colors.HexColor('#4F8D82')),('friction_score','阻力',colors.HexColor('#C4914E')),('confidence_score','信心',NAVY))):
            val=item.get(key,item.get('fortune_score') if key=='flow_score' else None)
            if not isinstance(val,(int,float)) or not 0<=val<=100: raise ValueError(f'invalid {key} for score row {i}')
            yy=y+(22-j*5.6)*mm; d.para(c,name,x+43*mm,yy,10*mm,5*mm,'small'); c.setFillColor(colors.HexColor('#E7ECEF')); c.roundRect(x+54*mm,yy+.8*mm,19*mm,3.2*mm,1.6*mm,0,1)
            if isinstance(val,(int,float)): c.setFillColor(color); c.roundRect(x+54*mm,yy+.8*mm,19*mm*max(0,min(100,val))/100,3.2*mm,1.6*mm,0,1)
            d.para(c,str(val),x+75*mm,yy,6*mm,5*mm,'small')
    d.end(c)
    annual_by_year={int(x['year']):x for x in (packet or {}).get('annual_rulings',[]) if str(x.get('year','')).isdigit()}; expected=list(range(start_year,start_year+5)); missing_years=[year for year in expected if year not in annual_by_year]
    if missing_years: raise ValueError(f'missing annual rulings for {missing_years}')
    d.header(c,4,'TIME INDEX',f'{start_year}-{start_year+4} 時間索引','先看事件次序，再到正文閱讀成立條件與失效邊界。'); annual=[annual_by_year[year] for year in expected]; c.setStrokeColor(d.BLUE); c.setLineWidth(3); c.line(31*mm,210*mm,31*mm,66*mm)
    for i,item in enumerate(annual):
        y=(197-i*32)*mm; c.setFillColor(NAVY); c.circle(31*mm,y+8*mm,5*mm,0,1); d.card(c,43*mm,y-5*mm,149*mm,26*mm,(GREEN,SOFT,PURPLE,AMBER,GREEN)[i],shadow=False); d.para(c,str(item.get('year')),49*mm,y+7*mm,22*mm,8*mm,'h2'); d.para(c,str(item.get('central_task') or item.get('theme') or '年度主題'),75*mm,y+8*mm,105*mm,7*mm,'h3'); detail=item.get('strongest_opportunity') or item.get('result_preparing_next_year') or ''; d.para(c,str(detail),75*mm,y-1*mm,105*mm,7*mm,'small')
    d.end(c); c.save()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('markdown',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--packet',type=Path,required=True); ap.add_argument('--scores',type=Path,required=True); ap.add_argument('--title',default='命運裁決報告'); ap.add_argument('--subject',required=True); ap.add_argument('--generated',default=date.today().isoformat()); ap.add_argument('--start-year',type=int,default=2026)
    a=ap.parse_args(); md=a.markdown.read_text(encoding='utf-8'); packet=json.loads(a.packet.read_text(encoding='utf-8')); scores=json.loads(a.scores.read_text(encoding='utf-8')); a.output.parent.mkdir(parents=True,exist_ok=True); body=a.output.with_suffix('.body.tmp.pdf'); front=a.output.with_suffix('.front.tmp.pdf')
    try:
        body_pdf(md,body,'4PIE 深讀報告'); titles=chapter_titles(md); front_pdf(front,titles,page_map(body,titles),scores,packet,a.title,a.subject,a.generated,a.start_year); writer=PdfWriter()
        for src in (front,body):
            for page in PdfReader(str(src)).pages: writer.add_page(page)
        writer.add_metadata({'/Title':a.title,'/Author':'4PIE'}); writer.write(str(a.output)); print(a.output)
    except Exception:
        if a.output.exists(): a.output.unlink()
        raise
    finally:
        for temp in (body,front):
            if temp.exists(): temp.unlink()

if __name__=='__main__': main()
