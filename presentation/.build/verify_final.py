from pathlib import Path
from zipfile import ZipFile
import json,re,xml.etree.ElementTree as ET
root=Path(__file__).parent
pth=root.parent/'output'/'Deep_Graph_26_Slides_Final.pptx'
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
data=json.loads((root/'slides-notes.json').read_text(encoding='utf-8'))
with ZipFile(pth) as z:
    sl=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
    nt=[n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)]
    wk=[n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]
    assert len(sl)==26 and len(nt)==26
    assert len(wk)==3, wk
    for i,d in enumerate(data,1):
        tree=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
        txt='\n'.join(x.text or '' for x in tree.findall('.//a:t',ns))
        assert d['script'] in txt, (i,'script incomplete')
        assert d['action'] in txt and d['refs'] in txt
    for n in [19,20,23]:
        tree=ET.fromstring(z.read(f'ppt/slides/slide{n}.xml'))
        assert tree.find('.//c:chart',ns) is not None
print(json.dumps({'slides':len(sl),'complete_notes':len(nt),'embedded_workbooks':len(wk),'seconds_by_speaker':{str(n):sum(d['seconds'] for d in data if d['speaker']==n) for n in range(1,5)},'pptx_bytes':pth.stat().st_size}))
