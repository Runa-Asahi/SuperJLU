// 课表个人修改：前端纯函数 + 冲突提示渲染。node tests/js_schedule_edit_test.js
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/../jlu_toolkit/ui_page.py','utf8').split('\n');
const pick=n=>{const i=src.findIndex(l=>l.startsWith(n));if(i<0)throw Error('missing '+n);let j=i+1;while(j<src.length&&/^[ \t]/.test(src[j]))j++;return src.slice(i,j).join('\n')};
const names=['function nextClass(','function nextClassLabel(','const KB_WD=','const KB_FIELD=','function kbSlot(','function kbOcc(','function kbBlankSeed(','function kbWeeks(','function kbPreset(','function kbTarget(','function kbOpText(',
 'function kbIssueTitle(','function kbIssueActions(','function kbCls(','function kbSrcText(','function kbIsBase(','function kbCourse(','function kbOpSet(','function kbSkipReq(',
 'function kbDeleteReq(','function kbEditReq(','function adjInfoText(','function renderAdjToggle(','function renderShareHint(','function renderKbExtras(','const KB_DONE=','function kbActionClick(','function kbImportText(','async function kbPost('];
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{id,hidden:false,innerHTML:'',textContent:''});return nodes.get(id)};
const calls=[],toasts=[];
const ctx=vm.createContext({D:null,$:node,esc:s=>String(s??'').replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';'),toast:(m,bad)=>toasts.push([m,!!bad]),
 renderGrid:()=>calls.push('grid'),api:async(p,b)=>{calls.push([p,b]);if(b.action==='bad')throw new Error('找不到要修改的课程，请刷新后重试');return{ok:true,schedule_edits:9}}});
vm.runInContext(names.map(pick).join('\n')+'\nthis.KB={nextClass,nextClassLabel,adjInfoText,renderAdjToggle,kbSlot,kbOcc,kbBlankSeed,kbWeeks,kbPreset,kbTarget,kbOpText,kbIssueActions,kbCls,kbSkipReq,kbDeleteReq,kbEditReq,renderKbExtras,kbActionClick,kbImportText,kbPost,kbSrcText};',ctx);
const K=ctx.KB,J=x=>x===undefined?x:JSON.parse(JSON.stringify(x)),eq=(a,b)=>assert.deepEqual(J(a),J(b));
(async()=>{
 assert.equal(K.kbSlot({weekday:1,start:1,end:2}),'周一 第1-2节');
 const occ=K.kbOcc([{weekday:3,start:1,end:2},{weekday:3,start:5,end:5}]);
 eq(K.kbBlankSeed(3,3,occ,6,11),{name:'',location:'',teacher:'',weekday:3,start:3,end:4,weeks:[6]});
 eq(K.kbBlankSeed(3,4,occ,6,11),{name:'',location:'',teacher:'',weekday:3,start:3,end:4,weeks:[6]});
 eq(K.kbBlankSeed(3,1,occ,6,11),null);
 eq(K.kbBlankSeed(3,5,occ,6,11),null);
 eq(K.kbBlankSeed(3,6,occ,6,11),{name:'',location:'',teacher:'',weekday:3,start:6,end:6,weeks:[6]});
 eq(K.kbBlankSeed(1,11,occ,6,11),{name:'',location:'',teacher:'',weekday:1,start:11,end:11,weeks:[6]});
 assert.equal(K.kbBlankSeed(0,1,occ,6,11),null);
 assert.equal(K.kbBlankSeed(1,1,occ,0,11),null);
 assert.equal(K.kbSlot({weekday:7,start:5,end:5}),'周日 第5节');
 assert.equal(K.kbWeeks([5,1,2,3,8,9,12]),'第1-3、5、8-9、12周');
 assert.equal(K.kbWeeks([]),'');assert.equal(K.kbWeeks([1,3,5,7]),'第1-7周（单周）');assert.equal(K.kbWeeks([2,4,6]),'第2-6周（双周）');assert.equal(K.kbWeeks([1,3]),'第1、3周');
 eq([...K.kbPreset('odd',7)],[1,3,5,7]);eq([...K.kbPreset('even',6)],[2,4,6]);assert.equal(K.kbPreset('all',16).length,16);
 eq({...K.kbTarget('线性代数|A|3|5-6')},{name:'线性代数|A',weekday:3,start:5,end:6});
 assert.equal(K.kbOpText({op:'hide',target:'高等数学|1|1-2',weeks:[8]}),'「高等数学」 周一 第1-2节 第8周不上');
 assert.equal(K.kbOpText({op:'hide',target:'高等数学|1|1-2',weeks:null}),'「高等数学」 周一 第1-2节 所有周不上');
 assert.equal(K.kbOpText({op:'edit',target:'高等数学|1|1-2',weeks:[9],set:{location:'逸夫楼301',weekday:5,start:3}}),'「高等数学」 周一 第1-2节 第9周：地点改为逸夫楼301，星期改为周五，开始节改为第3节');
 assert.equal(K.kbOpText({op:'add',course:{name:'社团',weekday:6,start:1,end:2,weeks:[3,4]}}),'添加了「社团」 周六 第1-2节 第3-4周');
 // 冲突按钮：教务有变动 / 找不到（修改 vs 隐藏）/ 损坏
 const acts=i=>K.kbIssueActions(i).map(a=>a[1]).join('|');
 assert.equal(acts({kind:'changed',op:'edit'}),'我知道了|删掉这条修改');
 assert.equal(acts({kind:'missing',op:'edit'}),'我知道了|保留为自定义课|删掉这条修改');
 assert.equal(acts({kind:'missing',op:'hide'}),'我知道了|删掉这条修改');
 assert.equal(acts({kind:'invalid'}),'删掉这条修改');
 assert.equal(K.kbCls({src:'custom'}),' custom');assert.equal(K.kbCls({src:'edited'}),' edited');assert.equal(K.kbCls({src:'official'}),'');
 assert.match(K.kbSrcText({src:'edited',from:'高等数学|1|1-2'}),/周一 第1-2节/);
 // 请求体
 const off={src:'official',key:'高等数学|1|1-2',name:'高等数学',teacher:'王五',location:'经信A101',weekday:1,start:1,end:2,weeks:[1,2,3]};
 const cus={src:'custom',oid:'c1',name:'社团',teacher:'',location:'体育馆',weekday:6,start:1,end:2,weeks:[3,4]};
 const edi={src:'edited',oid:'e1',key:'高等数学|1|1-2',from:'高等数学|1|1-2',name:'高等数学',teacher:'王五',location:'逸夫楼301',weekday:1,start:1,end:2,weeks:[9]};
 eq(K.kbSkipReq(off,2),{action:'hide',target:off.key,weeks:[2]});
 eq(K.kbSkipReq(cus,3),{action:'update',id:'c1',course:{name:'社团',teacher:'',location:'体育馆',weekday:6,start:1,end:2,weeks:[4]}});
 eq(K.kbSkipReq({...cus,weeks:[3]},3),{action:'remove',id:'c1'});
 assert.equal(K.kbSkipReq(edi,9),null);
 eq(K.kbDeleteReq(off),{action:'hide',target:off.key});eq(K.kbDeleteReq(cus),{action:'remove',id:'c1'});
 const vals={name:'高等数学',teacher:'王五',location:'逸夫楼301',weekday:1,start:1,end:2};
 eq(K.kbEditReq(off,vals,'week',2),{action:'edit',target:off.key,weeks:[2],set:{location:'逸夫楼301'}});
 eq(K.kbEditReq(off,vals,'all',2).weeks,null);
 ctx.D={schedule_ops:[{id:'e1',op:'edit',set:{location:'逸夫楼301'}}]};
 eq(K.kbEditReq(edi,{...vals,start:3,end:4},'',9),{action:'update',id:'e1',set:{location:'逸夫楼301',start:3,end:4}});
 assert.equal(K.kbEditReq(cus,{...vals,weeks:[1]},'',1).course.name,'高等数学');
 // 冲突提示条 + 「我的课表修改」卡片
 ctx.D={schedule_issues:[{oid:'e1',kind:'missing',op:'edit',name:'高<b>数',weekday:1,start:1,end:2,message:'暂未生效'}],
  schedule_ops:[{id:'h1',op:'hide',target:'大学英语|3|3-4',weeks:[2]}],schedule_other_terms:3,schedule_can_undo_reset:true};
 K.renderKbExtras();
 const box=node('#kb-issues');assert.equal(box.hidden,false);assert.match(box.innerHTML,/有 1 条课表修改需要你看一下/);
 assert.match(box.innerHTML,/保留为自定义课/);assert.ok(!box.innerHTML.includes('<b>数'),'escaped');
 assert.match(node('#kb-edits-sum').textContent,/本学期你改了 1 处课表/);assert.match(node('#kb-edits-sum').textContent,/其他学期还有 3 处/);
 assert.match(node('#kb-edits-list').innerHTML,/第2周不上/);assert.equal(node('#kb-reset').hidden,false);assert.equal(node('#kb-undo').hidden,false);
 ctx.D={schedule_issues:[],schedule_ops:[]};K.renderKbExtras();
 assert.equal(node('#kb-issues').hidden,true);assert.match(node('#kb-edits-sum').textContent,/还没有修改过课表/);assert.equal(node('#kb-reset').hidden,true);
 // 不出现技术词
 for(const t of [node('#kb-edits-sum').textContent,box.innerHTML])assert.ok(!/json|overlay|api|csv/i.test(t),t);
 // 按钮点击 → 请求；失败给中文提示
 calls.length=0;K.kbActionClick({target:{closest:()=>({dataset:{a:'ack',id:'e1'}})}});await new Promise(r=>setTimeout(r,0));
 eq(calls[0],['/api/schedule/overlay',{action:'ack',id:'e1'}]);assert.equal(ctx.D.schedule_edits,9);assert.ok(calls.includes('grid'));
 assert.equal(await K.kbPost({action:'bad'}),false);eq(toasts.at(-1),['找不到要修改的课程，请刷新后重试',true]);
 await K.kbImportText('不是备份');eq(toasts.at(-1),['这不是课表修改备份',true]);
 assert.equal(await K.kbImportText('{"version":2,"terms":{}}'),true);
 // 调课：「调」角标、详情说明、设置开关文案；请求带教学班
 assert.equal(K.kbCls({src:'official',adj:'调课：原 周五 第3-4节 第6周'}),' adjusted');
 assert.equal(K.kbCls({src:'edited',adj:'x'}),' edited');
 assert.match(K.kbSrcText({src:'official',adj:'调课：原 周五 第3-4节 第6周 · 逸夫楼第十阶梯'}),/^教务调课：原 周五/);
 eq(K.kbSkipReq({...off,jxbid:'J1'},2),{action:'hide',target:off.key,jxbid:'J1',weeks:[2]});
 eq(K.kbDeleteReq({...off,jxbid:'J1'}),{action:'hide',target:off.key,jxbid:'J1'});
 eq(K.kbEditReq({...off,jxbid:'J1'},vals,'all',2),{action:'edit',target:off.key,jxbid:'J1',weeks:null,set:{location:'逸夫楼301'}});
 assert.match(K.adjInfoText({enabled:false}),/已关闭/);
 assert.match(K.adjInfoText({enabled:true,applied:2,count:2}),/2 处调课\/停课.*「调」/);
 assert.match(K.adjInfoText({enabled:true,applied:0,count:0}),/不影响课表和登录/);
 ctx.D={schedule_adjust:{enabled:false}};node('#adj-on').checked=true;K.renderAdjToggle();
 assert.equal(node('#adj-on').checked,false);assert.match(node('#adj-info').textContent,/已关闭/);
 ctx.D={};K.renderAdjToggle();assert.equal(node('#adj-on').checked,true);  // 默认开
 for(const a of [{enabled:false},{enabled:true,applied:1},{}])assert.ok(!/SUPERJLU|环境变量|json|api/i.test(K.adjInfoText(a)));
 // 停课灰显
 assert.equal(K.kbCls({src:'cancelled',adj:'停课：原 周一'}),' cancelled');
 assert.match(K.kbSrcText({src:'cancelled',adj:'停课：原 周一 第1-2节 第8周 · 经信A101（2026-10-01 申请）'}),/^教务停课：原 周一.*申请/);
 assert.match(K.adjInfoText({enabled:true,applied:2}),/灰色带「停」字/);
 // 下一节：按当前时间，停课不算；正在上优先于之后的课
 const P={1:["08:00","08:45"],2:["08:55","09:40"],3:["10:00","10:45"],4:["10:55","11:40"],5:["13:30","14:15"],6:["14:25","15:10"]};
 const FM="2026-09-07"; // 周一；2026-10-22 是第 7 周周四
 const cs=[
  {name:"已结束",location:"A",weekday:4,start:1,end:1,weeks:[7]},
  {name:"停课",location:"B",weekday:4,start:3,end:4,weeks:[7],src:"cancelled"},
  {name:"离散数学",location:"逸夫楼",weekday:4,start:3,end:4,weeks:["7"]},
  {name:"高等数学",location:"经信",weekday:5,start:1,end:2,weeks:[7]},
  {name:"大学英语",location:"东荣",weekday:1,start:1,end:1,weeks:[8]},
 ];
 const at=(h,mi,day=22)=>new Date(2026,9,day,h,mi,0);
 const hit930=K.nextClass(cs,P,FM,at(9,30),16);
 eq(hit930,{kind:"next",name:"离散数学",location:"逸夫楼",weekday:4,start:3,end:4,week:7,hm:"10:00",ymd:"2026-10-22",mins:30,thisWeek:true});
 eq(K.nextClassLabel(hit930,at(9,30)),{k:"下一节",t:"离散数学",sub:"今天 10:00 · 第3-4节 · 逸夫楼"});
 const hit1030=K.nextClass(cs,P,FM,at(10,30),16);
 assert.equal(hit1030.kind,"now");assert.equal(hit1030.name,"离散数学");assert.equal(hit1030.mins,70);
 eq(K.nextClassLabel(hit1030,at(10,30)),{k:"正在上",t:"离散数学",sub:"第3-4节 · 逸夫楼 · 还剩 70 分钟"});
 const hitNight=K.nextClass(cs,P,FM,at(21,0),16);
 assert.equal(hitNight.name,"高等数学");assert.equal(hitNight.ymd,"2026-10-23");
 eq(K.nextClassLabel(hitNight,at(21,0)),{k:"下一节",t:"高等数学",sub:"明天 08:00 · 第1-2节 · 经信"});
 const hitFri=K.nextClass(cs,P,FM,at(18,0,23),16);
 assert.equal(hitFri.name,"大学英语");assert.equal(hitFri.week,8);assert.equal(hitFri.thisWeek,false);
 eq(K.nextClassLabel(hitFri,at(18,0,23)),{k:"下一节",t:"大学英语",sub:"第8周 周一 08:00 · 第1节 · 东荣"});
 assert.equal(K.nextClass(cs,P,FM,at(9,0,26),16),null);
 eq(K.nextClassLabel(null,at(9,0)),{k:"课表",t:"本学期没有更多课程",sub:""});
 assert.equal(K.nextClass([],P,"",at(9,30),16),null);
 const overlap=K.nextClass([
  {name:"长课",location:"",weekday:4,start:1,end:4,weeks:[7]},
  {name:"短课",location:"",weekday:4,start:3,end:4,weeks:[7]},
 ],P,FM,at(10,30),16);
 assert.equal(overlap.kind,"now");assert.equal(overlap.name,"短课");
 assert.ok(!src.some(l=>l.includes("nextexam")||l.includes("下一场考试")));
 assert.ok(src.some(l=>l.includes('id="kb-next"')));
 console.log('js_schedule_edit_test ok');
})().catch(e=>{console.error(e);process.exit(1)});
