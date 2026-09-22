"""Readable telemetry over a real physics capture; never edits the robot motion."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont


class HUD:
    def __init__(self,width,height,subtitle=None):
        self.width,self.height=width,height
        self.subtitle=subtitle or 'Learned CEM gait  /  IMU feedback  /  MuJoCo + BAM'
        self.speed=0.;self.tilt=0.;self.path=[]
        candidates=['/System/Library/Fonts/Supplemental/Arial.ttf',
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
        font=next((p for p in candidates if Path(p).exists()),None)
        self.font=ImageFont.truetype(font,20) if font else ImageFont.load_default()
        self.small=ImageFont.truetype(font,15) if font else ImageFont.load_default()
        self.title=ImageFont.truetype(font,26) if font else ImageFont.load_default()

    def draw(self,frame,t,command,velocity,tilt,qpos):
        image=Image.fromarray(frame).convert('RGBA')
        overlay=Image.new('RGBA',image.size);d=ImageDraw.Draw(overlay)
        w,h=image.size
        d.rectangle((0,0,w,87),fill=(12,23,29,235))
        d.text((26,15),'ARACHNE / 18',font=self.title,fill=(240,248,247))
        d.text((27,52),self.subtitle,font=self.small,fill=(151,183,185))
        vx,vy,wz=command
        if np.linalg.norm(command)<.005:label='STAND'
        elif abs(wz)>.08 and np.linalg.norm(command[:2])<.02:label='TURN LEFT' if wz>0 else 'TURN RIGHT'
        elif abs(wz)>.08:label='WALK + TURN'
        elif abs(vy)<.025:label='FORWARD' if vx>0 else 'BACKWARD'
        elif abs(vx)<.025:label='SIDEWAYS'
        else:label='DIAGONAL'
        box=(w-252,18,w-24,65)
        d.rounded_rectangle(box,8,fill=(45,115,105,255))
        d.text((w-234,30),label,font=self.font,fill='white')
        self.speed=.94*self.speed+.06*np.linalg.norm(velocity[:2])
        self.tilt=.94*self.tilt+.06*np.rad2deg(tilt)
        d.rectangle((0,h-66,w,h),fill=(12,23,29,232))
        d.text((26,h-53),f'{self.speed*100:4.1f} cm/s    Tilt {self.tilt:.2f} deg',font=self.font,fill=(236,246,243))
        d.text((26,h-26),f'Command  vx {vx:+.2f} m/s   vy {vy:+.2f} m/s   yaw {wz:+.2f} rad/s',font=self.small,fill=(151,183,185))
        d.text((w-113,h-48),f'{t:4.1f} s',font=self.font,fill=(236,246,243))
        return np.asarray(Image.alpha_composite(image,overlay).convert('RGB'))
