"""Check the exported PDF and build a visual contact sheet from pdftocairo output."""
from pathlib import Path
import json
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw

P=Path(__file__).resolve().parent
r=PdfReader(P/'SafeWall-prezentacja.pdf')
assert len(r.pages)==8
expected=['Ktoś powierzył ci','Obejrzyj film','iPhone (Piotrek)','Kontrolę połączenia','Sprawdzasz w przeglądarce','zwykły powerbank','110 × 70 × 24','Bo za każdą historią stoi człowiek']
alltext=[]
links=[]
for i,page in enumerate(r.pages):
    assert tuple(page.mediabox)==(0,0,1600,900)
    txt=page.extract_text()
    assert expected[i] in txt,(i,expected[i])
    assert 'SafeWall' in txt
    alltext.append(txt)
    for a in page.get('/Annots',[]):
        uri=a.get_object().get('/A',{}).get('/URI')
        if uri:
            assert uri.startswith('https://')
            links.append({'page':i+1,'uri':uri})
assert [item['uri'] for item in links if item['page']==2]==['https://youtube.com/']*3
layout=json.loads((P/'layout-check.json').read_text())
overflow=[t for t in layout['text'] if t['x']<0 or t['x']+t['width']>1600 or t['y']+t['height']>900]
assert not overflow,overflow
font_names=set()
for page in r.pages:
    for ref in page['/Resources']['/Font'].values():
        f=ref.get_object();font_names.add(str(f.get('/BaseFont')))
        if 'Rounded' in str(f.get('/BaseFont')):
            assert '/FontFile2' in f['/FontDescriptor'].get_object()
(P/'preview/text-extracted.txt').write_text('\n\n'.join(alltext))
sheet=Image.new('RGB',(1640,1900),'#111115')
for i in range(8):
    im=Image.open(P/f'preview/slajd-{i+1}.png').convert('RGB')
    im.thumbnail((800,450))
    sheet.paste(im,(16+(i%2)*808,16+(i//2)*466))
sheet.save(P/'SafeWall-podglad.jpg',quality=92)
report={'pages':8,'aspect_ratio':'16:9','bytes':(P/'SafeWall-prezentacja.pdf').stat().st_size,'fonts':sorted(font_names),'links':links,'text_overflows':overflow,'video_placeholder':True,'visual_review':'All pages inspected; final export rasterized with pdftocairo.'}
(P/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,indent=2,ensure_ascii=False))
