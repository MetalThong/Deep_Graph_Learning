import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT = path.resolve('../..');
const DATA = JSON.parse(await fs.readFile('combined-content.json', 'utf8'));
const TRAFFIC = path.resolve('../../traffic');
const ELLIPTIC = path.resolve('../../elliptic');
const SKILL = 'C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const { applyPresentationChartFont } = await import(pathToFileURL(SKILL + '/container_tools/artifact_tool_utils.mjs'));
const P = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = { paper:'#F7F6F0', ink:'#163B3B', teal:'#087E73', muted:'#657B79', amber:'#BE7B2F', line:'#D7E1D9', red:'#CE704C', white:'#FFFFFF', gray:'#98A8A6' };
const speakerNames = Object.fromEntries(DATA.speakers.map(x => [x.name.split(' · ')[0].replace('Người ', ''), x.name]));
const chartSlides = [], tableSlides = [];

function txt(s, value, x, y, w, h, size=28, opt={}) {
  const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0},name:opt.name??String(value).slice(0,44)});
  sh.text=value;
  sh.text.style={typeface:'Arial',fontSize:size,color:C.ink,autoFit:'none',wrap:'square',insets:0,verticalAlignment:'top',...opt};
  return sh;
}
function rect(s,x,y,w,h,fill=C.line,lineFill='none',lineWidth=0){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:lineFill,width:lineWidth}});}
function ellipse(s,x,y,w,h,fill=C.teal,lineFill='none',lineWidth=0){return s.shapes.add({geometry:'ellipse',position:{left:x,top:y,width:w,height:h},fill,line:{fill:lineFill,width:lineWidth}});}
function bulletList(s,items,{x=76,y=190,w=1110,size=27,row=78}={}){
  items.forEach((it,i)=>{
    ellipse(s,x,y+i*row+10,11,11,i===0?C.teal:C.amber);
    txt(s,it,x+27,y+i*row,w-28,row-6,size,{color:i===0?C.ink:C.ink});
  });
}
function footer(s,index,d){
  rect(s,64,674,1152,1,C.line);
  const who=DATA.speakers.find(x=>x.name.startsWith(`Người ${d.speaker} `));
  txt(s,`${who.name}  ·  ${d.seconds} giây`,64,682,900,20,15,{color:C.muted});
  txt(s,`${String(index).padStart(2,'0')} / 32`,1118,682,98,20,15,{color:C.muted,alignment:'right'});
}
function header(s,index,d){
  txt(s,`DEEP GRAPH  /  NGƯỜI ${d.speaker}`,64,23,650,22,15,{bold:true,color:C.teal});
  txt(s,d.title,64,55,1152,92,43,{bold:true,name:'slide-title'});
  footer(s,index,d);
}
function takeaway(s,value,x=64,y=594,w=1152){
  rect(s,x,y,w,2,C.line);
  txt(s,value,x,y+14,w,45,26,{bold:true,color:C.teal});
}
function foot(s,value){txt(s,value,64,642,1150,26,16,{color:C.muted});}
function table(s,values,x,y,w,h,widths,size=23){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
  t.styleOptions={headerRow:false,bandedRows:false};
  t.borders.assign({width:.8,fill:C.line});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:'Arial',fontSize:size,color:C.ink},margins:{left:12,right:10,top:9,bottom:8},fill:C.paper,anchor:'center'});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.ink,textStyle:{typeface:'Arial',fontSize:size,color:C.white,bold:true}});
  tableSlides.push(P.slides.items.length);
  return t;
}
async function image(s,file,x,y,w,h,fit='contain'){
  const bytes=await fs.readFile(file);
  s.images.add({blob:bytes,contentType:'image/png',alt:path.basename(file),fit,position:{left:x,top:y,width:w,height:h}});
}
function connect(s,a,b,color=C.line,width=2){
  const c=s.shapes.connect(a,b,{kind:'straight',line:{fill:color,width},tail:{type:'triangle',width:'med',length:'med'}});
  c.sendToBack();return c;
}
function drawGraph(s,x,y,scale=1,focus=3){
  const pts=[[10,110],[145,10],[145,210],[290,110],[425,10],[425,210]];
  const ns=pts.map(([a,b],i)=>ellipse(s,x+a*scale,y+b*scale,52*scale,52*scale,i===focus?C.red:(i%2?C.teal:'#5C8E83')));
  [[0,1],[0,2],[1,3],[2,3],[3,4],[3,5]].forEach(([a,b])=>connect(s,ns[a],ns[b]));
  ns.forEach((_,i)=>txt(s,String.fromCharCode(65+i),x+pts[i][0]*scale,y+pts[i][1]*scale+12*scale,52*scale,25*scale,19*scale,{bold:true,color:C.white,alignment:'center'}));
  return ns;
}
function flow(s,labels,x,y,width,options={}){
  const gap=options.gap??14,cell=(width-gap*(labels.length-1))/labels.length;
  labels.forEach((label,i)=>{
    rect(s,x+i*(cell+gap),y,cell,88, i===labels.length-1?C.teal:C.white, C.line,1);
    txt(s,label,x+i*(cell+gap)+10,y+15,cell-20,60,options.size??23,{bold:true,color:i===labels.length-1?C.white:C.ink,alignment:'center',verticalAlignment:'middle'});
    if(i<labels.length-1)txt(s,'→',x+i*(cell+gap)+cell,y+24,gap,40,23,{bold:true,color:C.teal,alignment:'center'});
  });
}
function barChart(s,categories,values,x,y,w,h,max,unit=''){
  const chart=s.charts.add('bar',{
    position:{left:x,top:y,width:w,height:h},
    categories,
    series:[{name:unit||'Giá trị',values,points:values.map((_,i)=>({idx:i,fill:[C.gray,C.amber,C.teal,C.red][i%4]}))}],
    hasLegend:false,barOptions:{direction:'column',gapWidth:95},
    chartFill:C.paper,chartLine:{fill:'none',width:0},plotAreaFill:C.paper,plotAreaLine:{fill:'none',width:0},
    xAxis:{textStyle:{fontSize:18,fill:C.ink},line:{fill:C.line,width:1},majorGridlines:null},
    yAxis:{min:0,max,majorUnit:max/4,numberFormatCode:'0',textStyle:{fontSize:17,fill:C.muted},majorGridlines:{fill:C.line,width:.8},line:{fill:'none',width:0}},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:19,fill:C.ink,bold:true}}
  });
  applyPresentationChartFont(chart,{fontFamily:'Arial'});
  chartSlides.push(P.slides.items.length);
  return chart;
}
function drawTemporalGraph(s){
  const x0=90,y0=280;
  for(let i=0;i<12;i++){
    const h=34+((i*29)%70);
    rect(s,x0+i*46,y0+106-h,25,h,i===11?C.teal:'#9EB6A9');
  }
  txt(s,'12 mốc lịch sử',88,402,555,39,24,{bold:true,color:C.teal});
  txt(s,'→',650,320,90,70,50,{bold:true,color:C.amber,alignment:'center'});
  drawGraph(s,770,258,.68,3);
  txt(s,'GCN + GRU',940,446,260,36,23,{bold:true,color:C.teal,alignment:'center'});
}

let elapsed=0;
for(let i=0;i<DATA.slides.length;i++){
  const d=DATA.slides[i],s=P.slides.add(),slideNo=i+1,start=elapsed;
  elapsed+=d.seconds;s.background.fill=C.paper;
  const clock=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  s.speakerNotes.text=`NGƯỜI ${d.speaker} · SLIDE ${slideNo}/32 · ${d.seconds} GIÂY · ${clock(start)}–${clock(elapsed)}

LỜI THUYẾT TRÌNH
${d.script}

THAO TÁC
${d.action??'Trình bày theo thứ tự từ trái sang phải.'}

CHUYỂN TIẾP
${d.transition??''}

NGUỒN
${d.refs??''}`;

  if(d.kind==='cover'){
    s.background.fill=C.ink;
    rect(s,64,112,9,460,C.teal);
    txt(s,'DEEP GRAPH\nLEARNING',102,130,1015,185,72,{bold:true,color:C.white});
    txt(s,d.lead,105,344,1070,83,40,{color:'#D4E8DF'});
    txt(s,DATA.course,105,507,1000,38,25,{color:'#D4E8DF'});
    txt(s,'HAI DEMO  ·  GIAO THÔNG + BITCOIN',105,573,1050,36,20,{bold:true,color:C.white});
    txt(s,'38 phút trình bày  +  2 phút hỏi đáp',105,622,1050,30,19,{color:'#BBD6CB'});
    footer(s,slideNo,d);
    continue;
  }
  if(d.kind==='section'){
    s.background.fill=C.ink;
    txt(s,`NGƯỜI ${d.speaker}  /  DEMO THỰC NGHIỆM`,64,54,1100,33,18,{bold:true,color:'#A6D6C6'});
    txt(s,d.title,64,153,1110,155,57,{bold:true,color:C.white});
    rect(s,64,347,1150,3,C.teal);
    txt(s,d.lead,64,390,1075,100,35,{color:'#E1EEE9'});
    txt(s,d.speaker===3?'DỮ LIỆU LỊCH SỬ  ·  METR-LA  ·  HỒI QUY':'ELLIPTIC  ·  PHÂN LOẠI GIAO DỊCH  ·  NHÃN MẤT CÂN BẰNG',64,552,1125,40,21,{bold:true,color:'#A6D6C6'});
    footer(s,slideNo,d);
    continue;
  }
  header(s,slideNo,d);

  switch(d.kind){
    case 'course':
      bulletList(s,d.items,{y:181,row:73,size:25});takeaway(s,d.takeaway,64,565);break;
    case 'representation':
      bulletList(s,d.items,{x:85,y:206,w:1090,row:82,size:29});
      txt(s,'Dữ liệu quan hệ',775,539,420,40,22,{bold:true,color:C.teal,alignment:'right'});break;
    case 'graph':
      drawGraph(s,100,205,1.0,3);
      txt(s,'NÚT',685,198,430,43,24,{bold:true,color:C.teal});
      txt(s,'Đối tượng được mô tả',685,241,475,43,28);
      txt(s,'CẠNH',685,325,430,43,24,{bold:true,color:C.teal});
      txt(s,'Quan hệ giữa hai đối tượng',685,368,510,50,28);
      txt(s,'FEATURE / LABEL',685,455,465,43,24,{bold:true,color:C.teal});
      txt(s,'Đầu vào / đáp án cần học',685,498,500,50,28);
      foot(s,'Định nghĩa nút và cạnh phụ thuộc bài toán.');break;
    case 'tasks':
      d.items.forEach((item,j)=>{
        const x=66+j*294;
        rect(s,x,207,3,265,j===3?C.red:C.teal);
        const [head,...rest]=item.split(' · ');
        txt(s,head,x+19,206,260,56,31,{bold:true,color:j===3?C.red:C.teal});
        txt(s,rest.join(' · '),x+19,286,251,142,26);
      });
      takeaway(s,'Chọn đúng đơn vị dự đoán trước khi chọn loss và metric.',64,550);break;
    case 'message':
      drawGraph(s,64,206,.77,3);
      bulletList(s,d.items,{x:605,y:196,w:610,row:92,size:25});
      takeaway(s,d.takeaway,64,562);break;
    case 'cnn':
      txt(s,'CNN',92,194,400,58,36,{bold:true,color:C.teal});
      txt(s,'Lưới pixel\nVùng lân cận cố định\nBộ lọc dùng chung',92,275,460,185,31);
      txt(s,'→',577,296,100,76,52,{bold:true,color:C.amber,alignment:'center'});
      txt(s,'GNN',728,194,420,58,36,{bold:true,color:C.teal});
      txt(s,'Nút và cạnh\nSố hàng xóm thay đổi\nQuy tắc cập nhật dùng chung',728,275,475,185,31);
      takeaway(s,d.takeaway,64,548);break;
    case 'takeaway':
      bulletList(s,d.items,{x:78,y:204,w:1105,row:87,size:28});
      takeaway(s,d.takeaway,64,562);break;
    case 'gcn':
      drawGraph(s,90,208,.78,3);
      txt(s,'TỰ THÂN',610,207,490,40,24,{bold:true,color:C.teal});
      txt(s,'+',610,257,50,50,35,{bold:true,color:C.amber});
      txt(s,'THÔNG TIN HÀNG XÓM',668,263,530,41,24,{bold:true,color:C.teal});
      txt(s,'↓',811,312,64,49,31,{bold:true,color:C.amber,alignment:'center'});
      txt(s,'biến đổi đã học',674,361,402,52,31,{bold:true,alignment:'center'});
      txt(s,d.takeaway,607,455,568,84,29,{bold:true,color:C.teal,alignment:'center'});
      foot(s,'Một lớp lan thông tin qua một bước cạnh.');break;
    case 'selfloop':
      txt(s,'TRƯỚC',110,203,420,43,24,{bold:true,color:C.muted});
      const a=ellipse(s,190,294,90,90,C.teal);txt(s,'A',215,320,40,37,29,{bold:true,color:C.white,alignment:'center'});
      const b=ellipse(s,422,294,90,90,C.gray);txt(s,'B',447,320,40,37,29,{bold:true,color:C.white,alignment:'center'});connect(s,a,b);
      txt(s,'SAU KHI THÊM SELF-LOOP',660,203,500,43,24,{bold:true,color:C.teal});
      const c=ellipse(s,730,294,90,90,C.teal);txt(s,'A',755,320,40,37,29,{bold:true,color:C.white,alignment:'center'});
      const e=ellipse(s,994,294,90,90,C.gray);txt(s,'B',1019,320,40,37,29,{bold:true,color:C.white,alignment:'center'});connect(s,c,e);
      txt(s,'↻',760,383,38,39,31,{bold:true,color:C.amber});txt(s,'↻',1023,383,38,39,31,{bold:true,color:C.amber});
      bulletList(s,d.items,{x:123,y:477,w:1040,row:43,size:22});break;
    case 'model-compare':
      table(s,d.table,64,194,1152,327,[290,500,362],23);
      takeaway(s,d.takeaway,64,553);break;
    case 'gat':
      bulletList(s,d.items,{x:82,y:207,w:1090,row:90,size:28});break;
    case 'temporal':
      drawTemporalGraph(s);
      txt(s,d.takeaway,80,539,1120,40,24,{bold:true,color:C.teal,alignment:'center'});break;
    case 'training':
      flow(s,d.items.map(x=>x.split(' · ')[0]),74,241,1132,{size:22});
      d.items.forEach((x,j)=>txt(s,x.split(' · ')[1],77+j*282,359,250,90,23,{color:C.muted,alignment:'center'}));
      takeaway(s,d.takeaway??'Tách train và validation; chỉ test sau lựa chọn.',64,536);break;
    case 'split':
      const sx=110,sy=260,sw=1050;
      rect(s,sx,sy,sw*.61,80,'#8FB3A5');rect(s,sx+sw*.61,sy,sw*.15,80,C.amber);rect(s,sx+sw*.76,sy,sw*.24,80,C.teal);
      txt(s,'TRAIN',sx,sy+21,sw*.61,40,27,{bold:true,color:C.white,alignment:'center'});
      txt(s,'VAL',sx+sw*.61,sy+21,sw*.15,40,23,{bold:true,color:C.white,alignment:'center'});
      txt(s,'TEST',sx+sw*.76,sy+21,sw*.24,40,25,{bold:true,color:C.white,alignment:'center'});
      bulletList(s,d.items,{x:98,y:393,w:1080,row:48,size:22});break;
    case 'metrics':
      table(s,[["Mục tiêu","Chỉ số chính","Đọc như thế nào"],["Tốc độ (liên tục)","MAE / RMSE","Độ lệch theo km/h"],["Nhãn hiếm","Precision / Recall / F1","Trade-off tại ngưỡng"],["Xếp hạng","Average Precision","Chất lượng qua ngưỡng"]],64,196,1152,304,[285,365,502],24);
      takeaway(s,d.takeaway??'Baseline, split và đơn vị phải khớp giữa các mô hình.',64,548);break;
    case 'kg-rag':
      table(s,d.table,64,202,1152,300,[285,460,407],23);
      takeaway(s,d.takeaway??'Có thể kết hợp, nhưng là những vai trò khác nhau.',64,542);break;
    case 'traffic-data':
      drawGraph(s,105,223,.79,3);
      bulletList(s,d.items,{x:620,y:206,w:575,row:88,size:25});
      foot(s,'Los Angeles · tháng 3–6/2012 · không phải dữ liệu thời gian thực.');break;
    case 'traffic-model':
      barChart(s,['Giữ nguyên','GRU','GCN+GRU'],[5.6289,4.8754,4.8439],64,183,690,375,6.5,'MAE km/h');
      table(s,d.table,790,218,426,255,[210,116,100],19);
      foot(s,'Ba seed mỗi mạng. ± là SD qua seed; test v2 đã từng được xem trong v1.');break;
    case 'traffic-fresh':
      await image(s,`${TRAFFIC}/results/demo-workspace.png`,64,174,666,410,'contain');
      bulletList(s,d.items,{x:775,y:196,w:438,row:86,size:25});
      foot(s,d.lead);break;
    case 'traffic-stale':
      await image(s,`${TRAFFIC}/results/demo-warning-v2.png`,64,177,642,430,'contain');
      bulletList(s,d.items,{x:748,y:194,w:468,row:81,size:24});
      foot(s,'Cảnh báo chất lượng đầu vào; chưa phải xác suất mô hình dự báo sai.');break;
    case 'traffic-hard':
      await image(s,`${TRAFFIC}/results/audit_v2/case-2.png`,64,178,800,405,'contain');
      bulletList(s,d.items,{x:892,y:192,w:318,row:83,size:23});
      foot(s,'Không có nhãn sự cố để kết luận nguyên nhân.');break;
    case 'traffic-live':
      bulletList(s,d.items,{x:82,y:196,w:1110,row:86,size:26});
      takeaway(s,'Tổng thời gian live: 4 phút. Ẩn đáp án cho tới khi lớp dự đoán.',64,567);break;
    case 'traffic-limit':
      bulletList(s,d.items,{x:86,y:202,w:1085,row:88,size:27});break;
    case 'elliptic-data':
      drawGraph(s,78,219,.68,3);
      txt(s,'49',600,210,240,105,80,{bold:true,color:C.teal,alignment:'center'});
      txt(s,'LÁT CẮT',600,307,240,38,23,{bold:true,color:C.muted,alignment:'center'});
      bulletList(s,d.items,{x:855,y:195,w:350,row:91,size:23});
      foot(s,'Nhãn trong benchmark, không phải phán quyết ngoài đời.');break;
    case 'elliptic-results':
      barChart(s,['RF local','RF all','MLP','GCN'],[77.0,79.3,64.5,61.3],64,183,690,375,90,'F1 illicit (%)');
      table(s,d.table,790,205,426,305,[210,116,100],18);
      foot(s,'RF all dùng thêm 72 feature tổng hợp hàng xóm; GCN dùng graph. Ba seed.');break;
    case 'elliptic-live-intro':
      await image(s,`${ELLIPTIC}/qa/workspace.png`,64,178,1152,405,'contain');
      foot(s,d.items.join('   ·   '));break;
    case 'elliptic-detected':
      txt(s,d.lead,74,191,1098,49,30,{bold:true,color:C.teal});
      table(s,[["Đầu ra mô hình","Ngưỡng","Nhãn tham chiếu"],["GCN 0,9972","~0,7079","Illicit"]],74,274,1120,151,[380,350,390],25);
      takeaway(s,'Hỏi lớp dự đoán trước khi hiện nhãn.',74,477,1120);break;
    case 'elliptic-false':
      txt(s,d.lead,74,191,1098,49,30,{bold:true,color:C.red});
      table(s,[["Điểm GCN","Ngưỡng","Nhãn tham chiếu","Diễn giải"],["0,8350","~0,7079","Licit","Cảnh báo nhầm"]],74,274,1120,151,[250,250,310,310],25);
      takeaway(s,'Một điểm trên ngưỡng vẫn có thể là false positive.',74,477,1120);break;
    case 'elliptic-missed':
      table(s,[["Trường hợp","Điểm GCN","Nhãn","Kết luận"],["67673076 · lát cắt 35","0,3591","Illicit","Bỏ sót / FN"],["56460695 · lát cắt 35","0,9616","Unknown","Chưa thể xác nhận"]],64,202,1152,229,[350,220,260,322],23);
      bulletList(s,["Unknown không được xem là licit","Threshold thấp hơn thường tăng Recall và tăng cảnh báo nhầm","Có người rà soát trước khi hành động"],{x:93,y:466,w:1090,row:52,size:23});
      foot(s,'Điểm mô hình chưa được hiệu chỉnh thành xác suất.');break;
    case 'closing':
      bulletList(s,d.items,{x:88,y:193,w:1100,row:76,size:27});
      txt(s,'Cảm ơn thầy và các bạn · Hỏi đáp',74,530,1100,50,32,{bold:true,color:C.teal});
      foot(s,'Cùng một nguyên tắc: định nghĩa quan hệ, so baseline, kiểm tra dữ liệu và nêu giới hạn.');break;
    default: throw new Error(`Unknown slide kind: ${d.kind}`);
  }
}

if(DATA.slides.length!==32 || elapsed!==2280) throw new Error(`Unexpected deck: ${DATA.slides.length} slides / ${elapsed} seconds`);
await fs.mkdir('combined-previews',{recursive:true});
await fs.writeFile('combined-deck.json',JSON.stringify(P.toProto()));
await fs.writeFile('combined-slides-notes.json',JSON.stringify(DATA.slides,null,2));
await (await PresentationFile.exportPptx(P)).save('combined-candidate.pptx');
console.log(JSON.stringify({slides:P.slides.items.length,seconds:elapsed,tables:[...new Set(tableSlides)],charts:[...new Set(chartSlides)]}));
for(let i=0;i<P.slides.items.length;i++){
  const b=await P.export({slide:P.slides.items[i],format:'png',scale:1});
  await fs.writeFile(`combined-previews/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await b.arrayBuffer()));
  console.log(`Rendered ${i+1}`);
}
await fs.writeFile('combined-montage.webp',new Uint8Array(await(await P.export({format:'webp',montage:true,scale:.22})).arrayBuffer()));
