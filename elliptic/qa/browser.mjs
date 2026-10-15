import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const manifest=JSON.parse(await fs.readFile('../site/dist/data/manifest.json','utf8'));
const cases=Object.fromEntries(manifest.cases.map(c=>[c.key,c]));
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
await page.goto('http://127.0.0.1:8767');await page.waitForFunction(()=>window.ellipticDemo,{timeout:30000});
const first=await page.evaluate(()=>window.ellipticDemo.getState());assert.equal(first.id,cases.detected.id);assert(first.score>=first.threshold);assert(Math.abs(first.score-cases.detected.scores.gcn)<2e-5);
await page.locator('#workspace').scrollIntoViewIfNeeded();await page.screenshot({path:'desktop.png',fullPage:true});await page.locator('.workbench').screenshot({path:'workspace.png'});
await page.locator('#reveal').click();assert.equal(await page.locator('#truth').innerText(),'Nhãn tham chiếu: illicit');
for(const key of ['false_alarm','missed','disagree','unknown']){
 const c=cases[key];await page.getByRole('button',{name:c.title,exact:true}).click();await page.waitForFunction(id=>window.ellipticDemo.getState().id===id,c.id);const state=await page.evaluate(()=>window.ellipticDemo.getState());
 if(key==='missed')assert(state.score<state.threshold);if(key==='false_alarm')assert(state.score>=state.threshold);
 await page.locator('#reveal').click();const truth=await page.locator('#truth').innerText();assert.equal(truth,c.label<0?'Unknown: chưa có nhãn để xác nhận':`Nhãn tham chiếu: ${c.label===1?'illicit':'licit'}`);
 if(key==='false_alarm')await page.locator('.workbench').screenshot({path:'false-alarm.png'});
}
for(const model of ['rf_all','gcn']){
 await page.locator('#model').selectOption(model);const original=await page.locator('#threshold-stats').innerText();
 for(const threshold of [.1,.5,.95]){
  await page.locator('#threshold').evaluate((el,t)=>{el.value=String(t);el.dispatchEvent(new Event('input',{bubbles:true}))},threshold);
  let tp=0,fp=0,fn=0;manifest.test_scores.labels.forEach((y,i)=>{const q=manifest.test_scores.scores[model][i]>=threshold;if(q){y===1?tp++:fp++;}else if(y===1)fn++;});
  const actual=(await page.locator('#threshold-stats b').allTextContents()).slice(0,3).map(s=>Number(s.replaceAll('.','')));assert.deepEqual(actual,[tp,fp,fn]);
 }
 await page.locator('#reset-threshold').click();assert.equal(await page.locator('#threshold-stats').innerText(),original);
}
await page.locator('#tx-search').fill('999999999999');await page.locator('#search').click();assert.match(await page.locator('#search-error').innerText(),/Không tìm/);
await page.locator('#hops').selectOption('1');await page.locator('#graph .node').last().click();
for(const step of ['35','42','49']){await page.locator('#step').selectOption(step);await page.waitForFunction(s=>window.ellipticDemo.getState().step===Number(s),step);}
await page.getByRole('button',{name:cases.detected.title,exact:true}).click();await page.waitForFunction(id=>window.ellipticDemo.getState().id===id,cases.detected.id);await page.locator('#hops').selectOption('2');await page.locator('.workbench').screenshot({path:'workspace.png'});
assert.match(await page.locator('#optimization').innerText(),/test cũ/);
await page.setViewportSize({width:390,height:844});await page.screenshot({path:'mobile.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
await page.goto('http://127.0.0.1:8767/optimization.html');assert.match(await page.locator('h1').innerText(),/F1/);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
for(const file of ['Elliptic_Deep_Graph_26_Slides.pptx','Elliptic_Loi_Thuyet_Trinh_Va_Demo.pdf','Elliptic_Tai_Lieu_Hoc_3_Ngay.pdf']){const res=await page.request.get('http://127.0.0.1:8767/downloads/'+file);assert.equal(res.status(),200);}
await fs.writeFile('browser-report.json',JSON.stringify({passed:!errors.length,revision:2,errors,checks:['initial neural inference','all five cases','exact reference labels','false positive and false negative','unknown handling','model switch','threshold counts independently recomputed','reset threshold','invalid search','hop control','node click','snapshot switch','optimization disclosure','mobile overflow','learning downloads'],first},null,2));assert.deepEqual(errors,[]);await browser.close();console.log('Browser checks passed');
