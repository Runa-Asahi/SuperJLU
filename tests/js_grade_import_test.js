// Run with node tests/js_grade_import_test.js. Only synthetic transcript data.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const page=fs.readFileSync('jlu_toolkit/ui_page.py','utf8');
const helpers='// Grade calculation helpers:'+page.split('// Grade calculation helpers:')[1].split('// Grade rendering')[0];
const imports=page.slice(page.indexOf('let gradeImporting=false;'),page.indexOf('async function switchGradeSource'));
const local={grade_source:'import',grade_filename:'synthetic.xlsx',grades:[{key:'local'}],grade_notes:[],has_imported_grades:true};
const remote={grade_source:'jwxt',grades:[{key:'remote'}],courses:[{name:'updated timetable'}]};
async function main(){
 const events={},messages=[],calls=[];
 let active=true,allowConfirm=true,pending=null;
 const elements={
  '#grade-import':{disabled:false,textContent:''},'#grade-file':{value:''},
  '#grade-sync-status':{textContent:''},'#t-cj':{classList:{contains:()=>active}}
 };
 const ctx=vm.createContext({Array,Promise,console,
  D:{grade_source:'jwxt',grades:[]},dirty:false,gradeSyncing:false,gradeSessionState:'expired',
  $:selector=>elements[selector],document:{addEventListener:(event,handler)=>events[event]=handler},
  toast:(message,error)=>messages.push({message,error}),confirm:()=>allowConfirm,
  FileReader:class{readAsDataURL(){this.result='data:application/octet-stream;base64,c3ludGhldGlj';this.onload()}},
  api:(path,body)=>{calls.push({path,body});return pending||Promise.resolve({...local})},
  renderAll:()=>{},resetGradeFilters:()=>{}
 });
 vm.runInContext(helpers+imports,ctx);
 assert.match(ctx.gradeStatusText(local,'expired'),/无需登录/);
 for(const state of ['missing','expired'])assert.match(ctx.gradeStatusText(remote,state),/仍可导入/);
 const merged=ctx.gradeRefreshSnapshot(local,remote);
 assert.equal(merged.grades,local.grades);
 assert.equal(merged.grade_source,'import');
 assert.equal(merged.courses,remote.courses);
 assert.equal(remote.grade_source,'jwxt'); // No mutation of the response.
 assert.equal(ctx.gradeRefreshSnapshot(remote,remote),remote);
 function event(files,types=['Files'],target='page-margin'){
  return {target:{id:target},dataTransfer:{types,files},prevented:false,preventDefault(){this.prevented=true}};
 }
 const file={name:'synthetic.xlsx',size:100};
 // Margins, header and grade content all reach the same single document handler.
 for(const target of ['page-margin','header','t-cj']){
  ctx.D={grade_source:'jwxt',grades:[]};
  const drag=event([file],['Files'],target);events.dragover(drag);
  assert.equal(drag.prevented,true);assert.equal(drag.dataTransfer.dropEffect,'copy');
  const drop=event([file],['Files'],target),before=calls.length;
  await events.drop(drop);
  assert.equal(drop.prevented,true);assert.equal(calls.length,before+1);
  assert.equal(ctx.D.grade_source,'import');
  assert.match(elements['#grade-sync-status'].textContent,/无需登录/);
 }
 active=false;
 const elsewhere=event([file]);await events.drop(elsewhere);
 assert.equal(elsewhere.prevented,true);assert.match(messages.at(-1).message,/切换到/);
 const rejected=event([file]);events.dragover(rejected);assert.equal(rejected.dataTransfer.dropEffect,'copy');
 active=true;
 const before=calls.length;
 const text=event([],['text/plain']);events.drop(text);events.dragover(text);assert.equal(text.prevented,false);
 await events.drop(event([file,file]));assert.match(messages.at(-1).message,/一份/);
 await events.drop(event([{name:'invalid.pdf',size:100}]));assert.match(messages.at(-1).message,/xlsx/);
 await events.drop(event([{name:'large.xlsx',size:5*1024*1024+1}]));assert.match(messages.at(-1).message,/5 MB/);
 allowConfirm=false;await events.drop(event([file]));assert.equal(calls.length,before);
 allowConfirm=true;ctx.D={grade_source:'jwxt',grades:[]};
 let resolve;pending=new Promise(done=>resolve=done);
 const first=events.drop(event([file]));await Promise.resolve();
 assert.equal(elements['#grade-import'].disabled,true);
 await events.drop(event([file]));assert.match(messages.at(-1).message,/正在导入/);
 resolve({...local});await first;pending=null;assert.equal(calls.length,before+1);
 assert.equal(elements['#grade-import'].disabled,false);
 // A session response arriving after a local import must not start an automatic sync.
 const load=page.split('\n').find(line=>line.startsWith('async function load(){'));
 for(const state of ['missing','expired','ok']){
  let sessionResolve,refreshes=0,opened=0;
  const loaded=vm.createContext({D:null,gradeSessionState:'unknown',gradeImporting:false,gradeSyncing:false,
   week:1,Math,Date,Promise,$:()=>({textContent:''}),
   api:path=>path==='/api/data'?Promise.resolve({...remote,needs_bootstrap:true}):new Promise(done=>sessionResolve=done),
   weekOf:()=>1,maxWeek:()=>16,renderAll:()=>{},rdToWeek:()=>{},lgInfo:()=>{},renderSession:()=>{},
   openLogin:()=>opened++,fullRefresh:()=>refreshes++,refreshGradeData:()=>refreshes++});
  vm.runInContext(helpers+load,loaded);
  await loaded.load();
  if(state==='ok')loaded.D={...local};
  sessionResolve({state,logged_in:state==='ok',needs_login:state!=='ok'});
  await Promise.resolve();await Promise.resolve();
  assert.equal(refreshes,0);assert.equal(opened,0);
 }
 // loadSubs must appear before fullRefresh so isolated extracts / early calls see it.
 const loadSubsAt=page.indexOf('async function loadSubs(');
 const fullRefreshAt=page.indexOf('async function fullRefresh(');
 assert.ok(loadSubsAt!==-1&&fullRefreshAt!==-1&&loadSubsAt<fullRefreshAt,'loadSubs must be defined before fullRefresh');
 // A successful full refresh (including the one after login) updates the other
 // modules while retaining the imported transcript and unsaved selection.
 const refresh=page.split('\n').find(line=>line.startsWith('async function fullRefresh('));
 let loadSubsCalls=0;
 const refreshed=vm.createContext({D:{...local},dirty:true,bootRefreshing:false,
  $:()=>({innerHTML:'refresh',disabled:false}),window:{__rm:1},
  setSyncInd:()=>{},
  api:async()=>({...remote,result:{}}),renderAll:()=>{},toast:()=>{},
  refreshSummary:()=>'',loadOA:()=>Promise.resolve(),loadSubs:()=>{loadSubsCalls++;return Promise.resolve()}});
 vm.runInContext(helpers+refresh,refreshed);
 await refreshed.fullRefresh({});
 await Promise.resolve();await Promise.resolve();
 assert.equal(refreshed.D.grade_source,'import');
 assert.equal(refreshed.D.grades,local.grades);
 assert.equal(refreshed.D.courses,remote.courses);
 assert.equal(refreshed.dirty,true);
 assert.equal(loadSubsCalls,1,'fullRefresh must chain loadSubs after loadOA');
 console.log('Grade import: offline states, refresh preservation, file limits and document-wide drops passed.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
