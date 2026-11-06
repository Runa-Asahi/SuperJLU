const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('jlu_toolkit/ui_page.py','utf8');
const code=source.slice(source.indexOf('let OA_DETAIL='),source.indexOf('$("#oa-kw").oninput'));
async function main(){
 const nodes=new Map(),pending=[],frames=[],events={},stack=[{}];let index=0,y=10413,focused=0;
 const row={dataset:{id:'a'},focus(o){assert.equal(o.preventScroll,true);focused++}};
 const $=s=>{if(!nodes.has(s))nodes.set(s,{hidden:false,innerHTML:'',querySelectorAll:()=>s==='#oa-box'?[row]:[]});return nodes.get(s)};
 const history={scrollRestoration:'auto',get state(){return stack[index]},pushState(s){stack.splice(++index);stack[index]=s},replaceState(s){stack[index]=s},back(){if(index){index--;events.popstate({state:stack[index]})}},forward(){if(index+1<stack.length){index++;events.popstate({state:stack[index]})}}};
 const ctx=vm.createContext({$,history,get scrollY(){return y},scrollTo(o){y=o.top},requestAnimationFrame:f=>frames.push(f),window:{addEventListener:(n,f)=>events[n]=f},document:{querySelector:()=>({click(){}})},api:()=>new Promise((resolve,reject)=>pending.push({resolve,reject})),esc:String,oaLink:()=>''});
 vm.runInContext(code,ctx);
 const result={item:{title:'Synthetic',text:'Readable',attachments:[]}};
 let request=ctx.openOA('a');assert.equal(index,1);assert.equal(y,0);assert.match($('#oa-detail-v').innerHTML,/oa-back/);
 // Back during loading must restore the list; a late response must not replace it.
 ctx.oaBack();frames.splice(0).forEach(f=>f());assert.equal(index,0);assert.equal(y,10413);assert.equal($('#oa-list-v').hidden,false);assert.equal(focused,1);
 pending.shift().resolve(result);await request;assert.equal($('#oa-detail-v').hidden,true);
 // Browser/System WebView Back uses the same history entry as the page Back button.
 request=ctx.openOA('a');pending.shift().resolve(result);await request;
 history.back();frames.splice(0).forEach(f=>f());assert.equal(y,10413);assert.equal(history.scrollRestoration,'auto');
 history.forward();pending.shift().resolve(result);await new Promise(setImmediate);assert.equal($('#oa-detail-v').hidden,false);
 history.back();frames.splice(0).forEach(f=>f());assert.equal(y,10413);
 // Failed requests keep Back available. Leaving for another tab invalidates pending content.
 request=ctx.openOA('a');pending.shift().reject(new Error('offline'));await request;assert.match($('#oa-detail-v').innerHTML,/读取失败/);ctx.oaBack();frames.splice(0).forEach(f=>f());assert.equal(y,10413);
 request=ctx.openOA('a');ctx.oaLeave();pending.shift().resolve(result);await request;assert.equal($('#oa-detail-v').hidden,true);assert.equal(history.state.sjNotice,undefined);
 console.log('Notice navigation: scroll restoration, browser back/forward, loading/error back and stale responses passed.');
}
function roomChecks(){
 const start=source.indexOf('// Room detail navigation:'),end=source.indexOf('function showRoomDetail(',start);
 const actions=[],frames=[],listeners={},stack=[{}];let index=0,y=2400,focus=0;
 const dialog={open:false,close(){if(this.open){this.open=false;actions.push(()=>listeners.close?.({}))}}};
 const history={scrollRestoration:'auto',get state(){return stack[index]},pushState(s){stack.splice(++index);stack[index]=s},replaceState(s){stack[index]=s},back(){actions.push(()=>{if(index)index--;listeners.popstate({state:stack[index]})})}};
 const query={periods:[1,2]},room={name:'Synthetic classroom'};
 const c=vm.createContext({history,get scrollY(){return y},scrollTo(o){y=o.top},requestAnimationFrame:f=>frames.push(f),ROOM_DETAIL:null,ROOM_RESULT:query,roomBackdropStart:null,
  $:()=>dialog,window:{addEventListener:(n,f)=>listeners[n]=f},document:{activeElement:{isConnected:true,focus(o){assert.equal(o.preventScroll,true);focus++}},querySelector:()=>({click(){}})}});
 vm.runInContext(source.slice(start,end),c);
 c.showRoomDetail=(r,j,b,entry)=>{if(c.roomHistoryOpen(r,j,b,entry)){dialog.open=true;c.ROOM_DETAIL={room:r,j,block:b}}};
 const flush=()=>{while(actions.length)actions.shift()();frames.splice(0).forEach(f=>f())};
 // Execute production cancel/close handlers too (the backdrop is tested separately).
 dialog.addEventListener=(n,f)=>listeners[n]=f;
 vm.runInContext(source.split('\n').filter(l=>l.startsWith('$("#room-detail").addEventListener("cancel"')||l.startsWith('$("#room-detail").addEventListener("close"')).join('\n'),c);
 c.showRoomDetail(room,query,-1);assert.equal(index,1);assert.equal(dialog.open,true);
 // Browser/WebView Back closes only the dialog and keeps the result position.
 index--;listeners.popstate({state:stack[index]});flush();assert.equal(dialog.open,false);assert.equal(y,2400);assert.equal(c.ROOM_DETAIL,null);assert.equal(history.scrollRestoration,'auto');assert.equal(focus,1);
 // Forward reopens the saved classroom without inserting another history entry.
 index++;listeners.popstate({state:stack[index]});assert.equal(dialog.open,true);assert.equal(stack.length,2);
 let cancelled=false;listeners.cancel({preventDefault(){cancelled=true}});flush();assert.ok(cancelled);assert.equal(index,0);assert.equal(dialog.open,false);
 // X/backdrop share one close path; duplicate closes must not back out of the app.
 c.showRoomDetail(room,query,-1);c.closeRoomDetail();c.closeRoomDetail();flush();assert.equal(index,0);assert.equal(dialog.open,false);
 // Programmatic closure (new query) also consumes its history marker once.
 c.showRoomDetail(room,query,-1);dialog.close();flush();assert.equal(index,0);assert.equal(c.ROOM_DETAIL,null);
 c.showRoomDetail(room,query,-1);c.roomLeave();flush();assert.equal(dialog.open,false);assert.equal(history.state.sjRoom,undefined);
 console.log('Room navigation: Back/Forward, Escape, repeated close, programmatic close, tab leave and result position passed.');
}
roomChecks();
main().catch(e=>{console.error(e);process.exitCode=1});
