'use strict';
let state=null,mode='iss',selected=0,lastAlert='',networkError='';
const view=document.querySelector('#view'),escapeHTML=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const e=escapeHTML, number=(n,d=1)=>Number.isFinite(n)?n.toFixed(d):'—';
const date=t=>t?new Date(t).toLocaleString(): 'Unscheduled';
const card=(title,value,unit='')=>`<section class="card"><h2>${e(title)}</h2><div class="value">${e(value)}<small>${e(unit)}</small></div></section>`;
function until(seconds){if(!Number.isFinite(seconds))return 'UNSCHEDULED';let s=Math.max(0,Math.floor(seconds));return `${Math.floor(s/86400)}d ${String(Math.floor(s/3600)%24).padStart(2,'0')}:${String(Math.floor(s/60)%60).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;}
function feedNote(name){let f=state?.[name];return !f?'Not loaded':f.error?`Unavailable: ${f.error}${f.data?' / showing cached data':''}`:f.stale?'STALE / cached data':`Updated ${f.updated?new Date(f.updated*1000).toLocaleTimeString():'never'}`;}
function launchData(){return Array.isArray(state?.launches?.data)?state.launches.data:[];}
function render(){
 if(mode==='sim'){if(!document.querySelector('#flight'))renderSim();return;}
 if(!state){view.innerHTML='<h1>Connecting…</h1><p>Waiting for the local station service.</p>';return;}
 if(mode==='iss'){
  const orbit=state.orbit||{}, data=state.iss?.data||{}, lat=orbit.latitude??data.latitude,lon=orbit.longitude??data.longitude,p=orbit.passes?.[0];
  view.innerHTML=`<span class="badge">ORBITAL TRACKING</span><h1>Where is the ISS?</h1><div class="map" aria-label="ISS latitude-longitude grid"><span id="dot">✦</span></div><p class="muted">Position grid, not a geographic basemap. ${e(feedNote('iss'))}</p><div class="grid">${card('LATITUDE',number(lat),'degrees')}${card('LONGITUDE',number(lon),'degrees')}${card('ALTITUDE',number(orbit.altitude_km??data.altitude),'km')}${card('ELEVATION',number(orbit.elevation),'degrees above local horizon')}</div><section class="card hero"><h2>NEXT PASS ABOVE 10°</h2><div class="countdown">${p?until(p.rise-Date.now()/1000):'—'}</div><p>${p?`${e(date(p.rise*1000))} · max ${e(p.max_elevation)}°`:'Set your observing coordinates in config.json to predict local passes.'}</p><p class="muted">${p?`Visibility at peak: ${p.visible_estimate===null?'unknown':p.visible_estimate?'potentially visible':'not predicted visible'}. Clouds can obstruct your view.`:e(orbit.error||'Pass predictions need fresh orbital elements.')} ${orbit.stale?'ORBITAL DATA STALE — alerts disabled.':''}</p></section>`;
  if(Number.isFinite(lat)&&Number.isFinite(lon)){let dot=document.querySelector('#dot');dot.style.left=((lon+180)/360*100)+'%';dot.style.top=((90-lat)/180*100)+'%';}
 }else if(mode==='launch'){
  let launches=launchData(); view.innerHTML=`<span class="badge">LAUNCH SCHEDULE</span><h1>Next off the pad.</h1><p class="muted">${e(feedNote('launches'))} · Times can change.</p><div class="list">${launches.map((l,i)=>`<button class="launch" data-launch="${i}"><span><strong>${e(l.name)}</strong><small>${e(l.status)} · ${e(l.pad)}</small><span class="muted">${e(date(l.net))}</span></span><span>${until((Date.parse(l.net)-Date.now())/1000)}</span></button>`).join('')||'<p>No launch schedule available. Try demo mode offline.</p>'}</div>`;
  view.querySelectorAll('[data-launch]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.launch);setMode('brief');});
 }else if(mode==='brief'){
  let launches=launchData();selected=Math.min(selected,Math.max(0,launches.length-1));let l=launches[selected];
  view.innerHTML=`<span class="badge">MISSION INTELLIGENCE</span><h1>Mission brief.</h1>${l?`<select id="mission" aria-label="Choose mission">${launches.map((x,i)=>`<option value="${i}" ${i===selected?'selected':''}>${e(x.name)}</option>`).join('')}</select><section class="card hero"><h2>${e(l.provider)}</h2><h1>${e(l.mission?.name||l.name)}</h1><p>${e(l.mission?.description||'Mission details have not been published.')}</p><p class="muted">ROCKET ${e(l.rocket)}<br>PAD ${e(l.pad)}<br>NET ${e(date(l.net))}<br>STATUS ${e(l.status)}</p></section>`:'<p>No mission details available.</p>'}`;
  let s=document.querySelector('#mission');if(s)s.onchange=()=>{selected=Number(s.value);render();};
 }else if(mode==='sky'){
  const w=state.weather?.data||{},c=w.current||{},d=w.daily||{};
  view.innerHTML=`<span class="badge">OBSERVING CONDITIONS</span><h1>Look up.</h1><p class="muted">${e(feedNote('weather'))}</p>${w.location_required?'<p>Set latitude and longitude in your private config.json.</p>':''}<div class="grid">${card('TEMPERATURE',number(c.temperature_2m),'°C')}${card('CLOUD COVER',number(c.cloud_cover,0),'%')}${card('HUMIDITY',number(c.relative_humidity_2m,0),'%')}${card('WIND',number(c.wind_speed_10m),'km/h')}</div><section class="card hero"><h2>SUNRISE / SUNSET</h2><p>${e(d.sunrise?.[0]||'—')}<br>${e(d.sunset?.[0]||'—')}</p><p class="muted">Weather is a forecast estimate. A nearby ISS pass is not automatically visible.</p></section>`;
 }
}
function setMode(next){mode=next;view.innerHTML='';document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));render();}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
document.querySelector('#mute').onclick=async()=>{try{let r=await fetch('/api/mute',{method:'POST'});if(!r.ok)throw Error(r.status);document.querySelector('#alert').textContent='Hardware buzzer muted for one hour';}catch{document.querySelector('#alert').textContent='Could not reach buzzer service';}};
async function update(){try{let r=await fetch('/api/state');if(!r.ok)throw Error(r.status);state=await r.json();networkError='';document.querySelector('#status').textContent=state.demo?'DEMO DATA / FICTIONAL LAUNCH / NO REAL ALERTS':'LIVE SERVICES / Cached data labelled per screen';let alert=state.alerts?.at(-1);if(alert&&String(alert.time)!==lastAlert){lastAlert=String(alert.time);document.querySelector('#alert').textContent=alert.text;}render();}catch(err){networkError=String(err);document.querySelector('#status').textContent='SERVICE DISCONNECTED / last values may be stale';}finally{setTimeout(update,5000);}}
setInterval(()=>{document.querySelector('#clock').textContent=new Date().toLocaleTimeString();if(mode==='iss'||mode==='launch')render();},1000);

// Deterministic fixed-step educational flight model; not an orbital simulator.
let sim,simClock=0,lastFrame=0,accumulator=0;
function resetFlight(){sim={height:0,vx:0,vz:0,x:0,angle:0,throttle:0.65,fuel:36,stage:1,dry:14,running:false,finished:false,message:'Target: reach 1,000 m. Set throttle, then ignite.'};}
function stepFlight(s,dt){
 if(!s.running||s.finished)return;
 const mass=s.dry+s.fuel,flow=1.4*s.throttle,used=Math.min(s.fuel,flow*dt),thrust=used>0?780*s.throttle:0,rad=s.angle*Math.PI/180;
 s.fuel=Math.max(0,s.fuel-used);const drag=.018;
 s.vx+=(Math.sin(rad)*thrust/mass-drag*s.vx*Math.abs(s.vx)/mass)*dt;
 s.vz+=(Math.cos(rad)*thrust/mass-9.81-drag*s.vz*Math.abs(s.vz)/mass)*dt;
 s.x+=s.vx*dt;s.height+=s.vz*dt;
 if(s.height>=1000){s.finished=true;s.running=false;s.message='TARGET REACHED! Reset for another flight.';}
 else if(Math.abs(s.angle)>70){s.finished=true;s.running=false;s.message='Flight lost: excessive tilt. Reset to retry.';}
 else if(s.height<=0){s.height=0;s.vz=0;s.finished=true;s.running=false;s.message='Landed. Increase throttle or improve your trajectory, then reset.';}
}
function renderSim(){
 if(!sim)resetFlight();
 view.innerHTML=`<span class="badge">OFFLINE / SIMPLIFIED PHYSICS</span><h1>Your turn to launch.</h1><div class="simlayout"><canvas id="flight" width="600" height="400" aria-label="Rocket flight visualization"></canvas><div><div class="grid"><section class="card">ALTITUDE<strong class="value" id="height"></strong></section><section class="card">FUEL<strong class="value" id="fuel"></strong></section></div><label for="throttle">THROTTLE <span id="throttleValue"></span></label><input id="throttle" type="range" min="0" max="100" value="${sim.throttle*100}"><div class="controls"><button id="left" aria-label="Tilt left">◀</button><button id="ignite">IGNITE</button><button id="right" aria-label="Tilt right">▶</button><button id="stage">STAGE</button><button id="reset">RESET</button></div></div></div><p id="simMessage"></p><p class="muted">Angle <span id="angle"></span>° · Stage <span id="stageNum"></span> · Earth gravity, variable mass and approximate drag. Staging discards 4 kg of dry mass once. No orbit or real rocket control.</p>`;
 document.querySelector('#throttle').oninput=ev=>sim.throttle=Number(ev.target.value)/100;
 document.querySelector('#left').onclick=()=>sim.angle=Math.max(-85,sim.angle-5);
 document.querySelector('#right').onclick=()=>sim.angle=Math.min(85,sim.angle+5);
 document.querySelector('#ignite').onclick=()=>{if(!sim.finished){sim.running=true;sim.message='Flight in progress.';}};
 document.querySelector('#stage').onclick=()=>{if(sim.running&&sim.stage===1){sim.stage=2;sim.dry-=4;sim.message='Stage separated. Dry mass reduced.';}};
 document.querySelector('#reset').onclick=()=>{resetFlight();renderSim();};
}
function frame(t){
 if(!lastFrame)lastFrame=t;accumulator+=Math.min((t-lastFrame)/1000,.1);lastFrame=t;
 while(accumulator>=1/60){if(mode==='sim'&&sim)stepFlight(sim,1/60);accumulator-=1/60;}
 if(mode==='sim'&&sim){let c=document.querySelector('#flight');if(c){let g=c.getContext('2d');g.clearRect(0,0,600,400);g.fillStyle='#0c202e';g.fillRect(0,0,600,400);g.strokeStyle='#244352';g.fillStyle='#8ba2b2';g.font='14px monospace';for(let i=0;i<=5;i++){let y=380-i*65;g.beginPath();g.moveTo(0,y);g.lineTo(600,y);g.stroke();g.fillText(`${i*200}m`,8,y-6);}let ry=380-Math.min(sim.height/1000,1)*325;g.save();g.translate(300+Math.max(-200,Math.min(200,sim.x/5)),ry);g.rotate(sim.angle*Math.PI/180);g.fillStyle='#e2edf0';g.beginPath();g.moveTo(0,-35);g.lineTo(13,0);g.lineTo(13,25);g.lineTo(-13,25);g.lineTo(-13,0);g.closePath();g.fill();g.fillStyle='#ff994c';if(sim.running&&sim.fuel>0){g.beginPath();g.moveTo(-8,25);g.lineTo(0,25+25*sim.throttle);g.lineTo(8,25);g.fill();}g.restore();document.querySelector('#height').textContent=number(sim.height,0)+'m';document.querySelector('#fuel').textContent=number(sim.fuel,1)+'kg';document.querySelector('#throttleValue').textContent=Math.round(sim.throttle*100)+'%';document.querySelector('#angle').textContent=sim.angle;document.querySelector('#stageNum').textContent=sim.stage;document.querySelector('#simMessage').textContent=sim.message;}}
 requestAnimationFrame(frame);
}
requestAnimationFrame(frame);update();
