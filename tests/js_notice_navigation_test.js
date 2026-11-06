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
main().catch(e=>{console.error(e);process.exitCode=1});
