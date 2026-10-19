// Production login completion: a VPN login is not necessarily JWXT authorization.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const page=fs.readFileSync('jlu_toolkit/ui_page.py','utf8');
const done=page.split('\n').find(line=>line.startsWith('async function lgDone('));
async function verify(target,result,expectedRefreshes){
 const calls={refresh:0,login:0,network:0,links:0,messages:[]};
 const c=vm.createContext({LG:{target},D:{grades:[]},
  $:()=>({close:()=>{}}),loadNetworkState:async()=>calls.network++,loadLinks:async()=>calls.links++,
  lgInfo:()=>calls.login++,loginFeedback:(message)=>{calls.feedback=message},renderSession:()=>{},toast:(message)=>calls.messages.push(message),
  fullRefresh:async()=>calls.refresh++});
 vm.runInContext(done,c);await c.lgDone(result);
 assert.equal(calls.refresh,expectedRefreshes);
 assert.equal(calls.login,expectedRefreshes);
 assert.equal(calls.network,expectedRefreshes?2:1);
 return calls;
}
function verifyChoice(){
 const nodes=new Map();
 const node=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',hidden:true});return nodes.get(id)};
 const buttons=['direct','webvpn'].map(mode=>({dataset:{loginMode:mode},classList:{toggle:(name,on)=>{}},setAttribute(name,value){this[name]=value}}));
 const c=vm.createContext({$:node,LOGGED:true,document:{querySelectorAll:()=>buttons}});
 const functions=['let LOGIN_MODE=','function syncLoginChoice(','function loginFeedback(','function renderNetworkState('];
 vm.runInContext(page.split('\n').filter(line=>functions.some(prefix=>line.startsWith(prefix))).join('\n'),c);
 c.renderNetworkState({mode:'webvpn'});
 assert.equal(buttons[1]['aria-pressed'],'true');
 assert.match(node('#network-route-current').textContent,/校外 WebVPN/);
 vm.runInContext('LOGIN_MODE="direct";syncLoginChoice()',c);
 assert.match(node('#lgbtn').textContent,/切换方式并登录/);
 assert.match(node('#network-route-current').textContent,/校外 WebVPN/); // Merely choosing never changes the active route.
 c.renderNetworkState({mode:'webvpn'}); // Late status response must not discard the user's choice.
 assert.equal(buttons[0]['aria-pressed'],'true');
 c.renderNetworkState({mode:'direct',last_connection:{route:'direct'}});
 assert.match(node('#lgbtn').textContent,/重新登录/);
 assert.match(node('#network-route-last').textContent,/最近成功连接：直连/);
 assert.equal(node('#network-route-last').hidden,false);
}
async function verifyModal(mode,expected){
 const nodes=new Map();
 const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:true,focus(){},showModal(){this.open=true}});return nodes.get(id)};
 const requests=[];
 const c=vm.createContext({LOGIN_MODE:mode,LOGGED:false,PW_MASK:'mask',$:node,lgErr(){},lgView(){},lgAcc(){},lgSync(){},fetch:async path=>{requests.push(path);return{json:async()=>({accounts:[]})}}});
 vm.runInContext(page.split('\n').find(line=>line.startsWith('async function openLogin(')),c);
 await c.openLogin();
 assert.equal(c.LG.target,expected);
 assert.equal(node('#login').open,true);
 assert.deepEqual(requests,['/api/login']); // Opening a modal must not switch route or submit credentials.
}
async function verifyManualStart(){
 const paths=[];let refreshes=0,opened=0;
 const c=vm.createContext({LOGGED:true,LOGIN_MODE:'direct',ACTIVE_LOGIN_MODE:'webvpn',
  $:()=>({disabled:false}),api:async path=>{paths.push(path);return {mode:'auto'}},
  renderNetworkState(){},fullRefresh:async()=>refreshes++,loadNetworkState:async()=>{},
  loginFeedback(){},openLogin:async()=>opened++});
 vm.runInContext(page.split('\n').find(line=>line.startsWith('async function startLogin(')),c);
 await c.startLogin();
 assert.deepEqual(paths,[]);assert.equal(refreshes,0);assert.equal(opened,1);
}
function verifyShortRoomFailures(){
 const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',hidden:true});return nodes.get(id)};
 const c=vm.createContext({$:node,RR:[{name:'synthetic cached room'}]});
 vm.runInContext(page.split('\n').find(line=>line.startsWith('function showRoomFailure(')),c);
 c.showRoomFailure({message:'空教室查询未成功；尝试：'+('cxkxjs.do/meta:HTTP404；'.repeat(12))});
 assert.equal(node('#room-error').hidden,false);assert.equal(node('#room-switch-login').hidden,false);
 assert.ok(node('#room-error-message').textContent.length<120);
 assert.doesNotMatch(node('#room-error-message').textContent,/HTTP404|cxkxjs|尝试：/);
 assert.match(node('#room-error-message').textContent,/保留上次/);
 c.RR=[];c.showRoomFailure({message:'请选择校区'});
 assert.equal(node('#room-error-message').textContent,'请选择校区');
 assert.equal(node('#room-switch-login').hidden,true);
}

function verifyNetworkCheckFooter(){
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
 const page=fs.readFileSync('jlu_toolkit/ui_page.py','utf8');
 const line=page.split('\n').find(l=>l.startsWith('function networkCheckFooter('));
 assert.ok(line, 'networkCheckFooter must exist');
 const c=vm.createContext({esc});
 vm.runInContext(line,c);
 const withHint=c.networkCheckFooter({hint:'教务直连未通，请到「更多 → 登录」选择「校外 WebVPN」后再登录/同步；本检测只测直连，不代表已通过应用内 WebVPN 验收。'});
 assert.match(withHint,/校外提示/);
 assert.match(withHint,/校外 WebVPN/);
 assert.match(withHint,/不会切换/);
 assert.doesNotMatch(withHint,/校园服务/);
 const plain=c.networkCheckFooter({services:[]});
 assert.match(plain,/校外 WebVPN/);
 assert.doesNotMatch(plain,/校外提示/);
}
(async()=>{
 verifyNetworkCheckFooter();
 verifyChoice();
 verifyShortRoomFailures();
 await verifyManualStart();
 await verifyModal('direct','jwxt');await verifyModal('webvpn','vpn');
 const partial=await verify('vpn',{jwxt_ready:false,warning:'business authorization not completed'},0);
 assert.equal(partial.messages[0],'business authorization not completed');
 assert.equal(partial.feedback,'business authorization not completed');
 await verify('vpn',{jwxt_ready:true},1);
 await verify('jwxt',{step:'success'},1);
 console.log('Manual routes require explicit login; selection preserves the active route and partial VPN authorization is distinct.');
})().catch(error=>{console.error(error);process.exitCode=1});
