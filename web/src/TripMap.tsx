import {useEffect,useMemo,useRef,useState} from 'react';
import * as L from 'leaflet';
import {ArrowUpRight,Clock3,ExternalLink,FileText,LocateFixed,MapPin,RefreshCw,Route,Utensils} from 'lucide-react';
import type {Activity,Day,Plan,Source} from './types';
import {platformLabel,statusLabel} from './types';
import {safeUrl} from './lib';
import {demoLocationFor} from './demo-locations';
import {diningAreaFor,type DiningArea} from './dining-areas';
import 'leaflet/dist/leaflet.css';
import './trip-map.css';

type Props={day:Day;destination:string;sources:Source[];mode:Plan['mode'];selectedActivityId:string|null;onSelect:(id:string)=>void;onOpenSources:(ids:string[])=>void};
type TileStatus='loading'|'ready'|'partial'|'error';
type LocatedActivity={activity:Activity;index:number;point:L.LatLngTuple;diningArea?:DiningArea};

function coordinates(activity:Activity):L.LatLngTuple|null{
 const {lat,lng}=activity;
 return typeof lat==='number'&&typeof lng==='number'&&Number.isFinite(lat)&&Number.isFinite(lng)&&Math.abs(lat)<=85&&Math.abs(lng)<=180?[lat,lng]:null;
}
function sourceState(source:Source){
 if(source.id.startsWith('import-'))return '手动提供 · 未核对原文';
 if(source.platform==='sample'||source.content_status==='sample')return '演示资料 · 非实时检索';
 return statusLabel[source.content_status]||'内容待核对';
}

export default function TripMap({day,destination,sources,mode,selectedActivityId,onSelect,onOpenSources}:Props){
 const hostRef=useRef<HTMLDivElement>(null);
 const mapRef=useRef<L.Map|null>(null);
 const tileRef=useRef<L.TileLayer|null>(null);
 const layersRef=useRef<L.LayerGroup|null>(null);
 const markerRefs=useRef(new Map<string,L.Marker>());
 const detailRef=useRef<HTMLElement>(null);
 const activitiesRef=useRef(day.activities);
 const sourcesRef=useRef(sources);
 const diningAreasRef=useRef(new Map<string,DiningArea>());
 const previousSelectionRef=useRef<{date:string;id:string|null}|null>(null);
 const selectRef=useRef(onSelect);
 selectRef.current=onSelect;
 activitiesRef.current=day.activities;
 sourcesRef.current=sources;
 const [tileStatus,setTileStatus]=useState<TileStatus>('loading');
 const [mapError,setMapError]=useState(false);
 const retryRef=useRef<()=>void>(()=>{});
 const reducedMotion=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const located=useMemo<LocatedActivity[]>(()=>day.activities.flatMap((activity,index)=>{
  const exactPoint=coordinates(activity);
  const diningArea=exactPoint?undefined:diningAreaFor(activity,mode,destination);
  const point:L.LatLngTuple|null=exactPoint||(diningArea?[diningArea.lat,diningArea.lng]:null);
  return point?[{activity,index,point,diningArea}]:[];
 }),[day.activities,mode,destination]);
 diningAreasRef.current=new Map(located.flatMap(item=>item.diningArea?[[item.activity.id,item.diningArea] as const]:[]));
 const areaCount=located.filter(item=>item.diningArea).length;
 const geometryKey=JSON.stringify(located.map(item=>[item.activity.id,item.activity.title,item.index,item.point,item.diningArea?.name]));
 const selected=day.activities.find(a=>a.id===selectedActivityId)||day.activities[0]||null;
 const selectedIndex=selected?day.activities.findIndex(a=>a.id===selected.id):-1;
 const selectedLocation=selected?demoLocationFor(selected,mode):undefined;
 const selectedDiningArea=selected?diningAreasRef.current.get(selected.id):undefined;
 const selectedSources=selected?sources.filter(source=>selected.source_ids.includes(source.id)):[];
 const unresolvedSources=selected?new Set(selected.source_ids.filter(id=>!sources.some(source=>source.id===id))).size:0;

 function fitPlaces(){
  const map=mapRef.current;if(!map||!located.length)return;
  const bounds=L.latLngBounds(located.map(item=>item.point));
  map.fitBounds(bounds,{padding:[42,42],maxZoom:15,animate:!reducedMotion()});
 }

 function popupContent(activityId:string){
  const activity=activitiesRef.current.find(item=>item.id===activityId);
  const content=document.createElement('div');content.className='trip-map-popup-content';
  if(!activity){content.textContent='这个地点已不在当前行程中。';return content;}
  content.setAttribute('role','group');content.setAttribute('aria-label',activity.title+'的地图信息');
  const title=document.createElement('strong');title.className='trip-map-popup-title';title.textContent=activity.title;content.append(title);
  const time=document.createElement('p');time.className='trip-map-popup-time';time.textContent=activity.time+'–'+activity.end_time;content.append(time);
  const diningArea=diningAreasRef.current.get(activityId);
  if(diningArea){
   const area=document.createElement('p');area.className='trip-map-popup-area';area.textContent=diningArea.name+' · 建议用餐区域';content.append(area);
   const hint=document.createElement('p');hint.className='trip-map-popup-area-note';hint.textContent='虚线圈为区域示意，具体餐馆待选择。';content.append(hint);
  }
  const references=sourcesRef.current.filter(source=>activity.source_ids.includes(source.id));
  const label=document.createElement('span');label.className='trip-map-popup-label';label.textContent=references.length?'引用资料':'暂未关联来源';content.append(label);
  references.slice(0,2).forEach(source=>{
   const row=document.createElement('p');row.className='trip-map-popup-source';
   const platform=document.createElement('span');platform.textContent=(platformLabel[source.platform]||'资料')+(source.platform==='sample'||source.content_status==='sample'?' · 演示':source.id.startsWith('import-')?' · 手动提供':'');
   const sourceTitle=document.createElement('span');sourceTitle.textContent=source.title;
   row.append(platform,sourceTitle);content.append(row);
  });
  const button=document.createElement('button');button.type='button';button.className='trip-map-popup-detail-button';button.textContent='查看地点与来源 →';
  button.addEventListener('click',()=>{detailRef.current?.scrollIntoView({behavior:reducedMotion()?'auto':'smooth',block:'start'});detailRef.current?.focus({preventScroll:true});});
  content.append(button);return content;
 }

 useEffect(()=>{
  if(!hostRef.current)return;
  let disposed=false;
  let timer:number|undefined;
  let batchSuccesses=0,batchErrors=0,totalSuccesses=0;
  const status=(value:TileStatus)=>{if(!disposed)setTileStatus(value);};
  let map:L.Map;
  try{
   map=L.map(hostRef.current,{center:located[0]?.point||[25,15],zoom:located.length?14:2,minZoom:2,maxZoom:19,scrollWheelZoom:false,keyboard:true,zoomControl:false,attributionControl:true,zoomAnimation:!reducedMotion(),fadeAnimation:!reducedMotion()});
  }catch{setMapError(true);return;}
  mapRef.current=map;
  L.control.zoom({zoomInTitle:'放大地图',zoomOutTitle:'缩小地图'}).addTo(map);
  map.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank" rel="noreferrer">Leaflet</a>');
  const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
   attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
   maxZoom:19,minZoom:2,updateWhenIdle:true,updateWhenZooming:false,keepBuffer:0,
  });
  tileRef.current=tiles;
  const startTimer=()=>{window.clearTimeout(timer);timer=window.setTimeout(()=>{if(!disposed&&batchSuccesses===0)status(totalSuccesses?'partial':'error');},14000);};
  const loading=()=>{batchSuccesses=0;batchErrors=0;status(totalSuccesses?'ready':'loading');startTimer();};
  const loadedTile=()=>{batchSuccesses++;totalSuccesses++;window.clearTimeout(timer);status(batchErrors?'partial':'ready');};
  const failedTile=()=>{batchErrors++;status(totalSuccesses?'partial':'error');};
  const loaded=()=>{window.clearTimeout(timer);status(batchErrors?(totalSuccesses?'partial':'error'):(totalSuccesses?'ready':'error'));};
  tiles.on('loading',loading).on('tileload',loadedTile).on('tileerror',failedTile).on('load',loaded);
  tiles.addTo(map);
  layersRef.current=L.layerGroup().addTo(map);
  retryRef.current=()=>{batchSuccesses=0;batchErrors=0;status('loading');startTimer();tiles.redraw();};
  const observer=new ResizeObserver(()=>{if(!disposed)map.invalidateSize({pan:false});});
  observer.observe(hostRef.current);
  return()=>{
   disposed=true;window.clearTimeout(timer);observer.disconnect();
   tiles.off('loading',loading).off('tileload',loadedTile).off('tileerror',failedTile).off('load',loaded);
   markerRefs.current.clear();layersRef.current=null;tileRef.current=null;mapRef.current=null;retryRef.current=()=>{};
   map.remove();
  };
 },[]);

 useEffect(()=>{
  const map=mapRef.current,layers=layersRef.current;if(!map||!layers)return;
  layers.clearLayers();markerRefs.current.clear();
  // Area suggestions are separate from actual POI coordinates and clearly styled.
  located.forEach(item=>{
   if(item.diningArea)L.circle(item.point,{radius:item.diningArea.radius,color:'#b18743',weight:1.5,dashArray:'5 5',fillColor:'#e5bc69',fillOpacity:.15,interactive:false,className:'trip-map-dining-area'}).addTo(layers);
  });
  // Link displayed itinerary nodes in order, including labelled dining areas.
  let segment:L.LatLngTuple[]=[];
  const drawSegment=()=>{
   if(segment.length>1){
    L.polyline(segment,{color:'#416d57',weight:3,opacity:.8,dashArray:'6 9',interactive:false}).addTo(layers);
    for(let index=1;index<segment.length;index++){
     // Web Mercator is linear under zoom and pan, so the midpoint and heading
     // remain aligned with the Leaflet segment without attaching map listeners.
     const start=map.project(segment[index-1],0),end=map.project(segment[index],0);
     const dx=end.x-start.x,dy=end.y-start.y;
     if(Math.hypot(dx,dy)<1e-8)continue;
     const midpoint=map.unproject(L.point((start.x+end.x)/2,(start.y+end.y)/2),0);
     const arrow=document.createElement('span');arrow.className='trip-map-direction-arrow';arrow.style.transform=`rotate(${Math.atan2(dy,dx)*180/Math.PI}deg)`;
     const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');
     const shape=document.createElementNS('http://www.w3.org/2000/svg','path');shape.setAttribute('d','M 3 3 L 21 12 L 3 21 L 7 12 Z');svg.append(shape);arrow.append(svg);
     const direction=L.marker(midpoint,{icon:L.divIcon({className:'trip-map-direction',html:arrow,iconSize:[24,24],iconAnchor:[12,12]}),interactive:false,keyboard:false,zIndexOffset:-1000}).addTo(layers);
     direction.getElement()?.setAttribute('aria-hidden','true');
    }
   }
   segment=[];
  };
  located.forEach(item=>segment.push(item.point));
  drawSegment();
  located.forEach(({activity,index,point,diningArea}:LocatedActivity)=>{
   const number=document.createElement('span');number.className='trip-map-marker-number';number.textContent=String(index+1);
   if(diningArea){
    const badge=document.createElement('span');badge.className='trip-map-meal-icon';badge.setAttribute('aria-hidden','true');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d','M4 3v5c0 3 6 3 6 0V3M7 3v18M20 3c-4 3-4 9 0 9V3Zm0 9v9');svg.append(path);badge.append(svg);number.append(badge);
    const label=document.createElement('span');label.className='trip-map-meal-label';label.textContent='用餐区域';number.append(label);
   }
   const marker=L.marker(point,{icon:L.divIcon({className:'trip-map-marker'+(diningArea?' is-dining-area':''),html:number,iconSize:[36,36],iconAnchor:[18,18]}),keyboard:true,title:activity.title,alt:activity.title,riseOnHover:true}).addTo(layers);
   marker.bindPopup(()=>popupContent(activity.id),{className:'trip-map-popup',maxWidth:240,minWidth:180,offset:[0,-12],autoPanPadding:[18,25],closeButton:true});
   marker.on('click',()=>{selectRef.current(activity.id);marker.openPopup();});
   const element=marker.getElement();
   if(element){element.setAttribute('aria-label',`地图标记 ${index+1}：${activity.title}${diningArea?'，建议用餐区域':''}`);element.setAttribute('role','button');element.setAttribute('aria-pressed','false');element.addEventListener('keydown',event=>{if(event.key===' '){event.preventDefault();selectRef.current(activity.id);marker.openPopup();}});}
   markerRefs.current.set(activity.id,marker);
  });
  if(located.length)map.fitBounds(L.latLngBounds(located.map(item=>item.point)),{padding:[42,42],maxZoom:15,animate:false});
  else map.setView([25,15],2,{animate:false});
  // Keep nearby meal labels legible without changing the reference coordinates.
  const separateDiningLabels=()=>{
   located.filter(item=>item.diningArea).forEach(item=>{
    const marker=markerRefs.current.get(item.activity.id);if(!marker)return;
    const position=map.latLngToLayerPoint(item.point);
    const overlaps=located.some(other=>other.activity.id!==item.activity.id&&position.distanceTo(map.latLngToLayerPoint(other.point))<65);
    const element=marker.getElement();
    if(element){element.classList.toggle('is-offset-meal',overlaps);element.style.marginLeft=overlaps?'26px':'-18px';element.style.marginTop=overlaps?'-62px':'-18px';}
    const popup=marker.getPopup();if(popup){popup.options.offset=L.point(overlaps?44:0,overlaps?-56:-12);if(popup.isOpen())popup.update();}
   });
  };
  separateDiningLabels();map.on('zoomend',separateDiningLabels);
  return()=>{map.off('zoomend',separateDiningLabels);};
 },[day.date,geometryKey]);

 useEffect(()=>{
  if(selected&&selected.id!==selectedActivityId)selectRef.current(selected.id);
  markerRefs.current.forEach((marker,id)=>{
   const active=id===selected?.id;const element=marker.getElement();
   element?.classList.toggle('is-selected',active);element?.setAttribute('aria-pressed',String(active));marker.setZIndexOffset(active?1000:0);
  });
  const marker=selected?markerRefs.current.get(selected.id):undefined;
  if(marker&&mapRef.current)mapRef.current.panInside(marker.getLatLng(),{padding:[55,55],animate:!reducedMotion()});
  const previous=previousSelectionRef.current;
  if(previous&&previous.date===day.date&&previous.id!==selected?.id){
   if(marker)marker.openPopup();else mapRef.current?.closePopup();
  }
  previousSelectionRef.current={date:day.date,id:selected?.id||null};
 },[selected?.id,selectedActivityId,geometryKey,day.date]);

 return <section className="trip-map-panel" id="trip-map-panel" aria-label="当天行程地图与地点资料">
  <div className="trip-map-heading"><div><span className="trip-map-kicker">把日程放到地图上</span><h3><MapPin size={17}/>{destination}，走到哪里都清楚</h3></div><button className="trip-map-fit" onClick={fitPlaces} disabled={!located.length||mapError} title="缩放地图以显示当天全部已定位地点"><LocateFixed size={15}/>全部地点</button></div>
  <div className="trip-map-frame">
   <div className="trip-map-canvas" ref={hostRef} role="region" aria-label={`${destination}交互地图，使用方向键移动地图，使用加减按钮缩放`}/>
   {mapError&&<div className="trip-map-unavailable" role="status"><MapPin size={24}/><strong>地图暂时无法打开</strong><p>下方仍可选择地点，查看行程和资料。</p></div>}
   {!mapError&&tileStatus==='loading'&&<span className="trip-map-loading" role="status">正在加载地图底图…</span>}
   {!mapError&&!located.length&&<div className="trip-map-no-points"><MapPin size={20}/><strong>{day.activities.length?'这些地点还没有可靠位置':'这一天还没有安排地点'}</strong><p>{day.activities.length?'可先查看下方资料，核对位置后再标记。':'添加或恢复日程后，可在这里查看地图。'}</p></div>}
  </div>
  {!mapError&&(tileStatus==='error'||tileStatus==='partial')&&<div className="trip-map-network-note" role="status"><span>{tileStatus==='partial'?'部分地图底图未能加载。':'地图底图未能加载。'}{located.length?'标记仍按经纬度显示，可在下方查看资料。':'可在下方查看地点资料。'}</span><button onClick={()=>retryRef.current()}><RefreshCw size={13}/>重试底图</button></div>}
  <div className="trip-map-legend"><span><Route size={14}/>箭头表示游览顺序，非导航路线</span><span>{located.length}/{day.activities.length} 个行程节点</span></div>
  {!!areaCount&&<p className="trip-map-dining-legend"><Utensils size={13}/>{areaCount} 处建议用餐区域 · 虚线圈为示意，具体餐馆待选择</p>}
  {located.length<day.activities.length&&<p className="trip-map-position-note">还有 {day.activities.length-located.length} 个地点待定位；箭头仅串联已标记地点。</p>}
  {mode==='demo'&&<p className="trip-map-position-note">点位参考 OpenStreetMap，入口请核对；行程与攻略资料为演示。</p>}
  <div className="trip-map-stop-list" role="group" aria-label="选择地图地点">{day.activities.map((activity,index)=><button key={activity.id} className={'trip-map-stop '+(activity.id===selected?.id?'is-selected':'')} aria-pressed={activity.id===selected?.id} onClick={()=>onSelect(activity.id)}><span className="trip-map-stop-number">{index+1}</span><span>{activity.title}</span>{diningAreasRef.current.has(activity.id)?<small className="trip-map-area-tag">用餐区域</small>:!coordinates(activity)&&<small>待定位</small>}</button>)}</div>
  {selected?<article className="trip-map-detail" ref={detailRef} tabIndex={-1} data-testid="map-activity-detail" aria-label="所选地点信息与引用来源" aria-live="polite" aria-atomic="true">
   <div className="trip-map-detail-heading"><span className="trip-map-detail-number">{String(selectedIndex+1).padStart(2,'0')}</span><div><div className="trip-map-detail-time"><Clock3 size={12}/>{selected.time}–{selected.end_time}{selected.indoor&&<span>室内</span>}</div><h4>{selected.title}</h4></div></div>
   <p className="trip-map-description">{selected.description}</p>
   <div className="trip-map-detail-facts"><span>停留 {selected.duration_minutes} 分钟</span><span>{selected.cost>0?`参考费用 ¥${selected.cost.toLocaleString()}`:'费用待确认'}</span><span>{selectedDiningArea?'建议用餐区域':!coordinates(selected)?'位置待核查':mode==='demo'?'示例位置':'点位请核对实际入口'}</span></div>
   {selectedDiningArea&&<div className="trip-map-dining-detail"><strong><Utensils size={14}/>{selectedDiningArea.name} · 找一家喜欢的餐馆</strong><p>{selectedDiningArea.reason}</p><p>结合示例行程选择的用餐区域，虚线范围仅为示意；尚未检索具体商家、营业时间或步行路线。</p><a href={selectedDiningArea.source_url} target="_blank" rel="noopener noreferrer">查看区域参考位置<ExternalLink size={12}/></a></div>}
   {selectedLocation&&<div className="trip-map-location-source"><p>{selectedLocation.note}</p><a href={selectedLocation.source_url} target="_blank" rel="noopener noreferrer">查看 OpenStreetMap 点位<ExternalLink size={12}/></a></div>}
   <div className="trip-map-evidence-heading"><h5><FileText size={14}/>这个地点的资料来源</h5><span>{selectedSources.length} 条</span></div>
   {selectedSources.length?<div className="trip-map-evidence-list">{selectedSources.map(source=>{const url=safeUrl(source.url);return <section className="trip-map-evidence" key={source.id}><div className="trip-map-source-meta"><span className={'trip-map-platform '+source.platform}>{platformLabel[source.platform]||'资料'}</span><span>{sourceState(source)}</span></div><h6>{source.title}</h6><p>{source.excerpt||'当前没有可展示的正文或摘要，请打开来源核查。'}</p><div className="trip-map-source-actions"><button onClick={()=>onOpenSources([source.id])}>查看完整资料<ArrowUpRight size={13}/></button>{url?<a href={url} target="_blank" rel="noopener noreferrer">{source.platform==='sample'||source.content_status==='sample'?'文旅官网核查':source.id.startsWith('import-')?'查看提供的链接':'打开原文'}<ExternalLink size={12}/></a>:<span>暂无原文链接</span>}</div></section>;})}</div>:<div className="trip-map-no-evidence"><FileText size={18}/><p>这个地点暂未关联攻略来源。请先核查公开资料，再决定是否前往。</p></div>}
   {!!unresolvedSources&&<p className="trip-map-position-note">另有 {unresolvedSources} 条引用暂时缺少对应资料，尚无法查看。</p>}
  </article>:<div className="trip-map-empty-detail"><MapPin size={18}/><p>选择一个地点，就能查看对应的安排与攻略出处。</p></div>}
 </section>;
}
