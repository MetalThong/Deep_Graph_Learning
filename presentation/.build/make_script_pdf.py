from pathlib import Path
import json, html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

root=Path(__file__).parent
slides=json.loads((root/'slides-notes.json').read_text(encoding='utf-8'))
out=root.parent/'output'/'Loi_Thuyet_Trinh_4_Nguoi.pdf'
pdfmetrics.registerFont(TTFont('ArialVN','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialVNBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('ArialVN',normal='ArialVN',bold='ArialVNBold',italic='ArialVN',boldItalic='ArialVNBold')
ink=colors.HexColor('#102E33');teal=colors.HexColor('#087F78');muted=colors.HexColor('#52696D')
styles={
 'title':ParagraphStyle('Title',fontName='ArialVNBold',fontSize=25,leading=31,textColor=ink,spaceAfter=18),
 'h1':ParagraphStyle('H1',fontName='ArialVNBold',fontSize=17,leading=22,textColor=ink,spaceAfter=10),
 'h2':ParagraphStyle('H2',fontName='ArialVNBold',fontSize=10.5,leading=15,textColor=teal,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('Body',fontName='ArialVN',fontSize=10.8,leading=15.3,textColor=ink,spaceAfter=8),
 'small':ParagraphStyle('Small',fontName='ArialVN',fontSize=9.1,leading=12.8,textColor=muted,spaceAfter=6),
 'source':ParagraphStyle('Source',fontName='ArialVN',fontSize=7.6,leading=10.5,textColor=muted,spaceAfter=3,wordWrap='CJK'),
 'cell':ParagraphStyle('Cell',fontName='ArialVN',fontSize=10.2,leading=14,textColor=ink),
 'cellhead':ParagraphStyle('CellHead',fontName='ArialVNBold',fontSize=10.2,leading=14,textColor=colors.white),
}
def p(text,style='body'):
    return Paragraph(html.escape(text).replace('\n','<br/>'),styles[style])
def time(n):return f'{n//60:02d}:{n%60:02d}'
def header(c,doc):
    c.saveState();c.setFont('ArialVN',8.5);c.setFillColor(muted)
    c.drawString(42,A4[1]-27,'DEEP GRAPH LEARNING  /  KỊCH BẢN TRÌNH BÀY')
    c.drawRightString(A4[0]-42,24,f'{doc.page}')
    c.drawString(42,24,'Phát triển hệ thống thông minh · Trần Đình Quế')
    c.restoreState()
story=[p('Deep Graph Learning\nLời thuyết trình cho 4 người','title'),
 p('26 slide · 37 phút trình bày + 3 phút hỏi đáp','h1'),
 p('Bản này đi cùng PowerPoint và chứa cùng lời nói trong phần Notes. Tên thành viên chưa được cung cấp, nên các phần dùng tên Thành viên 1–4. Nhóm thay bằng tên thật khi phân công. Thời lượng là mốc tập luyện dự kiến, đã dành thời gian cho thao tác demo và tương tác với lớp.'),Spacer(1,14)]
rows=[['Người','Slide','Thời lượng','Mốc thời gian'],['Thành viên 1','1–6','8 phút','00:00–08:00'],['Thành viên 2','7–13','10 phút','08:00–18:00'],['Thành viên 3','14–20','10 phút','18:00–28:00'],['Thành viên 4','21–26','9 phút','28:00–37:00'],['Cả nhóm','Hỏi đáp','3 phút','37:00–40:00']]
t=Table([[p(x,'cellhead' if r==0 else 'cell') for x in row] for r,row in enumerate(rows)],colWidths=[125,80,110,190],hAlign='LEFT')
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),ink),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D5DFDA')),('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.extend([t,Spacer(1,19),p('Cách dùng khi tập nói','h2'),p('Đọc phần lời nói để nắm mạch, sau đó tập giải thích bằng cách diễn đạt của mình. Các đoạn “Thao tác và nhịp trình bày” và “Chuyển tiếp” dành cho người trình bày, không đọc nguyên văn cho lớp. Người tiếp theo nên có mặt ở vị trí sẵn sàng trước mốc chuyển phần.'),
 p('Chuẩn bị demo','h2'),p('Mở sẵn ứng dụng và thử hai mã 444191, 158614. Link triển khai đang private, cần tài khoản chủ sở hữu. Chạy sẵn bản local bằng python -m http.server 8765 --directory dist trong thư mục demo và mở http://localhost:8765. Các số liệu thực nghiệm đã nằm trong slide, không cần huấn luyện lại trên lớp.'),
 p('Mã nguồn, dữ liệu, checkpoint và hướng dẫn: D:\\School\\PT HTTM\\DeepGraph\\demo','small'),PageBreak()])
for i,s in enumerate(slides):
    story += [p(f'{i+1:02d}. {s["title"]}','h1'),p(f'Thành viên {s["speaker"]}  |  {s["seconds"]} giây  |  Mốc {time(s["start"])}–{time(s["end"])}','small')]
    for para in s['script'].split('\n\n'):story.append(p(para))
    story += [p('Thao tác và nhịp trình bày','h2'),p(s['action'],'small'),p('Chuyển tiếp','h2'),p(s['transition'],'small'),p('Nguồn đối chiếu','h2'),p(s['refs'],'source'),PageBreak()]

qa=[
('Vì sao thấy node test trong graph mà vẫn được coi là đánh giá hợp lệ?', 'Vì protocol là transductive: được dùng X và A của toàn graph, chỉ dùng nhãn train trong loss. Validation chọn checkpoint. Test chỉ đánh giá sau đó. Nếu mục tiêu là các nút chưa xuất hiện hoặc dự đoán tương lai, phải thiết kế inductive hoặc temporal split tương ứng.', 'Thành viên 3'),
('Tại sao không so trực tiếp với accuracy trong bài báo GCN?', 'Nhóm dùng split tùy chỉnh, cách đối xứng hóa và siêu tham số được ghi trong code. Khác split có thể khác độ khó. Muốn so trực tiếp phải thống nhất dữ liệu, tiền xử lý, split, ngân sách tìm siêu tham số và cách tổng hợp kết quả.', 'Thành viên 3'),
('GAT mới hơn, tại sao kết quả thấp hơn GCN?', 'Đã đo dưới một cấu hình chung, chưa tune riêng từng kiến trúc. Attention làm tăng khả năng biểu diễn nhưng không đảm bảo cải thiện trên mọi dữ liệu. Kết quả này chỉ xác nhận GCN có trung bình cao nhất trong các lần chạy hiện tại.', 'Thành viên 3'),
('GCN 8 lớp thất bại có chứng minh oversmoothing không?', 'Chưa. Accuracy thấp có thể liên quan cả tối ưu, dropout, biểu diễn và cấu hình. Cần đo tương đồng embedding, phân tích gradient hoặc learning curve, rồi thử các thay đổi có kiểm soát để phân biệt nguyên nhân.', 'Thành viên 2 hoặc 3'),
('GraphSAGE có phải mô hình duy nhất xử lý được nút mới?', 'Không. GraphSAGE nhấn mạnh học hàm tổng hợp có thể áp dụng cho nút mới và cơ chế sampling. Một phép GCN cũng có thể áp dụng với đặc trưng và cấu trúc mới nếu hệ thống và protocol phù hợp. Demo hiện tại chưa đánh giá inductive cho bất kỳ mô hình nào.', 'Thành viên 2 hoặc 3'),
('Vì sao bỏ cạnh mà điểm softmax lại tăng?', 'Mỗi hàng xóm có thể đóng góp tín hiệu khác nhau. Bỏ cạnh còn làm thay đổi chuẩn hóa theo bậc. Ở node 444191, điểm Neural Networks tăng nhưng đó là một trường hợp với trọng số cố định. Không thể suy ra rằng bỏ cạnh nói chung làm mô hình tốt hơn.', 'Thành viên 4'),
('Trọng số nào được học? Có học ma trận A không?', 'Trong mô hình đang chạy, X và A cố định, optimizer học các ma trận biến đổi W và tham số attention nếu là GAT. GAT học hệ số attention trên những cạnh được xét, không đồng nghĩa học tự do toàn bộ cấu trúc A.', 'Thành viên 2'),
('Số 5.278 cạnh khác một số tài liệu Cora là do đâu?', 'Đây là số cạnh vô hướng duy nhất sau xử lý của code hiện tại. Quan hệ hai chiều được lưu thành 10.556 cạnh có hướng trước self-loop. Số được trích ở nguồn khác có thể dùng quy tắc đếm hoặc tiền xử lý khác. Cần xem chính file và quy trình thay vì so các số rời rạc.', 'Thành viên 1 hoặc 3'),
('Có chứng minh GNN luôn tốt hơn MLP không?', 'Không. Chênh lệch 19,91 điểm phần trăm là kết quả trên Cora trong protocol đã nêu. Muốn kết luận rộng hơn cần thêm dữ liệu, nhiều điều kiện graph và ngân sách tune hợp lý. Graph có cạnh sai hoặc heterophily có thể khiến tổng hợp lân cận không phù hợp.', 'Thành viên 3'),
('Website đang chạy mô hình gì, có gọi API không?', 'JavaScript chạy GCN hai lớp với trọng số từ NumPy seed42, split2026. Nó tải file dữ liệu và trọng số tĩnh, không gọi API LLM. MLP/LR dùng dự đoán đã lưu để đối chiếu. Bảng PyG là báo cáo từ thực nghiệm offline.', 'Thành viên 4'),
('Mean ± std có phải khoảng tin cậy 95% không?', 'Không. Std ở đây là numpy.std với ddof=0 qua các runs. Các split có thể trùng node. Báo cáo này mô tả biến động theo split và khởi tạo, chưa cung cấp phép suy luận thống kê về mọi dataset.', 'Thành viên 3'),
('Nếu có thêm thời gian, nhóm sẽ nghiên cứu gì?', 'Ưu tiên một thay đổi có giả thuyết rõ: thêm dataset có heterophily, hoặc đánh giá inductive, hoặc kiểm tra tỷ lệ cạnh nhiễu với nhiều seed. Giữ nguyên nguyên tắc chọn mô hình bằng validation và chỉ báo cáo test sau khi đã chốt cấu hình.', 'Cả nhóm')
]
for start in (0,6):
    story.append(p(f'Câu hỏi phản biện ({start//6+1}/2)','h1'))
    for j,(q,a,who) in enumerate(qa[start:start+6],start+1):
        story.append(KeepTogether([p(f'{j}. {q}','h2'),p(a,'body'),p(f'Người trả lời gợi ý: {who}','small')]))
    if start==0:story.append(PageBreak())
doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=52,bottomMargin=44,title='Deep Graph Learning - Lời thuyết trình cho 4 người',author='Nhóm thuyết trình Deep Graph')
doc.build(story,onFirstPage=header,onLaterPages=header)
print(out)
