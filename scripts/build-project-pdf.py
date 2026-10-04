from pathlib import Path
import os
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
P=Path(__file__).resolve().parent.parent
def font_path(variable, candidates):
 override=os.environ.get(variable)
 paths=[Path(override)] if override else [Path(p) for p in candidates]
 for path in paths:
  if path.is_file():return str(path)
 raise RuntimeError(f'Font unavailable; set {variable} to a TTF with Polish glyphs.')
pdfmetrics.registerFont(TTFont('Arial',font_path('SAFEWALL_FONT_REGULAR',[
 '/System/Library/Fonts/Supplemental/Arial.ttf',
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])))
pdfmetrics.registerFont(TTFont('Arial-Bold',font_path('SAFEWALL_FONT_BOLD',[
 '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'])))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
ink=HexColor('#172C40'); teal=HexColor('#087F8C')
brand_logo=svg2rlg(str(P/'brand/svg/safewall-logo.svg'))
def draw_brand(c,x,y,width):
 c.saveState();c.translate(x,y);c.scale(width/brand_logo.width,width/brand_logo.width)
 renderPDF.draw(brand_logo,c,0,0);c.restoreState()
styles={
 'title':ParagraphStyle('title',fontName='Arial-Bold',fontSize=33,leading=39,textColor=ink,spaceAfter=3),
 'sub':ParagraphStyle('sub',fontName='Arial',fontSize=14,leading=19,textColor=teal,spaceAfter=8),
 'meta':ParagraphStyle('meta',fontName='Arial',fontSize=8,leading=11,textColor=HexColor('#596779'),spaceAfter=15),
 'head':ParagraphStyle('head',fontName='Arial-Bold',fontSize=11,leading=15,textColor=ink,spaceBefore=11,spaceAfter=5,keepWithNext=True),
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,textColor=ink,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=8,leading=11,textColor=HexColor('#596779'),spaceAfter=4)}
class BrandTitle(Flowable):
 def __init__(self,title):Flowable.__init__(self);self.width=499;self.height=46;self.title=title
 def draw(self):
  draw_brand(self.canv,0,7,64)
  self.canv.setFillColor(ink);self.canv.setFont('Arial-Bold',33);self.canv.drawString(80,8,self.title)
class Diagram(Flowable):
 def __init__(self):Flowable.__init__(self);self.width=499;self.height=92
 def draw(self):
  c=self.canv
  labels=[('Telefon','radia wyłączone'),('Raspberry Pi','filtr + Tor + panel'),('Modem LTE','SIM i antena'),('Sieć Tor','opcjonalny most'),('Internet','usługi HTTPS')]
  w=91;gap=11
  for i,(a,b) in enumerate(labels):
   x=i*(w+gap);c.setFillColor(HexColor('#EAF3F5'));c.setStrokeColor(teal);c.roundRect(x,28,w,48,7,fill=1,stroke=0)
   c.setFillColor(ink);c.setFont('Arial-Bold',9);c.drawCentredString(x+w/2,57,a);c.setFont('Arial',7);c.drawCentredString(x+w/2,42,b)
   if i<4:
    c.setStrokeColor(teal);c.setLineWidth(1);c.line(x+w+1,52,x+w+gap-1,52);c.line(x+w+gap-4,55,x+w+gap-1,52);c.line(x+w+gap-4,49,x+w+gap-1,52)
  c.setFont('Arial',7.5);c.setFillColor(ink);c.drawString(0,13,'Telefon–Pi: USB-C / Ethernet     •     Pi–modem: USB     •     Tor: warstwa logiczna ruchu')
def footer(c,d):
 c.setStrokeColor(HexColor('#D8E3E9'));c.line(48,42,A4[0]-48,42)
 draw_brand(c,48,25,24)
 c.setFont('Arial',8);c.setFillColor(HexColor('#596779'));c.drawString(80,28,'SafeWall  /  Draft projektu  /  04.10.2026');c.drawRightString(A4[0]-48,28,str(d.page))
source=(P/'projekt/Draft-projektu.md').read_text()
flow=[];skip=False
for line in source.splitlines():
 if not line.strip():continue
 if line.startswith('<img '):continue
 if line=='---':flow.append(PageBreak());flow.append(Paragraph('SafeWall — plan rozwoju',styles['sub']));continue
 if line.startswith('# '):flow.append(BrandTitle(line[2:]));continue
 if line.startswith('## '):flow.append(Paragraph(escape(line[3:]),styles['sub']));continue
 if line.startswith('### '):
  flow.append(Paragraph(escape(line[4:]),styles['head']))
  if line=='### Schemat docelowy':flow.append(Diagram())
  continue
 if line.startswith('Telefon →'):continue
 style='meta' if line.startswith('Draft projektu') else 'body'
 if line.startswith('Dokumentacja Apple:'):style='small'
 flow.append(Paragraph(escape(line),styles[style]))
flow.append(Paragraph('Źródła: <link href="https://support.apple.com/en-gb/108785" color="#087F8C">Apple — tryb samolotowy</link> · <link href="https://support.torproject.org/tor-browser/security/using-tb-safely/" color="#087F8C">Tor — zasady ochrony</link> · <link href="https://support.torproject.org/tor-browser/circumvention/unblocking-tor/" color="#087F8C">Tor — mosty</link> · <link href="https://support.torproject.org/relays/legal-and-abuse/ddos/" color="#087F8C">Tor — UDP</link>',styles['small']))
doc=SimpleDocTemplate(str(P/'projekt/Draft-projektu.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=38,bottomMargin=56,title='SafeWall — draft projektu',author='SafeWall')
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(P/'projekt/Draft-projektu.pdf')
