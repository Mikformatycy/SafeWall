"""Native-speed edit: Seedance + Workbench + explanatory motion graphics + actual demo.

Run with the small preview-venv Python. Uses only existing media and drawn graphics.
"""
import array
import functools
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization/launch-preview-v18'
W,H,FPS=960,540,24
DURATION=79.75
N=round(DURATION*FPS)
INK=(16,23,33);WHITE=(235,240,247);MUTED=(153,170,190);PURPLE=(153,133,236);TEAL=(90,208,196)
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'


@functools.lru_cache(maxsize=32)
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)


def ease(x):
    x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))


def text(draw,xy,value,size=24,fill=WHITE,bold=False,anchor='la'):
    draw.text(xy,value,font=font(size,bold),fill=fill,anchor=anchor)


def background(t):
    # Small drifting highlight, so even explanatory holds retain subtle movement.
    yy,xx=np.mgrid[0:H,0:W]
    v=np.exp(-((xx-(470+60*math.sin(t*.19)))**2/300000+(yy-230)**2/120000))
    a=np.empty((H,W,3),dtype=np.uint8)
    for i,c in enumerate(INK):a[:,:,i]=c+v*(8+i*3)
    return Image.fromarray(a)


def phone(draw,x,y,scale=1,screen=None):
    w,h=74*scale,143*scale
    draw.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),radius=12*scale,fill=(31,43,58),outline=(176,188,205),width=2)
    draw.rounded_rectangle((x-w/2+6,y-h/2+7,x+w/2-6,y+h/2-7),radius=8*scale,fill=screen or (12,20,30))
    draw.rounded_rectangle((x-13*scale,y-h/2+10,x+13*scale,y-h/2+15),radius=3,fill=(75,87,103))
    draw.line((x-13,y+h/2-12,x+13,y+h/2-12),fill=(162,174,190),width=2)


def shield(draw,x,y,size=26,color=TEAL):
    pts=[(x-size*.7,y-size*.6),(x,y-size),(x+size*.7,y-size*.6),(x+size*.6,y+size*.4),(x,y+size),(x-size*.6,y+size*.4)]
    draw.polygon(pts,fill=(27,52,59));draw.line(pts+[pts[0]],fill=color,width=2)
    draw.line([(x-size*.35,y),(x-size*.05,y+size*.3),(x+size*.38,y-size*.3)],fill=color,width=3)


def moving_link(draw,a,b,t,color=TEAL,phase=0):
    draw.line([a,b],fill=(69,87,108),width=2)
    for n in range(3):
        u=(t*.35+n/3+phase)%1
        x=a[0]+(b[0]-a[0])*u;y=a[1]+(b[1]-a[1])*u
        draw.ellipse((x-3,y-3,x+3,y+3),fill=color)


def tor_graphic(t):
    im=background(t);d=ImageDraw.Draw(im)
    focus=ease((t-8.1)/1.0)
    title='Połączenie przez Tor' if focus<.5 else 'Kontrola połączenia poza telefonem'
    text(d,(62,45),title,34,bold=True)
    if focus<.5:text(d,(64,94),'Kilka przekaźników pomiędzy Tobą a internetem.',20,MUTED)
    else:text(d,(64,94),'Osobna brama pilnuje wybranej trasy.',20,MUTED)
    points=[(102,270),(280,270),(452,215),(590,328),(724,215),(866,270)]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        moving_link(d,a,b,t,TEAL,i*.12)
    phone(d,*points[0],.85)
    d.rounded_rectangle((240,205,320,335),radius=15,fill=(38,47,64),outline=PURPLE,width=3)
    d.rounded_rectangle((259,222,302,248),radius=5,fill=(14,23,33))
    text(d,(280,235),'87%',14,anchor='mm')
    shield(d,280,288,20)
    for i,(x,y) in enumerate(points[2:5],1):
        pulse=2*math.sin(t*2+i)
        d.ellipse((x-29-pulse,y-29-pulse,x+29+pulse,y+29+pulse),outline=PURPLE,width=2)
        text(d,(x,y),str(i),22,bold=True,anchor='mm')
    x,y=points[-1]
    d.rounded_rectangle((x-34,y-31,x+34,y+31),radius=8,fill=(33,48,59),outline=TEAL,width=2)
    for j in range(3):d.line((x-22,y-16+j*15,x+22,y-16+j*15),fill=(151,180,190),width=2)
    text(d,(102,365),'Telefon',18,MUTED,anchor='ma')
    text(d,(280,365),'SafeWall',19,bold=True,anchor='ma')
    text(d,(590,385),'Przekaźniki Tor',18,MUTED,anchor='ma')
    text(d,(864,365),'Internet',18,MUTED,anchor='ma')
    if t<12.8:
        text(d,(480,465),'Trudniej ustalić, kto z kim się komunikuje.',24,anchor='mm')
    else:
        a=ease((t-12.8)/.6)
        y=454+15*(1-a)
        d.rounded_rectangle((202,y-24,758,y+33),radius=15,fill=(35,48,63),outline=(82,102,124),width=1)
        text(d,(480,y+4),'Internet przez Tor albo brak połączenia',23,bold=True,anchor='mm')
    return im


def radios_graphic(t):
    im=background(t);d=ImageDraw.Draw(im)
    text(d,(62,45),'Telefon zdradza swoją obecność',33,bold=True)
    text(d,(64,94),'Przykład: widoczność w AirDrop przy odbieraniu od wszystkich.',18,MUTED)
    phone(d,260,300,1.6)
    off=ease((t-7.05)/1.0)
    for n in range(3):
        radius=65+((t*.5+n/3)%1)*160
        strength=(1-((t*.5+n/3)%1))*(1-off)
        color=tuple(int(INK[i]+(PURPLE[i]-INK[i])*strength*.8) for i in range(3))
        d.arc((260-radius,300-radius,260+radius,300+radius),-65,65,fill=color,width=2)
    arrive=ease(t/1.1)
    x=485+80*(1-arrive)
    d.rounded_rectangle((x,200,x+362,350),radius=20,fill=(38,49,66),outline=(91,112,139),width=2)
    text(d,(x+25,221),'W POBLIŻU',14,MUTED,bold=True)
    text(d,(x+25,258),'iPhone (Piotrek)',30,bold=True)
    text(d,(x+25,307),'AirDrop',18,PURPLE)
    labels=['Wi-Fi','Bluetooth','Sieć komórkowa']
    for i,label in enumerate(labels):
        cx=235+i*245
        d.rounded_rectangle((cx-89,427,cx+89,478),radius=12,fill=(35,45,58),outline=(73,94,117),width=1)
        text(d,(cx-10,452),label,18,MUTED if off>.5 else WHITE,anchor='mm')
        dot=(100,112,128) if off>.5 else TEAL
        d.ellipse((cx+64,446,cx+75,457),fill=dot)
    return im


@functools.lru_cache(maxsize=12)
def frame_image(kind,index):
    p=OUT/(kind+'-frames')/f'{index:04d}.png'
    return Image.open(p).convert('RGB')


def sampled(kind,t,total):
    index=max(1,min(total,int(round(t*FPS))+1))
    im=frame_image(kind,index).copy()
    if kind=='docking':
        # Minimal moving crop keeps the end of the magnetic catch alive during narration.
        z=1+.025*ease(t/4)
        im=im.resize((round(W*z),round(H*z)),Image.Resampling.BICUBIC)
        im=ImageOps.fit(im,(W,H))
    return im


def closing(t):
    im=background(t);d=ImageDraw.Draw(im)
    reveal=ease((t-5.2)/1.0)
    if reveal<1:
        text(d,(64,65),'To nasz prototyp.',38,bold=True)
        text(d,(66,121),'Kolejny krok',22,PURPLE)
        items=['Miniaturyzacja','Testy bezpieczeństwa','Próby z użytkownikami']
        for i,label in enumerate(items):
            progress=ease((t-i*1.5)/.65)
            if progress:
                y=211+i*78+12*(1-progress)
                d.ellipse((73,y+5,87,y+19),fill=TEAL)
                text(d,(110,y),label,27,tuple(int(c*progress) for c in WHITE),bold=i==1)
    if reveal>0:
        final=background(t);fd=ImageDraw.Draw(final)
        logo=Image.open(ROOT.parent/'brand/png/logo/safewall-logo-512.png').convert('RGBA')
        logo=ImageOps.contain(logo,(98,98))
        final.paste(logo,(round((W-logo.width)/2),117),logo)
        text(fd,(480,263),'SafeWall',57,bold=True,anchor='mm')
        text(fd,(480,345),'Bo za każdą historią stoi człowiek.',27,anchor='mm')
        im=Image.blend(im,final,reveal)
    return im


# Overlaps are explicit; the voice stays at its original speed and offset.
clips=[
    {'name':'seedance','start':0.,'end':15.5,'frames':372},
    {'name':'assembly','start':15.,'end':22.,'frames':168},
    {'name':'docking','start':21.75,'end':25.75,'frames':96},
    {'name':'tor','start':25.5,'end':48.25},
    {'name':'radios','start':48.,'end':56.25},
    {'name':'prototype','start':55.75,'end':60.5,'frames':114},
    {'name':'live','start':59.75,'end':68.75,'frames':215},
    {'name':'closing','start':68.5,'end':79.75},
]


def clip_image(c,t):
    local=t-c['start']
    if c['name']=='tor':return tor_graphic(local)
    if c['name']=='radios':return radios_graphic(local)
    if c['name']=='closing':return closing(local)
    return sampled(c['name'],local,c['frames'])


def render_at(t):
    active=[c for c in clips if c['start']<=t<c['end']]
    assert active,(t,'No visual at this time')
    a=clip_image(active[0],t)
    if len(active)==2:
        incoming=active[1]
        alpha=ease((t-incoming['start'])/(active[0]['end']-incoming['start']))
        a=Image.blend(a,clip_image(incoming,t),alpha)
    return a


if '--stills' in sys.argv:
    times=[15.25,16.3,18.5,21.1,23.7,28.5,39,46,52.7,56.6,58.5,60.25,63,66.5,70.8,77.3]
    sheet=Image.new('RGB',(960,4*158),(16,23,33));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=render_at(t);im.save(OUT/f'check-{t:05.2f}s.png')
        x=i%4*240;y=i//4*158;sheet.paste(im.resize((240,135)),(x,y));text(d,(x+8,y+137),f'{t:.2f}s',13)
    sheet.save(OUT/'edit-contact-sheet.png')
    print('V18_EDIT_STILLS_READY')
    raise SystemExit

for c in clips:
    if 'frames' in c:
        missing=[i for i in range(1,c['frames']+1) if not (OUT/(c['name']+'-frames')/f'{i:04d}.png').exists()]
        assert not missing,(c['name'],missing[:10])
video=OUT/'SafeWall-launch-preview-v18-picture.mp4'
command=['rtk','ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
with (OUT/'encode-picture.log').open('w') as log:
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
    for i in range(N):
        proc.stdin.write(render_at(i/FPS).tobytes())
        if i%240==0:print('V18_EDIT_PROGRESS',i,N,flush=True)
    proc.stdin.close()
    assert proc.wait()==0,'Picture encoding failed; see encode-picture.log'
(OUT/'edit-timeline.json').write_text(json.dumps({'fps':FPS,'resolution':[W,H],'duration':DURATION,'frames':N,'clips':clips,'voice':'../voiceover-v16/SafeWall-voiceover-pl-daniel-v16.wav','voice_offset':0,'native_speed_live_demo':True,'full_preview_only':True,'transition_method':'Framing-matched eased cross-dissolves; no optical-flow warping of actual Tor-check footage'},ensure_ascii=False,indent=2)+'\n')
print('V18_PICTURE_READY',video,flush=True)
