import fs from 'node:fs';
import {featureProjection,infer,removeIncidentEdges} from '../../demo/dist/gnn.mjs';
const d=JSON.parse(fs.readFileSync('../../demo/dist/data.json','utf8'));
const w=JSON.parse(fs.readFileSync('../../demo/dist/weights.json','utf8'));
const x=featureProjection(d.features,w.w1);
const orig=infer(x,d.edges,w,d.ids.length);
for(const id of ['444191','158614']){
 const node=d.ids.findIndex(v=>String(v)===id);
 if(node<0)throw new Error('ID missing');
 const r=removeIncidentEdges(d.edges,node,1);
 const changed=infer(x,r.edges,w,d.ids.length);
 console.log(JSON.stringify({id,true:d.classes[d.labels[node]],gcn:d.classes[orig.predictions[node]],mlp:d.classes[d.mlp[node]],lr:d.classes[d.lr[node]],softmax:Math.max(...orig.probabilities[node]),removed:r.removed,afterClass:d.classes[changed.predictions[node]],after:Math.max(...changed.probabilities[node])}));
}
