import test from 'node:test';
import assert from 'node:assert/strict';
import { generateWriting, parseWritingResult } from '../bundle/ai.mjs';
const cover = {tone:'modern',email_subject:'Application',cover_letter:'Dear team',linkedin_dm:'Hello'};
const rewrite = {rewrites:[{original:'Built Python services.',xyz_rewrite:'Built Python services, improving [add verified metric].',keyword_rewrite:'Python: built services.'}]};
const interview = {questions:Array.from({length:5},()=>({category:'Technical',question:'How would you test this?',why_asked:'Checks depth',star_guide:{Situation:'Describe context',Task:'State goal',Action:'Describe actions',Result:'Give verified outcome'}}))};
for (const [action, data] of Object.entries({rewrite_bullets:rewrite, cover_letter:cover, interview_prep:interview})) {
  test(`${action}: calls Anna and validates result`, async () => {
    let request;
    const anna = {llm:{complete:async req => {request=req;return {content:{text:JSON.stringify(data)}};}}};
    const result = await generateWriting(anna,action,{resume_text:'Built Python services.',job_description:'Python',role_title:'Engineer'});
    assert.ok(result);
    assert.equal(request.maxTokens,4000);
    assert.ok(request.messages[0].content.includes('Never invent'));
    assert.equal(JSON.parse(request.messages[1].content).resume_text,'Built Python services.');
  });
}
test('accepts fenced JSON',()=>assert.deepEqual(parseWritingResult('cover_letter','```json\n'+JSON.stringify(cover)+'\n```'),cover));
test('rejects malformed, partial and empty results',()=>{
 for (const text of ['not JSON','{}','{"questions":[]}']) assert.throws(()=>parseWritingResult('interview_prep',text));
 assert.throws(()=>parseWritingResult('cover_letter','{}'));
 assert.throws(()=>parseWritingResult('rewrite_bullets','{"rewrites":[]}'));
});
test('unavailable, denied and truncated LLM are errors, never templates',async()=>{
 await assert.rejects(generateWriting(null,'cover_letter',{}),/unavailable/);
 await assert.rejects(generateWriting({llm:{complete:async()=>{throw Error('Permission denied');}}},'cover_letter',{}),/Permission denied/);
 await assert.rejects(generateWriting({llm:{complete:async()=>({stopReason:'max_tokens'})}},'cover_letter',{}),/truncated/);
});
test('manifest grants LLM and no chat; buttons removed',async()=>{
 const {readFile}=await import('node:fs/promises');
 const manifest=JSON.parse(await readFile(new URL('../manifest.json',import.meta.url),'utf8'));
 assert.deepEqual(manifest.ui.host_api.llm,['complete']);
 assert.deepEqual(manifest.ui.host_api.chat,[]);
 const html=await readFile(new URL('../bundle/index.html',import.meta.url),'utf8');
 assert.ok(!/pin-artifact-btn|ask-coach-btn/.test(html));
 const js=await readFile(new URL('../bundle/app.js',import.meta.url),'utf8');
 assert.ok(!/anna.chat|renderBulletsFromScan/.test(js));
 for(const action of ['rewrite_bullets','cover_letter','interview_prep']) assert.ok(js.includes(`callWritingAI("${action}"`));
});
