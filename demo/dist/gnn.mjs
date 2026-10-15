// The same two-layer GCN as train.py. Labels are never used in inference.
export function adjacency(n, edges) {
  const neighbors = Array.from({length:n}, (_,i)=>[i]);
  for(const [u,v] of edges) { neighbors[u].push(v); neighbors[v].push(u); }
  return neighbors.map(ns => ns.map(j=>[j,1/Math.sqrt(ns.length*neighbors[j].length)]));
}
function aggregate(values, adj, width) {
  const out=new Float64Array(values.length);
  for(let i=0;i<adj.length;i++) for(const [j,scale] of adj[i])
    for(let k=0;k<width;k++) out[i*width+k]+=scale*values[j*width+k];
  return out;
}
export function featureProjection(features, w1) {
  const width=w1[0].length, out=new Float64Array(features.length*width);
  for(let i=0;i<features.length;i++) for(const f of features[i])
    for(let k=0;k<width;k++) out[i*width+k]+=w1[f][k]/Math.max(features[i].length,1);
  return out;
}
export function infer(projected, edges, weights, n) {
  const h=weights.w1[0].length, c=weights.w2[0].length, adj=adjacency(n,edges);
  const hidden=aggregate(projected,adj,h);
  for(let i=0;i<hidden.length;i++) hidden[i]=Math.max(0,hidden[i]);
  const nodeLogits=new Float64Array(n*c);
  for(let i=0;i<n;i++) for(let k=0;k<h;k++) for(let j=0;j<c;j++)
    nodeLogits[i*c+j]+=hidden[i*h+k]*weights.w2[k][j];
  const logits=aggregate(nodeLogits,adj,c), predictions=[], probabilities=[];
  for(let i=0;i<n;i++) {
    const row=Array.from(logits.slice(i*c,(i+1)*c)), max=Math.max(...row);
    const exp=row.map(z=>Math.exp(z-max)), sum=exp.reduce((a,b)=>a+b,0);
    probabilities.push(exp.map(z=>z/sum)); predictions.push(row.indexOf(max));
  }
  return {logits,predictions,probabilities};
}
export function removeIncidentEdges(edges,node,fraction) {
  const incident=edges.filter(([a,b])=>a===node||b===node);
  const count=Math.round(incident.length*fraction);
  const removed=new Set(incident.slice(0,count));
  return {edges:edges.filter(e=>!removed.has(e)),removed:count};
}
