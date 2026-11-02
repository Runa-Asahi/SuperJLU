const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const lines=fs.readFileSync('jlu_toolkit/ui_page.py','utf8').split('\n');
const names=['function academicTime(','function academicCard(','function startAcademicRecalculation(','async function submitAcademicRecalculation(','async function updateAcademicData(','async function pollAcademicRecalculation('];
const code=lines.filter(l=>names.some(p=>l.startsWith(p))).join('\n');
async function check(){
 let state='running',scheduled=0;const calls=[],dialog={open:false,showModal(){this.open=true},close(){this.open=false}};
 const c=vm.createContext({D:{academic_meta:{local_synced_at:'2026-11-01T17:35:54',school_calculated_at:'2026-11-01 17:35:24',cached_calculated_at:'OLD',checked_at:'CHECK_ONLY'}},
  esc:s=>String(s),academicBusy:false,academicJob:{state:'idle'},academicNotice:null,academicUpdating:false,academicPollTimer:null,bootRefreshing:false,
  $:()=>dialog,renderProgress(){},renderAll(){},gradeRefreshSnapshot:(a,b)=>b,
  setTimeout:()=>{scheduled++;return 1},clearTimeout(){},
  api:async(path,body)=>{calls.push({path,body});return path==='/api/data'||path==='/api/academic/refresh'?{academic_meta:{}}:{state,message:'synthetic'}}});
 vm.runInContext(code,c);
 assert.equal(c.academicTime('2026-11-01T17:35:54'),'2026-11-01 17:35:54');
 assert.equal(c.academicTime('2026-11-01 17:35:24'),'2026-11-01 17:35:24');
 assert.equal(c.academicTime('garbage'),'暂无记录');assert.equal(c.academicTime(null),'暂无记录');
 let card=c.academicCard();assert.ok(!card.includes('最近核对时间')&&!card.includes('CHECK_ONLY'));
 assert.match(card,/从教务更新/);assert.match(card,/教务已有新的计算结果/);
 c.startAcademicRecalculation();assert.equal(calls.length,0);assert.equal(dialog.open,true);
 dialog.close();assert.equal(calls.length,0);
 c.startAcademicRecalculation();await c.submitAcademicRecalculation();assert.equal(dialog.open,false);
 assert.equal(calls[0].body.confirmed,true);assert.equal(c.academicBusy,true);assert.equal(scheduled,1);
 await c.submitAcademicRecalculation();assert.equal(calls.filter(x=>x.body).length,1);
 state='success';await c.pollAcademicRecalculation();assert.equal(c.academicBusy,false);
 assert.equal(calls.at(-1).path,'/api/data');assert.equal(c.PROG_ERR,'');assert.match(c.academicCard(),/data-state="success"/);
 calls.length=0;await c.updateAcademicData();assert.equal(calls.length,1);assert.equal(calls[0].path,'/api/academic/refresh');
 assert.equal(c.academicNotice.state,'success');assert.equal(c.academicBusy,false);
 assert.ok(!calls.some(x=>x.path==='/api/refresh'||x.path==='/api/academic/recalculate'));
 console.log('Academic UI: readable dates, native-style dialog, explicit submit, prominent status and academic-only manual update passed.');
}
check().catch(e=>{console.error(e);process.exitCode=1});
