from pathlib import Path
import json, html, shutil
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

R=Path(__file__).resolve().parent;D=json.loads((R/'presentation/.build/content.json').read_text(encoding='utf-8'));OUT=R/'output/V2';OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
ink=HexColor('#182B2D');teal=HexColor('#16796F');muted=HexColor('#5B6F71');paper=HexColor('#F4F3ED')
styles={
 'title':ParagraphStyle('title',fontName='Arial-Bold',fontSize=31,leading=39,textColor=ink,spaceAfter=24),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=20,leading=27,textColor=ink,spaceAfter=16),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=12,leading=17,textColor=teal,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='Arial',fontSize=11.2,leading=16.4,textColor=ink,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=9,leading=13,textColor=muted,spaceAfter=7),
 'quote':ParagraphStyle('quote',fontName='Arial',fontSize=11.3,leading=16.7,textColor=ink,spaceAfter=8),
}
def clean(s):return s.replace('–','-').replace('—','-').replace('‑','-')
def para(s,key='body'):return Paragraph(html.escape(clean(s)).replace('\n','<br/>'),styles[key])
def page(c,doc):
 w,h=A4;c.saveState();c.setFillColor(paper);c.rect(0,0,w,h,fill=1,stroke=0);c.setFont('Arial',8);c.setFillColor(muted);c.drawString(48,h-29,'ELLIPTIC / DEEP GRAPH / PHÁT TRIỂN HỆ THỐNG THÔNG MINH');c.setStrokeColor(HexColor('#D5DDDA'));c.line(48,40,w-48,40);c.drawString(48,25,'Dữ liệu lịch sử. Kết quả thực nghiệm của nhóm.');c.drawRightString(w-48,25,str(doc.page));c.restoreState()
def doc(path,story,title):
 d=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=57,bottomMargin=55,title=title,author='Deep Graph study project')
 d.build(story,onFirstPage=page,onLaterPages=page)
 print(path.name,len(PdfReader(path).pages),'pages')
def cover(title,subtitle,details):
 return [Spacer(1,76),para('ELLIPTIC BITCOIN','h2'),para(title,'title'),para(subtitle,'h1'),Spacer(1,16),*[para(t) for t in details],Spacer(1,26),para('Demo online','h2'),Paragraph(f'<link href="{D["url"]}" color="#16796F">{D["url"]}</link>',styles['small']),PageBreak()]
def sources():
 out=[para('Nguồn và cách kiểm tra số liệu','h1')]
 for s in D['sources']:out.extend([para(s['title'],'h2'),Paragraph(f'<link href="{s["url"]}" color="#16796F">{s["url"]}</link>',styles['small'])])
 out.extend([para('Kết quả do nhóm chạy','h2'),para('results/data_summary.json: số nút, nhãn, split và SHA-256 của CSV. results/metrics.json: chỉ số, ngưỡng, seed và giao thức. results/demo_cases.json: ví dụ thật. qa/metrics-integrity.json: kiểm tra lại số liệu. qa/inference-parity.json: đối chiếu suy luận web và Python.'),para('Phân biệt nguồn và đóng góp','h2'),para('Elliptic cung cấp dữ liệu và bài toán. Code huấn luyện, cách chia validation, mô hình gọn, demo, slide và tài liệu trong bộ này là phần triển khai cho bài học. Không tuyên bố tái lập nguyên vẹn kết quả bài báo. Hình minh họa và ví dụ được ghi rõ trong slide.'),para('Cách chạy local','h2'),para('Mở PowerShell tại thư mục elliptic rồi chạy:\npython -m http.server 8767 --bind 127.0.0.1 --directory site/dist\nMở http://127.0.0.1:8767\nDừng server bằng Ctrl+C.'),para('Bản demo online','h2'),para('Site được triển khai riêng tư cho tài khoản chủ site. Nếu cần trình chiếu trên máy khác, hãy đăng nhập bằng tài khoản có quyền hoặc dùng bản local đã kèm. Việc thay đổi quyền chia sẻ cần thực hiện riêng.')])
 return out

study=cover('Tài liệu học\ntrong 3 ngày','Dành cho người trực tiếp demo',[
 'Mục tiêu: hiểu bài toán, chạy demo bảy phút và trả lời những câu hỏi cơ bản mà không đọc thuộc lòng.',
 'Mỗi ngày khoảng ba giờ. Ngày 1: dữ liệu và graph. Ngày 2: mô hình và đánh giá. Ngày 3: thao tác và phản biện.',
 'Bản cập nhật: '+'. '.join(D['slides'][25]['body'])+'. Test cũ được dùng để đánh giá lại.'])
for ch in D['study']:
 study.append(para(ch['title'],'h1'))
 for sec in ch['sections']:study.extend([para(sec['heading'],'h2'),para(sec['text'])])
 study.append(PageBreak())
study+=sources();doc(OUT/'Elliptic_Tai_Lieu_Hoc_3_Ngay.pdf',study,'Elliptic - Tài liệu học 3 ngày')

script=cover('Lời thuyết trình\nvà kịch bản demo','26 slide / một người trình bày',[
 'Thời lượng gợi ý: 38 phút, đã bao gồm bảy phút demo. Có thể dành thêm hai phút hỏi đáp để thành buổi 40 phút.',
 'Đọc để hiểu ý, sau đó kể lại bằng lời của mình. Phần Notes trong PowerPoint có cùng lời nói và chỉ dẫn thao tác.',
 'Nếu chỉ phụ trách demo, ưu tiên slide 4, 6, 13, 16, 20-24 và kịch bản bảy phút ở cuối tài liệu.'])
elapsed=0
for i,s in enumerate(D['slides']):
 if i%2==0 and i:script.append(PageBreak())
 mm=lambda v:f'{v//60:02d}:{v%60:02d}'
 script.extend([para(f"Slide {i+1:02d} / {s['title'].replace(chr(10),' ')}",'h1'),para(f"Mốc {mm(elapsed)} - {mm(elapsed+s['seconds'])} / {s['seconds']} giây",'small'),para(s['script'],'quote'),para('Thao tác: '+s['action'],'small'),Spacer(1,12)])
 elapsed+=s['seconds']
script.append(PageBreak());demo=D['study'][7];script.append(para('Kịch bản thao tác bảy phút','h1'))
for sec in demo['sections']:script.extend([para(sec['heading'],'h2'),para(sec['text'])])
script.append(PageBreak());script+=sources();doc(OUT/'Elliptic_Loi_Thuyet_Trinh_Va_Demo.pdf',script,'Elliptic - Lời thuyết trình và demo')

# Native HTML reading material is also available beside the deployed demo.
parts=['<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Elliptic · Học và demo trong 3 ngày</title><link rel="stylesheet" href="style.css"></head><body><header><a class="brand" href="index.html"><span class="brand-icon">E</span><strong>ELLIPTIC LAB</strong></a><a href="index.html">Trở về demo</a></header><main class="learn"><p class="eyebrow">TÀI LIỆU CHO NGƯỜI DEMO</p><h1>Hiểu bài toán.<br>Tự tin trình diễn.</h1><p>Ba ngày chuẩn bị, một kịch bản bảy phút. Tài liệu dựa trên thực nghiệm của bộ code đi kèm.</p><p><a href="downloads/Elliptic_Tai_Lieu_Hoc_3_Ngay.pdf">Tải tài liệu 3 ngày (PDF)</a> · <a href="downloads/Elliptic_Loi_Thuyet_Trinh_Va_Demo.pdf">Lời thuyết trình (PDF)</a> · <a href="downloads/Elliptic_Deep_Graph_26_Slides.pptx">26 slide (PowerPoint)</a></p>']
for ch in D['study']:
 parts.append('<section><h2>'+html.escape(ch['title'])+'</h2>')
 for sec in ch['sections']:parts.append('<h3>'+html.escape(sec['heading'])+'</h3><p>'+html.escape(sec['text'])+'</p>')
 parts.append('</section>')
parts.append('<h2>Lời nói theo 26 slide</h2>')
for i,s in enumerate(D['slides']):parts.append('<details><summary>'+html.escape(f"{i+1:02d}. {s['title']}")+'</summary><p>'+html.escape(s['script'])+'</p><p><strong>Thao tác:</strong> '+html.escape(s['action'])+'</p></details>')
parts.append('<h2>Nguồn</h2><ul>'+''.join(f'<li><a href="{s["url"]}">{s["title"]}</a></li>' for s in D['sources'])+'</ul></main></body></html>')
(R/'site/dist/learn.html').write_text('\n'.join(parts),encoding='utf-8')
(R/'site/dist/downloads').mkdir(exist_ok=True)
for p in OUT.glob('*.pdf'):shutil.copy2(p,R/'site/dist/downloads'/p.name)
