from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import pypdfium2 as pdfium
from pypdf import PdfReader

root = Path(__file__).parent / 'assets'
def download(item):
    name, aid = item
    target = root / f'{name}.pdf'
    if not target.exists():
        urllib.request.urlretrieve('https://arxiv.org/pdf/' + aid, target)
    reader = PdfReader(target)
    matches = []
    for i, page in enumerate(reader.pages):
        if 'Figure 1:' in page.extract_text():
            matches.append(i)
    doc = pdfium.PdfDocument(target)
    for i in matches[:1]:
        page = doc[i]
        page.render(scale=1.7).to_pil().save(root / f'{name}-page.png')
        print(name, 'page', i+1, 'size', page.get_size(), flush=True)
    return name
with ThreadPoolExecutor(max_workers=3) as pool:
    print(list(pool.map(download, [('gcn','1609.02907'),('sage','1706.02216'),('gat','1710.10903')])))
