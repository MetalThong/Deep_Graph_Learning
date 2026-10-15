import {featureProjection,infer,removeIncidentEdges} from './gnn.mjs';
const $=id=>document.getElementById(id);
const colors=['#007e71','#d17847','#6d70b1','#458aa7','#a875aa','#8e9c41','#d4ad48'];
const names=['Case Based','Genetic Algorithms','Neural Networks','Probabilistic Methods','Reinforcement Learning','Rule Learning','Theory'];
let data,weights,report,history,projected,original,result,node,activeEdges;
const percentage=n=>(n*100).toFixed(1)+'%';
const name=k=>names[k]??data.classes[k].replaceAll('_',' ');
const svgNS='http://www.w3.org/2000/svg';
function svgElement(type,attrs,text){const e=document.createElementNS(svgNS,type);for(const [k,v] of Object.entries(attrs)) e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;}

document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b===button));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id===button.dataset.tab));
}));

function drawGraph(){
  const neighbors=Array.from({length:data.ids.length},()=>[]);
  for(const [a,b] of activeEdges){neighbors[a].push(b);neighbors[b].push(a);}
  const first=neighbors[node].slice(0,24);
  const second=[...new Set(first.flatMap(i=>neighbors[i]))].filter(i=>i!==node&&!first.includes(i)).slice(0,60-first.length);
  const shown=[node,...first,...second], allowed=new Set(shown);
  const positions=new Map([[node,[360,205]]]);
  for(const [layer,radius] of [[first,105],[second,182]]) layer.forEach((id,i)=>{
    const angle=2*Math.PI*i/Math.max(layer.length,1)-Math.PI/2;
    positions.set(id,[360+radius*1.55*Math.cos(angle),205+radius*Math.sin(angle)]);
  });
  const svg=svgElement('svg',{viewBox:'0 0 720 410',role:'img','aria-label':`Lân cận bài báo ${data.ids[node]}, ${shown.length} node hiển thị`});
  const title=svgElement('title',{},'Bấm một node để xem dự đoán. Vị trí chỉ phục vụ minh họa khoảng cách hop.');svg.append(title);
  for(const [a,b] of activeEdges) if(allowed.has(a)&&allowed.has(b)){
    const [x1,y1]=positions.get(a),[x2,y2]=positions.get(b),selected=a===node||b===node;
    svg.append(svgElement('line',{x1,y1,x2,y2,stroke:selected?'#77a696':'#d7e2d9','stroke-width':selected?1.7:1,opacity:selected?.8:.65}));
  }
  for(const id of shown){
    const [cx,cy]=positions.get(id),selected=id===node,r=selected?17:(first.includes(id)?8:5);
    if(selected)svg.append(svgElement('circle',{cx,cy,r:27,fill:colors[result.predictions[id]],opacity:.12}));
    const dot=svgElement('circle',{cx,cy,r,fill:colors[result.predictions[id]],stroke:'white','stroke-width':selected?3:1.5,tabindex:'0',role:'button','aria-label':`Bài báo ${data.ids[id]}, dự đoán ${name(result.predictions[id])}`});
    dot.append(svgElement('title',{},`${data.ids[id]} · ${name(result.predictions[id])} · ${data.split[id]}`));
    const choose=()=>{$('drop').value='0';selectNode(id);};
    dot.addEventListener('click',choose);dot.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});svg.append(dot);
    if(selected)svg.append(svgElement('text',{x:cx,y:cy+42,'text-anchor':'middle','font-size':12,'font-weight':600,fill:'#142b2a'},'#'+data.ids[id]));
  }
  $('graph').replaceChildren(svg);
  $('graph-caption').textContent=`${shown.length} node minh họa · ${neighbors[node].length} hàng xóm trực tiếp · tối đa 61 node`;
}

function updateDetails(){
  const pred=result.predictions[node],probs=result.probabilities[node];
  $('paper').value=data.ids[node];$('paper-id').textContent='PAPER #'+data.ids[node];$('split').textContent=data.split[node].toUpperCase();
  $('prediction').textContent=name(pred);$('prediction').style.color=colors[pred];
  $('confidence').textContent=`Softmax cao nhất: ${percentage(probs[pred])} · ${data.features[node].length} đặc trưng có giá trị`;
  $('probabilities').replaceChildren();
  [...probs.keys()].sort((a,b)=>probs[b]-probs[a]).forEach(k=>{
    const row=document.createElement('div');row.className='probability';
    const label=document.createElement('div');label.className='prob-label';
    const left=document.createElement('span');left.textContent=name(k);const right=document.createElement('span');right.textContent=percentage(probs[k]);label.append(left,right);
    const track=document.createElement('div');track.className='track';const bar=document.createElement('div');bar.className='bar';bar.style.width=percentage(probs[k]);bar.style.background=colors[k];track.append(bar);row.append(label,track);$('probabilities').append(row);
  });
  $('truth').textContent=`Nhãn thật: ${name(data.labels[node])}. GCN ${pred===data.labels[node]?'dự đoán đúng':'dự đoán sai'} với đồ thị hiện tại.`;
  $('baselines').textContent=`MLP: ${name(data.mlp[node])}. Logistic Regression: ${name(data.lr[node])}.`;
}

function selectNode(id){
  node=id;
  const change=removeIncidentEdges(data.edges,node,Number($('drop').value));activeEdges=change.edges;
  result=change.removed?infer(projected,activeEdges,weights,data.ids.length):original;
  const old=original.predictions[node],now=result.predictions[node],delta=(result.probabilities[node][old]-original.probabilities[node][old])*100;
  $('delta').textContent=change.removed?`Đã bỏ ${change.removed} cạnh. ${name(old)} → ${name(now)}. Điểm của lớp ban đầu thay đổi ${delta>=0?'+':''}${delta.toFixed(1)} điểm %.`:'Giữ nguyên đồ thị gốc. Chọn 50% hoặc 100% để chạy lại suy luận.';
  updateDetails();drawGraph();
  $('status').className='';$('status').textContent=`Đã tính GCN cho ${data.ids.length.toLocaleString('vi-VN')} node · trọng số seed ${weights.seed} · không huấn luyện trong trình duyệt`;
}

function renderMetrics(){
  for(const row of report.summary){
    const tr=document.createElement('tr');if(row.model==='GCN')tr.className='gcn';
    const values=[row.model,row.model==='GCN'?'X + A':'X',percentage(row.accuracy_mean)+(row.runs>1?` ± ${(row.accuracy_std*100).toFixed(2)}`:''),(row.macro_f1_mean*100).toFixed(2)+'%'];
    for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td);}$('metrics').append(tr);
  }
  const cm=report.runs.find(r=>r.model==='GCN'&&r.seed===weights.seed).confusion_matrix;
  const table=document.createElement('table');table.className='matrix';
  const header=document.createElement('tr');for(const label of ['↓ / →',...names.map((_,i)=>String(i+1))]){const th=document.createElement('th');th.textContent=label;header.append(th);}table.append(header);
  const max=Math.max(...cm.flat());cm.forEach((row,i)=>{const tr=document.createElement('tr');const th=document.createElement('th');th.textContent=String(i+1);th.title=name(i);tr.append(th);row.forEach(value=>{const td=document.createElement('td');td.textContent=value;td.style.background=`rgba(0,126,113,${.03+.8*value/max})`;if(value/max>.55)td.style.color='white';tr.append(td);});table.append(tr);});$('confusion').append(table);
  const classKey=document.createElement('p');classKey.className='micro';classKey.textContent=names.map((n,i)=>`${i+1}. ${n}`).join(' · ');$('confusion').append(classKey);
  const keys=['train_loss_dropout','val_loss'], maxY=Math.max(...history.flatMap(h=>keys.map(k=>h[k])))*1.1;
  const svg=svgElement('svg',{viewBox:'0 0 460 220',role:'img','aria-label':'Đường train loss và validation loss theo epoch'});
  for(let i=0;i<=4;i++){const y=175-i*35;svg.append(svgElement('line',{x1:34,y1:y,x2:440,y2:y,stroke:'#e0e6dd'}));svg.append(svgElement('text',{x:2,y:y+3,'font-size':9,fill:'#61706d'},(i*maxY/4).toFixed(1)));}
  keys.forEach((key,j)=>{const points=history.map((h,i)=>`${34+i/Math.max(1,history.length-1)*406},${175-h[key]/maxY*140}`).join(' ');svg.append(svgElement('polyline',{points,fill:'none',stroke:j?'#cb5936':'#007e71','stroke-width':2}));});
  svg.append(svgElement('text',{x:35,y:196,'font-size':10,fill:'#61706d'},'Epoch 1'));
  svg.append(svgElement('text',{x:365,y:196,'font-size':10,fill:'#61706d'},String(history.length)));
  svg.append(svgElement('text',{x:35,y:215,'font-size':10,fill:'#007e71'},'— Train (+ dropout, L2)'));
  svg.append(svgElement('text',{x:225,y:215,'font-size':10,fill:'#cb5936'},'— Validation'));$('curves').append(svg);
}

async function renderResearch(){
  const research=await loadJson('research.json');
  function row(values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td);}return tr;}
  for(const r of research.summary){
    const accuracy=`${(r.accuracy_mean*100).toFixed(2)} ± ${(r.accuracy_std*100).toFixed(2)}%`;
    if(['Logistic Regression','MLP-2','GCN-2','GraphSAGE-2','GAT-2'].includes(r.model))
      $('research-metrics').append(row([r.model,accuracy,(r.macro_f1_mean*100).toFixed(2)+'%',r.parameters.toLocaleString('vi-VN')]));
  }
  for(const depth of [1,2,4,8]){
    const r=research.summary.find(r=>r.model===`GCN-${depth}`);
    if(r)$('depth-metrics').append(row([depth,`${(r.accuracy_mean*100).toFixed(2)} ± ${(r.accuracy_std*100).toFixed(2)}%`,(r.macro_f1_mean*100).toFixed(2)+'%',r.seconds_mean.toFixed(1)]));
  }
}

async function loadJson(path){const r=await fetch(path);if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.json();}
try{
  [data,weights,report,history]=await Promise.all(['data.json','weights.json','report.json','history.json'].map(loadJson));
  projected=featureProjection(data.features,weights.w1);original=infer(projected,data.edges,weights,data.ids.length);
  for(let i=0;i<names.length;i++){const span=document.createElement('span');const dot=document.createElement('i');dot.style.background=colors[i];span.append(dot,document.createTextNode(`${i+1}. ${name(i)}`));$('legend').append(span);}
  renderMetrics();selectNode(data.examples.gcn_correct_mlp_wrong);
  renderResearch().catch(error=>{const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=4;td.textContent='Chưa có research.json. Chạy research.py để tạo kết quả nghiên cứu mở rộng.';tr.append(td);$('research-metrics').append(tr);console.warn(error.message);});
  $('paper-form').addEventListener('submit',e=>{e.preventDefault();const id=data.ids.indexOf($('paper').value.trim());if(id<0){$('status').className='error';$('status').textContent='Không có mã bài báo này trong Cora. Dùng tình huống gợi ý hoặc chọn ngẫu nhiên.';return;}$('drop').value='0';selectNode(id);});
  $('example').addEventListener('change',()=>{$('drop').value='0';selectNode(data.examples[$('example').value]);});
  $('drop').addEventListener('change',()=>selectNode(node));
  $('random').addEventListener('click',()=>{const test=data.split.map((s,i)=>s==='test'?i:-1).filter(i=>i>=0);$('drop').value='0';selectNode(test[Math.floor(Math.random()*test.length)]);});
}catch(error){$('status').className='error';$('status').textContent=`Không tải được demo: ${error.message}. Hãy chạy bằng HTTP server, không mở trực tiếp file HTML.`;console.error(error);}
