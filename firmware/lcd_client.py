"""Small portrait UI for Waveshare SKU16446 ST7789 revision + XPT2046.

No Linux desktop needed. Hardware bring-up and touch calibration remain mandatory.
HX8347D revisions need a different driver and are deliberately rejected.
"""
from pathlib import Path
import argparse,json,time,statistics
from flight import Flight
from urllib.request import urlopen
from PIL import Image, ImageDraw, ImageFont

class Display:
    def __init__(self):
        import spidev
        from gpiozero import OutputDevice,InputDevice
        self.dc=OutputDevice(25);self.reset=OutputDevice(27);self.bl=OutputDevice(18,initial_value=False)
        self.irq=InputDevice(24,pull_up=True)
        self.lcd=spidev.SpiDev();self.lcd.open(0,0);self.lcd.max_speed_hz=16000000;self.lcd.mode=0
        self.touch=spidev.SpiDev();self.touch.open(0,1);self.touch.max_speed_hz=1000000;self.touch.mode=0
        self.reset.off();time.sleep(.05);self.reset.on();time.sleep(.15)
        self.command(0x01);time.sleep(.15);self.command(0x11);time.sleep(.12)
        self.command(0x3A,[0x55]);self.command(0x36,[0x00])
        self.command(0x21);self.command(0x13);self.command(0x29);time.sleep(.05);self.bl.on()
    def command(self,cmd,data=None):
        self.dc.off();self.lcd.writebytes([cmd]);self.dc.on()
        if data:self.lcd.writebytes(data)
    def show(self,image):
        self.command(0x2A,[0,0,0,239]);self.command(0x2B,[0,0,1,63]);self.command(0x2C)
        # RGB565 big-endian, 240x320 full-frame writes; low refresh saves CPU/SPI bandwidth.
        data=bytearray()
        for r,g,b in image.convert('RGB').getdata():
            value=((r&0xF8)<<8)|((g&0xFC)<<3)|(b>>3);data.extend((value>>8,value&255))
        for i in range(0,len(data),4096):self.lcd.writebytes2(data[i:i+4096])
    def raw_touch(self):
        if not self.irq.is_active:return None
        def read(command):
            v=self.touch.xfer2([command,0,0]);return ((v[1]<<8)|v[2])>>3
        # Sample both axes; final transaction powers down ADC, restoring PENIRQ.
        x=int(statistics.median(read(0xD0) for _ in range(5)))
        y=int(statistics.median(read(0x90) for _ in range(5)))
        return x,y
    def close(self):
        self.bl.off();self.lcd.close();self.touch.close()
        for pin in (self.dc,self.reset,self.bl,self.irq):pin.close()

def fonts():
    path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try:return ImageFont.truetype(path,12),ImageFont.truetype(path,20)
    except OSError:return ImageFont.load_default(),ImageFont.load_default()

def calibrate(display,path):
    values=[];small,big=fonts()
    for x,y in [(20,30),(220,290)]:
        im=Image.new('RGB',(240,320),'#08131b');d=ImageDraw.Draw(im)
        d.text((35,145),'Tap the crosshair',font=small,fill='white')
        d.line((x-10,y,x+10,y),fill='orange',width=2);d.line((x,y-10,x,y+10),fill='orange',width=2);display.show(im)
        while display.raw_touch() is not None:time.sleep(.05)
        sample=None
        while sample is None:sample=display.raw_touch();time.sleep(.05)
        values.append(sample)
    # Two-point calibration assumes axes match; --swap-touch handles swapped hardware axes.
    if any(abs(values[1][axis]-values[0][axis])<300 for axis in (0,1)):raise ValueError('Calibration failed; retry')
    path.write_text(json.dumps({'raw':values}));print('Touch calibration saved:',path)

def touch_point(raw,cal,swap=False):
    if raw is None:return None
    x,y=raw
    if swap:x,y=y,x
    a,b=cal['raw']
    return round(20+(x-a[0])*200/(b[0]-a[0])),round(30+(y-a[1])*260/(b[1]-a[1]))

def main():
    p=argparse.ArgumentParser();p.add_argument('--driver',choices=['st7789'],default='st7789');p.add_argument('--calibrate',action='store_true');p.add_argument('--swap-touch',action='store_true');p.add_argument('--calibration',type=Path,default=Path(__file__).with_name('touch-calibration.json'));p.add_argument('--port',type=int,default=8080);args=p.parse_args()
    display=Display();small,big=fonts();mode=0;selected=0;last_fetch=0;state={};last_touch=0
    flight=Flight();last=time.monotonic();touch_held=False
    try:
        if args.calibrate:calibrate(display,args.calibration);return
        if not args.calibration.exists():raise RuntimeError('Run --calibrate first')
        cal=json.loads(args.calibration.read_text())
        if args.swap_touch:cal={'raw':[[y,x] for x,y in cal['raw']]}
        while True:
            now=time.monotonic();dt=min(now-last,.1);last=now
            if now-last_fetch>=5:
                try:
                    with urlopen(f'http://127.0.0.1:{args.port}/api/state',timeout=2) as response:state=json.load(response);state.pop('disconnected',None)
                except Exception:state['disconnected']=True
                last_fetch=now
            point=touch_point(display.raw_touch(),cal,args.swap_touch)
            if point and not touch_held and now-last_touch>.22:
                last_touch=now;x,y=point
                if y>280:mode=max(0,min(4,x//48))
                elif mode==4:
                    if 220<y<274:
                        if x<60:flight.angle=max(-85,flight.angle-5)
                        elif x<120:flight.toggle()
                        elif x<180:flight.angle=min(85,flight.angle+5)
                        else:flight=Flight(target=flight.target)
                    elif 170<y<210:flight.throttle=max(0,min(1,(x-10)/220))
                    elif 135<y<165:flight.separate()
                    elif 75<y<110 and not flight.running:flight=Flight(target={1000:2500,2500:5000,5000:1000}[flight.target])
                elif mode in (0,1,2):selected+=1
            touch_held=point is not None
            if mode==4:flight.step(dt)
            im=Image.new('RGB',(240,320),'#08131b');d=ImageDraw.Draw(im)
            def text(y,s,large=False,color='#dae7ed'):d.text((10,y),str(s)[:33],font=big if large else small,fill=color)
            text(5,'LAUNCHPAD',True,'#ff994c');text(32,'OFFLINE / LAST DATA' if state.get('disconnected') else 'DEMO DATA' if state.get('demo') else 'MISSION CONTROL',color='#abf078')
            labels=['ISS','LAUNCH','BRIEF','SKY','SIM'];text(55,labels[mode],True)
            feed_key=['iss','launches','launches','weather',None][mode]
            if not state.get('disconnected') and feed_key and (state.get(feed_key) or {}).get('stale'):text(32,'CACHED / STALE DATA',color='#ff994c')
            launch=(state.get('launches') or {}).get('data') or []
            if mode==0:
                pos=(state.get('iss') or {}).get('data') or {};orbit=state.get('orbit') or {};passes=orbit.get('passes') or []
                text(90,'LAT '+str(round(pos.get('latitude',0),2)) if pos else 'Position unavailable')
                text(115,'LON '+str(round(pos.get('longitude',0),2)) if pos else '')
                if passes:
                    event=passes[selected%len(passes)];text(150,'PASS IN '+str(max(0,int(event['rise']-time.time())))+'s',True);text(180,'Max elevation '+str(event.get('max_elevation')))
                else:text(150,'No predicted pass available')
                text(215,'Orbit stale' if orbit.get('stale') else 'Pass visibility is conditional');text(245,'Tap to browse '+str(len(passes))+' passes')
            elif mode in (1,2):
                if launch:
                    item=launch[selected%len(launch)];text(90,item.get('name'));text(115,item.get('status'));text(140,item.get('net'))
                    if mode==1:
                        try:seconds=int(datetime_seconds(item['net'])-time.time());text(175,str(max(0,seconds))+'s',True)
                        except (KeyError,ValueError):text(175,'Unscheduled')
                    else:
                        desc=(item.get('mission') or {}).get('description','No published brief')
                        import textwrap
                        for i,line in enumerate(textwrap.wrap(desc,30)[:5]):text(170+i*18,line)
                    text(260,'Tap to browse next launch')
                else:text(100,'Schedule unavailable')
            elif mode==3:
                weather=(state.get('weather') or {}).get('data') or {};c=weather.get('current') or {}
                for y,key,title,unit in [(90,'temperature_2m','Temp','C'),(125,'cloud_cover','Cloud','%'),(160,'relative_humidity_2m','Humidity','%'),(195,'wind_speed_10m','Wind','km/h')]:text(y,f'{title}: {c.get(key,"--")} {unit}')
                text(245,'Configure location for weather')
            else:
                text(79,f'Target {flight.target}m - tap to change');text(98,f'{flight.height:.0f}m  {flight.fuel:.1f}kg',True);text(122,f'{flight.velocity:.1f}m/s  {flight.elapsed:.1f}s  S{flight.stage}')
                d.rectangle((10,136,230,164),outline='#385061');text(141,'TAP HERE TO STAGE')
                d.rectangle((10,176,230,205),outline='#ff994c');d.rectangle((10,176,10+int(220*flight.throttle),205),fill='#344b39');text(181,f'Throttle {flight.throttle:.0%}')
                for i,label in enumerate(['LEFT','RESUME' if flight.paused else 'PAUSE' if flight.running else 'IGNITE','RIGHT','RESET']):d.rectangle((i*60,222,i*60+58,267),outline='#385061');d.text((i*60+4,238),label,font=small,fill='white')
                text(267,flight.message)
            for i,label in enumerate(labels):
                d.rectangle((i*48,283,i*48+46,319),fill='#abf078' if i==mode else '#142734');d.text((i*48+5,294),label,font=small,fill='black' if i==mode else 'white')
            display.show(im);time.sleep(.08)
    finally:display.close()

def datetime_seconds(value):
    from datetime import datetime
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
if __name__=='__main__':main()
