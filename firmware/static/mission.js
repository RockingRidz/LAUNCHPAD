/* Shared, dependency-free mission and flight calculations. */
(function(root){
 'use strict';
 const compass=degrees=>Number.isFinite(degrees)?['N','NE','E','SE','S','SW','W','NW'][Math.round(((degrees%360)+360)%360/45)%8]:'Unknown';
 function flightStep(s,dt){
  if(!s.running||s.finished||s.paused)return;
  if(!Number.isFinite(dt)||dt<=0)return;
  dt=Math.min(dt,.1);s.elapsed=(s.elapsed||0)+dt;
  const mass=s.dry+s.fuel,used=Math.min(s.fuel,1.4*s.throttle*dt),rad=s.angle*Math.PI/180;
  const thrust=used>0?780*s.throttle:0;
  s.fuel=Math.max(0,s.fuel-used);
  const ax=Math.sin(rad)*thrust/mass-.018*s.vx*Math.abs(s.vx)/mass;
  const az=Math.cos(rad)*thrust/mass-9.81-.018*s.vz*Math.abs(s.vz)/mass;
  s.vx+=ax*dt;s.vz+=az*dt;s.x+=s.vx*dt;s.height+=s.vz*dt;
  s.peak=Math.max(s.peak||0,s.height);s.speed=Math.hypot(s.vx,s.vz);s.acceleration=Math.hypot(ax,az);
  const target=s.target||1000;
  if(s.height>=target){s.finished=true;s.running=false;s.success=true;s.message='TARGET REACHED! Reset for another flight.';}
  else if(Math.abs(s.angle)>70){s.finished=true;s.running=false;s.message='Flight lost: excessive tilt. Reset to retry.';}
  else if(s.height<=0){s.height=0;s.vz=0;s.finished=true;s.running=false;s.message='Landed. Increase throttle or improve your trajectory, then reset.';}
 }
 const api={compass,flightStep};root.Mission=api;
 if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
