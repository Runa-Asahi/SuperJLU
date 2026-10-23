// Synthetic-only regression checks for the production inline UI.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const page=fs.readFileSync('jlu_toolkit/ui_page.py','utf8');
for(const [,script] of page.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(script);
const helpers='// Room presentation helpers:'+page.split('// Room presentation helpers:')[1].split('// Room presentation rendering.')[0];
const storage=new Map(),ctx=vm.createContext({localStorage:{getItem:k=>storage.get(k)}});
vm.runInContext(helpers,ctx);
// Location prefixes belong in the muted subtitle, not the room's main label.
const roomNames=[
 [{name:'前卫-敬信教学楼-C区307',campus:'前卫校区',building:'前卫-敬信教学楼'},'C区307'],
 [{name:'前卫-敬信教学楼-D203（卓越法治基地）',campus:'前卫校区',building:'前卫-敬信教学楼'},'D203（卓越法治基地）'],
 [{name:'前卫-敬信教学楼-D区二楼涉外教室',campus:'前卫校区',building:'前卫-敬信教学楼'},'D区二楼涉外教室'],
 [{name:'前卫-敬信教学楼-E区201-C1诚意课堂',campus:'前卫校区',building:'前卫-敬信教学楼'},'E区201-C1诚意课堂'],
 [{name:'前卫--107',campus:'前卫校区',building:'前卫-'},'107'],
 [{name:'前卫-生科楼107',campus:'前卫校区',building:'前卫-'},'107'],
 [{name:'前卫-生命科学楼',campus:'前卫校区',building:'前卫-'},'生命科学楼'],
 [{name:'前卫校区-前卫楼报告厅',campus:'前卫校区',building:'前卫楼'},'报告厅'],
 [{name:'前卫-敬信教学楼-F区第八阶梯',campus:'前卫校区',building:'前卫-敬信教学楼'},'F区第八阶梯'],
 [{name:'前卫-敬信教学楼',campus:'前卫校区',building:'前卫-敬信教学楼'},'敬信教学楼'],
 [{name:'逸夫楼梯间101',campus:'前卫校区'},'逸夫楼梯间101'],
 [{name:'101',campus:'前卫校区',building:'101楼'},'101'],
 [{name:'报告厅'},'报告厅'],[{name:'A-101'},'A-101'],[{name:''},'未命名教室'],
];
for(const [room,expected] of roomNames){const original=JSON.stringify(room);assert.equal(ctx.roomCardName(room),expected);assert.equal(JSON.stringify(room),original)}
assert.equal(ctx.roomViewPreference(),'cards');
storage.set('jlu-room-view','table');assert.equal(ctx.roomViewPreference(),'table');
storage.set('jlu-room-view','invalid');assert.equal(ctx.roomViewPreference(),'cards');
assert.equal(ctx.roomIsTiered({kind:'普通教室',name:'101'}),false);
assert.equal(ctx.roomIsTiered({kind:'阶梯教室',name:'101'}),true);
assert.equal(ctx.roomIsTiered({name:'F区第八阶梯'}),true);
assert.equal(ctx.roomIsTiered({name:'报告厅',seats:500}),false); // Capacity is not room type.
assert.equal(ctx.roomIsTiered({kind:'普通教室',name:'阶梯楼101'}),false);
const rooms=Array.from({length:150},(_,i)=>({name:'R'+i,kind:i%4===0?'阶梯教室':'普通教室'}));
for(let columns=1;columns<=8;columns++){
 const layout=ctx.roomColorLayout(rooms,columns),cells=new Map();
 assert.equal(layout.length,rooms.length);
 assert.equal(new Set(layout.map(r=>r.tone)).size,10);
 layout.forEach((r,i)=>{
  assert.ok(r.tone>=0&&r.tone<10);
  assert.equal(r.span,rooms[i].kind==='阶梯教室'?Math.min(2,columns):1);
  assert.ok(r.col+r.span<=columns);
  for(let c=r.col;c<r.col+r.span;c++){
   const key=r.row+':'+c;assert.equal(cells.has(key),false);cells.set(key,{i,tone:r.tone});
  }
 });
 for(const [key,a] of cells){
  const [row,col]=key.split(':').map(Number);
  for(const k of [row+':'+(col+1),(row+1)+':'+col]){
   const b=cells.get(k);if(b&&a.i!==b.i)assert.notEqual(a.tone,b.tone,'Touching room tiles must have different colors');
  }
 }
 assert.deepEqual(JSON.parse(JSON.stringify(ctx.roomColorLayout(rooms,columns))),JSON.parse(JSON.stringify(layout)));
}
const query={mode:'week',weeks:'6-8',weekday:4,periods:[3,4]};
assert.equal(ctx.roomQueryLabel(query),'第6-8周 周四');
assert.match(ctx.roomQueryLabel({mode:'date',date:'2026-10-22',week:7,weekday:4}),/2026-10-22.*第7周.*周四/);

// Batch actions must ignore the currently displayed search/term subset.
const elements=Object.fromEntries(['#all','#none','#grade-required'].map(k=>[k,{}]));
const batch=vm.createContext({$:k=>elements[k],D:{grades:[{key:'a',required:true,credit:2},{key:'b',required:false,credit:3},{key:'c',required:true,credit:0}]},include:new Set(['stale']),gradeReady:()=>true,visibleGrades:()=>[{key:'a'}],renderGrades:()=>{}});
vm.runInContext(page.split('\n').filter(l=>/^\$\("#(all|none|grade-required)"\)\.onclick=/.test(l)).join('\n'),batch);
elements['#all'].onclick();assert.deepEqual([...batch.include].sort(),['a','b','c','stale']);
elements['#none'].onclick();assert.equal(batch.include.size,0);
batch.include.add('b');elements['#grade-required'].onclick();assert.deepEqual([...batch.include].sort(),['a','b']);

// An open rules panel stays open during course edits, but resets on template changes.
const rules={'#grade-rules':{dataset:{},open:true},'#grade-rules-title':{},'#grade-policy':{},'#grade-template-dirty':{}};
const ruleCtx=vm.createContext({$:k=>rules[k],current:'builtin',dirty:false,GRADE_BUILTINS:{builtin:{name:'保研加权'}},gradeBase:'postgraduate',gradeBaseName:()=> '保研加权',gradePolicy:()=> '基础规则',esc:s=>s,D:{grades:[]}});
vm.runInContext(page.slice(page.indexOf('function renderGradeRules(){'),page.indexOf('function renderTemplateSummary(){')),ruleCtx);
ruleCtx.renderGradeRules();assert.equal(rules['#grade-rules'].open,false);
rules['#grade-rules'].open=true;ruleCtx.renderGradeRules();assert.equal(rules['#grade-rules'].open,true);
ruleCtx.dirty=true;ruleCtx.renderGradeRules();assert.equal(rules['#grade-template-dirty'].hidden,false);
ruleCtx.current='custom';ruleCtx.renderGradeRules();assert.equal(rules['#grade-rules'].open,false);
assert.equal(rules['#grade-rules-title'].textContent,'基于保研加权的自定义模板');
assert.match(rules['#grade-policy'].innerHTML,/基础规则/);

const status=vm.createContext({esc:s=>s,SST:{missing:['未登录','chip']}});
vm.runInContext(page.slice(page.indexOf('function siteHasLoginStatus('),page.indexOf('let LOGIN_MODE=')),status);
for(const id of ['xsxk','lib'])for(const state of ['missing','unknown','ok'])assert.equal(status.stBadge({id,state,checked_at:'today'}),'');
assert.match(status.stBadge({id:'jwxt',state:'missing'}),/未登录/);
console.log('Room names retain room codes and special names; location prefixes shortened without changing source data. Room colors: 1–8 columns, wide tiles and 10-color adjacency passed. Grade batch scope, folded rules and external login badges passed.');

// Daily cards distinguish confirmed absence from unknown, including period 12.
const sample={name:'R101',building:'B1'},other={name:'R101',building:'B2'};
const dayQuery={date:'2026-10-22',periods:[5,6],day:{records:{}}};
assert.equal(ctx.roomDayState(sample,5,dayQuery),'free');
assert.equal(ctx.roomDayState(sample,12,dayQuery),'unknown');
assert.equal(ctx.roomDayStats(sample,dayQuery).unknown,10);
dayQuery.day.records[12]={free:[ctx.roomKey(sample)]};
assert.equal(ctx.roomDayState(sample,12,dayQuery),'free');
assert.equal(ctx.roomDayState(other,12,dayQuery),'unavailable');
dayQuery.day.records[11]={free:[ctx.roomKey(sample)]};
dayQuery.day.records[10]={free:[ctx.roomKey(sample)]};
dayQuery.day.records[9]={free:[ctx.roomKey(sample)]};
assert.equal(ctx.roomDayStats(sample,dayQuery).best.length,4);
assert.equal(ctx.roomDayStats(sample,dayQuery).best.end,12);
assert.equal(ctx.roomDayTime(12,{}),'时间未提供');
assert.equal(ctx.roomDayTime(12,{12:['21:15','22:00']}),'21:15–22:00');
assert.equal(ctx.roomDayMatches(sample,dayQuery,3,4,false,new Set()),true);
assert.equal(ctx.roomDayMatches(sample,dayQuery,1,0,false,new Set()),false);
assert.equal(ctx.roomDayMatches(sample,dayQuery,0,0,true,new Set()),false);
assert.equal(ctx.roomDayMatches(sample,dayQuery,0,0,true,new Set([ctx.roomFavoriteKey(sample,dayQuery)])),true);
assert.notEqual(ctx.roomFavoriteKey(sample,{query:{campus:'01'}}),ctx.roomFavoriteKey(sample,{query:{campus:'02'}}));
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(ROOM_DAY_BLOCKS[2].periods)',ctx)),[9,10,11,12]);

// Exercise actual preloading, local intersections, TTL, cancellation and retries.
async function dailyLoaderChecks(){
 const calls=[];let failSingle=3,release,schoolMain=0;
 const modal={open:false},button={},free=[1,2,5,6,7,8,9],otherFree=[3,4,5,6,7,8,9,10,11,12];
 const special={name:'实验室',building:'B1',special:true,seats:'30'},fullSample={...sample,seats:'60',kind:'普通教室'};
 const available=p=>[...[fullSample].filter(()=>free.includes(p)),...[other].filter(()=>otherFree.includes(p)),special];
 const c=vm.createContext({roomKey:ctx.roomKey,roomDayRecord:ctx.roomDayRecord,roomDayState:ctx.roomDayState,roomDayStats:ctx.roomDayStats,
  $:q=>q==='#rq'?button:q==='#room-error'?{}:q==='#t-js'?{addEventListener(){}}:modal,
  document:{querySelectorAll:()=>[]},periodMap:()=>({5:['13:30','14:15'],6:['14:25','15:10']}),
  refreshRoomDetail(){},updateRoomNextBadges(){},clearTimeout(){},
  api:async(path,body)=>{if(path==='/api/rooms'){schoolMain++;return{mode:'date',date:body.date,periods:body.periods.split('-').map(Number),rooms:[fullSample,other],weekday:4,week:7}}
   calls.push(body);assert.ok(!body.day_ranges);assert.ok(body.day_periods.length<=4);
   const records=body.day_periods.filter(p=>p!==failSingle).map(p=>({complete:true,date:body.date,period:p,rooms:available(p)}));
   return{date:body.date,records,partial:records.length!==body.day_periods.length};}
 });
 vm.runInContext('let ROOM_BUILDINGS_READY=Promise.resolve(),ROOM_REQUEST=1,ROOM_RESULT=null,ROOM_DETAIL=null,RR=[],ROOM_DAY_ONLY_FAV=false,RS={k:"name"};'+page.slice(page.indexOf('// Memory-only inventories:'),page.indexOf('function showRoomFailure(')),c);
 const query={mode:'date',campus:'01',building:'B1',date:'2026-10-22',periods:'5-6',hide_special:false};
 c.query=query;const entry=c.roomCacheEntry(query);entry.meta={mode:'date',date:query.date,weekday:4,week:7};
 const j={rooms:[fullSample,other],query,date:query.date,periods:[5,6],day:entry.day};
 c.j=j;c.sample=sample;c.other=other;vm.runInContext('ROOM_RESULT=j',c);
 // Starts with no dialog open. A second call shares the same request promise.
 const preloading=c.loadRoomDay(j,1);assert.strictEqual(c.loadRoomDay(j,1),preloading);await preloading;
 assert.match(j.day.error,/部分节次/);assert.equal(j.day.loading,false);assert.equal(Object.keys(j.day.records).length,11);
 assert.deepEqual(calls.map(b=>Array.from(b.day_periods)),[[7,8,9,10],[11,12,1,2],[3,4,5,6]]);
 failSingle=0;calls.length=0;await c.loadRoomDay(j,1);assert.deepEqual(calls.map(b=>Array.from(b.day_periods)),[[3]]);
 for(let p=1;p<=12;p++)assert.equal(ctx.roomDayState(sample,p,j),free.includes(p)?'free':'unavailable');
 calls.length=0;vm.runInContext('ROOM_DETAIL={j,room:other}',c);modal.open=true;await c.loadRoomDay(j,1);assert.equal(calls.length,0);
 // AND intersection across all selected periods; keep metadata and special-room rule.
 let cached=c.roomCachedResult({...query,periods:'1-2',hide_special:true});
 assert.deepEqual(Array.from(cached.rooms,r=>r.name),[sample.name]);assert.equal(cached.hidden_special,1);assert.equal(cached.rooms[0].seats,'60');
 cached=c.roomCachedResult({...query,periods:'5-6',hide_special:true});assert.equal(cached.rooms[0].free_periods,'5,6');assert.equal(cached.rooms[0].free_time,'13:30–15:10');
 assert.equal(c.roomCachedResult({...query,building:'B2'}),null);assert.equal(c.roomCachedResult({...query,date:'2026-10-23'}),null);
 assert.equal(c.roomCachedResult({...query,mode:'week'}),null);
 // Five-minute expiry is per record and does not get extended by another read.
 const expiry=j.day.records[1].expires;c.roomCachedResult({...query,periods:'1-2'});assert.equal(j.day.records[1].expires,expiry);
 j.day.records[1].expires=0;assert.equal(c.roomCachedResult({...query,periods:'1-2'}),null);
 calls.length=0;await c.loadRoomDay(j,1);assert.deepEqual(calls.map(b=>Array.from(b.day_periods)),[[1]]);
 // Dialog closure does not cancel page-level background preloading.
 j.day.records={};calls.length=0;const regular=c.api;
 c.api=(path,body)=>{calls.push(body);return new Promise(resolve=>{release=()=>resolve({date:j.date,records:body.day_periods.map(p=>({complete:true,date:j.date,period:p,rooms:available(p)}))})})};
 const closing=c.loadRoomDay(j,1);await Promise.resolve();modal.open=false;vm.runInContext('ROOM_DETAIL=null',c);c.api=regular;release();await closing;assert.equal(calls.length,3);
 // Scope change stops future batches; the new scope waits for the old in-flight batch.
 j.day.records={};calls.length=0;c.api=(path,body)=>{calls.push(body);return new Promise(resolve=>{release=()=>resolve({date:j.date,records:body.day_periods.map(p=>({complete:true,date:j.date,period:p,rooms:available(p)}))})})};
 const oldTask=c.loadRoomDay(j,1);await Promise.resolve();
 const q2={...query,building:'B2'},j2={...j,query:q2,day:c.roomCacheEntry(q2).day};c.j2=j2;vm.runInContext('ROOM_RESULT=j2',c);
 c.api=regular;const newTask=c.loadRoomDay(j2,2);assert.equal(calls.length,1);release();await Promise.all([oldTask,newTask]);
 assert.equal(calls.length,4);assert.equal(Object.keys(j.day.records).length,0);assert.equal(Object.keys(j2.day.records).length,12);
 assert.ok(calls.slice(1).every(b=>b.building==='B2'));
 // Expiry retains successes as unknowns, and stops later batches.
 j2.day.records={};calls.length=0;c.api=async(path,body)=>{calls.push(body);return{date:j2.date,records:[{complete:true,date:j2.date,period:body.day_periods[0],rooms:available(body.day_periods[0])}],partial:true,session_expired:true}};
 await c.loadRoomDay(j2,2);assert.equal(calls.length,1);assert.match(j2.day.error,/部分节次/);
 // Authentication invalidation discards cache and in-flight responses.
 j2.day.records={};c.api=()=>new Promise(resolve=>{release=resolve});const stale=c.loadRoomDay(j2,2);await Promise.resolve();c.clearRoomCache();release({date:j2.date,records:[{complete:true,date:j2.date,period:7,rooms:[sample]}]});await stale;assert.equal(j2.day.records[7],undefined);assert.equal(c.roomCachedResult(q2),null);
 // The actual query handler shows the selected result without waiting for full day.
 c.api=regular;c.roomReadQuery=()=>query;c.showRoomFailure=e=>{throw e};c.roomScrollTo=()=>{};
 c.renderRooms=value=>{c.value=value;vm.runInContext('ROOM_RESULT=value',c)};
 vm.runInContext(page.slice(page.indexOf('async function runRoomQuery('),page.indexOf('let OA=null')),c);
 const beforeForm=calls.length;c.roomFormChanged();c.roomFormChanged();await Promise.resolve();assert.equal(schoolMain,0);assert.equal(calls.length,beforeForm,'Editing conditions never starts a query');
 let releaseMain;c.api=(path,body)=>path==='/api/rooms'?new Promise(resolve=>{releaseMain=()=>resolve(regular(path,body))}):regular(path,body);
 const requested=c.runRoomQuery(),duplicate=c.runRoomQuery();
 for(let tick=0;tick<6&&!releaseMain;tick++)await Promise.resolve();assert.ok(releaseMain);assert.equal(calls.length,beforeForm,'Full-day loading waits for selected results');
 releaseMain();await Promise.all([requested,duplicate]);c.api=regular;assert.equal(schoolMain,1);
 await c.value.day.request;const before=calls.length;c.roomReadQuery=()=>({...query,periods:'1-2',hide_special:true});await c.runRoomQuery();assert.equal(schoolMain,1,'Time changes use full inventories locally');assert.equal(calls.length,before);assert.equal(c.value.rooms.length,1);
 console.log('Preload: explicit query only, no dialog needed, selected results first, shared requests, local intersection, metadata, TTL, scope queue, retry and auth invalidation passed.');
}
dailyLoaderChecks().catch(e=>{console.error(e);process.exitCode=1});
// Opening the page initializes selectors only, even on repeated navigation.
let roomEntryHandler,roomInitializations=0;
const entryContext=vm.createContext({window:{},roomAutoSlot(){},roomsInit(){roomInitializations++},
 document:{querySelector:()=>({addEventListener:(event,handler)=>{roomEntryHandler=handler}})},
 runRoomQuery(){throw new Error('Navigation must never query rooms')},loadRoomDay(){throw new Error('Navigation must never preload')}});
vm.runInContext(page.split('\n').find(line=>line.startsWith("document.querySelector('nav button[data-t=\"js\"]').addEventListener")),entryContext);
roomEntryHandler();roomEntryHandler();assert.equal(roomInitializations,1);


async function loginCodeFocusChecks(){
 for(const target of ['jwxt','vpn']){
  const nodes={'#lg2':{hidden:true},'#lg3':{hidden:true},'#lgo':{},'#lgw':{value:'old'}};
  let focused=0,result={step:'code_sent'};const paths=[];
  nodes['#lgw'].focus=()=>{assert.equal(nodes['#lg2'].hidden,false);assert.equal(nodes['#lg3'].hidden,false);focused++};
  const c=vm.createContext({LG:{step:'cap',target},$:k=>nodes[k],toast(){},lgErr(){},lgPost:async path=>{paths.push(path);return result}});
  vm.runInContext(page.split('\n').filter(l=>l.startsWith('function lgView(')||l.startsWith('async function lgSendCode(')).join('\n'),c);
  assert.equal(await c.lgSendCode(),true);assert.equal(focused,1);assert.equal(nodes['#lgw'].value,'');
  assert.equal(paths[0],target==='vpn'?'/api/vpn/login/send_code':'/api/login/send_code');
  nodes['#lgw'].value='keep';result={step:'captcha_retry',error:'synthetic failure'};
  assert.equal(await c.lgSendCode(),false);assert.equal(focused,1);assert.equal(nodes['#lgw'].value,'keep');
 }
 console.log('Login code: direct/WebVPN sends reveal the input before focus; failed sends preserve focus and input.');
}
loginCodeFocusChecks().catch(e=>{console.error(e);process.exitCode=1});

// Compact cards only describe the next period; no inferred claim of a class.
const followQuery={query:{campus:'01'},periods:[5,6],day:{records:{}}};
assert.equal(ctx.roomFollowup(sample,followQuery).label,'后续待查');
followQuery.day.records[7]=ctx.roomDayRecord([sample],'test');
assert.equal(ctx.roomFollowup(sample,followQuery).label,'下节空闲');
assert.equal(ctx.roomFollowup(other,followQuery).label,'下节无空闲');
assert.equal(ctx.roomFollowup(sample,{periods:[11,12],day:{records:{}}}).state,'end');
assert.equal(ctx.roomFollowup(sample,{periods:[5,6]}).label,'所选时段空闲');
for(let columns=1;columns<=8;columns++)for(const wide of [true,false]){
 const tones=ctx.roomGroupColors(500,columns,wide),perRow=Math.max(1,Math.floor(columns/(wide?Math.min(2,columns):1)));
 for(let i=0;i<tones.length;i++){assert.ok(tones[i]>=0&&tones[i]<10);if(i%perRow)assert.notEqual(tones[i],tones[i-1]);if(i>=perRow)assert.notEqual(tones[i],tones[i-perRow]);}
}
const compactCtx=vm.createContext({roomIsTiered:ctx.roomIsTiered,roomFavoriteKey:ctx.roomFavoriteKey,roomFollowup:ctx.roomFollowup,roomCardName:ctx.roomCardName,roomKey:ctx.roomKey,roomIcon:()=>'<svg></svg>',esc:s=>String(s).replaceAll('<','&lt;'),roomDayGauge:()=>{throw new Error('Gauge cannot be rendered on the outer card')}});
vm.runInContext(page.slice(page.indexOf('function roomDayCard('),page.indexOf('function renderRooms(')),compactCtx);
const compactHTML=compactCtx.roomDayCard({...sample,seats:60},followQuery,0,new Set());
assert.doesNotMatch(compactHTML,/room-day-gauge|最长连空|room-day-blocks/);
assert.match(compactHTML,/data-room-followup/);assert.match(compactHTML,/60 座/);
console.log('Compact cards: no outer gauge, clear next-period states and linear grouped color adjacency passed.');

// The renderer and gauge expose all twelve periods, including unknowns.
const renderCtx=vm.createContext({esc:s=>s,roomCardName:ctx.roomCardName,roomDayStats:ctx.roomDayStats,roomDayState:ctx.roomDayState,roomDayArc:ctx.roomDayArc,roomDayTime:ctx.roomDayTime,periodMap:()=>({}),ROOM_DAY_BLOCKS:[{name:'上午',periods:[1,2,3,4]},{name:'下午',periods:[5,6,7,8]},{name:'晚上',periods:[9,10,11,12]}],document:{querySelectorAll:()=>[]}});
const rendered={innerHTML:''};renderCtx.$=selector=>selector==='#room-detail-day'?rendered:null;
renderCtx.ROOM_DETAIL={room:sample,j:{periods:[5,6],day:{records:{},loading:true}},block:-1};
vm.runInContext(page.slice(page.indexOf('function roomDayGauge('),page.indexOf('function roomDayCard('))+page.slice(page.indexOf('function renderRoomDayDetail('),page.indexOf('$("#room-detail-close")')),renderCtx);
renderCtx.renderRoomDayDetail();assert.equal((rendered.innerHTML.match(/data-room-period=/g)||[]).length,12);assert.equal((rendered.innerHTML.match(/<path /g)||[]).length,12);assert.doesNotMatch(rendered.innerHTML,/data-room-pair=|查看单节详情/);assert.match(rendered.innerHTML,/未确认/);
