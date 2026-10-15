import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {buildGraph,infer} from './site/dist/inference.mjs';
const base=new URL('./site/dist/data/',import.meta.url),weights=JSON.parse(await fs.readFile(new URL('weights.json',base),'utf8'));
const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',base),'utf8'));
let comparisons=0,maxError=0;const perStep=[];
for(let step=35;step<=49;step++){
 const s=JSON.parse(await fs.readFile(new URL(`snapshot-${step}.json`,base),'utf8'));
 const b=await fs.readFile(new URL(`snapshot-${step}.bin`,base));const x=new Float32Array(b.buffer,b.byteOffset,b.byteLength/4),rows=buildGraph(s.ids.length,s.src,s.dst);
 for(const m of ['gcn','mlp']){const p=infer(x,rows,weights[m],m==='gcn');let err=0,mismatches=0;for(let i=0;i<p.length;i++){assert(Number.isFinite(p[i]));err=Math.max(err,Math.abs(p[i]-s.scores[m][i]));if((Number(p[i].toFixed(6))>=manifest.runs[m].threshold)!==(s.scores[m][i]>=manifest.runs[m].threshold))mismatches++;}assert(err<2e-5,`${m} t${step}: ${err}`);assert.equal(mismatches,0,`${m} t${step}: decision mismatch`);comparisons+=p.length;maxError=Math.max(maxError,err);perStep.push({step,model:m,n:p.length,max_error:err,decision_mismatches:mismatches});}
}
const result={passed:true,comparisons,max_error:maxError,tolerance:2e-5,per_step:perStep};await fs.writeFile(new URL('./qa/inference-parity.json',import.meta.url),JSON.stringify(result,null,2));console.log(JSON.stringify({passed:true,comparisons,maxError}));
