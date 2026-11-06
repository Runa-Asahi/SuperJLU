// 「版本」卡片：版本号不被状态文字覆盖、已是最新提示、失败原因进技术信息；Android 下载入口走原生外链。node tests/js_update_card_test.js
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/../jlu_toolkit/ui_page.py','utf8').split('\n');
const pick=n=>{const i=src.findIndex(l=>l.startsWith(n));if(i<0)throw Error('missing '+n);return src[i]};
const names=['const UPD_TXT=','function updVer(','function updMsg(','function updWhy(','function updOk(','function updHosts(','function updOpen(','function updRender(','async function updCheck('];
function mkNode(id,extra){const n={id:id.replace(/^#/,''),hidden:id==='#upd-tech',innerHTML:'',textContent:'',href:'#',classList:{toggle(){}},getAttribute(k){return k==='href'?this.href:null},...extra};return n}
function run(resp,bridge,opts){
 const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,mkNode(id));return nodes.get(id)};
 node('#upd-v').textContent='';const toasts=[];const opened=[];const assigned=[];
 const sj=bridge||null;
 const ctx=vm.createContext({UPD:null,$:node,esc:s=>String(s??''),toast:(m,bad)=>toasts.push([m,!!bad]),localStorage:{getItem:()=>null},
  document:{querySelector:()=>null},setTimeout,clearTimeout,AbortController,URL,
  window:{SuperJLU:sj,open:(u,t,f)=>{opened.push([u,t,f]);return opts&&opts.openFails?null:{}}},
  SuperJLU:sj,location:{assign:u=>assigned.push(u)},
  fetch:async()=>{if(resp instanceof Error)throw resp;return{json:async()=>resp}}});
 vm.runInContext(names.map(pick).join('\n')+'\nthis.T={updVer,updCheck,updMsg,updOk,updOpen,updRender,updHosts,UPD_TXT};',ctx);
 return {T:ctx.T,node,toasts,opened,assigned};
}
(async()=>{
 // 已是最新：版本号保留，提示「当前已是最新版本哦！」
 let r=run({ok:true,current:'1.2.0',latest:'1.2.0',has_update:false});
 r.T.updMsg('正在检查…');await r.T.updCheck(true);
 assert.equal(r.node('#upd-v').textContent,'1.2.0');
 assert.match(r.node('#upd-m').innerHTML,/已是最新版本/);
 assert.deepEqual(r.toasts,[['当前已是最新版本哦！',false]]);
 assert.equal(r.node('#upd-tech').hidden,true);
 // 查不到：原因进技术信息，版本号仍在
 r=run({ok:true,current:'1.2.0',has_update:false,unavailable:true,reason:'native-api OSError: x'});
 await r.T.updCheck(true);
 assert.equal(r.node('#upd-v').textContent,'1.2.0');
 assert.equal(r.node('#upd-tech').hidden,false);assert.match(r.node('#upd-why').textContent,/native-api/);
 assert.equal(r.toasts[0][1],true);assert.notEqual(r.toasts[0][0],'当前已是最新版本哦！');
 // 本地接口挂了：用安卓桥的 versionName 兜底，错误类型与「连不上 GitHub」不同
 r=run(new TypeError('Failed to fetch'),{appVersion:()=>'1.2.0'});
 await r.T.updCheck(true);
 assert.equal(r.node('#upd-v').textContent,'1.2.0');
 assert.match(r.node('#upd-why').textContent,/^page TypeError/);
 // 空版本不会把已有版本号清空
 r=run({ok:true,current:'',has_update:false});r.node('#upd-v').textContent='1.2.0';await r.T.updCheck(false);
 assert.equal(r.node('#upd-v').textContent,'1.2.0');
 // 点「检查更新」不得再整体覆盖 #upd-s（旧 bug：清掉 #upd-v 后 updRender 抛错）
 const all=src.join('\n');assert.ok(!all.includes('$("#upd-s").textContent='));assert.ok(!all.includes('s.innerHTML=`当前版本'));

 // --- Android 下载入口：有 mirrors 时填真实 https，点击走 openExternal，绝不传 # ---
 const gh='https://github.com/Runa-Asahi/SuperJLU/releases/tag/v9.0.0';
 const quark='https://pan.quark.cn/s/216d5fbd8095';
 const baidu='https://pan.baidu.com/s/50ch5v2DmkgXIirwbN-1Brw';
 const calls=[];
 r=run({ok:true,current:'1.2.0',latest:'9.0.0',has_update:true,url:gh,
  mirrors:{quark:{url:quark},baidu:{url:baidu}}},{openExternal:u=>calls.push(u)});
 r.T.updRender({ok:true,current:'1.2.0',latest:'9.0.0',has_update:true,url:gh,
  mirrors:{quark:{url:quark},baidu:{url:baidu}}},false);
 assert.equal(r.node('#upd-dl').hidden,false);
 assert.equal(r.node('#upd-go').href,gh);
 assert.equal(r.node('#upd-quark').href,quark);
 assert.equal(r.node('#upd-baidu').href,baidu);
 let prevented=false;
 r.T.updOpen({preventDefault(){prevented=true},currentTarget:r.node('#upd-go')});
 assert.ok(prevented);assert.deepEqual(calls,[gh]);
 prevented=false;r.T.updOpen({preventDefault(){prevented=true},currentTarget:r.node('#upd-quark')});
 assert.deepEqual(calls,[gh,quark]);
 prevented=false;r.T.updOpen({preventDefault(){prevented=true},currentTarget:r.node('#upd-baidu')});
 assert.deepEqual(calls,[gh,quark,baidu]);
 assert.ok(!calls.includes('#'));assert.ok(calls.every(u=>u.startsWith('https://')));

 // href 仍是 # 时：toast，不静默回顶，也不把 # 传给原生
 const badCalls=[];prevented=false;
 r=run({ok:true},{openExternal:u=>badCalls.push(u)});
 r.node('#upd-go').href='#';
 r.T.updOpen({preventDefault(){prevented=true},currentTarget:r.node('#upd-go')});
 assert.ok(prevented);assert.deepEqual(badCalls,[]);
 assert.equal(r.toasts.length,1);assert.equal(r.toasts[0][1],true);assert.match(r.toasts[0][0],/下载链接暂不可用/);

 // 非白名单域名不得打开
 const evilCalls=[];
 r=run({ok:true},{openExternal:u=>evilCalls.push(u)});
 r.node('#upd-go').href='https://evil.example/x';
 r.T.updOpen({preventDefault(){},currentTarget:r.node('#upd-go')});
 assert.deepEqual(evilCalls,[]);assert.equal(r.toasts[0][1],true);

 // 浏览器（无 SuperJLU bridge）走 window.open，仍不依赖锚点 #
 r=run({ok:true},null);
 r.node('#upd-go').href=gh;
 r.T.updOpen({preventDefault(){},currentTarget:r.node('#upd-go')});
 assert.deepEqual(r.opened,[[gh,'_blank','noopener,noreferrer']]);

 console.log('js_update_card_test ok');
})().catch(e=>{console.error(e);process.exit(1)});
