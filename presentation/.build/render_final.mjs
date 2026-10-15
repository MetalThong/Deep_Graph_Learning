import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('../output/Deep_Graph_26_Slides_Final.pptx'));
await fs.mkdir('final-previews',{recursive:true});
for(let i=0;i<p.slides.items.length;i++){
 const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(`final-previews/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await b.arrayBuffer()));
}
console.log('Final PPTX: 26 slides reimported and rendered');
