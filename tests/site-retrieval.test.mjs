import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,writeFile,copyFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {retrieve,prepare} from '../site/api/context.mjs';
const docs=JSON.parse(await readFile(new URL('../site/knowledge/battery.json',import.meta.url),'utf8'));
test('retrieval finds direction-specific limits and preserves the failed measured evidence',()=>{
 const a=retrieve('Can cells charge during module discharge? What limits apply?',docs);
 assert.ok(a.some(x=>x.id==='limits'));
 const b=retrieve('Is the battery safe and validated by numerical verification?',docs);
 assert.ok(b.some(x=>x.id==='scope'&&x.text.includes('missed all 12')));
});
test('compact context preserves selected numerical result, editable identities and source scope',()=>{
 const out=prepare(JSON.stringify({context:{editable_design:{cells:[{id:'cell1',name:'Cell 1',charge_pct:70}],connections:[],output:{}},test:{id:'historical',software_hash:'old',summary:{metrics:{minimum_voltage_V:3.524959,peak_temperature_C:27.37}},rows:new Array(300).fill({}),trace:[{time_s:0}]}},conversation:[{role:'user',content:'Explain the lowest voltage and temperature'}]}),docs);
 assert.equal(out.context.test.summary.metrics.minimum_voltage_V,3.52496);
 assert.equal(out.context.editable_design.cells[0].id,'cell1');
 assert.equal(out.context.test.software_hash,'old');
 assert.equal(out.context.test.rows,undefined);
 assert.ok(out.retrieved_sources.length>0);
});
test('Groq route keeps the secret server-side, attaches sources and refuses malformed output',async()=>{
 const dir=await mkdtemp(path.join(tmpdir(),'vf-groq-test-')),previous=process.env.GROQ_API_KEY,fetcher=globalThis.fetch;
 await writeFile(path.join(dir,'package.json'),'{"type":"module"}');
 await writeFile(path.join(dir,'_prompt.js'),'export const SYSTEM="Test system";export const SCHEMA={properties:{actions:{items:{properties:{op:{enum:["set_load"]},target:{type:"string"}}}}}};');
 await writeFile(path.join(dir,'_knowledge.js'),'export const KNOWLEDGE='+JSON.stringify(docs)+';');
 for(const name of ['ai.js','context.mjs'])await copyFile(new URL('../site/api/'+name,import.meta.url),path.join(dir,name));
 const {default:handler}=await import(pathToFileURL(path.join(dir,'ai.js')));
 const prompt=JSON.stringify({context:{},conversation:[{role:'user',content:'Explain the Pi load assumptions'}]});
 let sent,mode='ok';process.env.GROQ_API_KEY='synthetic-test-secret';
 globalThis.fetch=async(url,options)=>{sent={url,headers:options.headers,body:JSON.parse(options.body)};return {ok:mode==='ok',status:mode==='quota'?429:200,json:async()=>({choices:[{message:{content:JSON.stringify(mode==='bad'?{message:'wrong'}:{message:'25 W is the supply-rating scenario [pi].',actions:[]})}}]})};};
 const invoke=async()=>{let out={};const res={setHeader(){},status(code){out.code=code;return this;},json(body){out.body=body;return this;}};await handler({method:'POST',headers:{host:'example.com',origin:'https://example.com','x-forwarded-for':String(Math.random())},body:{prompt}},res);return out;};
 try{
 const ok=await invoke();assert.equal(ok.code,200);assert.equal(sent.url,'https://api.groq.com/openai/v1/chat/completions');
 assert.equal(sent.headers.Authorization,'Bearer synthetic-test-secret');assert.ok(sent.body.response_format.json_schema.schema.properties.actions.items.properties.target.enum.includes('cell1'));assert.ok(!sent.body.response_format.json_schema.schema.properties.actions.items.properties.target.enum.includes('Cell 1'));assert.equal(sent.body.response_format.json_schema.strict,true);
 assert.ok(ok.body.sources.some(s=>s.id==='pi'));assert.ok(!JSON.stringify(ok).includes('synthetic-test-secret'));
 mode='bad';assert.equal((await invoke()).code,502);
 mode='quota';assert.equal((await invoke()).code,429);
 }finally{globalThis.fetch=fetcher;if(previous===undefined)delete process.env.GROQ_API_KEY;else process.env.GROQ_API_KEY=previous;}
});
