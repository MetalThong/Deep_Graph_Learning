import {forecastAll,forecastSensor} from './inference.mjs';
import {assessFreshness,ageLabel} from './freshness.mjs';
const $=id=>document.getElementById(id),f=v=>Number(v).toFixed(1).replace('.',','),label={persistence:'Giữ nguyên',gru:'GRU',gcn_gru:'GCN + GRU'};
let meta,data,models,report,origin,node=0,revealed=false,playing=null,predictions,elapsed;
async function json(p){const r=await fetch(p,{cache:'no-store'});if(!r.ok)throw Error(`Không tải được ${p}`);return r.json();}
async function binary(p,Type){const r=await fetch(p,{cache:'no-store'});if(!r.ok)throw Error(`Không tải được ${p}`);return new Type(await r.arrayBuffer());}
function observed(t,n){return !!data.mask[t*meta.nodes.length+n];}
function speed(t,n){return data.speed[t*meta.nodes.length+n]*meta.kmh;}
function current(t,n){return observed(t,n)?speed(t,n):null;}
function color(v){return v===null?'#91a1a0':v<30?'#df754f':v<60?'#dfb65c':'#38a895';}
function stop(){if(playing)clearInterval(playing);playing=null;$('play').textContent='▶ Phát lại';}
function project(n){return [35+(n.lon+118.58)/.39*490,315-(n.lat-34.015)/.24*280];}
function map(){
 const selected=new Set(meta.rows[node].map(r=>r[0])),pred=$('map-mode').value==='forecast';
 let s='<svg viewBox="0 0 560 345" role="img" aria-label="Graph cảm biến theo tọa độ địa lý"><text x="22" y="27" font-size="11" fill="#738f86">LOS ANGELES · SENSOR GRAPH</text><text x="525" y="28" font-size="11" fill="#738f86">N ↑</text>';
 for(const [a,b] of meta.edges){const [x,y]=project(meta.nodes[a]),[u,v]=project(meta.nodes[b]),active=a===node||b===node;s+=`<line x1="${x}" y1="${y}" x2="${u}" y2="${v}" stroke="${active?'#397a70':'#c8d7ce'}" stroke-width="${active?1.7:.65}" opacity="${active?1:.5}"/>`;}
 meta.nodes.forEach((n,i)=>{const [x,y]=project(n),v=pred?predictions.gcn_gru[i]*meta.kmh:current(origin,i);s+=`<circle data-node="${i}" cx="${x}" cy="${y}" r="${i===node?7:selected.has(i)?4:3}" fill="${color(v)}" stroke="${i===node?'#153c36':'white'}" stroke-width="${i===node?2:1}" tabindex="0" role="button" aria-label="Chọn cảm biến ${n.id}"><title>${n.id}: ${v===null?'thiếu dữ liệu':f(v)+' km/h'}</title></circle>`;});
 s+='</svg>';$('map').innerHTML=s;
 $('map').querySelectorAll('[data-node]').forEach(el=>{const select=()=>{node=+el.dataset.node;$('sensor').value=node;revealed=false;render(false);};el.onclick=select;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};});
}
function chart(){
 const x=t=>42+(t+11)/14*445,y=v=>186-v/130*160;
 let svg='<svg viewBox="0 0 510 225" role="img" aria-label="Tốc độ trong quá khứ và dự báo sau 15 phút">';
 for(let v=0;v<=120;v+=30)svg+=`<line x1="42" y1="${y(v)}" x2="490" y2="${y(v)}" stroke="#e3e9e3"/><text x="30" y="${y(v)+4}" text-anchor="end" font-size="10" fill="#7c8e87">${v}</text>`;
 svg+=`<text x="4" y="14" font-size="10" fill="#7c8e87">km/h</text><line x1="${x(0)}" y1="20" x2="${x(0)}" y2="190" stroke="#91a89f" stroke-dasharray="3 4"/><rect x="${x(0)+1}" y="20" width="${x(3)-x(0)}" height="168" fill="#e8f3ec" opacity=".5"/>`;
 let pts=[];for(let k=-11;k<=0;k++){const v=current(origin+k,node);if(v!==null){pts.push(`${x(k)},${y(v)}`);}else{if(pts.length)svg+=`<polyline points="${pts.join(' ')}" fill="none" stroke="#203f3c" stroke-width="2.4"/>`;pts=[];}}
 if(pts.length)svg+=`<polyline points="${pts.join(' ')}" fill="none" stroke="#203f3c" stroke-width="2.4"/>`;
 const now=speed(origin,node),styles={persistence:'#929e9a',gru:'#be7b2f',gcn_gru:'#087e73'};
 for(const key of ['persistence','gru','gcn_gru']){const val=predictions[key][node]*meta.kmh;svg+=`<line x1="${x(0)}" y1="${y(now)}" x2="${x(3)}" y2="${y(val)}" stroke="${styles[key]}" stroke-width="${key==='gcn_gru'?2.5:1.5}" stroke-dasharray="5 4"/><circle cx="${x(3)}" cy="${y(val)}" r="4" fill="${styles[key]}"/>`;}
 if(!observed(origin,node))svg+=`<circle cx="${x(0)}" cy="${y(now)}" r="5" fill="white" stroke="#be7b2f" stroke-width="2"><title>Giá trị điền từ quá khứ, không phải quan sát hiện tại</title></circle>`;
 if(revealed){let p=[];const flush=()=>{if(p.length)svg+=`<polyline points="${p.join(' ')}" fill="none" stroke="#203f3c" stroke-width="2.5"/>`;p=[];};for(let k=0;k<=3;k++){const v=current(origin+k,node);if(v!==null){p.push(`${x(k)},${y(v)}`);svg+=`<circle cx="${x(k)}" cy="${y(v)}" r="3" fill="#203f3c"/>`;}else flush();}flush();if(observed(origin+3,node))svg+=`<circle cx="${x(3)}" cy="${y(speed(origin+3,node))}" r="5" fill="#203f3c"/>`;}
 for(const [k,t] of [[-11,'−55 phút'],[-6,'−30'],[0,'Hiện tại'],[3,'+15']])svg+=`<text x="${x(k)}" y="211" text-anchor="middle" font-size="10" fill="#7c8e87">${t}</text>`;
 $('chart').innerHTML=svg+'</svg>';
}
function sensitivity(){const check=$('identity').checked,orig=predictions.gcn_gru[node]*meta.kmh;if(!check){$('sensitivity-result').textContent='Bật tùy chọn để tính lại dự báo với graph chỉ có cạnh bản thân.';return;}const other=forecastSensor(meta,data,models.gcn_gru,origin,node,false)*meta.kmh;$('sensitivity-result').textContent=`Graph đầy đủ: ${f(orig)} km/h. Chỉ cạnh bản thân: ${f(other)} km/h. Thay đổi ${f(other-orig)} km/h. Trọng số giữ nguyên, không huấn luyện lại.`;}
function freshness(){
 const q=assessFreshness(meta,data,origin,node),box=$('quality');box.className=`quality ${q.severity}`;
 $('quality-title').textContent=q.severity==='critical'?'Dữ liệu đầu vào quá cũ':q.severity==='warning'?'Lịch sử đầu vào có dữ liệu thiếu':'Quan sát hiện tại đã có';
 $('quality-age').textContent=q.age===0?'Tuổi dữ liệu: 0 phút':`Tuổi dữ liệu: ${ageLabel(q.age)}`;
 $('quality-detail').textContent=`${q.lastObserved?'Lần đo gần nhất: '+q.lastObserved+'. ':'Chưa có lần đo hợp lệ; đang dùng trung vị train. '}Cửa sổ của cảm biến: ${12-q.missing}/12 mốc có quan sát. Hàng xóm: ${q.missingNeighbors}/${q.neighbors} thiếu ở mốc hiện tại, ${q.staleNeighbors} có dữ liệu cũ từ 60 phút hoặc chưa từng được quan sát.`;
 $('quality-action').textContent=q.severity==='critical'?'Dự báo vẫn được tính để minh họa lỗi khi mất dữ liệu. Không xem giá trị đã bù là tình trạng giao thông hiện tại.':q.severity==='warning'?'Mô hình có thể dùng giá trị đã bù từ quá khứ; xem tuổi dữ liệu trước khi diễn giải dự báo.':'Cảnh báo này mô tả chất lượng đầu vào, không bảo đảm dự báo sẽ đúng.';
 document.querySelector('.forecast').classList.toggle('unreliable',q.severity==='critical');
}
function render(compute=true){
 if(compute){const start=performance.now();predictions={gcn_gru:forecastAll(meta,data,models.gcn_gru,origin,true),gru:forecastAll(meta,data,models.gru,origin,false),persistence:Float64Array.from(meta.nodes,(_,i)=>data.speed[origin*meta.nodes.length+i])};elapsed=performance.now()-start;}
 $('time').value=origin;$('datetime').value=meta.timestamps[origin].replace(' ','T').slice(0,16);$('clock').textContent=meta.timestamps[origin].slice(0,16);$('sensor-title').textContent=`Cảm biến ${meta.nodes[node].id}`;
 $('neighbor-count').textContent=`${meta.rows[node].length-1} hàng xóm`;
 const now=current(origin,node),forecast=predictions.gcn_gru[node]*meta.kmh;
 $('current').textContent=now===null?'Thiếu dữ liệu':`${f(now)} km/h`;
 $('missing-note').textContent=now===null?`Đầu vào bù từ quá khứ: ${f(speed(origin,node))} km/h`:meta.timestamps[origin].slice(11,16);
 $('prediction').textContent=`${f(forecast)} km/h`;$('delta').textContent=`${forecast>=speed(origin,node)?'Tăng':'Giảm'} ${f(Math.abs(forecast-speed(origin,node)))} km/h so với đầu vào cuối`;
 $('reveal').textContent=revealed?'Ẩn dữ liệu tương lai':'Xem điều gì thực sự xảy ra';
 const target=current(origin+3,node);$('outcome').textContent=!revealed?'Dữ liệu tương lai đang được ẩn.':target===null?'Mốc mục tiêu thiếu dữ liệu, không tính sai số.':`Thực tế lúc ${meta.timestamps[origin+3].slice(11,16)}: ${f(target)} km/h. Sai số GCN + GRU: ${f(Math.abs(forecast-target))} km/h.`;
 $('comparison').innerHTML=['persistence','gru','gcn_gru'].map(k=>`<div>${label[k]}<b>${f(predictions[k][node]*meta.kmh)}</b><small>${revealed&&target!==null?'Lệch '+f(Math.abs(predictions[k][node]*meta.kmh-target)):'km/h'}</small></div>`).join('');
 $('latency').textContent=`Tính lại hai mô hình cho 207 cảm biến: ${elapsed.toFixed(0)} ms trên trình duyệt này. Dự báo dùng trọng số đã học. Các đường đứt nối tới mục tiêu +15 phút chỉ hỗ trợ đọc biểu đồ.`;
 freshness();map();chart();sensitivity();
}
function example(index){stop();const c=meta.cases[index];origin=c.origin;node=c.node;$('sensor').value=node;revealed=false;render();}
async function init(){
 [meta,models,report]=await Promise.all([json('meta.json'),json('models.json'),json('report.json')]);
 if(!report.run_id||meta.run_id!==report.run_id||models.gru.run_id!==report.run_id||models.gcn_gru.run_id!==report.run_id)throw Error('Dữ liệu và mô hình không cùng phiên bản. Hãy tải lại trang');
 const [speed,mask,calendar,age]=await Promise.all([binary('speeds.f32',Float32Array),binary('observed.u8',Uint8Array),binary('calendar.f32',Float32Array),binary('age.i32',Int32Array)]);data={speed,mask,calendar,age};
 if(speed.length!==meta.steps*207||mask.length!==speed.length||age.length!==speed.length||calendar.length!==meta.steps*4)throw Error('Kích thước dữ liệu không khớp');
 $('sensor').innerHTML=meta.nodes.map((n,i)=>`<option value="${i}">${n.id}</option>`).join('');$('time').min=meta.origin_min;$('time').max=meta.origin_max;
 $('datetime').min=meta.timestamps[meta.origin_min].replace(' ','T').slice(0,16);$('datetime').max=meta.timestamps[meta.origin_max].replace(' ','T').slice(0,16);
 $('sensor').onchange=()=>{node=+$('sensor').value;revealed=false;render(false);};
 $('time').oninput=()=>{stop();origin=+$('time').value;revealed=false;render();};
 $('datetime').onchange=()=>{stop();const val=$('datetime').value.replace('T',' ')+':00';const idx=meta.timestamps.indexOf(val);if(idx<meta.origin_min||idx>meta.origin_max){$('datetime').setCustomValidity('Chọn mốc 5 phút trong tập kiểm tra.');$('datetime').reportValidity();return;}$('datetime').setCustomValidity('');origin=idx;revealed=false;render();};
 $('play').onclick=()=>{if(playing){stop();return;}$('play').textContent='Ⅱ Tạm dừng';playing=setInterval(()=>{if(origin>=meta.origin_max){stop();return;}origin++;revealed=false;render();},1000);};
 $('good').onclick=()=>example(0);$('hard').onclick=()=>example(1);$('stale').onclick=()=>example(2);$('reveal').onclick=()=>{revealed=!revealed;render(false);};$('map-mode').onchange=map;$('identity').onchange=sensitivity;
 const best=Math.min(...report.summary.map(r=>r.mae_kmh));$('results').innerHTML=report.summary.map(r=>`<tr class="${r.mae_kmh===best?'best':''}"><td>${label[r.model]}</td><td>${r.mae_kmh.toFixed(3)}${r.runs>1?' ± '+r.mae_std_kmh.toFixed(3):''}</td><td>${r.rmse_kmh.toFixed(2)}</td><td>${r.slow_mae_kmh.toFixed(2)}</td></tr>`).join('');
 const g=report.summary.find(r=>r.model==='gcn_gru'),b=report.summary.find(r=>r.model==='gru'),improve=(b.mae_kmh-g.mae_kmh)/b.mae_kmh*100;
 $('finding').textContent=`Trong lần chia thời gian này, MAE trung bình của GCN + GRU ${improve>=0?'thấp':'cao'} hơn GRU ${Math.abs(improve).toFixed(1)}%. Đây là kết quả của kiến trúc gọn và quy trình riêng của nhóm, không phải số liệu tái lập paper.`;
 $('runs').innerHTML=report.runs.filter(r=>r.seed!==null).map(r=>`<tr><td>${label[r.model]}</td><td>${r.seed}</td><td>${r.best_epoch}</td><td>${r.val_mae_kmh.toFixed(3)}</td><td>${r.mae_kmh.toFixed(3)}</td><td>${r.fit_seconds.toFixed(1)} giây</td></tr>`).join('');
 $('protocol').textContent=`Bản v2. Test: ${report.manifest.splits.test.windows.toLocaleString('vi')} cửa sổ, từ ${report.manifest.splits.test.target_start} đến ${report.manifest.splits.test.target_end}. Chấm mọi mốc validation và test; bỏ hai mục tiêu đầu mỗi ranh giới để nhãn trước đó đã sẵn sàng ở lúc dự báo. Mô hình demo: GRU seed ${models.gru.seed}, GCN + GRU seed ${models.gcn_gru.seed}.`;
 $('loading').hidden=true;$('lab').hidden=false;example(0);window.trafficLab={meta,report,models,data,get state(){return {origin,node,revealed,elapsed,predictions};}};
}
init().catch(e=>{$('loading').className='error';$('loading').textContent=`Không nạp được demo: ${e.message}. Nếu chạy local, hãy dùng máy chủ HTTP theo README.`;console.error(e);});
