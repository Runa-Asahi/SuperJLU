// 课表滑动判定 + 小组件导出：node tests/js_swipe_widget_test.js
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/../jlu_toolkit/ui_page.py','utf8').split('\n');
const pick=n=>{const i=src.findIndex(l=>l.startsWith(n));if(i<0)throw Error('missing '+n);let j=i+1;while(j<src.length&&/^[ \t]/.test(src[j]))j++;return src.slice(i,j).join('\n')};
const ctx=vm.createContext({});
vm.runInContext(['function kbSwipe(','function widgetExport('].map(pick).join('\n')+'\nthis.T={kbSwipe,widgetExport};',ctx);
const {kbSwipe,widgetExport}=ctx.T;
// 明确的整屏左滑/右滑
assert.equal(kbSwipe(-200,10,300,400),1);
assert.equal(kbSwipe(200,-10,300,400),-1);
// 太短（以前 60px 就切）
assert.equal(kbSwipe(-90,0,150,400),0);
assert.equal(kbSwipe(-130,0,200,400),0); // < 35% * 400 = 140
// 斜向 / 竖向滚动
assert.equal(kbSwipe(-200,100,300,400),0);
assert.equal(kbSwipe(-10,-300,300,400),0);
// 太慢（拖着看）
assert.equal(kbSwipe(-200,0,1200,400),0);
assert.equal(kbSwipe(-200,0,800,400),0);
// 点按 / 双击
assert.equal(kbSwipe(0,0,80,400),0);assert.equal(kbSwipe(3,2,0,400),0);
// 宽度未知时至少 120px
assert.equal(kbSwipe(-125,0,200,0),0);assert.equal(kbSwipe(-130,0,200,0),1);
const w=JSON.parse(JSON.stringify(widgetExport({first_monday:'2026-09-07T00:00',updated:'u',grades:[1],periods:{1:['08:00','08:45'],2:['x']},courses:[{name:'高数',location:'A',weekday:1,start:1,end:2,weeks:[1,'2']},{name:'X',weekday:2,start:1,src:'cancelled',weeks:[1]},{name:'坏',weekday:9,start:1,weeks:[1]}]})));
assert.deepEqual(w,{v:1,first_monday:'2026-09-07',periods:{1:['08:00','08:45']},courses:[{name:'高数',location:'A',teacher:'',weekday:1,start:1,end:2,weeks:[1,2]}],updated:'u'});
assert.equal(widgetExport(null),null);
console.log('ok');
