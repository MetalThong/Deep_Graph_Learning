// Full-graph parity between Python training and browser inference.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {featureProjection,infer,removeIncidentEdges} from './dist/gnn.mjs';
const read=path=>JSON.parse(fs.readFileSync(new URL(path,import.meta.url),'utf8'));
const data=read('./dist/data.json'),weights=read('./dist/weights.json');
const expected=read('./results/reference_logits.json').flat();
const projected=featureProjection(data.features,weights.w1);
const actual=infer(projected,data.edges,weights,data.ids.length);
let maxError=0;
for(let i=0;i<expected.length;i++)maxError=Math.max(maxError,Math.abs(expected[i]-actual.logits[i]));
assert(maxError<1e-10,`GCN parity failed: ${maxError}`);
const node=data.examples.gcn_correct_mlp_wrong;
const removed=removeIncidentEdges(data.edges,node,1);
assert(removed.removed>0);
assert(!removed.edges.some(([a,b])=>a===node||b===node));
const isolated=infer(projected,removed.edges,weights,data.ids.length);
const h=weights.w1[0].length,c=weights.w2[0].length;
for(let j=0;j<c;j++){
  let sum=0;for(let k=0;k<h;k++)sum+=Math.max(0,projected[node*h+k])*weights.w2[k][j];
  assert(Math.abs(sum-isolated.logits[node*c+j])<1e-10);
}
console.log(JSON.stringify({nodes:data.ids.length,maxLogitError:maxError,isolatedNodeCheck:'passed',removedEdges:removed.removed}));
