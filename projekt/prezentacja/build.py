"""SafeWall jury deck. Run with scripts/.pdf-venv/bin/python projekt/prezentacja/build.py.

Original models/images are placed unchanged. SVG logo paths remain PDF vectors.
The presentation uses local SF Rounded glyphs, with a small outline for headline weight.
"""
from pathlib import Path
import json
import math
import re
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.svgpath import SvgPath
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / 'SafeWall-prezentacja.pdf'
W, H = 1600, 900
BG, CARD, EDGE = '#000000', '#1B1C1E', '#303136'
WHITE, MUTED, DIM = '#F7FAFF', '#B8BDC8', '#888F9D'
BLUE, PURPLE, LILAC, GREEN = '#3898FF', '#7D67E9', '#B39AFB', '#74E082'
pdfmetrics.registerFont(TTFont('Rounded', '/System/Library/Fonts/SFNSRounded.ttf'))
pdfmetrics.registerFont(TTFont('Mono', '/System/Library/Fonts/SFNSMono.ttf'))
c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
c.setTitle('SafeWall. Bo za każdą historią stoi człowiek')
c.setAuthor('SafeWall')
c.setSubject('Prezentacja projektu dla jury hackathonu: prototyp, konstrukcja i rozwój')
c.setCreator('SafeWall / ReportLab')
checks = []
page_no = 0

def color(v):
    return HexColor(v)

def rect(x, y, w, h, fill=CARD, radius=28, stroke=None, sw=1):
    c.setFillColor(color(fill))
    if stroke:
        c.setStrokeColor(color(stroke)); c.setLineWidth(sw)
    c.roundRect(x, H-y-h, w, h, radius, fill=1, stroke=int(stroke is not None))

def clip_rect(x, y, w, h, radius=28):
    p = c.beginPath(); p.roundRect(x, H-y-h, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)

def text(s, x, y, size=28, fill=WHITE, bold=False, align='left', font='Rounded'):
    """Position by approximate cap-box top; baseline is y + .81 * size."""
    width = pdfmetrics.stringWidth(s, font, size)
    if align == 'center': x -= width/2
    elif align == 'right': x -= width
    checks.append({'page': page_no, 'text': s, 'x': round(x,1), 'y': y, 'width': round(width,1), 'height': size})
    c.saveState(); c.setFillColor(color(fill)); c.setStrokeColor(color(fill))
    t = c.beginText(x, H-y-size*.81); t.setFont(font, size)
    if bold:
        c.setLineWidth(size*.022); t.setTextRenderMode(2)
    t.textOut(s); c.drawText(t); c.restoreState()
    return width

def lines(s, x, y, size=56, fill=WHITE, bold=True, leading=None, align='left'):
    leading = leading or size*1.08
    for i, line in enumerate(s.split('\n')):
        text(line, x, y+i*leading, size, fill, bold, align)
    return y + len(s.split('\n'))*leading

def para(s, x, y, width, size=26, fill=MUTED, leading=None, bold=False):
    leading = leading or size*1.38
    rendered = []
    for segment in s.split('\n'):
        line = ''
        for word in segment.split():
            trial = (line+' '+word).strip()
            if pdfmetrics.stringWidth(trial, 'Rounded', size) > width and line:
                rendered.append(line); line = word
            else: line = trial
        rendered.append(line)
    for i,line in enumerate(rendered):
        text(line, x, y+i*leading, size, fill, bold)
    return y+len(rendered)*leading

def gradient(x, y, w, h, a=BLUE, b=PURPLE, radius=28):
    c.saveState(); clip_rect(x,y,w,h,radius)
    c.linearGradient(x,H-y,x+w,H-y-h,[color(a),color(b)],extend=True)
    c.restoreState()

def gradient_text(s, x, y, size=52, align='left'):
    width=pdfmetrics.stringWidth(s,'Rounded',size)
    if align=='center': x-=width/2
    c.saveState()
    t=c.beginText(x,H-y-size*.81);t.setFont('Rounded',size);t.setTextRenderMode(7)
    t.textOut(s);c.drawText(t)
    c.linearGradient(x,0,x+width,0,[color(BLUE),color(LILAC)],extend=True)
    c.restoreState()

def pill(s,x,y,fill='#242529',fg=WHITE,size=20,pad=18,h=42):
    w=pdfmetrics.stringWidth(s,'Rounded',size)+2*pad
    rect(x,y,w,h,fill,h/2)
    text(s,x+pad,y+(h-size)/2-1,size,fg,True)
    return w

def line(x1,y1,x2,y2,fill=EDGE,sw=1):
    c.setStrokeColor(color(fill));c.setLineWidth(sw);c.line(x1,H-y1,x2,H-y2)

def circle(x,y,r,fill,stroke=None,sw=1):
    c.setFillColor(color(fill))
    if stroke: c.setStrokeColor(color(stroke));c.setLineWidth(sw)
    c.circle(x,H-y,r,fill=1,stroke=int(stroke is not None))

def arrow(x1,y,x2,fill=DIM):
    line(x1,y,x2,y,fill,3)
    line(x2-9,y-7,x2,y,fill,3);line(x2-9,y+7,x2,y,fill,3)

def svg_path(d):
    """Parse exactly the M/H/V/A/Z commands used by the canonical brand SVG."""
    tok=re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)',d)
    i=0;x=y=0;sx=sy=0;p=c.beginPath()
    while i<len(tok):
        cmd=tok[i];i+=1
        if cmd=='M':
            x,y=map(float,tok[i:i+2]);i+=2;sx,sy=x,y;p.moveTo(x,y)
        elif cmd=='H': x=float(tok[i]);i+=1;p.lineTo(x,y)
        elif cmd=='V': y=float(tok[i]);i+=1;p.lineTo(x,y)
        elif cmd=='A':
            rx,ry,angle,large,sweep,nx,ny=map(float,tok[i:i+7]);i+=7
            assert angle==0 and rx==ry and large==0
            dx=(x-nx)/2;dy=(y-ny)/2
            k=math.sqrt(max(0,(rx*rx-dx*dx-dy*dy)/(dx*dx+dy*dy)))
            if large==sweep:k=-k
            cx=(x+nx)/2+k*dy;cy=(y+ny)/2-k*dx
            start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx)
            delta=(end-start)%(2*math.pi)
            if not sweep:delta-=2*math.pi
            count=max(1,math.ceil(abs(delta)/(math.pi/2)))
            for n in range(count):
                a=start+n*delta/count;b=a+delta/count
                v=4/3*math.tan((b-a)/4)
                p.curveTo(cx+rx*(math.cos(a)-v*math.sin(a)),cy+ry*(math.sin(a)+v*math.cos(a)),cx+rx*(math.cos(b)+v*math.sin(b)),cy+ry*(math.sin(b)-v*math.cos(b)),cx+rx*math.cos(b),cy+ry*math.sin(b))
            x,y=nx,ny
        elif cmd=='Z':p.close();x,y=sx,sy
        else:raise ValueError(cmd)
    return p

def logo(x,y,w=66):
    root=ET.parse(ROOT/'brand/svg/safewall-logo.svg').getroot()
    c.saveState();c.translate(x,H-y);c.scale(w/856,-w/856)
    for e in root.findall('{http://www.w3.org/2000/svg}path'):
        c.setFillColor(color(e.attrib['fill']));c.drawPath(svg_path(e.attrib['d']),fill=1,stroke=0)
    c.restoreState()

def image(path,x,y,w,h,radius=28,mode='cover'):
    path=ROOT/path
    iw,ih=Image.open(path).size
    factor=(max if mode=='cover' else min)(w/iw,h/ih)
    dw,dh=iw*factor,ih*factor
    c.saveState();clip_rect(x,y,w,h,radius)
    c.drawImage(str(path),x+(w-dw)/2,H-y-h+(h-dh)/2,dw,dh,mask='auto')
    c.restoreState()

def tor_icon(x,y,size=36,fg=LILAC):
    root=ET.parse(HERE/'reference/tor-onion-glyph.svg').getroot()
    _,_,vw,vh=map(float,root.attrib['viewBox'].split())
    drawing=Drawing(vw,vh)
    for e in root.iter('{http://www.w3.org/2000/svg}path'):
        drawing.add(SvgPath(e.attrib['d'],fillColor=color(fg),strokeColor=None,fillMode=0))
    scale=size/max(vw,vh)
    c.saveState();c.translate(x,H-y);c.scale(scale,-scale)
    renderPDF.draw(drawing,c,0,0)
    c.restoreState()

def link(label,url,x,y,size=18,fill=BLUE):
    w=text(label,x,y,size,fill,True)
    c.linkURL(url,(x,H-y-size*1.2,x+w,H-y+3),relative=0,thickness=0)

def icon(kind,x,y,size=50,fg=LILAC):
    # Original, simple vector diagrams for the presentation, not brand replacements.
    c.saveState();c.translate(x,H-y-size);s=size/50;c.scale(s,s)
    c.setStrokeColor(color(fg));c.setFillColor(color(fg));c.setLineWidth(2.3);c.setLineCap(1);c.setLineJoin(1)
    if kind=='phone':
        c.roundRect(13,2,25,46,6,fill=0,stroke=1);c.line(22,7,29,7);c.line(22,43,29,43)
    elif kind=='box':
        c.roundRect(4,9,42,31,8,fill=0,stroke=1);c.roundRect(17,25,16,7,2,fill=0,stroke=1);c.line(10,16,15,16)
    elif kind=='lte':
        for k in range(4):c.roundRect(5+k*11,5,6,8+k*9,2,stroke=0,fill=1)
    elif kind=='globe':
        c.circle(25,25,21,stroke=1,fill=0);c.ellipse(15,4,35,46,stroke=1,fill=0);c.line(4,25,46,25)
    elif kind=='check':
        p=c.beginPath();p.moveTo(10,25);p.lineTo(21,14);p.lineTo(40,36);c.drawPath(p)
    elif kind=='lock':
        c.roundRect(10,4,30,25,5,fill=0,stroke=1);c.arc(16,20,34,46,0,180);c.line(16,31,16,29);c.line(34,31,34,29);c.circle(25,17,2,fill=1,stroke=0)
    elif kind=='play':
        p=c.beginPath();p.moveTo(17,8);p.lineTo(40,25);p.lineTo(17,42);p.close();c.drawPath(p,fill=1,stroke=0)
    c.restoreState()

def start(section,blue=False,glow=True):
    global page_no
    page_no+=1
    c.bookmarkPage(f'p{page_no}');c.addOutlineEntry(section,f'p{page_no}',0,False)
    if blue:gradient(0,0,W,H,'#155CE2','#3929A2',0)
    else:
        rect(0,0,W,H,BG,0)
        if glow:
            c.saveState();clip_rect(0,0,W,H,0)
            c.radialGradient(1130,230,680,[color('#221440'),color('#0B0617'),color('#000000')],[0,.52,1],extend=True)
            c.restoreState()
    logo(64,42,65);text('SafeWall',147,41,29,WHITE,True)

def finish():c.showPage()

def label(s,x,y):text(s.upper(),x,y,18,LILAC,True)

# 01: introduction, with the centered hierarchy and overlapping panels of RainbowKit.
start('Idea')
gradient_text('SafeWall',800,123,48,'center')
lines('Ktoś powierzył ci\nswoją historię.',800,192,67,align='center',leading=73)
text('Teraz chcesz ją przekazać dalej i chronić osobę, która ci zaufała.',800,363,27,MUTED,False,'center')
for s,x in [('Dla dziennikarzy',374),('Dla aktywistów',643),('Dla organizacji',891)]:pill(s,x,414,size=20)
image('physical-design/visualization/assembled-preview-v04.png',553,465,640,360,32)
rect(140,528,444,256,CARD,30,EDGE)
label('Dlatego projektujemy SafeWall',174,558)
para('Są miejsca, w których dostęp do informacji ogranicza cenzura. Właśnie tam prywatność ma szczególne znaczenie.',174,600,375,24,WHITE,leading=31)
text('Sprzętowa brama prywatności',174,748,22,LILAC,True)
pill('Koncepcja obudowy',934,766,fill='#242529',size=19)
finish()

# 02: show the video immediately after the introduction.
start('Demonstracja wideo')
label('Film demonstracyjny',64,139)
lines('Zobacz, jak działa\nSafeWall.',64,181,64,leading=71)
text('Zeskanuj kod QR',1020,174,30,WHITE,True)
text('lub otwórz link',1020,225,23,MUTED)
link('youtube.com','https://youtube.com/',1020,271,25)
qr_size=210
qr=QrCodeWidget('https://youtube.com/',barLevel='M',barBorder=4)
qx0,qy0,qx1,qy1=qr.getBounds()
qr_drawing=Drawing(qr_size,qr_size,transform=[qr_size/(qx1-qx0),0,0,qr_size/(qy1-qy0),0,0])
qr_drawing.add(qr)
rect(1326,135,qr_size,qr_size,'#FFFFFF',16)
renderPDF.draw(qr_drawing,c,1326,H-135-qr_size)
c.linkURL('https://youtube.com/',(1326,H-345,1536,H-135),relative=0,thickness=0)
rect(64,358,1472,438,CARD,34,EDGE)
gradient(91,386,63,63,BLUE,PURPLE,22);icon('play',105,399,35,WHITE)
text('Obejrzyj film',178,399,31,WHITE,True)
c.linkURL('https://youtube.com/',(91,H-449,480,H-386),relative=0,thickness=0)
text('Podłączenie telefonu i test połączenia',1502,411,22,MUTED,False,'right')
stills=[('physical-design/visualization/exploded-preview-v04.png','01','Projekt i składanie'),
        ('physical-design/references/live-demo-v13/connection-02.0s.png','02','Podłączenie prototypu'),
        ('physical-design/references/live-demo-v13/tor-positive-07.0s.png','03','Wynik Tor Check')]
for i,(path,n,caption) in enumerate(stills):
    x=91+i*480
    image(path,x,481,453,232,22)
    text(n,x+3,741,21,LILAC,True)
    text(caption,x+49,738,26,WHITE,True)
finish()

# 03: the exact voiceover hook, contextualized as AirDrop discovery.
start('Potrzeba użytkownika')
label('Telefon może ujawniać swoją obecność',64,139)
lines('„iPhone (Piotrek)”.',64,197,70)
lines('Nietrudno się domyślić,\ndo kogo należy.',64,304,45,leading=54)
para('Z SafeWall możesz wyłączyć Wi-Fi, Bluetooth i łączność komórkową telefonu. Łączysz go przewodem z bramą, która ma własny modem LTE.',64,639,720,28)
rect(900,181,573,549,CARD,34,EDGE)
text('AirDrop',1186,218,34,WHITE,True,'center')
circle(1186,415,77,'#28223D')
circle(1186,415,64,'#32294D')
icon('phone',1154,383,64,LILAC)
text('iPhone (Piotrek)',1186,527,42,WHITE,True,'center')
text('Nazwa widoczna urządzeniom w pobliżu',1186,592,23,MUTED,False,'center')
finish()

# 04: technical mechanism, bounded protection claims.
start('Mechanizm')
lines('Kontrolę połączenia\nprzenosimy poza telefon.',64,136,60,leading=67)
para('Tor prowadzi ruch przez kilka przekaźników, utrudniając ustalenie, kto z kim się komunikuje.',64,298,1472,27,leading=32)
rect(400,356,800,264,'#110E1B',32,'#6853AD',2)
icon('box',428,377,36)
text('SafeWall',480,379,30,WHITE,True)
nodes=[(64,256,'phone','Telefon','Radia wyłączone'),
       (428,324,'lte','LTE','Własny modem'),
       (848,324,'tor','Tor','Klient Tor'),
       (1280,256,'globe','Internet','Usługi przez HTTPS')]
for x,w,kind,head,sub in nodes:
    rect(x,436,w,160,CARD,24,EDGE)
    if kind=='tor':
        tor_icon(x+24,452,36)
    else:
        icon(kind,x+24,452,36)
    text(head,x+24,502,31,WHITE,True)
    text(sub,x+24,552,20,MUTED)
for x1,x2 in [(338,382),(770,830),(1218,1262)]:
    arrow(x1,516,x2,LILAC)
pill('USB-C / Ethernet',82,618,size=19)
text('Brama łączy się z siecią Tor przez LTE.',428,638,23,MUTED)
text('Jeśli Tor przestanie działać, internet ma się odłączyć.',842,686,27,WHITE,True)
para('Brama ma blokować bezpośrednie wyjście do internetu po awarii Tora. Działanie tej blokady musimy jeszcze przetestować.',842,739,690,23)
finish()

# 05: proof of work, latest recorded demo, no invented full-system verification.
start('Obecny prototyp')
label('To nasz prototyp',64,139)
lines('Podłączasz przewód.\nNadal masz internet.',64,181,62,leading=69)
image('physical-design/references/live-demo-v13/tor-positive-07.0s.png',64,362,898,424,30)
rx=1030
label('Sprzęt',rx,366)
text('Raspberry Pi + PiTalk',rx,404,32,WHITE,True)
para('Raspberry Pi 4, modem Quectel EG25-G oraz telefon połączony przez adapter Ethernet.',rx,455,487,25)
line(rx,565,1536,565,EDGE)
label('Test połączenia',rx,596)
text('Sprawdzasz w przeglądarce',rx,635,31,WHITE,True)
para('Po podłączeniu przewodu i odświeżeniu strony Tor Check pojawia się pozytywny wynik.',rx,686,487,25)
finish()

# 06: existing, intentionally unbranded CAD/renders stay unchanged.
start('Projekt produktu')
label('Projekt obudowy',64,139)
lines('Z zewnątrz przypomina\nzwykły powerbank.',64,181,61,leading=68)
image('physical-design/visualization/exploded-preview-v04.png',64,351,869,449,30)
rx=999
for i,(num,heading,body) in enumerate([
    ('01','Obudowa i ekran','Obudowa z małym ekranem. Model wyświetlacza nie został jeszcze wybrany.'),
    ('02','Komputer i łączność','Moduł obliczeniowy, modem LTE i płytka łącząca podzespoły.'),
    ('03','Własne zasilanie','Akumulator w obudowie i mocowanie do telefonu. Zasilanie oraz mocowanie wymagają testów.')]):
    yy=362+i*147
    circle(rx+18,yy+20,19,'#29223F');text(num,rx+18,yy+8,18,LILAC,True,'center')
    text(heading,rx+55,yy+3,30,WHITE,True)
    para(body,rx+55,yy+48,475,23)
text('Model koncepcyjny. Projekt płytki i obudowy wymaga dalszych prac.',64,812,19,MUTED)
finish()

# 07: enclosure dimensions and battery runtime target.
start('Przenośność w liczbach')
lines('Kolejny krok:\nminiaturyzacja.',64,138,64,leading=71)
text('Projektowana obudowa pomieści elektronikę i własne zasilanie.',64,302,27,MUTED)
cards=[(64,'WYMIARY PROJEKTU','110 × 70 × 24','mm','Projektowane wymiary obudowy.\nDługość × szerokość × grubość.'),
       (818,'CEL PROJEKTOWY','2 godziny','pracy','Zakładany czas pracy na baterii.\nJeszcze niezmierzony.')]
for x,tag,big,unit,body in cards:
    rect(x,381,718,320,CARD,30,EDGE)
    label(tag,x+28,411)
    text(big,x+28,468,54 if len(big)>11 else 62,WHITE,True)
    text(unit,x+28,547,25,LILAC,True)
    para(body,x+28,600,662,24,leading=32)
finish()

# 08: blue RainbowKit section adapted into the close and roadmap.
start('Następny etap',blue=True,glow=False)
lines('SafeWall.\nBo za każdą historią stoi człowiek.',800,145,62,align='center',leading=73)
text('Kolejny krok: miniaturyzacja, testy bezpieczeństwa i próby z przyszłymi użytkownikami.',800,329,28,'#E4E7FF',False,'center')
for x,n,title,body in [
    (64,'TERAZ','Prototyp i projekt','Prototyp sprzętowy, projekt obudowy i nagranie testu Tor Check. Panel działa na danych demo.'),
    (566,'NASTĘPNIE','Testy bezpieczeństwa','Sprawdzimy DNS, IPv6 i zachowanie po awarii Tora. Podłączymy panel i filtry do urządzenia.'),
    (1068,'DOCELOWO','Wersja przenośna','Własna płytka, bateria i obudowa. Testy w terenie z dziennikarzami i organizacjami społecznymi.')]:
    rect(x,423,468,259,'#FAFBFF',30)
    text(n,x+28,452,18,'#6651CD',True)
    text(title,x+28,497,33,'#17171C',True)
    para(body,x+28,553,412,24,'#4E5362',leading=32)
rect(1133,721,403,68,'#FFFFFF',34)
text('Kod i dokumentacja',1334,742,27,'#343AAE',True,'center')
c.linkURL('https://github.com/Mikformatycy/SafeWall',(1133,H-789,1536,H-721),relative=0,thickness=0)
finish()

c.save()
(HERE/'layout-check.json').write_text(json.dumps({'size':[W,H],'pages':page_no,'text':checks},ensure_ascii=False,indent=2))
assert page_no==8
print(OUT)
print(f'{page_no} pages, {OUT.stat().st_size/1024/1024:.2f} MiB')
