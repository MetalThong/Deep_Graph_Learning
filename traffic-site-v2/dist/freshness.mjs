// Data availability only. These labels are not calibrated prediction confidence.
export function ageLabel(minutes){
 if(minutes<0)return 'Chưa có quan sát trước đó';
 if(minutes===0)return 'Vừa được quan sát';
 const h=Math.floor(minutes/60),m=minutes%60;
 return `${h?`${h} giờ `:''}${m||!h?`${m} phút`:''}`.trim();
}
export function observationTime(timestamp,minutes){
 if(minutes<0)return null;
 const time=new Date(timestamp.replace(' ','T')+'Z');
 time.setUTCMinutes(time.getUTCMinutes()-minutes);
 return time.toISOString().slice(0,16).replace('T',' ');
}
export function assessFreshness(meta,data,origin,node){
 const n=meta.nodes.length,age=data.age[origin*n+node];
 let missing=0;for(let t=origin-11;t<=origin;t++)if(!data.mask[t*n+node])missing++;
 const neighbors=meta.rows[node].filter(([j])=>j!==node).map(([j])=>j);
 const staleNeighbors=neighbors.filter(j=>data.age[origin*n+j]>=60||data.age[origin*n+j]<0).length;
 const missingNeighbors=neighbors.filter(j=>!data.mask[origin*n+j]).length;
 const severity=age<0||age>=60?'critical':age>0||missing>0||staleNeighbors>0?'warning':'fresh';
 return {age,missing,staleNeighbors,missingNeighbors,neighbors:neighbors.length,severity,
   lastObserved:observationTime(meta.timestamps[origin],age)};
}
