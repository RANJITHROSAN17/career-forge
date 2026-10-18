import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {JSDOM} from 'jsdom';
import {generateWriting} from '../bundle/ai.mjs';

test('fresh DOM: preset scan, custom input, all AI tabs, failure and recovery (mock host)',async()=>{
 const html=await readFile(new URL('../bundle/index.html',import.meta.url),'utf8');
 const dom=new JSDOM(html,{runScripts:'outside-only',url:'https://example.test/'});
 const w=dom.window;
 const requests=[];
 let deny=false;
 const anna={
  storage:{get:async()=>null,set:async()=>null},
  window:{set_title:async()=>null},
  tools:{invoke:async ({args})=>{
   requests.push(args);
   if(args.action==='get_state') return {data:{active_scan:null}};
   assert.equal(args.action,'analyze');
   return {data:{scan:{role_title:args.role_title,overall_score:65,sub_scores:{},matched_keywords:[],missing_keywords:[],top_priorities:[],section_checks:[]},stats:{},recent:[]}};
  }},
  llm:{complete:async(req)=>{
   if(deny) throw Error('LLM permission denied');
   const inputs=JSON.parse(req.messages[1].content);requests.push(inputs);
   let data;
   if(inputs.task==='rewrite_bullets') data={rewrites:[{original:'Built Python services.',xyz_rewrite:'Built Python services [add verified metric].',keyword_rewrite:'Python services <script>unsafe</script>'}]};
   if(inputs.task==='cover_letter') data={tone:inputs.tone,email_subject:'Application: Engineer',cover_letter:'Dear hiring team',linkedin_dm:'Hello recruiter'};
   if(inputs.task==='interview_prep') data={questions:Array.from({length:5},()=>({category:'Technical',question:'Explain a project',why_asked:'Depth',star_guide:{Situation:'Context',Task:'Goal',Action:'Steps',Result:'Verified result'}}))};
   return {content:{text:JSON.stringify(data)}};
  }}
 };
 w.generateWriting=generateWriting;w.AnnaAppRuntime={connect:async()=>anna};
 let js=await readFile(new URL('../bundle/app.js',import.meta.url),'utf8');
 js=js.replace(/^import .*;\n/gm,'');
 w.eval(js);
 const settle=()=>new Promise(r=>setImmediate(r));
 const click=async(id)=>{w.document.querySelector(id).click();await settle();};
 try {
  await settle();await settle();
  assert.equal(w.document.querySelector('#overall-score-val').textContent,'65%');
  assert.ok(w.document.querySelector('#bullets-list').textContent.includes('Click Generate'));
  await click('[data-preset="data-scientist"]');
  assert.ok(requests.at(-1).role_title.includes('Scientist'));
  await click('#clear-inputs-btn');
  for(const [id,value] of Object.entries({'role-input':'Custom Engineer','resume-input':'Built Python services.','jd-input':'Python and testing'})) w.document.getElementById(id).value=value;
  await click('#scan-btn');assert.equal(requests.at(-1).role_title,'Custom Engineer');
  await click('#run-bullets-btn');assert.ok(w.document.querySelector('#bullets-list').textContent.includes('[add verified metric]'));
  assert.equal(w.document.querySelector('#bullets-list script'),null);
  await click('#run-cover-btn');assert.ok(w.document.querySelector('#cover-output').textContent.includes('Hello recruiter'));
  await click('#run-interview-btn');assert.equal(w.document.querySelectorAll('.qa-card').length,5);
  deny=true;await click('#run-cover-btn');assert.ok(w.document.querySelector('#status-text').textContent.includes('permission denied'));
  assert.equal(w.document.querySelector('#run-cover-btn').disabled,false);
  deny=false;await click('#run-cover-btn');assert.ok(w.document.querySelector('#status-text').textContent.includes('generated'));
  assert.equal(w.document.querySelector('#ask-coach-btn'),null);
 } finally {dom.window.close();}
});
