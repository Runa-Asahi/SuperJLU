// 课表紧凑偏好：默认开、关闭写 jlu-kb-compact、同步两个开关。node tests/js_timetable_compact_test.js
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/../jlu_toolkit/ui_page.py','utf8').split('\n');
const pick=n=>{const i=src.findIndex(l=>l.startsWith(n));if(i<0)throw Error('missing '+n);let j=i+1;while(j<src.length&&/^[ \t]/.test(src[j]))j++;return src.slice(i,j).join('\n')};
const store={};
const nodes=new Map();
const node=id=>{
  if(!nodes.has(id)){
    const o={id,checked:true,onchange:null,_class:new Set(),
      classList:{toggle(n,on){if(on)o._class.add(n);else o._class.delete(n);return on},contains(n){return o._class.has(n)}}};
    nodes.set(id,o);
  }
  return nodes.get(id);
};
const ctx=vm.createContext({
  localStorage:{getItem:k=>Object.prototype.hasOwnProperty.call(store,k)?store[k]:null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}},
  $:sel=>{if(sel==='#grid')return node('#grid');if(sel==='#kb-compact')return node('#kb-compact');if(sel==='#kb-compact-sz')return node('#kb-compact-sz');return null},
});
vm.runInContext([pick('function kbCompactOn('),pick('function applyKbCompact('),pick('function setKbCompact(')].join('\n')+'\nthis.API={kbCompactOn,applyKbCompact,setKbCompact};',ctx);
const A=ctx.API;

assert.equal(A.kbCompactOn(),true,'default compact on');
A.applyKbCompact();
assert.equal(node('#grid').classList.contains('kb-comfy'),false);
assert.equal(node('#kb-compact').checked,true);
assert.equal(node('#kb-compact-sz').checked,true);

A.setKbCompact(false);
assert.equal(store['jlu-kb-compact'],'false');
assert.equal(A.kbCompactOn(),false);
assert.equal(node('#grid').classList.contains('kb-comfy'),true);
assert.equal(node('#kb-compact').checked,false);
assert.equal(node('#kb-compact-sz').checked,false);

A.setKbCompact(true);
assert.equal(store['jlu-kb-compact'],'true');
assert.equal(node('#grid').classList.contains('kb-comfy'),false);
assert.equal(node('#kb-compact').checked,true);

// renderGrid 仍输出跨节与角标 class
const page=fs.readFileSync(__dirname+'/../jlu_toolkit/ui_page.py','utf8');
assert.match(page,/grid-row:\$\{c\.start\+1\}\/\$\{c\.end\+2\}/);
assert.match(page,/data-d="\$\{d\}" data-p="\$\{p\}"/);
assert.match(page,/function kbCls\(c\)\{return c\.src==="cancelled"\?" cancelled"/);
console.log('js_timetable_compact_test: ok');
