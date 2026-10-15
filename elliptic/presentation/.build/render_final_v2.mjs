import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root=path.resolve('../..');
const P=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/V2/Elliptic_Deep_Graph_26_Slides.pptx')));
const baseline=JSON.parse(await fs.readFile(path.join(root,'qa/v1-preview-hashes.json'),'utf8'));
await fs.mkdir('v2-final-previews',{recursive:true});const rows=[];
for(let i=0;i<P.slides.items.length;i++){
 const name=`slide-${String(i+1).padStart(2,'0')}.png`;
 const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});const bytes=new Uint8Array(await blob.arrayBuffer());
 const sha=crypto.createHash('sha256').update(bytes).digest('hex');
 await fs.writeFile(path.join('v2-final-previews',name),bytes);
 const draftSha=crypto.createHash('sha256').update(await fs.readFile(path.join('previews',name))).digest('hex');
 rows.push({slide:i+1,file:name,sha256:sha,matchesDraft:sha===draftSha,changedFromV1:sha!==baseline[name]});
 console.log('Final slide',i+1,'changed',sha!==baseline[name]);
}
await fs.writeFile('final-render-report-v2.json',JSON.stringify({slideCount:rows.length,allMatchDraft:rows.every(r=>r.matchesDraft),changedSlides:rows.filter(r=>r.changedFromV1).map(r=>r.slide),slides:rows},null,2));
