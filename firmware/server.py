"""LAUNCHPAD: local web app, cached public feeds and optional ISS pass alerts."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlsplit
import argparse, json, threading, time, math, logging

ROOT=Path(__file__).resolve().parent
LOG=logging.getLogger('launchpad')

def fetch_json(url):
    req=Request(url,headers={'User-Agent':'LAUNCHPAD/0.1 educational hardware project','Accept':'application/json'})
    with urlopen(req,timeout=12) as response:
        return json.load(response)

class Feed:
    def __init__(self,name,ttl,loader,cache):
        self.name=name; self.ttl=ttl; self.loader=loader; self.path=cache/(name+'.json')
        self.lock=threading.Lock(); self.data=None; self.updated=0; self.error=None; self.retry_at=0
        try:
            stored=json.loads(self.path.read_text()); self.data=stored['data']; self.updated=stored['updated']
        except (OSError,ValueError,KeyError): pass
    def update(self,now=None):
        now=time.time() if now is None else now
        if now<self.retry_at or now-self.updated<self.ttl: return
        try:
            data=self.loader()
            with self.lock: self.data=data; self.updated=now; self.error=None
            self.path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.path.with_suffix('.tmp'); tmp.write_text(json.dumps({'data':data,'updated':now})); tmp.replace(self.path)
        except Exception as exc:
            with self.lock: self.error=str(exc); self.retry_at=now+max(60,self.ttl)
            LOG.warning('%s unavailable: %s',self.name,exc)
    def snapshot(self):
        with self.lock:
            return {'data':self.data,'updated':self.updated,'stale':time.time()-self.updated>self.ttl*2,'error':self.error}

class Orbit:
    def __init__(self,config):
        self.config=config; self.ready=False; self.satellite=None; self.error='Not initialized'; self.next_reload=0
        self.events=[]; self.events_until=0
    def load(self):
        if time.time()<self.next_reload: return
        self.next_reload=time.time()+3600
        try:
            from skyfield.api import Loader, EarthSatellite, wgs84
            self.wgs84=wgs84; loader=Loader(str(ROOT/'cache'/'skyfield'))
            self.ts=loader.timescale(builtin=True)
            req=Request('https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE',headers={'User-Agent':'LAUNCHPAD/0.1'})
            with urlopen(req,timeout=12) as r: text=r.read().decode()
            lines=[x.strip() for x in text.splitlines() if x.strip()]
            first=next(x for x in lines if x.startswith('1 25544'))
            second=next(x for x in lines if x.startswith('2 25544'))
            self.satellite=EarthSatellite(first,second,'ISS',self.ts)
            self.ready=True; self.error=None; self.events_until=0
            # Ephemeris needed only for a visibility estimate. Tracking still works if unavailable.
            try: self.eph=loader('de421.bsp')
            except Exception: self.eph=None
        except Exception as exc: self.ready=False; self.error=str(exc)
    def snapshot(self):
        if not self.ready: return {'error':self.error,'passes':[]}
        t=self.ts.now(); age=abs(float(t-self.satellite.epoch))
        geo=self.wgs84.subpoint(self.satellite.at(t))
        result={'latitude':geo.latitude.degrees,'longitude':geo.longitude.degrees,'altitude_km':geo.elevation.km,'tle_age_days':round(age,2),'passes':[],'stale':age>7}
        lat=self.config.get('latitude'); lon=self.config.get('longitude')
        if lat is None or lon is None: result['location_required']=True; return result
        observer=self.wgs84.latlon(lat,lon)
        alt,az,distance=(self.satellite-observer).at(t).altaz()
        result.update(elevation=alt.degrees,azimuth=az.degrees,distance_km=distance.km)
        if time.time()>self.events_until:
            now=datetime.now(timezone.utc)
            times,events=self.satellite.find_events(observer,t,self.ts.from_datetime(now+timedelta(days=2)),altitude_degrees=10)
            passes=[]; current=None
            for ti,event in zip(times,events):
                timestamp=ti.utc_datetime().timestamp()
                if event==0: current={'rise':timestamp}
                elif event==1 and current is not None:
                    a,z,_=(self.satellite-observer).at(ti).altaz()
                    current.update(peak=timestamp,max_elevation=round(a.degrees,1),azimuth=round(z.degrees,1))
                    current['visible_estimate']=None
                    if self.eph is not None:
                        sunalt=(self.eph['earth']+observer).at(ti).observe(self.eph['sun']).apparent().altaz()[0].degrees
                        current['visible_estimate']=bool(self.satellite.at(ti).is_sunlit(self.eph) and sunalt<-6)
                elif event==2 and current is not None:
                    current['set']=timestamp
                    if 'peak' in current: passes.append(current)
                    current=None
            self.events=passes; self.events_until=time.time()+900
        result['passes']=[p for p in self.events if p['set']>time.time()][:8]
        return result

class Station:
    def __init__(self,config,demo=False):
        self.config=config; self.demo=demo; self.started=time.time(); self.stop=threading.Event(); self.orbit=Orbit(config)
        self.lock=threading.Lock(); self.orbit_data={'passes':[],'error':'Starting orbit service'}
        self.alerts=[]; self.notified=set(); self.buzzer=None; self.muted_until=0
        cache=ROOT/'cache'
        self.feeds={
          'iss':Feed('iss',15,lambda:fetch_json('https://api.wheretheiss.at/v1/satellites/25544'),cache),
          'launches':Feed('launches',1800,self.launches,cache),
          'weather':Feed('weather',900,self.weather,cache)}
        if config.get('buzzer_enabled') and not demo:
            try:
                from gpiozero import OutputDevice
                self.buzzer=OutputDevice(17,initial_value=False)
            except Exception as exc: LOG.warning('Buzzer disabled: %s',exc)
    def launches(self):
        raw=fetch_json('https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=8&mode=normal')
        return [{'id':x['id'],'name':x.get('name'),'net':x.get('net'),'status':(x.get('status') or {}).get('name'),
                 'mission':x.get('mission') or {},'rocket':((x.get('rocket') or {}).get('configuration') or {}).get('name'),
                 'pad':(x.get('pad') or {}).get('name'),'provider':(x.get('launch_service_provider') or {}).get('name')} for x in raw['results']]
    def weather(self):
        lat=self.config.get('latitude'); lon=self.config.get('longitude')
        if lat is None or lon is None: return {'location_required':True}
        query=urlencode({'latitude':lat,'longitude':lon,'current':'temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m','daily':'sunrise,sunset','forecast_days':2,'timezone':'auto'})
        return fetch_json('https://api.open-meteo.com/v1/forecast?'+query)
    def run_feed(self,feed):
        while not self.stop.is_set(): feed.update(); self.stop.wait(5)
    def run_orbit(self):
        while not self.stop.is_set():
            self.orbit.load()
            try:
                result=self.orbit.snapshot()
                with self.lock: self.orbit_data=result
                self.check_alerts(result)
            except Exception as exc:
                with self.lock: self.orbit_data={'passes':[],'error':str(exc)}
            self.stop.wait(5)
    def check_alerts(self,result,now=None):
        now=time.time() if now is None else now
        if result.get('stale') or result.get('error'): return
        for event in result.get('passes',[]):
            if self.config.get('visible_passes_only',False) and event.get('visible_estimate') is not True: continue
            key=event['rise']; seconds=key-now
            if 0<=seconds<=self.config.get('alert_seconds',120) and key not in self.notified:
                self.notified.add(key)
                with self.lock: self.alerts.append({'time':now,'text':'ISS pass starts soon (above 10 degrees). Check visibility and clouds.'}); self.alerts=self.alerts[-10:]
                hour=datetime.fromtimestamp(now).hour
                quiet=self.config.get('quiet_hours',[22,7]); is_quiet=(hour>=quiet[0] or hour<quiet[1]) if quiet[0]>quiet[1] else quiet[0]<=hour<quiet[1]
                if self.buzzer and not is_quiet and now>self.muted_until:
                    try:
                        for _ in range(3):
                            self.buzzer.on(); self.stop.wait(.12); self.buzzer.off(); self.stop.wait(.15)
                    finally: self.buzzer.off()
        self.notified={x for x in self.notified if x>now-86400}
    def start(self):
        if self.demo: return
        for feed in self.feeds.values(): threading.Thread(target=self.run_feed,args=(feed,),daemon=True).start()
        threading.Thread(target=self.run_orbit,daemon=True).start()
    def snapshot(self):
        if self.demo:
            now=time.time()
            launch={'id':'demo','name':'DEMO / Aurora test flight','net':datetime.fromtimestamp(self.started+3600,timezone.utc).isoformat(),'status':'Simulated schedule','rocket':'Aurora Mk I (fictional)','provider':'LAUNCHPAD demo','pad':'Demonstration pad','mission':{'name':'Educational payload','description':'Fictional demonstration data. No real launch is represented.'}}
            wrap=lambda d:{'data':d,'updated':now,'stale':False,'error':None}
            day=datetime.now().date().isoformat()
            passes=[{'rise':self.started+600+i*5700,'peak':self.started+780+i*5700,'set':self.started+960+i*5700,'max_elevation':58-i*8,'azimuth':45+i*90,'visible_estimate':i==0} for i in range(3)]
            return {'demo':True,'iss':wrap({'latitude':12.3,'longitude':76.5,'altitude':420}),'launches':wrap([launch]),'weather':wrap({'current':{'temperature_2m':26,'cloud_cover':35,'relative_humidity_2m':65,'wind_speed_10m':8},'daily':{'sunrise':[day+'T06:20'],'sunset':[day+'T18:05']}}),'orbit':{'passes':passes,'tle_age_days':0,'stale':False},'alerts':[]}
        with self.lock: orbit=dict(self.orbit_data); alerts=list(self.alerts)
        return {'demo':False,**{k:v.snapshot() for k,v in self.feeds.items()},'orbit':orbit,'alerts':alerts}
    def close(self):
        self.stop.set()
        if self.buzzer: self.buzzer.off(); self.buzzer.close()

def make_handler(station):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'static'),**kwargs)
        def do_GET(self):
            path=urlsplit(self.path).path
            if path=='/api/state':
                body=json.dumps(station.snapshot(),allow_nan=False).encode()
                self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
            elif path in ('/','/index.html','/app.js','/mission.js','/style.css'):
                super().do_GET()
            else: self.send_error(404)
        def do_POST(self):
            if self.path!='/api/mute': self.send_error(404); return
            # State-changing calls must originate on this local app, not a foreign page.
            origin=self.headers.get('Origin')
            if origin and urlsplit(origin).netloc!=self.headers.get('Host'): self.send_error(403); return
            station.muted_until=time.time()+3600
            self.send_response(204); self.end_headers()
        def log_message(self,*args): LOG.info(args[0],*args[1:])
    return Handler

def load_config(path):
    config=json.loads(path.read_text())
    for name,limit in [('latitude',90),('longitude',180)]:
        value=config.get(name)
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>limit): raise ValueError('Invalid '+name)
    if (config.get('latitude') is None)!=(config.get('longitude') is None): raise ValueError('Set both latitude and longitude')
    if not 0<=config.get('alert_seconds',120)<=900: raise ValueError('alert_seconds must be 0..900')
    quiet=config.get('quiet_hours',[22,7])
    if not isinstance(config.get('visible_passes_only',False),bool): raise ValueError('visible_passes_only must be true or false')
    if len(quiet)!=2 or any(not isinstance(x,int) or not 0<=x<24 for x in quiet): raise ValueError('Invalid quiet_hours')
    return config

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--demo',action='store_true'); parser.add_argument('--port',type=int,default=8080); parser.add_argument('--config',type=Path,default=ROOT/'config.json'); args=parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    config=load_config(args.config if args.config.exists() else ROOT/'config.example.json')
    station=Station(config,args.demo); station.start()
    http=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(station))
    print(f'LAUNCHPAD: http://127.0.0.1:{args.port}  demo={args.demo}',flush=True)
    try: http.serve_forever()
    except KeyboardInterrupt: pass
    finally: station.close(); http.server_close()
if __name__=='__main__': main()
