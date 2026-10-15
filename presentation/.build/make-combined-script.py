from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether, HRFlowable

B=Path(__file__).resolve().parent
ROOT=B.parents[0]
DATA=json.loads((B/'combined-content.json').read_text(encoding='utf8'))
OUT=ROOT/'output'/'Deep_Graph_Traffic_Bitcoin_Kich_Ban_4_Nguoi.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
regular=Path('C:/Windows/Fonts/arial.ttf');bold=Path('C:/Windows/Fonts/arialbd.ttf')
if not regular.exists(): regular=Path('C:/Windows/Fonts/calibri.ttf');bold=Path('C:/Windows/Fonts/calibrib.ttf')
pdfmetrics.registerFont(TTFont('Body',str(regular)));pdfmetrics.registerFont(TTFont('Body-Bold',str(bold)))
INK=colors.HexColor('#163B3B');TEAL=colors.HexColor('#087E73');MUTED=colors.HexColor('#657B79');PALE=colors.HexColor('#E8F0EB');LINE=colors.HexColor('#D7E1D9')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('CoverTitle',fontName='Body-Bold',fontSize=25,leading=31,textColor=INK,spaceAfter=7*mm))
styles.add(ParagraphStyle('DeckSub',fontName='Body',fontSize=12,leading=18,textColor=MUTED,spaceAfter=5*mm))
styles.add(ParagraphStyle('H1X',fontName='Body-Bold',fontSize=19,leading=24,textColor=INK,spaceBefore=3*mm,spaceAfter=4*mm,keepWithNext=True))
styles.add(ParagraphStyle('H2X',fontName='Body-Bold',fontSize=12.3,leading=16,textColor=TEAL,spaceBefore=3*mm,spaceAfter=1.5*mm,keepWithNext=True))
styles.add(ParagraphStyle('BodyX',fontName='Body',fontSize=10.3,leading=15,textColor=INK,spaceAfter=2.1*mm))
styles.add(ParagraphStyle('SmallX',fontName='Body',fontSize=8.4,leading=11.5,textColor=MUTED,spaceAfter=1.2*mm))
styles.add(ParagraphStyle('LabelX',fontName='Body-Bold',fontSize=9.3,leading=12,textColor=TEAL,spaceBefore=1*mm,spaceAfter=.5*mm))
styles.add(ParagraphStyle('TableHeadX',fontName='Body-Bold',fontSize=9.2,leading=12,textColor=colors.white))
styles.add(ParagraphStyle('TableX',fontName='Body',fontSize=9,leading=12,textColor=INK))

def clean(t):
    s=str(t)
    for ch in ['–','—','−','‐','‑']: s=s.replace(ch,'-')
    return escape(s).replace('\n','<br/>')
def para(t,style='BodyX'): return Paragraph(clean(t),styles[style])
def clock(n): return f'{n//60:02d}:{n%60:02d}'
def page(canvas,doc):
    canvas.saveState();w,h=A4
    if doc.page>1:
        canvas.setStrokeColor(LINE);canvas.setLineWidth(.6);canvas.line(18*mm,h-15*mm,w-18*mm,h-15*mm)
        canvas.setFont('Body-Bold',8);canvas.setFillColor(TEAL);canvas.drawString(18*mm,h-11.5*mm,'DEEP GRAPH  /  KỊCH BẢN 4 NGƯỜI')
    canvas.setStrokeColor(LINE);canvas.setLineWidth(.6);canvas.line(18*mm,14*mm,w-18*mm,14*mm)
    canvas.setFont('Body',8);canvas.setFillColor(MUTED);canvas.drawString(18*mm,9*mm,'Phát triển hệ thống thông minh · METR-LA + Elliptic');canvas.drawRightString(w-18*mm,9*mm,str(doc.page));canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=22*mm,bottomMargin=19*mm,title='Deep Graph - kịch bản thuyết trình hai demo',author='Nhóm sinh viên')
story=[Spacer(1,16*mm),para('DEEP GRAPH LEARNING','CoverTitle'),para('Kịch bản thuyết trình 4 người<br/>Dự báo giao thông + sàng lọc giao dịch Bitcoin','DeckSub'),HRFlowable(width='100%',thickness=2,color=TEAL,spaceBefore=2*mm,spaceAfter=5*mm),para('38 phút trình bày + 2 phút hỏi đáp','H1X'),para('Mỗi thành viên nhận đúng 8 slide và 9 phút 30 giây. Hai người đầu trình bày lý thuyết; người thứ ba chạy demo giao thông; người thứ tư chạy demo Elliptic. Lời nói trong tài liệu cũng được đặt trong Speaker Notes của PowerPoint.','BodyX')]
grid=[[para('Người','TableHeadX'),para('Phần phụ trách','TableHeadX'),para('Slide','TableHeadX'),para('Thời lượng','TableHeadX')]]
for s in DATA['speakers']: grid.append([para(s['name'].split(' · ')[0],'TableX'),para(s['name'].split(' · ')[1],'TableX'),para(s['slides'],'TableX'),para('9 phút 30 giây','TableX')])
t=Table(grid,colWidths=[27*mm,81*mm,28*mm,37*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('GRID',(0,0),(-1,-1),.6,LINE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE])]))
story += [t,Spacer(1,5*mm),para('Cách dùng','H2X'),para('Đọc để hiểu ý, sau đó kể bằng lời tự nhiên. Dòng “Thao tác” là chỉ dẫn cho người nói, không đọc thành lời. Chờ lớp trả lời ở các ví dụ rồi mới mở nhãn thực tế. Nếu website yêu cầu tài khoản hoặc mạng không ổn định, dùng bản local đã đóng gói.','BodyX'),para('Demo giao thông · https://traffic-graph-lab-v2.fitdace1.chatgpt.site<br/>Offline · giải nén traffic rồi mở RUN_DEMO.cmd','SmallX'),para('Demo Elliptic · https://elliptic-transaction-lab.pinkwand512.chatgpt.site<br/>Offline · chạy elliptic/start_demo.ps1','SmallX'),para('Thời lượng tổng','H2X'),para('Người 1: 00:00-09:30 · Người 2: 09:30-19:00 · Người 3: 19:00-28:30 · Người 4: 28:30-38:00 · hỏi đáp: 38:00-40:00.','BodyX'),PageBreak()]

elapsed=0
for si,sp in enumerate(DATA['speakers']):
    who=si+1;chosen=[(idx,x) for idx,x in enumerate(DATA['slides'],1) if x['speaker']==who];start=elapsed
    story += [para(f"{sp['name']}  ·  Slide {sp['slides']}",'H1X'),para(f"Thời lượng: 9 phút 30 giây  ·  Mốc tổng: {clock(start)}-{clock(start+570)}",'SmallX')]
    for idx,d in chosen:
        st=elapsed;elapsed+=d['seconds']
        block=[para(f"Slide {idx:02d}  ·  {clock(st)}-{clock(elapsed)}  ·  {d['seconds']} giây",'LabelX'),para(d['title'],'H2X'),para(d['script'],'BodyX')]
        for item in d.get('items',[]): block.append(para('• '+item,'SmallX'))
        if d.get('table'):
            for row in d['table']: block.append(para(' | '.join(row),'SmallX'))
        if d.get('action'): block += [para('Thao tác','LabelX'),para(d['action'],'SmallX')]
        if d.get('transition'): block += [para('Chuyển tiếp','LabelX'),para(d['transition'],'SmallX')]
        if d.get('refs'): block += [para('Nguồn','LabelX'),para(d['refs'],'SmallX')]
        block.append(HRFlowable(width='100%',thickness=.5,color=LINE,spaceBefore=2*mm,spaceAfter=2*mm))
        story.append(KeepTogether(block))
    if si<3: story.append(PageBreak())

story += [PageBreak(),para('Ôn nhanh lý thuyết','H1X'),para('Mạch 5 chương trong môn học','H2X')]
course=[('Chương 1 · Hệ thống thông minh','Model chỉ là một phần. Hệ thống nhận thông tin từ môi trường, biểu diễn trạng thái, học hoặc suy luận, ra quyết định và tạo đầu ra.'),('Chương 2 · Dữ liệu và biểu diễn','Feature cần đúng ý nghĩa và thời điểm. Tiền xử lý, scaler và split là một phần của thực nghiệm; scaler chỉ học từ train.'),('Chương 3 · Mạng neural','Mạng học nhiều lớp biểu diễn bằng loss và backpropagation. Deep Graph đổi cấu trúc thông tin đầu vào và phép tổng hợp, không đổi nguyên lý supervised.'),('Chương 4 · CNN','CNN dùng vùng cục bộ và trọng số chia sẻ trên lưới ảnh. GNN giữ ý tưởng cục bộ nhưng thay lưới bằng quan hệ cạnh.'),('Chương 5 · Knowledge Graph + RAG','KG lưu tri thức thành bộ ba chủ thể-quan hệ-đối tượng. RAG truy xuất đoạn văn bản, dựng ngữ cảnh rồi gọi LLM. GNN học biểu diễn/dự đoán trên graph; vai trò khác nhưng có thể kết hợp.')]
for h,b in course: story += [para(h,'H2X'),para(b,'BodyX')]
story += [para('Từ vựng cần nhớ','H2X'),para('Node/nút: đối tượng. Edge/cạnh: quan hệ. Feature: đầu vào. Label: nhãn. Message passing: gửi, thu, tổng hợp, cập nhật thông tin lân cận. GCN: tổng hợp chuẩn hóa. GraphSAGE: lấy mẫu hàng xóm và học hàm tổng hợp. GAT: học trọng số attention. Inductive: áp dụng quy tắc cho nút mới nếu feature và lân cận sẵn có. Transductive: dự đoán trên graph đã biết.','BodyX')]

story += [PageBreak(),para('Kết quả và câu hỏi phản biện','H1X'),para('Traffic · METR-LA','H2X'),para('Giữ nguyên 5,629 km/h MAE; GRU 4,875 ± 0,002; GCN + GRU 4,844 ± 0,009. Graph chỉ cải thiện khoảng 0,64% so với GRU trong cấu hình này. Với nhãn +15 phút dưới 30 km/h, MAE GCN + GRU khoảng 12,217 km/h. Một ca có dữ liệu cũ 9 giờ 45 phút và sai số trên 100 km/h. Cảnh báo freshness nêu chất lượng đầu vào, không phải độ tin cậy.','BodyX'),para('Elliptic · giao dịch Bitcoin','H2X'),para('F1 trung bình ba seed: RF local 77,0%; RF all 79,3%; MLP 64,5%; GCN 61,3%. RF all nhận thêm 72 feature tổng hợp hàng xóm. Có false positive, false negative và 157.205 giao dịch unknown. Điểm neural chưa được hiệu chỉnh thành xác suất. Bản kết quả dùng lại test cũ sau khi phiên bản trước xem test, nên đây là đánh giá hồi cứu.','BodyX')]
for qa in DATA['q_and_a']: story += [para(qa['q'],'H2X'),para(qa['a'],'BodyX')]
story += [para('Nguồn môn học và thực nghiệm','H2X'),para('D:/School/PT HTTM/Chương1/Slide1.pdf; Chương2/Assignment2.pdf; Chương3/Slide3.pdf; Chương4/Slide4.pdf; Chương5/Slide5.pdf. Traffic: traffic/results/metrics.json. Elliptic: elliptic/results/metrics.json, elliptic/README.md.','SmallX')]
doc.build(story,onFirstPage=page,onLaterPages=page)
print(json.dumps({'path':str(OUT),'bytes':OUT.stat().st_size,'speakers':len(DATA['speakers']),'slides':len(DATA['slides']),'total_talk_seconds':elapsed},ensure_ascii=False))
