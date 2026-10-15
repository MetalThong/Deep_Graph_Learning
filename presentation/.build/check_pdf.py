from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image
root=Path(__file__).parent
pdf=root.parent/'output'/'Loi_Thuyet_Trinh_4_Nguoi.pdf'
reader=PdfReader(pdf)
print('PAGES',len(reader.pages))
for i,page in enumerate(reader.pages):
    t=page.extract_text()
    print(i+1, len(t),repr(t[:125]))
dest=root/'pdf-preview';dest.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(pdf)
for i,page in enumerate(doc):
    page.render(scale=1.35).to_pil().save(dest/f'page-{i+1:02d}.png')
for start in range(0,len(doc),6):
    sheet=Image.new('RGB',(900,1914),'#D5DFDA')
    for j in range(min(6,len(doc)-start)):
        im=Image.open(dest/f'page-{start+j+1:02d}.png');im.thumbnail((445,633))
        sheet.paste(im,((j%2)*450,(j//2)*638))
    sheet.save(dest/f'contact-{start+1:02d}.png')
