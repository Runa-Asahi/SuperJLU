// 回归：空教室自习时间 IIFE 若在 const DEF_PERIODS 之前调用 periodsToStudy，
// 会触发 TDZ（Cannot access 'DEF_PERIODS' before initialization），整页脚本中断，
// #boot「正在读取本地数据…」永远不消失。Run: node tests/js_boot_periods_tdz_test.js
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const page = fs.readFileSync('jlu_toolkit/ui_page.py', 'utf8');
const scripts = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.ok(scripts.length >= 1, 'expected inline scripts');
const main = scripts[scripts.length - 1];

const defIdx = main.indexOf('const DEF_PERIODS=');
const iifeIdx = main.indexOf('\nroomAutoSlot();');  // 打开页面时按当前时间选节次（原 IIFE）
const touchedIdx = main.indexOf('let _rTouched=');
assert.ok(defIdx >= 0, 'DEF_PERIODS missing');
assert.ok(iifeIdx >= 0, 'rooms init IIFE missing');
assert.ok(defIdx < iifeIdx, 'DEF_PERIODS must be initialized before roomAutoSlot() (TDZ)');
assert.ok(touchedIdx >= 0 && touchedIdx < iifeIdx, '_rTouched must be declared before roomAutoSlot() (TDZ)');
assert.ok(!main.includes('setRoomMode'), 'rooms mode tabs were removed (#113)');
assert.ok(main.includes('roomQueryMode'), 'roomQueryMode must pick date/week query');
assert.ok(main.includes('rdToWeek'), 'date↔week sync must remain');
assert.ok(main.includes('weekToRd'), 'week↔date sync must remain');

// 复现坏顺序会抛 TDZ；好顺序可安全调用
function runOrder(bad) {
  const body = bad
    ? `function periodMap(){return DEF_PERIODS}
       function periodsToStudy(){periodMap()}
       periodsToStudy();
       const DEF_PERIODS={1:["08:00","08:45"]};`
    : `const DEF_PERIODS={1:["08:00","08:45"]};
       function periodMap(){return DEF_PERIODS}
       function periodsToStudy(){periodMap()}
       periodsToStudy();`;
  vm.runInNewContext('"use strict";\n' + body);
}

assert.throws(() => runOrder(true), /DEF_PERIODS|before initialization|Cannot access/);
assert.doesNotThrow(() => runOrder(false));

// 编译整页主脚本（语法）；启动期 TDZ 已由上面顺序断言覆盖
new vm.Script(main);
console.log('js_boot_periods_tdz_test: ok');
