import fs from 'node:fs';
import assert from 'node:assert/strict';
import {forecastAll} from './dist/inference.mjs';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function bin(path,Type){const b=fs.readFileSync(path);return new Type(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));}
const meta=read('dist/meta.json'),models=read('dist/models.json');
assert.equal(meta.run_id,'v2_160epochs_fullval');
for(const model of Object.values(models))assert.equal(model.run_id,meta.run_id);
const data={speed:bin('dist/speeds.f32',Float32Array),mask:bin('dist/observed.u8',Uint8Array),calendar:bin('dist/calendar.f32',Float32Array)};
let maximum=0,checked=0;
for(const row of read('results/browser_reference.json'))for(const [name,expected] of Object.entries(row.prediction)){
  const model=models[name==='gcn_identity'?'gcn_gru':name];
  const actual=forecastAll(meta,data,model,row.origin,name==='gcn_gru');
  const err=Math.max(...actual.map((v,i)=>Math.abs(v-expected[i])));maximum=Math.max(maximum,err);
  assert.ok(err<0.001,`${name}: ${err} mph`);
  checked+=actual.length;
}
console.log(JSON.stringify({checked,max_error_mph:maximum,passed:true}));
