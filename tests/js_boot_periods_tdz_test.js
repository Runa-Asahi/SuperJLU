// 空教室已去掉自习时间 IIFE / DEF_PERIODS；保留主脚本可编译检查。
// Run: node tests/js_boot_periods_tdz_test.js
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const page = fs.readFileSync('jlu_toolkit/ui_page.py', 'utf8');
const scripts = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.ok(scripts.length >= 1, 'expected inline scripts');
const main = scripts[scripts.length - 1];

assert.ok(!main.includes('DEF_PERIODS'), 'DEF_PERIODS should be removed with study-time UI');
assert.ok(!main.includes('periodsToStudy'), 'periodsToStudy should be removed');
assert.ok(!main.includes('setRoomMode'), 'setRoomMode should be removed');
assert.ok(main.includes('rdToWeek'), 'date↔week sync must remain');
assert.ok(main.includes('weekToRd'), 'week↔date sync must remain');

new vm.Script(main);
console.log('js_boot_periods_tdz_test: ok');
