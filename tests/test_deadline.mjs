import test from 'node:test';
import assert from 'node:assert/strict';
import {withDeadline} from '../bundle/async.mjs';
test('never-settling bridge requests release busy state at deadline', async()=>{
 let busy=true;
 try {await assert.rejects(withDeadline(()=>new Promise(()=>{}),10,'Host timed out'),/Host timed out/);}
 finally {busy=false;}
 assert.equal(busy,false);
});
test('normal and rejected calls preserve their results',async()=>{
 assert.equal(await withDeadline(()=>42,100,'timeout'),42);
 await assert.rejects(withDeadline(()=>{throw Error('denied');},100,'timeout'),/denied/);
});
test('late host completion cannot replace a timeout result',async()=>{
 let finish;
 const result=withDeadline(()=>new Promise(resolve=>{finish=resolve;}),10,'timeout');
 await assert.rejects(result,/timeout/);
 finish('late result');
 await assert.rejects(result,/timeout/);
});
