#!/usr/bin/env python3
from __future__ import annotations

import argparse, html, json, re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

W, H = A4
BG=colors.HexColor('#F7F5F0'); WHITE=colors.white; INK=colors.HexColor('#17324D')
SECOND=colors.HexColor('#2F3A45'); MUTED=colors.HexColor('#6B7785'); LINE=colors.HexColor('#DCE3E8')
BLUE=colors.HexColor('#244E73'); BLUE_DARK=colors.HexColor('#173B5B'); BLUE_SOFT=colors.HexColor('#EAF1F6')
GREEN_SOFT=colors.HexColor('#DCEAE6'); AMBER_SOFT=colors.HexColor('#F3E8D2'); RED_SOFT=colors.HexColor('#F2DEDD'); PURPLE_SOFT=colors.HexColor('#E7E3ED')

def font_path(bold=False):
    names=['msjhbd.ttc','NotoSansTC-Bold.ttf','NotoSansCJKtc-Bold.otf'] if bold else ['msjh.ttc','NotoSansTC-Regular.ttf','NotoSansCJKtc-Regular.otf']
    roots=[Path('C:/Windows/Fonts'),Path('/usr/share/fonts/opentype/noto'),Path('/usr/share/fonts/truetype/noto')]
    for root in roots:
        for name in names:
            p=root/name
            if p.is_file(): return p
    raise RuntimeError('Traditional Chinese font not found')

def register_fonts():
    pdfmetrics.registerFont(TTFont('TC',str(font_path(False))))
    pdfmetrics.registerFont(TTFont('TCB',str(font_path(True))))

def rich(s):
    s=html.escape(s.strip())
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`([^`]+)`',r'<font name="TC">\1</font>',s)
    return s

class Card(Flowable):
    def __init__(self, para, width, bg=WHITE, accent=False):
        super().__init__(); self.para=para; self.width=width; self.bg=bg; self.accent=accent; self.pad=6*mm
    def wrap(self, aw, ah):
        self.width=min(self.width,aw); _,ph=self.para.wrap(self.width-2*self.pad,ah); self.height=ph+2*self.pad; return self.width,self.height
    def draw(self):
        c=self.canv; c.saveState(); c.setFillColor(colors.HexColor('#DEDEE3')); c.roundRect(0,-1,self.width,self.height,14,0,1)
        c.setFillColor(self.bg); c.roundRect(0,0,self.width,self.height,14,0,1)
        if self.accent: c.setFillColor(BLUE); c.roundRect(0,0,2.2*mm,self.height,1.1*mm,0,1)
        self.para.drawOn(c,self.pad+(2*mm if self.accent else 0),self.pad); c.restoreState()

def styles():
    return {
      'cover':ParagraphStyle('cover',fontName='TCB',fontSize=34,leading=45,textColor=INK,alignment=TA_CENTER),
      'coverSub':ParagraphStyle('coverSub',fontName='TC',fontSize=11,leading=18,textColor=MUTED,alignment=TA_CENTER),
      'h1':ParagraphStyle('h1',fontName='TCB',fontSize=24,leading=32,textColor=INK,spaceAfter=5*mm,keepWithNext=True),
      'h2':ParagraphStyle('h2',fontName='TCB',fontSize=16,leading=23,textColor=INK,spaceBefore=5*mm,spaceAfter=2.5*mm,keepWithNext=True),
      'body':ParagraphStyle('body',fontName='TC',fontSize=10.4,leading=17.2,textColor=SECOND,spaceAfter=3.2*mm),
      'lead':ParagraphStyle('lead',fontName='TCB',fontSize=13.2,leading=21,textColor=BLUE_DARK,spaceAfter=3*mm),
      'bullet':ParagraphStyle('bullet',fontName='TC',fontSize=10.1,leading=16.5,textColor=SECOND,leftIndent=6*mm,firstLineIndent=-3.5*mm,spaceAfter=2*mm),
      'table':ParagraphStyle('table',fontName='TC',fontSize=8.1,leading=12.2,textColor=SECOND),
      'tableHead':ParagraphStyle('tableHead',fontName='TCB',fontSize=8.3,leading=12.2,textColor=INK),
      'small':ParagraphStyle('small',fontName='TC',fontSize=8.3,leading=12.5,textColor=MUTED),
      'metric':ParagraphStyle('metric',fontName='TCB',fontSize=10.5,leading=15,textColor=INK),
      'micro':ParagraphStyle('micro',fontName='TC',fontSize=7.2,leading=10.5,textColor=MUTED),
    }

POSITION_SYMBOL={'support':'●','refine':'修','limit':'限','oppose':'衝','not_comparable':'○','not_applicable':'○','insufficient':'?'}
TIER_LABEL={'high_consensus':'高共識','moderate_consensus':'中度共識','single_school_strong_signal':'單派強訊號','conflict':'派別分歧','insufficient':'證據不足'}
TIER_BG={'high_consensus':GREEN_SOFT,'moderate_consensus':BLUE_SOFT,'single_school_strong_signal':PURPLE_SOFT,'conflict':AMBER_SOFT,'insufficient':RED_SOFT}
SCHOOL_LABEL={'western':'西洋占星','ziwei':'紫微斗數','vedic':'吠陀占星','bazi':'八字'}
DOMAIN_LABEL={'career':'事業','wealth':'財富','relationship':'感情','home_family':'家宅／家庭','authority_status':'地位／權力'}

class ReportDocTemplate(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'h1':
            text=flowable.getPlainText(); key=f'section-{self.seq.nextf("section")}'
            self.canv.bookmarkPage(key); self.canv.addOutlineEntry(text,key,0,False)
            self.notify('TOCEntry',(0,text,self.page,key))

def p(value, style):
    return Paragraph(rich(str(value or '—')), style)

def section_title(st, kicker, title, subtitle=''):
    items=[p(kicker,st['small']),p(title,st['h1'])]
    if subtitle: items.append(p(subtitle,st['small']))
    return items

def dashboard_pages(packet, doc, st):
    if not packet: return []
    story=[]
    judgments=packet.get('consequential_judgments') or packet.get('consensus_matrix',[])[:5]
    story += section_title(st,'EXECUTIVE DASHBOARD','一頁掌握人生主線','只顯示已有裁決；不使用虛構分數。')
    cards=[]
    for idx,item in enumerate(judgments[:5],1):
        if isinstance(item,str): title=item; claim=item; tier='insufficient'; years=''
        else:
            title=item.get('title') or item.get('domain') or f'重要結論 {idx}'
            claim=item.get('ruling') or item.get('plain_language_claim') or item.get('claim') or ''
            tier=item.get('consensus_tier','insufficient'); years=item.get('main_years') or item.get('activation_periods') or ''
        if isinstance(years,list): years='、'.join(map(str,years))
        label=TIER_LABEL.get(tier,tier)
        content=f'<b>{idx:02d}　{html.escape(str(title))}</b><br/>{html.escape(str(claim))}<br/><font color="#6B7785">{html.escape(label)}' + (f' · {html.escape(str(years))}' if years else '') + '</font>'
        cards.append([Card(Paragraph(content,st['metric']),doc.width,TIER_BG.get(tier,WHITE),True)])
    if cards:
        t=Table(cards,colWidths=[doc.width],hAlign='LEFT'); t.setStyle(TableStyle([('BOTTOMPADDING',(0,0),(-1,-1),3*mm)])); story.append(t)
    else: story.append(Card(p('本次資料沒有 consequential_judgments；Dashboard 不補寫推測。',st['body']),doc.width,AMBER_SOFT))
    story.append(PageBreak())

    story += section_title(st,'METHOD MAP','四派在本次報告中的角色','同一套盤，各派回答的問題不同；缺資料時會直接降級。')
    manifest=packet.get('school_role_manifest',[]); by_school={x.get('school'):x for x in manifest if isinstance(x,dict)}
    method_rows=[]
    for school in ('western','ziwei','vedic','bazi'):
        item=by_school.get(school,{})
        role=item.get('role_in_run') or '本次未提供角色說明'
        qualified='、'.join(item.get('qualified_questions',[])[:4]) or '未列明'
        downgraded='、'.join(item.get('downgraded_modules',[])[:3]) or '無'
        body=f'<b>{SCHOOL_LABEL[school]}</b><br/>{html.escape(str(role))}<br/><font color="#6B7785">可回答：{html.escape(qualified)}<br/>降級：{html.escape(downgraded)}</font>'
        method_rows.append(Card(Paragraph(body,st['body']),doc.width/2-3*mm,WHITE,school in ('western','vedic')))
    grid=Table([[method_rows[0],method_rows[1]],[method_rows[2],method_rows[3]]],colWidths=[doc.width/2]*2,hAlign='LEFT')
    grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),3*mm),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),4*mm)])); story.append(grid); story.append(PageBreak())

    story += section_title(st,'CONSENSUS MATRIX','四派共識矩陣','●支持　修＝修正　限＝限制　衝＝衝突　○不適用　?資料不足')
    rows=[[p('主題',st['tableHead'])]+[p(SCHOOL_LABEL[s],st['tableHead']) for s in ('western','ziwei','vedic','bazi')]+[p('裁決',st['tableHead'])]]
    for item in packet.get('consensus_matrix',[])[:10]:
        positions=item.get('school_positions',{})
        domain=item.get('domain')
        row=[p(DOMAIN_LABEL.get(domain,domain) or item.get('question') or item.get('claim_id'),st['table'])]
        for school in ('western','ziwei','vedic','bazi'):
            raw=positions.get(school,{})
            pos=raw.get('position') if isinstance(raw,dict) else raw
            row.append(p(POSITION_SYMBOL.get(pos,'?'),st['tableHead']))
        row.append(p(TIER_LABEL.get(item.get('consensus_tier'),item.get('consensus_tier')),st['table']))
        rows.append(row)
    if len(rows)==1: rows.append([p('尚無透明裁決資料',st['table'])]+[p('?',st['table']) for _ in range(5)])
    widths=[42*mm,21*mm,21*mm,21*mm,21*mm,doc.width-126*mm]
    matrix=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    matrix.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE_SOFT),('BACKGROUND',(0,1),(-1,-1),WHITE),('GRID',(0,0),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,1),(4,-1),'CENTER'),('LEFTPADDING',(0,0),(-1,-1),2*mm),('RIGHTPADDING',(0,0),(-1,-1),2*mm),('TOPPADDING',(0,0),(-1,-1),2.5*mm),('BOTTOMPADDING',(0,0),(-1,-1),2.5*mm)])); story.append(matrix); story.append(Spacer(1,5*mm))
    story.append(Card(p('共識強度表示四派對結構判斷的收斂程度；事件確定性另由時間層與現實觸發條件判斷。',st['small']),doc.width,BLUE_SOFT)); story.append(PageBreak())
    return story

def plain_front_pages(packet, scores, doc, st):
    story=[]
    story += section_title(st,'CONTENTS','目錄與閱讀路線','先讀結論和評分，再按人生領域進入深讀正文。')
    toc=TableOfContents(); toc.levelStyles=[ParagraphStyle('toc0',fontName='TC',fontSize=8.8,leading=13,textColor=SECOND,leftIndent=0,firstLineIndent=0,spaceBefore=0.6*mm)]
    story.extend([toc,PageBreak()])

    story += section_title(st,'DOMAIN SCOREBOARD','領域評分 Dashboard','分數是固定公式產生的閱讀索引，不是命中率、人格價值或事件機率。')
    rows=[]
    raw=(scores or {}).get('domains',[]) if isinstance(scores,dict) else []
    for item in raw:
        name=DOMAIN_LABEL.get(item.get('domain'),item.get('domain','未命名'))
        vals=[item.get('flow_score','—'),item.get('potential_score','—'),item.get('friction_score','—'),item.get('confidence_score','—')]
        body=f'<b>{html.escape(str(name))}</b><br/><font color="#6B7785">順勢 {vals[0]}　潛力 {vals[1]}　阻力 {vals[2]}　信心 {vals[3]}</font>'
        rows.append([Card(Paragraph(body,st['metric']),doc.width/2-3*mm,WHITE)])
    if rows:
        paired=[rows[i]+(rows[i+1] if i+1<len(rows) else ['']) for i in range(0,len(rows),2)]
        grid=Table(paired,colWidths=[doc.width/2]*2,hAlign='LEFT')
        grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),3*mm),('BOTTOMPADDING',(0,0),(-1,-1),4*mm)])); story.append(grid)
    else:
        story.append(Card(p('未提供經公式計算的 domain_scores.json；本頁不補造分數。',st['body']),doc.width,AMBER_SOFT))
    story.append(PageBreak())

    story += section_title(st,'TIME INDEX','時間索引','只列本次已有年度裁決；詳細成立條件與失效邊界見正文。')
    annual=(packet or {}).get('annual_rulings',[]) if isinstance(packet,dict) else []
    for item in annual[:6]:
        year=item.get('year','—'); theme=item.get('central_task') or item.get('theme') or item.get('ruling') or '未提供年度主題'
        details=[]
        for key in ('career','wealth','relationship','residence_mobility'):
            if item.get(key): details.append(str(item[key]))
        content=f'<b>{html.escape(str(year))}　{html.escape(str(theme))}</b>'
        if details: content+='<br/><font color="#6B7785">'+html.escape('｜'.join(details[:3]))+'</font>'
        story.extend([Card(Paragraph(content,st['metric']),doc.width,BLUE_SOFT,True),Spacer(1,3*mm)])
    if not annual: story.append(Card(p('本次沒有已裁決的年度資料；不以本命配置補寫流年。',st['body']),doc.width,AMBER_SOFT))
    story.extend([Spacer(1,3*mm),p('日期代表週期切換或主題增強，不代表當日必然發生單一事件。',st['small']),PageBreak()])
    return story

def parse_table(lines,i):
    rows=[]
    while i<len(lines) and lines[i].lstrip().startswith('|'):
        cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
        if not all(re.fullmatch(r':?-{3,}:?',x) for x in cells): rows.append(cells)
        i+=1
    return rows,i

def build(md, out, title, subject, packet=None, scores=None, design='plain-deep'):
    register_fonts(); st=styles(); out.parent.mkdir(parents=True,exist_ok=True)
    def page(c,doc):
        c.saveState(); c.setFillColor(BG); c.rect(0,0,W,H,0,1)
        if doc.page>1:
            c.setFont('TC',7.5); c.setFillColor(MUTED); c.drawString(18*mm,9*mm,title[:24]); c.drawRightString(W-18*mm,9*mm,str(doc.page))
        c.restoreState()
    doc=ReportDocTemplate(str(out),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=17*mm,title=title,author='4PIE')
    doc.addPageTemplates([PageTemplate('main',[Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='f')],onPage=page)])
    edition='Plain Deep Report' if design=='plain-deep' else 'Dashboard 深讀版'
    story=[Spacer(1,48*mm),Paragraph('4PIE',ParagraphStyle('k',parent=st['small'],alignment=TA_CENTER,textColor=BLUE,spaceAfter=6*mm)),Paragraph(rich(title),st['cover']),Spacer(1,6*mm),Paragraph(rich(subject),st['coverSub']),Spacer(1,5*mm),Paragraph('四派命運裁決 · '+edition,st['coverSub']),PageBreak()]
    story.extend(plain_front_pages(packet,scores,doc,st) if design=='plain-deep' else dashboard_pages(packet,doc,st))
    lines=md.splitlines(); i=0; seen_document_title=False; paragraph=[]
    def flush():
        nonlocal paragraph
        if paragraph:
            txt=' '.join(x.strip() for x in paragraph).strip()
            if txt: story.append(Paragraph(rich(txt),st['body']))
            paragraph=[]
    while i<len(lines):
        line=lines[i].rstrip()
        if not line.strip(): flush(); i+=1; continue
        if line.startswith('# '):
            flush(); name=line[2:].strip()
            if not seen_document_title:
                seen_document_title=True
            else:
                story.extend([PageBreak(),Spacer(1,2*mm),Paragraph(rich(name),st['h1'])])
            i+=1; continue
        if line.startswith('## '):
            flush(); name=line[3:].strip()
            story.extend([Spacer(1,2*mm),Paragraph(rich(name),st['h1'])]); i+=1; continue
        if line.startswith('### '):
            flush(); story.append(Paragraph(rich(line[4:]),st['h2'])); i+=1; continue
        if re.match(r'^\d+\.\s+',line):
            flush(); content=re.sub(r'^\d+\.\s+','',line); p=Paragraph(rich(content),st['lead']); story.extend([Card(p,doc.width,BLUE_SOFT,True),Spacer(1,3*mm)]); i+=1; continue
        if line.startswith('- ') or line.startswith('* '):
            flush(); story.append(Paragraph('• '+rich(line[2:]),st['bullet'])); i+=1; continue
        if line.lstrip().startswith('|') and i+1<len(lines):
            flush(); rows,i=parse_table(lines,i)
            if rows:
                n=max(len(r) for r in rows); data=[]
                for ri,row in enumerate(rows): data.append([Paragraph(rich(x),st['tableHead'] if ri==0 else st['table']) for x in row]+['']*(n-len(row)))
                t=Table(data,colWidths=[doc.width/n]*n,repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE_SOFT),('BACKGROUND',(0,1),(-1,-1),WHITE),('GRID',(0,0),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),2.5*mm),('RIGHTPADDING',(0,0),(-1,-1),2.5*mm),('TOPPADDING',(0,0),(-1,-1),2.3*mm),('BOTTOMPADDING',(0,0),(-1,-1),2.3*mm)])); story.extend([t,Spacer(1,3*mm)])
            continue
        if line.startswith('> '):
            flush(); story.extend([Card(Paragraph(rich(line[2:]),st['small']),doc.width,BLUE_SOFT),Spacer(1,3*mm)]); i+=1; continue
        if line.endswith('  '): paragraph.append(line[:-2]); flush()
        else: paragraph.append(line)
        i+=1
    flush(); doc.multiBuild(story)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('markdown',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--title',default='完整命運裁決報告'); ap.add_argument('--subject',default='四派合參'); ap.add_argument('--packet',type=Path); ap.add_argument('--scores',type=Path); ap.add_argument('--design',choices=('plain-deep','dashboard'),default='plain-deep')
    a=ap.parse_args(); packet=json.loads(a.packet.read_text(encoding='utf-8')) if a.packet else None; scores=json.loads(a.scores.read_text(encoding='utf-8')) if a.scores else None
    build(a.markdown.read_text(encoding='utf-8'),a.output,a.title,a.subject,packet,scores,a.design)
if __name__=='__main__': main()
