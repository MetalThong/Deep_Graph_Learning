import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';

const deck=await PresentationFile.importPptx(await FileBlob.load('../output/Deep_Graph_Traffic_Bitcoin_32_Slides.pptx'));
const dir='combined-final-previews';
await fs.mkdir(dir,{recursive:true});
for(let i=0;i<deck.slides.items.length;i++){
  const blob=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
  await fs.writeFile(`${dir}/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
}
console.log(`Final PPTX: ${deck.slides.items.length} slides reimported and rendered`);
