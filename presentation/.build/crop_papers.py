from pathlib import Path
import pypdfium2 as pdfium
root=Path(__file__).parent/'assets'
for name,page_idx,crop in [('gcn',3,(108,562,108,80)),('sage',1,(107,604,107,50)),('gat',3,(107,520,107,75))]:
    doc=pdfium.PdfDocument(root/f'{name}.pdf')
    doc[page_idx].render(scale=4,crop=crop).to_pil().save(root/f'{name}-figure.png')
    print(name)
