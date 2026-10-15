// PyTorch-compatible GRU inference. All weights come from training checkpoints.
const sigmoid=x=>1/(1+Math.exp(-x));
const dot=(w,x)=>{let s=0;for(let j=0;j<w.length;j++)s+=w[j]*x[j];return s;};
export function forecastSensor(meta,data,model,origin,node,graph=true){
  const w=model.weights,H=model.hidden,S=model.spatial,N=meta.nodes.length;
  let h=new Float64Array(H),last=0;
  for(let t=origin-11;t<=origin;t++){
    const at=t*N+node,own=[(data.speed[at]-meta.mean)/meta.std,data.mask[at]];
    let near=own;
    if(graph){near=[0,0];for(const [j,a] of meta.rows[node]){
      const k=t*N+j;near[0]+=a*(data.speed[k]-meta.mean)/meta.std;near[1]+=a*data.mask[k];
    }}
    const raw=[...own,...near],x=new Float64Array(S+4);
    for(let j=0;j<S;j++)x[j]=Math.max(0,dot(w['spatial.weight'][j],raw)+w['spatial.bias'][j]);
    for(let j=0;j<4;j++)x[S+j]=data.calendar[t*4+j];
    const gi=new Float64Array(3*H),gh=new Float64Array(3*H);
    for(let j=0;j<3*H;j++){
      gi[j]=dot(w['gru.weight_ih_l0'][j],x)+w['gru.bias_ih_l0'][j];
      gh[j]=dot(w['gru.weight_hh_l0'][j],h)+w['gru.bias_hh_l0'][j];
    }
    const next=new Float64Array(H);
    for(let j=0;j<H;j++){
      const r=sigmoid(gi[j]+gh[j]),z=sigmoid(gi[H+j]+gh[H+j]);
      const candidate=Math.tanh(gi[2*H+j]+r*gh[2*H+j]);
      next[j]=(1-z)*candidate+z*h[j];
    }
    h=next;last=own[0];
  }
  return (last+dot(w['head.weight'][0],h)+w['head.bias'][0])*meta.std+meta.mean;
}
export function forecastAll(meta,data,model,origin,graph=true){
  return Float64Array.from(meta.nodes,(_,i)=>forecastSensor(meta,data,model,origin,i,graph));
}
