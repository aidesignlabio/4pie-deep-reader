"""Exact reusable visual primitives for the approved Plain Deep Report v1."""
import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

W,H=A4; MM=72/25.4
ROOT=Path(__file__).resolve().parents[1]
BG=colors.HexColor('#F7F4EE'); NAVY=colors.HexColor('#17324D'); BODY=colors.HexColor('#34414D'); MUTED=colors.HexColor('#71808D'); LINE=colors.HexColor('#D8E0E5')
BLUE=colors.HexColor('#6F93AE'); SOFT=colors.HexColor('#EAF1F5'); GREEN=colors.HexColor('#DDEBE8'); AMBER=colors.HexColor('#F3E6D2'); PURPLE=colors.HexColor('#E9E4EF'); WHITE=colors.white

def _font_path(bold=False):
    override=os.environ.get('FOURPIE_FONT_BOLD' if bold else 'FOURPIE_FONT_REGULAR')
    if override and Path(override).is_file(): return Path(override)
    names=['NotoSansTC-Variable.ttf','msjhbd.ttc','NotoSansTC-Bold.ttf','NotoSansCJKtc-Bold.otf'] if bold else ['NotoSansTC-Variable.ttf','msjh.ttc','NotoSansTC-Regular.ttf','NotoSansCJKtc-Regular.otf']
    roots=(ROOT/'assets'/'fonts',Path('C:/Windows/Fonts'),Path('/usr/share/fonts/opentype/noto'),Path('/usr/share/fonts/truetype/noto'),Path('/usr/local/share/fonts'),Path.home()/'.fonts')
    for root in roots:
        for name in names:
            candidate=root/name
            if candidate.is_file(): return candidate
    raise RuntimeError('Traditional Chinese font not found. Install Noto Sans CJK TC or set FOURPIE_FONT_REGULAR and FOURPIE_FONT_BOLD.')

def register_fonts():
    if 'TC' not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont('TC',str(_font_path(False))))
    if 'TCB' not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont('TCB',str(_font_path(True))))

register_fonts()
S={
 'h1':ParagraphStyle('h1',fontName='TCB',fontSize=29,leading=34,textColor=NAVY),
 'h2':ParagraphStyle('h2',fontName='TCB',fontSize=18,leading=23,textColor=NAVY),
 'h3':ParagraphStyle('h3',fontName='TCB',fontSize=11.5,leading=15,textColor=NAVY),
 'body':ParagraphStyle('body',fontName='TC',fontSize=9.2,leading=13.8,textColor=BODY),
 'small':ParagraphStyle('small',fontName='TC',fontSize=7.7,leading=11,textColor=MUTED),
 'center':ParagraphStyle('center',fontName='TC',fontSize=8.5,leading=12,textColor=BODY,alignment=TA_CENTER),
}

def para(c,text,x,y,w,h,style='body'):
    p=Paragraph(str(text or '—').replace('\n','<br/>'),S[style]); _,ph=p.wrap(w,h); p.drawOn(c,x,y+h-ph); return ph

def card(c,x,y,w,h,fill=WHITE,stroke=LINE,r=8,shadow=True):
    if shadow: c.setFillColor(colors.Color(.1,.2,.3,alpha=.06)); c.roundRect(x+1.2,y-1.5,w,h,r,0,1)
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(.5); c.roundRect(x,y,w,h,r,1,1)

def header(c,page,kicker,title,sub=''):
    c.setFillColor(BG); c.rect(0,0,W,H,0,1); para(c,kicker.upper(),18*MM,H-25*MM,80*MM,6*MM,'small'); para(c,title,18*MM,H-48*MM,W-36*MM,21*MM,'h1')
    if sub: para(c,sub,18*MM,H-57*MM,W-36*MM,8*MM,'small')
    c.setStrokeColor(LINE); c.line(18*MM,14*MM,W-18*MM,14*MM); para(c,'4PIE 深讀報告',18*MM,7*MM,60*MM,5*MM,'small'); para(c,f'{page:02d}',W-27*MM,7*MM,9*MM,5*MM,'small')

def end(c): c.showPage()

def cover(c,title,subject,thesis,generated):
    c.setFillColor(BG); c.rect(0,0,W,H,0,1); c.setFillColor(colors.HexColor('#DCE8EE')); c.setStrokeColor(colors.HexColor('#B7CBD7'))
    pts=[(0,110),(32,145),(61,120),(94,174),(130,128),(164,160),(210,112),(210,0),(0,0)]
    path=c.beginPath(); path.moveTo(pts[0][0]*MM,pts[0][1]*MM)
    for x,y in pts[1:]: path.lineTo(x*MM,y*MM)
    path.close(); c.drawPath(path,1,1); c.setStrokeColor(WHITE); c.setLineWidth(4); path=c.beginPath(); path.moveTo(105*MM,0); path.curveTo(95*MM,45*MM,126*MM,62*MM,105*MM,119*MM); c.drawPath(path)
    c.setFillColor(NAVY); c.setFont('TCB',38); c.drawString(18*MM,H-48*MM,'4PIE'); c.setFont('TCB',29); c.drawString(18*MM,H-70*MM,title)
    c.setFont('TC',10); c.setFillColor(BLUE); c.drawString(18*MM,H-80*MM,'PERSONAL STRATEGY REPORT'); para(c,thesis,18*MM,H-111*MM,125*MM,20*MM,'h3'); para(c,f'{subject}\n西洋占星 · 紫微斗數 · 吠陀占星 · 八字\n生成日期 {generated}',18*MM,31*MM,125*MM,25*MM,'small'); end(c)
