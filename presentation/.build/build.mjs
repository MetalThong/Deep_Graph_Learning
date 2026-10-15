import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {slides,source} from './content.mjs';

const ROOT=path.resolve('..');
const DEMO=path.resolve('../../demo');
const SKILL='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={bg:'#F7F6F0',ink:'#102E33',muted:'#52696D',teal:'#087F78',copper:'#B85F3B',line:'#D5DFDA',light:'#E5EEE8',white:'#FFFFFF'};
const metrics=JSON.parse(await fs.readFile(DEMO+'/results/research/metrics.json','utf8'));
const summary=Object.fromEntries(metrics.summary.map(r=>[r.model,r]));
const pct=v=>(v*100).toFixed(2).replace('.',',');
let now=0;
const clock=n=>`${Math.floor(n/60).toString().padStart(2,'0')}:${(n%60).toString().padStart(2,'0')}`;
function text(s,value,x,y,w,h,size=28,opt={}){
 const sh=s.shapes.add({geometry:'textbox',name:opt.name??String(value).slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;
 sh.text.style={typeface:opt.font??'Arial',fontSize:size,color:opt.color??C.ink,bold:opt.bold??false,alignment:opt.align??'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0,...(opt.style??{})};
 return sh;
}
function eq(s,v,x,y,w,h,size=40){return text(s,v,x,y,w,h,size,{font:'Cambria Math',color:C.teal});}
function label(s,v,x,y,w=1100){text(s,v,x,y,w,35,24,{bold:true,color:C.teal});}
function statement(s,v,y=585,ink=C.teal){text(s,v,64,y,1152,65,29,{color:ink,bold:true});}
function foot(s,v){text(s,v,64,650,1100,35,17,{color:C.muted});}
function table(s,values,x,y,w,h,widths,size=24,highlight=-1){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.styleOptions={headerRow:false,bandedRows:false};
 t.borders.assign({width:0.6,fill:C.line});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:'Arial',fontSize:size,color:C.ink},margins:{top:12,bottom:12,left:15,right:13},anchor:'center',fill:C.bg});
 t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.ink,textStyle:{typeface:'Arial',fontSize:size,bold:true,color:C.white}});
 if(highlight>0)t.cells.block({row:highlight,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.light,textStyle:{typeface:'Arial',fontSize:size,bold:true,color:C.teal}});
 return t;
}
async function img(s,file,x,y,w,h,opt={}){
 const bytes=await fs.readFile(file);
 return s.images.add({blob:bytes,contentType:'image/png',alt:opt.alt??path.basename(file),fit:opt.fit??'contain',position:{left:x,top:y,width:w,height:h},...(opt.crop?{crop:opt.crop}:{})});
}
function bars(s,cats,vals,x,y,w,h,highlight=-1,metric='Accuracy'){
 const c=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories:cats,series:[{name:metric,values:vals.map(v=>Number(v.toFixed(10))),fill:'#93B8AE',points:vals.map((v,i)=>({idx:i,fill:i===highlight?C.teal:'#93B8AE'}))}],barOptions:{direction:'column',grouping:'clustered',gapWidth:85},hasLegend:false,chartFill:C.bg,chartLine:{fill:'none',width:0},plotAreaFill:C.bg,plotAreaLine:{fill:'none',width:0},xAxis:{textStyle:{fontSize:22,fill:C.ink},line:{fill:C.line,width:1},majorGridlines:null},yAxis:{min:0,max:1,majorUnit:.2,numberFormatCode:'0%',textStyle:{fontSize:20,fill:C.muted},majorGridlines:{fill:C.line,width:.7},line:{fill:'none',width:0}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0%',textStyle:{fontSize:23,bold:true,fill:C.ink}}});
 applyPresentationChartFont(c,{fontFamily:'Arial'});return c;
}
for(let i=0;i<slides.length;i++){
 const d=slides[i],s=P.slides.add();s.background.fill=C.bg;
 if(i!==0){text(s,d.title,64,47,1152,105,44,{bold:true,name:'slide-title'});text(s,`${String(i+1).padStart(2,'0')} / 26`,1130,681,90,22,16,{color:C.muted,align:'right'});}
 d.start=now;now+=d.seconds;d.end=now;
 s.speakerNotes.text=`THÀNH VIÊN ${d.speaker} • SLIDE ${i+1}/26 • ${d.seconds} GIÂY • MỐC ${clock(d.start)}–${clock(d.end)}\n\nLỜI THUYẾT TRÌNH\n${d.script}\n\nTHAO TÁC VÀ NHỊP TRÌNH BÀY\n${d.action}\n\nCHUYỂN TIẾP\n${d.transition}\n\nNGUỒN\n${d.refs}`;
 switch(i+1){
 case 1:
  s.background.fill=C.ink;await img(s,'assets/cover.png',0,0,1280,720,{fit:'cover',alt:'Minh họa khái niệm mạng đồ thị, không phải dữ liệu thực nghiệm'});
  text(s,'DEEP GRAPH\nLEARNING',64,153,690,176,74,{bold:true,color:C.white});
  text(s,'Học sâu trên dữ liệu có quan hệ',68,361,660,90,35,{color:'#D6E9E2'});
  text(s,'Phát triển hệ thống thông minh\nGiảng viên: Trần Đình Quế',68,543,680,80,24,{color:'#D6E9E2'});
  text(s,'Nhóm 4 thành viên  ·  40 phút',68,646,650,30,21,{color:'#D6E9E2'});break;
 case 2:
  table(s,[['Kiến thức đã học','Phần tiếp nối trong Deep Graph'],['Chương 1 · Hệ thống thông minh','Biểu diễn quan hệ và đánh giá hệ thống'],['Chương 2 · Quy trình thực nghiệm','X, A, mask nhãn và kiểm soát leakage'],['Chương 3 · MLP và backpropagation','Giữ cách học, thêm tổng hợp hàng xóm'],['Chương 4 · CNN','Locality và chia sẻ trọng số trên graph'],['Chương 5 · Knowledge Graph, RAG','Phân biệt biểu diễn, học và truy xuất']],64,166,1152,372,[470,682],25);
  statement(s,'Cấu trúc dữ liệu thay đổi cách mô hình xử lý thông tin',565);
  foot(s,'Chương 2 đối chiếu Assignment2.pdf. Vị trí tài liệu chi tiết trong Notes.');break;
 case 3:
  text(s,'Nếu chỉ nhìn từng vector,\nta bỏ qua điều gì?',64,180,615,180,49,{bold:true});
  text(s,'Nội dung một bài báo\nchưa mô tả mạng trích dẫn của nó.',64,400,560,130,31,{color:C.muted});
  table(s,[['Đối tượng','Quan hệ có thể dùng'],['Bài báo','Trích dẫn'],['Người dùng, sản phẩm','Xem, mua, đánh giá'],['Nguyên tử','Liên kết hóa học']],725,180,490,337,[210,280],25);
  statement(s,'Graph hữu ích khi quan hệ mang tín hiệu phù hợp với bài toán',581);
  foot(s,'Chất lượng graph là một giả định cần kiểm chứng bằng baseline và thực nghiệm.');break;
 case 4:
  eq(s,'G = (V, E)',64,162,500,70,50);
  table(s,[['Ký hiệu','Ý nghĩa'],['V, E','Nút và cạnh'],['X','Đặc trưng từng nút'],['A','Ma trận kề'],['y','Nhãn cần dự đoán']],64,246,518,310,[145,373],26);
  label(s,'Ba khái niệm cần phân biệt',645,175,570);
  text(s,'GNN\nMô hình học biểu diễn trên graph',645,228,550,80,29);
  text(s,'Knowledge Graph\nBiểu diễn thực thể và quan hệ',645,345,550,80,29);
  text(s,'GraphRAG\nDùng graph trong truy xuất cho sinh văn bản',645,464,550,110,29);
  foot(s,'Demo dùng graph đồng nhất, vô hướng sau khi đối xứng hóa quan hệ trích dẫn.');break;
 case 5:
  table(s,[['Cấp độ','Đầu ra','Ví dụ'],['Nút','Một nhãn cho từng nút','Chủ đề bài báo trên Cora'],['Cạnh','Khả năng / loại liên kết','Tương tác người dùng–sản phẩm'],['Đồ thị','Một giá trị cho cả graph','Thuộc tính của một phân tử']],64,178,1152,334,[210,415,527],27,1);
  statement(s,'Thực nghiệm chính: phân loại nút trên Cora',557);
  foot(s,'Cấp độ dự đoán quyết định cách chia dữ liệu, loss và thước đo.');break;
 case 6:
  text(s,'Đổi ID nút, ý nghĩa của graph vẫn giữ nguyên',64,169,1100,68,35,{color:C.muted});
  eq(s,'f(PX, PAPᵀ) = P f(X, A)',100,289,1110,105,56);
  text(s,'Đầu ra theo nút đổi thứ tự tương ứng\nPermutation equivariance',64,440,680,108,30,{bold:true});
  text(s,'Số hàng xóm có thể thay đổi.\nPhép tổng hợp phải xử lý được tập\nkhông có thứ tự cố định.',790,437,424,146,27);
  foot(s,'P là ma trận hoán vị. Readout cho toàn graph thường cần tính invariant.');break;
 case 7:
  table(s,[['Khía cạnh','CNN trên ảnh','GNN trên graph'],['Lân cận','Cửa sổ trên lưới','Tập hàng xóm theo cạnh'],['Số phần tử','Theo kích thước kernel','Thay đổi theo nút'],['Trọng số','Dùng chung giữa vị trí','Dùng chung giữa nút'],['Cấu trúc','Tọa độ và trật tự không gian','Quan hệ, không có thứ tự nút tự nhiên']],64,175,1152,370,[260,410,482],26);
  statement(s,'Cùng khai thác locality, khác cách xác định lân cận',574);
  foot(s,'Cầu nối với Chương 4. GCN có định nghĩa phép tích chập riêng.');break;
 case 8:
  label(s,'THÔNG ĐIỆP',64,170,310);eq(s,'mᵤᵥ = M(hᵤ, hᵥ, eᵤᵥ)',402,161,785,68,41);
  label(s,'TỔNG HỢP',64,298,310);eq(s,'aᵥ = AGG { mᵤᵥ : u ∈ N(v) }',402,290,785,73,39);
  label(s,'CẬP NHẬT',64,426,310);eq(s,'h′ᵥ = U(hᵥ, aᵥ)',402,417,785,68,41);
  statement(s,'Một lớp nhận thông tin 1-hop; hai lớp mở rộng tới 2-hop',569);
  foot(s,'AGG có thể là sum, mean hoặc max. Các mô hình cụ thể chọn M và U khác nhau.');break;
 case 9:
  eq(s,'Hₗ₊₁ = σ(Â Hₗ Wₗ)',88,195,1110,110,67);
  table(s,[['Đại lượng','Vai trò'],['H₀ = X','Biểu diễn ban đầu của các nút'],['Â','Trộn thông tin theo graph đã chuẩn hóa'],['Wₗ','Biến đổi các chiều đặc trưng, dùng chung'],['σ','Hàm kích hoạt, ví dụ ReLU']],64,338,1152,247,[260,892],25);
  foot(s,'Nếu Â = I, bước trộn hàng xóm biến mất. Nguồn: Kipf & Welling, ICLR 2017.');break;
 case 10:
  eq(s,'Ã = A + I',64,170,520,85,52);
  text(s,'Self-loop giữ thông tin\ncủa chính nút.',64,278,500,130,34);
  eq(s,'Â = D̃^(−1/2) Ã D̃^(−1/2)',595,173,620,95,37);
  text(s,'D̃ dùng bậc sau self-loop.\nChuẩn hóa đóng góp theo\nbậc của cả hai đầu cạnh.',595,289,610,150,33);
  eq(s,'Âᵢⱼ = Ãᵢⱼ / √(d̃ᵢ d̃ⱼ)',64,497,1130,86,46);
  foot(s,'Chuẩn hóa đối xứng không phải trung bình cộng theo hàng.');break;
 case 11:
  eq(s,'A — B — C',64,165,500,65,44);
  text(s,'x = [2, 4, 6]       W = 1\nBậc sau self-loop: [2, 3, 2]',64,259,530,104,29);
  table(s,[['Ã','A','B','C'],['A','1','1','0'],['B','1','1','1'],['C','0','1','1']],64,397,472,198,[118,118,118,118],27);
  label(s,'Tính nút B',627,177,550);
  eq(s,'h′(B) = ReLU( 2/√6 + 4/3 + 6/√6 )',627,268,585,116,34);
  text(s,'4,599',627,421,570,100,75,{bold:true,color:C.teal});
  text(s,'Mean thông thường: 4',629,544,557,48,29,{color:C.muted});
  foot(s,'Ví dụ minh họa một lớp, một đặc trưng. Â tạo trọng số khác nhau theo bậc.');break;
 case 12:
  table(s,[['Tensor / trọng số','Kích thước'],['X','2708 × 1433'],['W₀','1433 × 32'],['H','2708 × 32'],['W₁','32 × 7'],['Z','2708 × 7']],64,172,510,362,[265,245],26);
  await img(s,'assets/gcn-figure.png',620,186,595,253,{alt:'Figure 1 GCN của Kipf và Welling, gồm kiến trúc và hình embedding của tác giả'});
  text(s,'H = ReLU(Â X W₀)\nZ = Â H W₁',630,473,580,110,37,{font:'Cambria Math',color:C.teal});
  foot(s,'Cross-entropy nhận logits Z. Softmax dùng khi hiển thị. Hình: Kipf & Welling (2017), Fig. 1.');break;
 case 13:
  text(s,'model.train()\noptimizer.zero_grad()\nlogits = model(x, edge_index)\nloss = F.cross_entropy(\n    logits[train_mask],\n    y[train_mask]\n)\nloss.backward()\noptimizer.step()',64,180,724,400,28,{font:'Consolas'});
  label(s,'Được học: W',835,184,380);
  text(s,'A và X cố định\ntrong thí nghiệm này.',835,237,380,103,29);
  label(s,'Chọn checkpoint',835,376,380);
  text(s,'Validation loss thấp nhất.\nTest sau khi đã chọn.',835,429,380,105,29);
  foot(s,'Gradient check bằng sai phân hữu hạn đạt. Logits NumPy/PyG lệch tối đa < 10⁻⁹ khi cùng trọng số.');break;
 case 14:
  table(s,[['Mô hình','Cách tổng hợp','Điểm cần chú ý'],['GCN','Trọng số theo bậc của graph','Công thức gọn, chuẩn hóa đối xứng'],['GraphSAGE','Học hàm tổng hợp đặc trưng','Có thể sampling và thiết kế inductive'],['GAT','Học attention giữa hàng xóm','Multi-head và hệ số phụ thuộc feature']],64,180,1152,351,[226,430,496],27);
  statement(s,'Kiến trúc phức tạp hơn chưa chắc cho kết quả cao hơn',580);
  foot(s,'Kipf & Welling (2017); Hamilton và cộng sự (2017); Veličković và cộng sự (2018).');break;
 case 15:
  eq(s,'h′ᵥ = σ( Wself hᵥ + Wnbr mean{hᵤ : u ∈ N(v)} )',64,169,1150,94,37);
  await img(s,'assets/sage-figure.png',99,276,1083,299,{alt:'Figure 1 của GraphSAGE: lấy mẫu, tổng hợp, dự đoán'});
  foot(s,'Hình: Hamilton và cộng sự (2017), Fig. 1. Thực nghiệm này dùng toàn bộ hàng xóm, transductive.');break;
 case 16:
  eq(s,'eᵢⱼ = LeakyReLU(aᵀ[Whᵢ ∥ Whⱼ])',64,176,610,107,31);
  eq(s,'αᵢⱼ = softmaxⱼ(eᵢⱼ)',64,319,610,65,41);
  eq(s,'h′ᵢ = σ(Σⱼ αᵢⱼ Whⱼ)',64,430,610,74,42);
  text(s,'Softmax theo lân cận của i.\nCode: 4 head × 8 chiều ở lớp ẩn.',64,558,1150,66,27);
  await img(s,'assets/gat-figure.png',715,184,500,319,{alt:'Figure 1 GAT minh họa attention và ba head, hình gốc của tác giả'});
  foot(s,'Hình gốc dùng 3 head để minh họa. Attention không tự động là giải thích nhân quả.');break;
 case 17:
  text(s,'2.708',64,170,340,78,63,{bold:true,color:C.teal});text(s,'bài báo',64,260,330,42,27);
  text(s,'5.278',442,170,340,78,63,{bold:true,color:C.teal});text(s,'cạnh vô hướng',442,260,345,42,27);
  text(s,'1.433',828,170,350,78,63,{bold:true,color:C.teal});text(s,'đặc trưng mỗi nút',828,260,385,42,27);
  table(s,[['Train','Validation','Test','Nhãn không dùng'],['140','500','1.000','1.068']],64,343,1152,150,[280,280,280,312],28);
  text(s,'3 split × 3 seed cho mỗi mạng. 7 chủ đề.\nTransductive: thấy X, A toàn graph; loss chỉ dùng nhãn train.',64,544,1150,82,28,{bold:true});
  foot(s,'Split tùy chỉnh 2026/2027/2028. Không đối chiếu trực tiếp với số trên public split Planetoid.');break;
 case 18:
  text(s,'Thiết lập chung cho các mạng',64,172,600,48,30,{bold:true});
  text(s,'Adam, lr = 0,01\nWeight decay = 0,0005\nHidden = 32, dropout = 0,5\nTối đa 300 epoch, patience = 60\nCheckpoint theo validation loss',64,255,610,262,29);
  text(s,'66 lần fit: 63 mạng + 3 LR',64,489,610,45,26,{bold:true,color:C.teal});
  table(s,[['Mạng 2 lớp','Tham số','Fit CPU (s)'],['MLP','46.080','3,03'],['GCN','46.080','4,55'],['GraphSAGE','92.160','19,48'],['GAT','46.158','4,32']],714,183,500,338,[194,157,149],24);
  statement(s,'Cùng protocol, chưa tune riêng từng kiến trúc',569);
  foot(s,'Runtime trung bình trong môi trường đã chạy. Bias tắt; GAT attention dropout = 0. Chi tiết trong Notes.');break;
 case 19:{
  const keys=['Logistic Regression','MLP-2','GCN-2','GraphSAGE-2','GAT-2'];
  bars(s,['LR','MLP','GCN','SAGE','GAT'],keys.map(k=>summary[k].accuracy_mean),64,183,610,364,2);
  table(s,[['Mô hình','Acc ± std (%)','Macro-F1 (%)'],...keys.map((k,j)=>[["LR","MLP","GCN","SAGE","GAT"][j],`${pct(summary[k].accuracy_mean)} ± ${pct(summary[k].accuracy_std)}`,pct(summary[k].macro_f1_mean)])],722,180,494,353,[115,233,146],23,3);
  statement(s,'GCN cao hơn MLP 19,91 điểm phần trăm',575);
  foot(s,'Mạng: 9 runs; LR: 3 runs. Std mô tả biến động, không phải khoảng tin cậy 95%.');break;}
 case 20:{
  const keys=['GCN-1','GCN-2','GCN-4','GCN-8'];
  bars(s,['1 lớp','2 lớp','4 lớp','8 lớp'],keys.map(k=>summary[k].accuracy_mean),64,181,690,372,1);
  table(s,[['Số lớp','Std (điểm %)'],...keys.map((k,j)=>[['1','2','4','8'][j],pct(summary[k].accuracy_std)])],841,196,375,291,[150,225],25);
  text(s,'Hai lớp tốt nhất\ntrong cấu hình đã chạy.',841,534,375,78,28,{bold:true,color:C.teal});
  foot(s,'Suy giảm accuracy chưa chứng minh riêng oversmoothing. Số tham số thay đổi theo độ sâu.');break;}
 case 21:
  table(s,[['Giai đoạn','Đầu vào / thao tác','Đầu ra'],['Huấn luyện offline','Python, Cora, split và optimizer','Weights, metrics, checkpoint'],['Đóng gói','Dữ liệu + trọng số cùng phiên bản','Các file JSON và mã JavaScript'],['Suy luận trong trình duyệt','X, A và GCN đã học','Dự đoán cho 2.708 nút'],['Hiển thị và đối chiếu','Chọn node, thay đổi cạnh','Lân cận tối đa 61 nút, baseline']],64,180,1152,352,[265,475,412],25);
  statement(s,'Web chạy GCN NumPy seed 42; bảng PyG là kết quả đã lưu',573);
  foot(s,'JavaScript và NumPy cho logits sai khác < 10⁻⁹ với cùng dữ liệu và trọng số.');break;
 case 22:
  await img(s,DEMO+'/results/demo-preview.png',64,164,810,463,{crop:{left:.04,top:.345,right:.025,bottom:.20},fit:'contain',alt:'Ứng dụng Deep Graph Lab hiển thị node 444191 và dự đoán'});
  label(s,'444191',923,186,294);text(s,'GCN đúng\nMLP sai',923,240,294,92,31,{bold:true});
  label(s,'158614',923,388,294);text(s,'GCN dự đoán sai\nNhãn thật: Theory',923,442,294,101,29);
  foot(s,'Mở đối chiếu để xem nhãn thật. Điểm softmax chưa được hiệu chỉnh thành độ tin cậy.');break;
 case 23:
  bars(s,['Graph gốc','Bỏ 100% cạnh'],[.382,.453],64,198,652,353,1,'Softmax: Neural Networks');
  text(s,'Paper 444191',792,177,420,46,31,{bold:true});
  text(s,'Giữ X và trọng số.\nBỏ 4 cạnh trực tiếp.\nTính lại chuẩn hóa và logits.',792,258,420,175,29);
  text(s,'Nhãn vẫn là\nNeural Networks',792,463,420,95,34,{bold:true,color:C.teal});
  text(s,'Trục dọc: điểm softmax của lớp Neural Networks',64,577,1145,40,24,{color:C.muted});
  foot(s,'Kiểm tra độ nhạy khi suy luận. Không huấn luyện lại, không kết luận quan hệ nhân quả.');break;
 case 24:{
  label(s,'Demo đã triển khai',64,172,1100);
  const link=text(s,'deep-graph-cora-lab.pinkwand512.chatgpt.site',64,228,1152,66,37,{bold:true,color:C.teal});
  link.text.get('deep-graph-cora-lab.pinkwand512.chatgpt.site').link={uri:'https://deep-graph-cora-lab.pinkwand512.chatgpt.site',isExternal:true};
  text(s,'Hiện ở chế độ private, cần tài khoản chủ sở hữu.',64,314,1145,50,27,{color:C.muted});
  label(s,'Dự phòng local · chạy từ thư mục demo',64,399,1100);
  text(s,'python -m http.server 8765 --directory dist\nMở http://localhost:8765',64,450,1152,89,29,{font:'Consolas'});
  text(s,'Tái chạy: research.py, split và checkpoint trong results/research',64,576,1150,43,26);
  foot(s,'Mã nguồn đầy đủ và hướng dẫn môi trường ở thư mục DeepGraph/demo.');break;}
 case 25:
  text(s,'Giới hạn của kết quả',64,171,610,54,34,{bold:true});
  text(s,'Cora nhỏ, tính homophily\nCạnh thiếu hoặc sai\nNhiều lớp có thể khó tối ưu\nGraph lớn cần kiểm soát chi phí',64,266,615,271,31);
  text(s,'Nối với chương 5',762,171,454,54,34,{bold:true});
  text(s,'Knowledge Graph tổ chức tri thức.\nGNN học biểu diễn từ graph.\nGraphRAG khai thác cấu trúc\ntrong truy xuất.',762,266,454,270,29);
  statement(s,'Hướng mở rộng: dự đoán quan hệ thiếu hoặc hệ gợi ý',579);
  foot(s,'Khả năng inductive, heterophily và quy mô lớn cần các thí nghiệm riêng.');break;
 case 26:
  text(s,'+19,91',64,183,675,126,91,{bold:true,color:C.teal});
  text(s,'điểm phần trăm accuracy\nGCN 2 lớp so với MLP 2 lớp',69,329,677,109,35);
  text(s,'Cora, 3 split\nCấu hình đã xác định\nKết quả có thể tái chạy',827,207,389,204,31);
  text(s,'Hỏi đáp',64,546,480,63,43,{bold:true});
  text(s,'Nếu graph có nhiều cạnh sai,\nta sẽ kiểm chứng ảnh hưởng như thế nào?',523,546,690,83,30);
  foot(s,'Nguồn chính: GCN (ICLR 2017), GraphSAGE (NIPS 2017), GAT (ICLR 2018). URL đầy đủ trong Notes.');break;
 }
}
await fs.mkdir('previews',{recursive:true});
await fs.writeFile('deck.json',JSON.stringify(P.toProto()));
await fs.writeFile('slides-notes.json',JSON.stringify(slides,null,2));
await (await PresentationFile.exportPptx(P)).save('candidate.pptx');
console.log('Draft exported. Slides:',slides.length,'Duration:',now);
for(let i=0;i<P.slides.items.length;i++){
 const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});
 await fs.writeFile(`previews/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
 console.log('Rendered',i+1);
}
await fs.writeFile('montage.webp',new Uint8Array(await(await P.export({format:'webp',montage:true,scale:.35})).arrayBuffer()));
if(process.argv.includes('--finalize')){
 const tableOwners=[2,4,5,7,9,11,12,14,17,18,19,20,21];
 const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:path.resolve('candidate.pptx'),finalPath:ROOT+'/output/Deep_Graph_26_Slides_Final.pptx',pythonExecutable:'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:26,requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:[19,20,23],requiredEmbeddedWorkbookChartOwnerSlides:[19,20,23],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:['Arial','Cambria Math','Consolas']},verifyArtifactToolImport:true,receiptPath:path.resolve('validation-final.json')});
 console.log(JSON.stringify(result));
}

