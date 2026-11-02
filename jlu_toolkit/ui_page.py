"""单页应用（内联 CSS/JS，无外部依赖）。"""

PAGE = r"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="/favicon.ico" sizes="any">
<meta name="theme-color" id="tc-l" content="#f6f7f9" media="(prefers-color-scheme: light)">
<meta name="theme-color" id="tc-d" content="#0e0f12" media="(prefers-color-scheme: dark)">
<script>/AppleWebKit/.test(navigator.userAgent)&&/SuperJLU-Android/.test(navigator.userAgent)&&document.documentElement.classList.add("in-app");</script>
<script>/* 首帧前应用主题，避免闪烁 */(function(){var P=window.__PREFS||{},t;try{var S=Storage.prototype,ls=window.localStorage,si=S.setItem,ri=S.removeItem;Object.keys(P).forEach(function(k){if(k.indexOf("jlu-")===0&&ls.getItem(k)!==P[k])si.call(ls,k,P[k])});var sync=function(o){try{fetch("/api/prefs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(o),keepalive:true}).catch(function(){})}catch(e){}};S.setItem=function(k,v){si.call(this,k,v);if(this===ls&&String(k).indexOf("jlu-")===0){var o={};o[k]=String(v);sync({set:o})}};S.removeItem=function(k){ri.call(this,k);if(this===ls&&String(k).indexOf("jlu-")===0)sync({remove:[String(k)]})};}catch(e){}t=P["jlu-theme"];if(t===undefined){try{t=localStorage.getItem("jlu-theme")}catch(e){}}window.__setTheme=function(t){var r=document.documentElement,l=document.getElementById("tc-l"),d=document.getElementById("tc-d");if(t==="light"||t==="dark")r.setAttribute("data-theme",t);else{r.removeAttribute("data-theme");t="system"}try{t==="system"?localStorage.removeItem("jlu-theme"):localStorage.setItem("jlu-theme",t)}catch(e){}if(l&&d){if(t==="system"){l.media="(prefers-color-scheme: light)";d.media="(prefers-color-scheme: dark)"}else{var c=t==="dark"?"#0e0f12":"#f6f7f9";l.content=d.content=c;l.media=d.media="all"}if(t==="system"){l.content="#f6f7f9";d.content="#0e0f12"}}document.querySelectorAll(".thm button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.theme===t))});window.__sjBars&&window.__sjBars(t)};if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);window.__sjBars=function(t){try{if(!window.SuperJLU)return;if(t!=="light"&&t!=="dark")t="system";var dk=t==="dark"||(t==="system"&&window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches);if(SuperJLU.setBars)SuperJLU.setBars(t);if(SuperJLU.setBarColors)SuperJLU.setBarColors(dk?"#0e0f12":"#f6f7f9",dk?"#17191e":"#ffffff",!!dk)}catch(e){}};window.__sjBars(t);try{matchMedia("(prefers-color-scheme: dark)").addEventListener("change",function(){var c=document.documentElement.getAttribute("data-theme");window.__sjBars(c||"system")})}catch(e){}})();</script>
<title>SuperJLU · 吉大人的一站式服务</title>
<style>
/* ===== 设计变量：柔和中性底色 + 单一沉稳强调色 ===== */
:root{--pri:#3b5bdb;--pri-h:#3249c0;--pri2:#edf1ff;--bg:#f6f7f9;--card:#fff;--card2:#fafbfc;--txt:#16181d;--sub:#6b7280;--line:#e8eaee;--ok:#16a34a;--ok2:#e9f7ee;--warn:#c2710c;--warn2:#fff4e5;--bad:#dc2626;--bad2:#fdeeee;--r:18px;--r-sm:12px;--sh:0 1px 2px rgba(16,24,40,.04),0 1px 3px rgba(16,24,40,.06);color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme]){--pri:#8ea2ff;--pri-h:#a5b4ff;--pri2:#1e2336;--bg:#0e0f12;--card:#17191e;--card2:#1c1f25;--txt:#eceef2;--sub:#9198a5;--line:#262a32;--ok:#4ade80;--ok2:#14261b;--warn:#fbbf24;--warn2:#2a2213;--bad:#f87171;--bad2:#2c1717;--sh:0 0 0 1px rgba(255,255,255,.03);color-scheme:dark}}
:root[data-theme=dark]{--pri:#8ea2ff;--pri-h:#a5b4ff;--pri2:#1e2336;--bg:#0e0f12;--card:#17191e;--card2:#1c1f25;--txt:#eceef2;--sub:#9198a5;--line:#262a32;--ok:#4ade80;--ok2:#14261b;--warn:#fbbf24;--warn2:#2a2213;--bad:#f87171;--bad2:#2c1717;--sh:0 0 0 1px rgba(255,255,255,.03);color-scheme:dark}
:root[data-theme=light]{color-scheme:light}
.thm{display:inline-flex;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:2px;gap:2px}.thm button{border:0;background:none;color:var(--sub);font:inherit;font-size:13px;padding:4px 10px;border-radius:999px;cursor:pointer}.thm button[aria-pressed=true]{background:var(--pri2);color:var(--pri);font-weight:600}
header .thm button{padding:4px 8px}
*{box-sizing:border-box}html,body{margin:0}
body{font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Source Han Sans SC","Microsoft YaHei",system-ui,sans-serif;background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased;padding-bottom:calc(84px + env(safe-area-inset-bottom))}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--pri2);color:var(--pri);padding:1px 6px;border-radius:6px}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 82%,transparent);backdrop-filter:saturate(1.6) blur(14px);-webkit-backdrop-filter:saturate(1.6) blur(14px);border-bottom:1px solid transparent;padding:calc(12px + env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) 12px max(16px,env(safe-area-inset-left));display:flex;align-items:center;gap:10px;min-width:0}
header .ttl{white-space:nowrap;flex:none}header>.thm,header>.btn{flex:none;white-space:nowrap}
@media(max-width:420px){header{gap:6px;padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right))}header .thm button{padding:3px 6px}header>.btn{padding-left:10px;padding-right:10px}header .lbl{display:none}}
@media(max-width:350px){header .logo{width:26px;height:26px}header h1{font-size:16px}header .thm button{padding:3px 4px}}
header .logo{width:30px;height:30px;color:var(--txt);flex:none;display:block}
header h1{font-size:17px;margin:0;flex:1;font-weight:680;letter-spacing:.2px;display:flex;flex-direction:column;line-height:1.25;min-width:0}
header small{color:var(--sub);font-size:12px;font-weight:450;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.btn{text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:4px;border:1px solid transparent;border-radius:999px;padding:7px 14px;font:inherit;font-size:14px;cursor:pointer;background:var(--pri2);color:var(--pri);font-weight:600;transition:background .15s,transform .1s,opacity .15s;white-space:nowrap}
.btn:hover{filter:brightness(.97)}.btn:active{transform:scale(.97)}.btn:disabled{opacity:.55;cursor:default}
.btn.pri{background:var(--pri);color:#fff}.btn.pri:hover{background:var(--pri-h);filter:none}
.btn.ghost{background:var(--card);border-color:var(--line);color:var(--txt)}
.btn[hidden]{display:none}
#del:disabled{display:none}
header .btn{background:var(--card);border-color:var(--line);color:var(--txt)}
:focus-visible{outline:2px solid var(--pri);outline-offset:2px}
main{max-width:1000px;margin:0 auto;padding:8px 14px 16px}
.card{background:var(--card);border-radius:var(--r);padding:18px;margin-bottom:14px;box-shadow:var(--sh);border:1px solid var(--line)}
.row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.sp{flex:1}
h2{font-size:16px;margin:0 0 12px;font-weight:680;letter-spacing:.2px}h2 .sub{font-weight:450;margin-left:4px}
.sub{color:var(--sub);font-size:13px}
/* 会话 / 状态横幅 */
.banner{display:flex;gap:12px;align-items:flex-start;border-radius:var(--r);padding:14px 16px;margin-bottom:14px;background:var(--warn2);color:var(--txt);border:1px solid color-mix(in srgb,var(--warn) 30%,transparent)}
.banner b{display:block;color:var(--warn);font-size:14px}.banner .sub{margin:2px 0 0}.banner .ic{font-size:18px;line-height:1.3;color:var(--warn)}
.banner.err{background:var(--bad2);border-color:color-mix(in srgb,var(--bad) 30%,transparent)}.banner.err b,.banner.err .ic{color:var(--bad)}
.academic-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.academic-head h2{margin:0}.academic-actions{display:flex;gap:8px;flex-wrap:wrap}.academic-actions .btn{white-space:nowrap}.academic-times{display:grid;gap:8px;margin:16px 0}.academic-times>div{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.academic-times dt{color:var(--sub);font-size:13px}.academic-times dd{margin:0;font-size:13px;font-weight:600;overflow-wrap:anywhere}.academic-status{padding:12px 14px;border-radius:var(--r);font-size:14px;font-weight:650;margin:12px 0 0;background:var(--pri2);color:var(--pri)}.academic-status[data-state=success]{background:color-mix(in srgb,var(--ok) 12%,var(--card));color:var(--ok)}.academic-status[data-state=failed],.academic-status[data-state=unconfirmed]{background:var(--bad2);color:var(--bad)}.academic-status:empty{display:none}@media(max-width:520px){.academic-head{display:block}.academic-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:12px}.academic-actions .btn{padding:9px 8px;font-size:13px}.academic-times>div{display:block}.academic-times dd{margin-top:3px}}
.progress-error{display:grid;grid-template-columns:minmax(0,1fr) auto}.progress-error>div{min-width:0;overflow-wrap:anywhere}.progress-error>.btn{white-space:nowrap}
@media(max-width:520px){.progress-error{grid-template-columns:minmax(0,1fr)}.progress-error>.btn{justify-self:end}}
.state{text-align:center;padding:48px 16px;color:var(--sub)}.state b{display:block;color:var(--txt);font-size:15px;margin-bottom:4px}
.spin{width:26px;height:26px;border-radius:50%;border:3px solid var(--line);border-top-color:var(--pri);margin:0 auto 12px;animation:sp 0.8s linear infinite}@keyframes sp{to{transform:rotate(360deg)}}
.sync-ind{width:16px;height:16px;border-radius:50%;border:2px solid var(--line);border-top-color:var(--pri);animation:sp .7s linear infinite;flex:none}
@media(prefers-reduced-motion:reduce){.sync-ind{animation:none;opacity:.75}}
.skel{height:14px;border-radius:8px;background:linear-gradient(90deg,var(--line),var(--card2),var(--line));background-size:200% 100%;animation:sk 1.2s ease-in-out infinite;margin:10px auto;max-width:420px}@keyframes sk{to{background-position:-200% 0}}
/* 底部导航：手机贴底，宽屏悬浮胶囊 */
nav{position:fixed;bottom:0;left:0;right:0;box-sizing:border-box;max-width:100vw;overflow:hidden;background:color-mix(in srgb,var(--card) 90%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-top:1px solid var(--line);display:flex;padding:4px 4px calc(4px + env(safe-area-inset-bottom));z-index:6}
nav button{flex:1 1 0;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border:0;background:none;padding:7px 0 6px;margin:2px;font:inherit;font-size:11.5px;color:var(--sub);cursor:pointer;border-radius:14px;transition:background .15s,color .15s}
nav button b{display:block;font-size:18px;line-height:1.25;font-weight:500}
.lga{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 6px}.lga span{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;font-size:13px;overflow:hidden}.lga span.on{border-color:var(--pri);background:var(--pri2);color:var(--pri)}.lga button{border:0;background:none;color:inherit;font:inherit;padding:5px 4px 5px 10px;cursor:pointer}.lga button.x{padding:5px 9px 5px 4px;color:var(--sub)}.lga button.add{padding:5px 10px;border:1px dashed var(--line);border-radius:999px;color:var(--sub)}
nav button{position:relative}nav button.upd-dot::after{content:"";position:absolute;top:6px;right:calc(50% - 16px);width:7px;height:7px;border-radius:50%;background:var(--pri)}
nav button.on{color:var(--pri);font-weight:650;background:var(--pri2)}
@media(max-width:380px){nav{padding-left:2px;padding-right:2px}nav button{margin:2px 1px;font-size:10.5px;padding:6px 0 5px;border-radius:11px}nav button b{font-size:16px}}
@media(min-width:760px){nav{left:50%;right:auto;bottom:18px;transform:translateX(-50%);border:1px solid var(--line);border-radius:999px;padding:5px;box-shadow:0 8px 30px rgba(16,24,40,.12)}nav button{flex:none;padding:7px 16px;border-radius:999px;font-size:13px;display:flex;align-items:center;gap:6px}nav button b{display:inline;font-size:15px}body{padding-bottom:100px}}
.tab{display:none}.tab.on{display:block;animation:fi .18s ease-out}@keyframes fi{from{opacity:0;transform:translateY(4px)}}
/* 课表 */
.wk{display:flex;align-items:center;gap:8px}
.wk .n{font-size:18px;font-weight:700;min-width:96px;text-align:center}
.wk .btn.ghost{width:36px;height:36px;padding:0;font-size:18px}
.kb-next{display:flex;align-items:center;gap:8px;margin:0 0 8px;min-width:0}
.kb-next[hidden]{display:none}
.kb-next .k{flex:none;font-size:11px;font-weight:700;line-height:1.6;color:var(--pri);background:var(--pri2);border-radius:999px;padding:1px 8px}
.kb-next .k.now{color:var(--ok);background:var(--ok2)}
.kb-next .main{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left;border:0;background:none;color:inherit;font:inherit;padding:2px 0;cursor:pointer}
.kb-next .main:disabled{cursor:default}
.kb-next .main b{font-weight:650}
.kb-next .sub{font-size:12px}
.kb-next .btn{flex:none;padding:4px 10px;font-size:12px}
.banner.slim{align-items:center;gap:8px;padding:7px 12px;margin-bottom:8px}
.banner.slim span{flex:1;min-width:0;font-size:13px;font-weight:650;color:var(--warn)}
.banner.slim .btn{padding:4px 12px;font-size:13px}
.grid{display:grid;grid-template-columns:22px repeat(7,minmax(0,1fr));gap:4px;margin-top:12px}
.card.kb{padding:14px 10px}
.grid .h{font-size:11px;line-height:1.35;color:var(--sub);text-align:center;padding:4px 0;border-radius:10px}
.grid .h.today{color:var(--pri);font-weight:700;background:var(--pri2)}
.grid .p{font-size:11px;color:var(--sub);text-align:center;display:flex;align-items:center;justify-content:center;line-height:1.15}
.grid .p em{font-style:normal;font-size:8.5px;opacity:.8}.grid .p em.pe{opacity:.5}
@media(min-width:640px){.grid .p em{font-size:10px}}
.off-card h3{font-size:15px;margin:0 0 10px;font-weight:680}.ogpa{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:2px 20px}
.ogpa div{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding:7px 0;font-size:13.5px}.ogpa b{color:var(--pri);font-variant-numeric:tabular-nums;font-size:15px}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:8px 0}.bar i{display:block;height:100%;background:var(--pri);border-radius:99px;transition:width .4s}
.grp{padding:12px 0;border-bottom:1px solid var(--line)}.grp:last-child{border:0}
.grp .row b{flex:1}
.miss,.done{display:inline-block;font-weight:600;font-size:12px;padding:1px 9px;border-radius:99px;line-height:1.6}
.miss{color:var(--bad);background:var(--bad2)}.done{color:var(--ok);background:var(--ok2)}
.big{font-size:34px;font-weight:750;color:var(--txt);letter-spacing:-.5px;font-variant-numeric:tabular-nums}
.cell{min-height:46px;border-radius:10px;background:var(--card2);border:1px dashed var(--line);cursor:pointer}
.cell{position:relative}.cell::after{content:"双击添加课程";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:2px;font-size:10px;line-height:1.2;color:var(--pri);opacity:0;transition:opacity .15s;pointer-events:none}
@media(hover:hover){.cell:hover{background:color-mix(in srgb,var(--pri) 12%,var(--card2));border-color:color-mix(in srgb,var(--pri) 55%,var(--line))}.cell:hover::after{opacity:.85}}
.cell.hint,.cell:focus-visible{background:color-mix(in srgb,var(--pri) 12%,var(--card2));border-color:color-mix(in srgb,var(--pri) 55%,var(--line))}.cell.hint::after,.cell:focus-visible::after{opacity:.85}
.cls{border-radius:10px;padding:4px 5px;font-size:10.5px;line-height:1.3;color:#fff;overflow:hidden;word-break:break-all;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12)}
.cls b{display:block;font-size:11px;font-weight:650}
@media(min-width:640px){.grid{grid-template-columns:36px repeat(7,minmax(0,1fr))}.cls{font-size:12.5px;padding:7px 8px}.cls b{font-size:13.5px}.cell{min-height:52px}}
.cls i{font-style:normal;opacity:.9}.cls i.tm span{display:inline-block;white-space:nowrap}.cls i.tm{display:block;margin-top:1px;font-size:.92em;opacity:.8;font-variant-numeric:tabular-nums}
.cls{cursor:pointer;position:relative}.cls:focus-visible{outline:2px solid var(--pri);outline-offset:1px}
.cls.custom{outline:2px dashed rgba(255,255,255,.95);outline-offset:-3px}
.cls.edited::after,.cls.custom::after,.cls.adjusted::after,.cls.cancelled::after{position:absolute;bottom:2px;right:2px;font-size:9px;font-weight:700;font-style:normal;line-height:14px;padding:0 3px;border-radius:6px;background:rgba(255,255,255,.92);color:#333}
.cls.edited::after{content:"改"}.cls.custom::after{content:"自"}.cls.adjusted::after{content:"调";background:#ffe08a}
.cls.cancelled{opacity:.62;box-shadow:inset 0 0 0 1px rgba(255,255,255,.35)}.cls.cancelled b,.cls.cancelled i{text-decoration:line-through}.cls.cancelled::after{content:"停";background:#fff;color:#b42318}
.adj-toggle{display:flex;align-items:center;gap:8px;margin-top:12px;font-weight:600}.adj-toggle input{width:18px;height:18px}
.kb-tools{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
#kb-issues{border-left:4px solid #e0a106}#kb-issues .kb-iss{border-top:1px solid var(--line);padding:10px 0 4px}#kb-issues .kb-iss:first-of-type{border-top:0}
.kb-form label{display:block;margin:8px 0 2px;font-size:13px}.kb-form input:not([type]),.kb-form input[type=text]{width:100%;box-sizing:border-box}
.kb-form .row label{display:inline-block;margin-right:6px}.kb-scope{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px}.kb-scope label{display:inline-flex;gap:4px;align-items:center}
.wkpick{display:grid;grid-template-columns:repeat(auto-fill,minmax(42px,1fr));gap:4px}.wkpick label{display:flex!important;align-items:center;gap:2px;margin:0!important;font-size:12.5px}
.kb-op{display:flex;align-items:center;gap:8px;justify-content:space-between;border-bottom:1px solid var(--line);padding:6px 0;font-size:13.5px}
#kb-backup-box textarea,#kb-paste{width:100%;box-sizing:border-box;font-size:12px}
.empty{color:var(--sub);text-align:center;padding:36px 0}
/* 成绩 */
.gpa{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;text-align:center}
.gpa div{background:var(--card2);border:1px solid var(--line);border-radius:var(--r-sm);padding:14px 4px}
.gpa div:nth-child(-n+2){background:var(--pri2);border-color:transparent}
.gpa b{display:block;font-size:26px;color:var(--txt);font-weight:720;font-variant-numeric:tabular-nums;letter-spacing:-.3px}.gpa div:nth-child(-n+2) b{color:var(--pri)}.gpa span{font-size:12px;color:var(--sub)}
.grade-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.grade-toolbar select{flex:1;min-width:160px}.grade-toolbar input[type=search]{flex:2;min-width:180px}
.grade-secondary{margin-top:12px;padding-top:10px;border-top:1px solid var(--line)}.grade-secondary>summary{font-size:12px;color:var(--sub)}.grade-secondary p{margin:8px 0}.grade-secondary .btn{font-size:12px}.grade-sync-status{min-height:20px;margin:6px 0 0}
.grade-caption{display:flex;align-items:center;gap:8px;margin:12px 0 0;flex-wrap:wrap}.grade-caption p{flex:1;margin:0;min-width:180px}.grade-policy{padding:10px 12px;margin-top:12px;background:var(--card2);border-radius:var(--r-sm);font-size:13px;color:var(--sub)}
.grade-rules{margin-top:12px;border:1px solid var(--line);border-radius:var(--r-sm);background:var(--card2);padding:10px 12px}.grade-rules>summary{font-size:13px;color:var(--pri);font-weight:600}.grade-rules>summary .sub{font-size:12px;font-weight:450;margin-left:8px}.grade-rules .grade-policy{margin:8px 0 0;padding:0;line-height:1.8}.grade-rules .grade-template-summary{margin-top:8px;background:var(--card)}.grade-visible{margin:12px 0 7px}.grade-bulk{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;max-width:440px}.grade-bulk .btn{min-width:0;padding:8px 10px;font-size:13px;min-height:40px}
@media(max-width:520px){.grade-rules>summary .sub{display:block;margin:2px 0 0 14px}.grade-bulk{gap:6px;max-width:none}.grade-bulk .btn{font-size:12px;padding:8px 5px}}
#grade-overview{position:relative;z-index:4;box-shadow:var(--sh),0 8px 20px rgba(16,24,40,.06)}
.grade-overview-slot{display:flow-root}
#grade-overview.grade-unpinned{position:static;box-shadow:var(--sh)}
.grade-delta{display:block;color:var(--sub);font-size:11px;line-height:1.5;font-weight:500;font-variant-numeric:tabular-nums}.grade-delta[hidden]{display:none}.grade-delta[data-direction=up]{color:var(--ok)}.grade-delta[data-direction=down]{color:var(--warn)}
.grade-issues{margin-top:12px;padding:12px 14px;border:1px solid color-mix(in srgb,var(--warn) 25%,var(--line));border-radius:var(--r-sm);background:var(--warn2)}.grade-issues[hidden]{display:none}.grade-issues h3{font-size:13px;margin:0 0 7px}.grade-issues p{font-size:12px;color:var(--sub);margin:6px 0 0}.grade-issues .grade-issue-critical{color:var(--bad);font-weight:600}.grade-issues .btn{font-size:12px;padding:4px 10px}.grade-issues .btn[aria-pressed=true]{background:var(--pri2);color:var(--pri);border-color:var(--pri)}
#grade-compact-live{display:none}
@media(min-width:521px){#grade-compact-live{visibility:hidden;pointer-events:none;position:fixed;top:calc(var(--app-header-height,76px) + 8px);z-index:4;display:flex;align-items:center;gap:14px;padding:10px 14px;margin:0;box-shadow:var(--sh),0 8px 20px rgba(16,24,40,.06)}#grade-compact-live.grade-compact-visible{visibility:visible;pointer-events:auto}#grade-compact-live>.gpa{flex:1;min-width:0;gap:8px}#grade-compact-live>.gpa>div{padding:2px 4px;border:0;background:none}#grade-compact-live>.gpa b{font-size:21px;line-height:1.25}#grade-compact-live>.gpa>div>span{font-size:11px}}
.grade-pin{font-size:12px;padding:5px 10px}.grade-pin svg{width:15px;height:15px;flex:none;transform:rotate(-35deg);transition:transform .15s}.grade-pin[aria-pressed=true]{background:var(--pri2);border-color:transparent;color:var(--pri)}.grade-pin[aria-pressed=true] svg{transform:none}
#dirty{color:var(--bad)}
.grade-unsaved{margin-left:6px}.grade-unsaved[hidden]{display:none}
.grade-mobile-live{display:none}
.grade-count .grade-count-selected{font:inherit;color:inherit}.grade-count .grade-count-total{font-size:.56em;color:var(--sub);font-weight:450;margin-left:3px;letter-spacing:0}.grade-count .grade-count-total span{font:inherit;color:inherit}
.grade-template-summary{margin-top:12px;padding:11px 13px;border:1px solid var(--line);border-radius:var(--r-sm);background:var(--card2);font-size:13px;line-height:1.8}.grade-template-summary[hidden]{display:none}.grade-template-summary p{margin:3px 0}.grade-template-base{color:var(--sub)}.grade-template-base strong{color:var(--txt);font-weight:600}.grade-change-label{font-weight:600;margin-right:5px}.grade-change-label.added{color:var(--ok)}.grade-change-label.removed{color:var(--warn)}.grade-change-course{overflow-wrap:anywhere}.grade-change-more{display:inline}.grade-change-more>summary{display:inline;list-style:none;color:var(--pri);cursor:pointer;font-size:12px;font-weight:600;margin-left:4px;white-space:nowrap}.grade-change-more>summary::before{content:none}.grade-change-more[open]>span{display:block;margin:4px 0 6px;padding:7px 10px;border-radius:8px;background:var(--card);color:var(--sub)}
@media(max-width:520px){#grade-overview{position:static;box-shadow:var(--sh)}#grade-overview>.gpa{display:none}#grade-overview .grade-caption{margin-top:0}.grade-pin{display:none}.grade-mobile-live{display:block;position:sticky;top:calc(var(--app-header-height,76px) + 6px);z-index:4;padding:10px!important;box-shadow:var(--sh),0 6px 18px rgba(16,24,40,.08)}.grade-mobile-live .gpa{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.grade-mobile-live .gpa>div{padding:8px 4px}.grade-mobile-live .gpa b{font-size:24px;line-height:1.3}.grade-live-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 4px 0;color:var(--sub);font-size:11px}.grade-live-meta b{font-size:14px;color:var(--txt);font-weight:650;font-variant-numeric:tabular-nums}.grade-live-meta .grade-count .grade-count-total{font-size:11px}.grade-template-summary{padding:9px 10px;font-size:12px}.grade-template-toolbar select{flex-basis:100%;min-width:0}.grade-template-toolbar .btn{font-size:12px;padding:7px 11px}}
#grade-filter{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}#grade-filter>summary{font-size:13px;font-weight:600;color:var(--pri)}#grade-filter .rgrid{margin-top:12px}
.grade-choices{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.grade-choices label{display:flex;align-items:center;gap:5px;font-size:12px;padding:4px 9px;background:var(--card2);border:1px solid var(--line);border-radius:999px}.grade-choices label:has(:checked){background:var(--pri2);border-color:var(--pri);color:var(--pri)}.grade-choices input{width:14px;height:14px;margin:0}
.grade-table{overflow-x:auto;padding:4px 8px}.grade-table table{min-width:640px}.grade-table th{position:static;white-space:nowrap}.grade-table th button{background:none;border:0;color:inherit;padding:0;font:inherit;cursor:pointer;text-align:inherit}.grade-table th[aria-sort=ascending],.grade-table th[aria-sort=descending]{color:var(--pri)}.grade-table .name{font-weight:550}.grade-table .chip{margin-top:3px}.grade-table tr.failed td,.grade-table tr.failed .sub,.grade-table tr.failed .chip{color:var(--bad)}.grade-table tr.failed .chip{background:var(--bad2)}.grade-table tr.failed.off td{opacity:.75}
.grade-table input[type=checkbox]{cursor:pointer}.grade-table .selected-label{display:block}.grade-badge{font-size:11px;color:var(--sub);font-weight:400;display:block}.grade-import-notes{margin-top:10px}.grade-import-notes p{margin:5px 0}.grade-import-notes summary{font-size:12px;color:var(--sub)}
dialog.grade-dialog{border:1px solid var(--line);border-radius:var(--r);padding:22px;width:min(92vw,540px);max-height:85vh;overflow:auto;background:var(--card);color:var(--txt);box-shadow:0 20px 65px rgba(0,0,0,.25)}dialog.grade-dialog::backdrop{background:rgba(0,0,0,.4);backdrop-filter:blur(3px)}.grade-dialog h3{font-size:14px;margin:18px 0 6px}.grade-dialog .grade-template-name{color:var(--pri);font-weight:600}.grade-dialog p{font-size:13px;color:var(--sub)}.grade-dialog a{color:var(--pri)}.grade-dialog .college-links{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grade-dialog .college-links a{font-size:13px;padding:10px;border:1px solid var(--line);border-radius:var(--r-sm);text-decoration:none}.grade-keywords{display:flex;flex-wrap:wrap;gap:7px}.grade-keywords button{white-space:normal;text-align:left;font-size:12px}
@media(max-width:520px){#t-cj .gpa{grid-template-columns:repeat(2,1fr)}.grade-toolbar input[type=search]{width:100%;flex-basis:100%}.grade-toolbar .btn{font-size:12px;padding:7px 11px}.grade-dialog .college-links{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left}
tbody tr:last-child td{border-bottom:0}
th{font-size:12px;color:var(--sub);font-weight:600;position:sticky;top:58px;background:var(--card)}
#network-report th{position:static;white-space:nowrap}#network-report td{vertical-align:top;font-size:12px;overflow-wrap:anywhere}#network-report td:first-child{min-width:90px}#network-report td:nth-child(2){white-space:nowrap}#network-report th:nth-child(2){width:60px}
#network-route{font-size:12.5px}#network-route strong{color:var(--pri);font-weight:650}.login-route-label{font-size:12px;font-weight:600}#network-route-current{font-size:16px;font-weight:700;line-height:1.4}#network-route-last{font-size:12px;font-weight:600}.room-error{margin-top:14px;flex-wrap:wrap}.room-error[hidden]{display:none}.room-error>div{flex:1;min-width:180px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover td{background:var(--card2)}
tr.off td{opacity:.42}
.term td{background:var(--pri2)!important;font-size:12px;color:var(--pri);font-weight:650;padding:6px 10px}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--pri)}
select,input[type=text],input[type=password],input[type=search],input[type=date],input[type=number],input:not([type]){font:inherit;font-size:14px;padding:8px 11px;border-radius:var(--r-sm);border:1px solid var(--line);background:var(--card2);color:var(--txt);min-height:38px;transition:border-color .15s,box-shadow .15s}
select:focus,input:focus{outline:0;border-color:var(--pri);box-shadow:0 0 0 3px var(--pri2)}
.chip{display:inline-block;font-size:11.5px;padding:1px 9px;border-radius:99px;background:var(--pri2);color:var(--pri);font-weight:550;line-height:1.6}
/* 考试 */
.exam{display:flex;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}
.exam:last-child{border:0}
.cd{min-width:74px;text-align:center;border-radius:var(--r-sm);padding:9px 4px;background:var(--pri2);color:var(--pri)}
.cd b{display:block;font-size:24px;line-height:1.1;font-variant-numeric:tabular-nums}.cd span{font-size:11px}
.cd.soon{background:var(--bad2);color:var(--bad)}.cd.past{background:var(--card2);color:var(--sub)}
.exam .t{flex:1}.exam .t b{display:block}
#toast{position:fixed;right:20px;bottom:96px;display:flex;flex-direction:column;align-items:flex-end;gap:8px;z-index:100;max-width:min(420px,90vw);pointer-events:none}.toast-item{background:var(--txt);color:var(--bg);padding:10px 18px;border-radius:var(--r-sm);font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.18);animation:toast-in .18s ease-out}.toast-item.bad{background:var(--bad);color:#fff}.toast-item.leaving{opacity:0;transform:translateY(-5px);transition:opacity .35s,transform .35s}@keyframes toast-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.toast-item{animation:none}.toast-item.leaving{transition:none}}
.seg{display:flex;gap:4px;margin-bottom:14px;background:var(--card2);border:1px solid var(--line);padding:4px;border-radius:999px}.seg button{flex:1;padding:7px;border:0;background:transparent;border-radius:999px;color:var(--sub);font:inherit;font-size:14px;cursor:pointer}.seg button.on{background:var(--card);color:var(--pri);font-weight:650;box-shadow:var(--sh)}
.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}.rgrid label{display:flex;flex-direction:column;font-size:12px;gap:5px;color:var(--sub);font-weight:550}.rgrid select,.rgrid input{width:100%;box-sizing:border-box}
.rng{display:flex;align-items:center;gap:4px}.rng input{min-width:0}
#t-js .room-form h2{margin-bottom:6px}
.rgrp{padding:10px 0;border-top:1px solid var(--line)}
.rgrp:first-of-type{border-top:0;padding-top:4px}
.rgrp-h{font-size:12px;font-weight:650;color:var(--sub);margin-bottom:6px;letter-spacing:.02em}
#t-js .rgrid.r2{display:grid;grid-template-columns:1fr 1fr;gap:8px 10px;margin-top:0}
#t-js .rgrid.r2 .r-full{grid-column:1/-1}
#t-js .rgrid label{font-size:12px;gap:3px}
#t-js .rgrid select,#t-js .rgrid input{height:34px;padding:4px 8px;font-size:13px;border-radius:8px;min-width:0}
#t-js .rng{gap:4px;color:var(--sub)}
#t-js input[type=time]{border:1px solid var(--line);background:var(--card2);color:var(--txt);font:inherit;font-size:13px;color-scheme:light dark}
#t-js .rng input{flex:1;text-align:center}
.rchips.seg{flex-wrap:nowrap;overflow-x:auto;margin:0;padding:3px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.rchips.seg::-webkit-scrollbar{display:none}
.rchips.seg button{flex:1 0 auto;padding:5px 12px;font-size:13px;min-width:52px}
.rchips-row{display:flex;align-items:center;gap:6px;margin-top:8px;flex-wrap:nowrap}
.rchips-row .sub{font-size:12px;margin-right:2px}
.chip{border:1px solid var(--line);background:var(--card);color:var(--txt);border-radius:999px;padding:4px 12px;font:inherit;font-size:12px;cursor:pointer;line-height:1.4}
.chip:active,.chip.on{background:var(--pri2);color:var(--pri);border-color:transparent}
.rcheck{display:flex;align-items:center;gap:6px;margin-top:8px;font-size:13px;color:var(--txt)}
.rcheck input{width:16px;height:16px;margin:0}
#rmore summary{font-size:13px;color:var(--sub);cursor:pointer}
#rmore #rextra{margin-top:8px}
.rq-btn{width:100%;margin-top:10px;padding:9px 14px;font-size:15px}
details#rmore{margin-top:12px}
table.rt{border-collapse:collapse;width:100%;font-size:13px}.rt th,.rt td{padding:8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}.rt th{cursor:pointer;user-select:none;position:static;top:auto;background:transparent}
.room-results,#room-error{scroll-margin-top:calc(var(--app-header-height,76px) + 14px)}.room-results:focus{outline:none}.room-results-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}.room-results-head h2{margin:0;flex:1;min-width:180px}.room-results-head h2 .sub{display:block;margin:4px 0 0;font-size:12px}.room-view{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:2px;background:var(--card2);border:1px solid var(--line);padding:3px;border-radius:999px;isolation:isolate;flex:none}.room-view::before{content:"";position:absolute;top:3px;bottom:3px;left:3px;width:calc((100% - 8px)/2);border-radius:999px;background:var(--pri);transition:transform .2s ease;z-index:-1}.room-view[data-view=cards]::before{transform:translateX(calc(100% + 2px))}.room-view button{border:0;background:transparent;color:var(--sub);font:inherit;font-size:12px;font-weight:600;padding:6px 12px;border-radius:999px;cursor:pointer}.room-view button[aria-pressed=true]{color:#fff}.room-sort{display:flex;justify-content:flex-end;align-items:center;gap:8px;margin-bottom:12px}.room-sort label{font-size:12px;color:var(--sub)}.room-sort select{font-size:12px;min-height:32px;padding:4px 8px;max-width:180px}.room-sort .btn{padding:4px 10px;font-size:12px;min-height:32px}
.room-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.room-tile{--room-color:#3b6ee8;display:flex;flex-direction:column;gap:14px;min-width:0;min-height:132px;padding:14px;text-align:left;border:2px solid var(--room-color);border-radius:var(--r-sm);background:color-mix(in srgb,var(--room-color) 10%,var(--card));color:var(--txt);font:inherit;cursor:pointer;transition:background .15s,box-shadow .15s}.room-tile:hover{background:color-mix(in srgb,var(--room-color) 16%,var(--card));box-shadow:0 3px 10px color-mix(in srgb,var(--room-color) 14%,transparent)}.room-tile[data-wide=true]{grid-column:span 2}.room-tile[data-tone="1"]{--room-color:#099a83}.room-tile[data-tone="2"]{--room-color:#9260dc}.room-tile[data-tone="3"]{--room-color:#df527e}.room-tile[data-tone="4"]{--room-color:#d58120}.room-tile[data-tone="5"]{--room-color:#189ebc}.room-tile[data-tone="6"]{--room-color:#b552bc}.room-tile[data-tone="7"]{--room-color:#629b30}.room-tile[data-tone="8"]{--room-color:#d46439}.room-tile[data-tone="9"]{--room-color:#6264d6}.room-tile-top{display:flex;align-items:flex-start;gap:8px}.room-tile-top b{font-size:15px;line-height:1.45;overflow-wrap:anywhere;flex:1;min-width:0}.room-type-icon{width:23px;height:23px;color:color-mix(in srgb,var(--room-color) 78%,var(--txt));flex:none}.room-tile-location{display:block;color:var(--sub);font-size:11px;line-height:1.5;margin-top:4px;overflow-wrap:anywhere}.room-tile-foot{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:6px;margin-top:auto}.room-tile-seats{font-size:12px;color:var(--sub);font-variant-numeric:tabular-nums}.room-free-label{font-size:11px;line-height:1.5;padding:3px 7px;border-radius:6px;background:color-mix(in srgb,var(--room-color) 15%,var(--card));color:color-mix(in srgb,var(--room-color) 65%,var(--txt));font-weight:650}.room-table-wrap{overflow-x:auto}.room-name-button{border:0;background:none;font:inherit;color:var(--pri);padding:4px 0;text-align:left;cursor:pointer}.rt th button{font:inherit;color:inherit;border:0;padding:0;background:none;cursor:pointer}.room-detail-heading{flex-wrap:nowrap;align-items:flex-start}.room-detail-heading h2{flex:1;min-width:0;margin:0;overflow-wrap:anywhere}.room-detail-fields{display:grid;grid-template-columns:90px minmax(0,1fr);gap:12px 16px;font-size:13px;margin:18px 0 0}.room-detail-fields dt{color:var(--sub)}.room-detail-fields dd{margin:0;overflow-wrap:anywhere}
@media(max-width:800px){.room-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:520px){.room-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.room-tile{padding:11px;min-height:128px;gap:12px}.room-tile-top{gap:6px}.room-tile-top b{font-size:14px}.room-type-icon{width:20px;height:20px}.room-results-head{gap:10px}.room-results-head h2{min-width:140px;font-size:14px}.room-view button{padding:6px 10px}.room-dialog{margin:auto 0 0!important;width:100%!important;max-width:none;max-height:80dvh!important;border-radius:20px 20px 0 0!important;padding-bottom:calc(22px + env(safe-area-inset-bottom))!important}.room-detail-fields{grid-template-columns:76px minmax(0,1fr);gap:12px}.room-sort{justify-content:flex-start}}
@media(prefers-reduced-motion:reduce){.room-view::before,.room-tile{transition:none}}

/* Compact result cards; daily instruments are created only inside the dialog. */
.room-list-tools{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:10px}.room-list-tools .room-sort{margin:0}.room-day-fav-only{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--sub)}.room-day-fav-only input{width:15px;height:15px;accent-color:var(--pri)}
.room-day-group h3{display:flex;align-items:center;gap:6px;font-size:13px;margin:14px 0 8px}.room-day-group h3 .sub{font-size:11px;font-weight:400}.room-day-group h3 svg{width:17px;height:17px;color:var(--sub)}
.room-grid.room-day-grid{grid-template-columns:repeat(6,minmax(0,1fr));grid-auto-flow:row;gap:8px}
.room-tile.room-day-card{cursor:pointer;min-height:86px;padding:10px;display:flex;flex-direction:column;gap:8px;grid-column:auto;background:color-mix(in srgb,var(--room-color) 6%,var(--card));border:1px solid color-mix(in srgb,var(--room-color) 40%,var(--line));border-left:3px solid var(--room-color);box-shadow:none}
.room-tile.room-day-card[data-wide=true]{grid-column:span 2}.room-day-card .room-tile-top{align-items:flex-start;gap:5px}.room-day-identity{flex:1;min-width:0}.room-day-name{font:inherit;font-size:14px;font-weight:700;line-height:1.4;overflow-wrap:anywhere;background:none;border:0;padding:0;color:var(--txt);text-align:left;cursor:pointer;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.room-day-name:hover{color:var(--pri)}
.room-day-card .room-type-icon{width:16px;height:16px;flex:none;margin-top:2px;color:color-mix(in srgb,var(--room-color) 72%,var(--txt))}.room-day-card[data-wide=true] .room-type-icon{width:19px;height:19px;margin-top:0}.room-day-star.btn{font-size:18px;min-width:22px;width:22px;height:24px;padding:0;border:0;background:transparent;color:var(--sub);flex:none}.room-day-star[aria-pressed=true]{color:var(--warn)}
.room-compact-meta{display:flex;align-items:center;justify-content:space-between;gap:4px;flex-wrap:wrap;font-size:10px;color:var(--sub);margin-top:auto}.room-compact-meta>span:first-child{white-space:nowrap}.room-next{font-size:10px;white-space:nowrap;color:var(--sub);line-height:1.6}.room-next[data-state=free]{color:var(--ok)}.room-next[data-state=unavailable]{color:var(--warn)}.room-compact-location{font-size:10px;color:var(--sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:-4px}.room-list-note{font-size:11px;color:var(--sub);margin:12px 0 0}
.room-detail-overview{display:flex;align-items:center;justify-content:center;padding:8px 0}.room-day-gauge{width:230px;max-width:100%;flex:none}.room-day-gauge svg{display:block;width:100%;overflow:visible}.room-day-gauge text{fill:var(--sub);font-size:11px}.room-day-gauge .room-day-total{fill:var(--txt);font-size:26px;font-weight:750}.room-day-gauge .room-day-total-note{font-size:10px}.room-day-free{stroke:var(--ok)}.room-day-unavailable{stroke:color-mix(in srgb,var(--sub) 22%,var(--card))}.room-day-unknown{stroke:var(--sub);stroke-dasharray:2 3;opacity:.65}
.room-day-blocks{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:3px}.room-day-blocks button{font:inherit;font-size:11px;color:var(--sub);padding:7px 1px;border:0;background:transparent;border-radius:6px;cursor:pointer}.room-day-blocks strong{color:var(--txt);font-size:12px;margin-left:4px}.room-day-blocks button:hover{color:var(--pri);background:var(--pri2)}
.room-day-status{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:11px;color:var(--sub);margin:0 0 12px}.room-day-status .btn{font-size:11px;padding:4px 8px}.room-day-detail-block{padding:11px 0;border-top:1px solid var(--line);scroll-margin-top:12px}.room-day-detail-block.active{background:var(--pri2);border-radius:8px;padding:11px 8px}.room-day-detail-head{display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px}.room-day-detail-head span{color:var(--sub);font-size:11px}.room-day-periods{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}.room-day-period{padding:8px 3px;border-radius:8px;background:var(--card2);text-align:center;font-size:11px;color:var(--sub);border:1px solid transparent}.room-day-period b{display:block;color:var(--txt);font-size:13px}.room-day-period small{display:block;font-size:10px;margin:4px 0}.room-day-period.free{background:var(--ok2);color:var(--ok);border-color:color-mix(in srgb,var(--ok) 25%,transparent)}.room-day-period.unknown{background:transparent;border:1px dashed var(--line)}.room-metadata{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.room-metadata>summary{font-size:12px;color:var(--sub)}
@media(max-width:1099px){.room-grid.room-day-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
@media(max-width:899px){.room-grid.room-day-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:699px){.room-grid.room-day-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:479px){.room-grid.room-day-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.room-list-tools{gap:8px}.room-list-tools .room-sort{gap:5px}.room-list-tools .room-sort select{max-width:115px}.room-tile.room-day-card{padding:9px;gap:7px}.room-day-card .room-type-icon{width:15px;height:15px}.room-day-name{font-size:14px}}
@media(max-width:299px){.room-grid.room-day-grid{grid-template-columns:1fr}.room-tile.room-day-card[data-wide=true]{grid-column:span 1}}
@media(pointer:coarse){.room-day-card{min-height:90px!important}.room-day-blocks button{min-height:44px}.room-day-name{min-height:26px}.room-day-star.btn{min-width:28px;height:30px}}

.room-query-period{display:inline-block;white-space:nowrap;margin-left:8px;font-size:13px;font-weight:500}
.room-grid{grid-auto-flow:row dense}
@media(max-width:520px){.room-query-period{display:block;margin:3px 0 0;font-size:12px;color:var(--sub)}}
details>summary{cursor:pointer;list-style:none}details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"›";display:inline-block;width:14px;color:var(--sub);transition:transform .15s;font-weight:700}details[open]>summary::before{transform:rotate(90deg)}
details.gc{margin-top:8px}details.gc summary{font-size:12.5px;color:var(--sub)}
details.tn{border-left:2px solid var(--line);padding:6px 0 6px 12px;margin-top:6px;border-radius:0 0 0 4px}details.tn>summary{padding:2px 0}
details.tn[open]{border-left-color:color-mix(in srgb,var(--pri) 35%,var(--line))}
@media(max-width:520px){main{padding:6px 10px 12px}.card{padding:14px;border-radius:16px}.gpa b{font-size:22px}.big{font-size:28px}}
/* OA 通知 */
.oal{list-style:none;margin:0;padding:0}.oal li{display:flex;gap:10px;align-items:flex-start;padding:12px 4px;border-bottom:1px solid var(--line);cursor:pointer;border-radius:10px}.oal li:last-child{border-bottom:0}.oal li:hover{background:var(--card2)}
.oal .tt{font-weight:600;line-height:1.45;flex:1;min-width:0}.oal .mt{display:block;color:var(--sub);font-size:12.5px;font-weight:450;margin-top:2px}.oal .ar{color:var(--sub);flex:none}
.pin{display:inline-block;background:var(--warn2);color:var(--warn);font-size:11.5px;font-weight:650;padding:0 7px;border-radius:999px;margin-right:6px;vertical-align:1px}
#oa-ch button{flex:none;white-space:nowrap;padding:7px 14px}.oaf{display:flex;gap:8px;flex-wrap:wrap}.oaf input{flex:2;min-width:160px}.oaf select{flex:1;min-width:120px}
.oad h2{font-size:18px;line-height:1.45}.oad .body{white-space:pre-wrap;line-height:1.8;margin:14px 0;word-break:break-word}.oad .att{display:flex;flex-direction:column;gap:6px;margin-top:8px}.oad .att a{color:var(--pri);text-decoration:none;font-weight:550}.oad .att a:hover{text-decoration:underline}
.soon{display:inline-block;background:var(--pri2);color:var(--pri);font-size:11.5px;font-weight:650;padding:1px 8px;border-radius:999px;vertical-align:2px;margin-left:6px}
/* 「更多」设置列表 */
.sl h2{margin-bottom:8px}.sl .seg{margin:8px 0 6px}.sl .row{margin:8px 0 2px;align-items:center}.sl-note{font-size:12px;margin:8px 0 0}
.srow{border-top:1px solid var(--line);padding:11px 2px;margin:0}.sl h2+.srow,.sl .srow:first-of-type{}
.srow.flat{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.srow.flat>span:first-child{flex:1;min-width:120px;font-size:14px}.srow.flat small{display:block;font-size:12px;margin-top:1px}
.srow>summary{cursor:pointer;font-size:14px;list-style:none;display:flex;align-items:center}.srow>summary::-webkit-details-marker{display:none}.srow[open]>summary{margin-bottom:8px}
label.srow{cursor:pointer}.srow .btn{padding:6px 12px;font-size:13px}.srow .thm button{padding:5px 10px;font-size:12.5px}
/* 校园服务：小方块 + #140 免登/状态 */
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:8px}
.lk{position:relative;display:flex;flex-direction:column;align-items:center;background:var(--card2);border:1px solid var(--line);border-radius:var(--r-sm);min-width:0}
.lk>a.go{display:flex;flex-direction:column;align-items:center;gap:6px;width:100%;padding:12px 6px 10px;color:var(--txt);text-decoration:none;border-radius:inherit}.lk>a.go:hover{background:var(--pri2)}
.lk .ic{width:36px;height:36px;border-radius:11px;background:var(--pri2);color:var(--pri);display:grid;place-items:center;font-size:18px}
.lk b{font-size:12.5px;font-weight:600;line-height:1.3;text-align:center;word-break:break-all}
.lk .vpn{font-size:11px;color:var(--pri);text-decoration:none;padding:0 6px 8px;margin-top:-4px}.lk .vpn:hover{text-decoration:underline}
.lk .dot{position:absolute;top:7px;right:7px;width:7px;height:7px;border-radius:50%;background:var(--sub)}.lk .dot.ok{background:var(--ok,#16a34a)}.lk .dot.bad{background:var(--warn)}.lk .dot.fail{background:var(--bad)}
.links-toolbar{margin:0 0 8px;gap:6px}.links-toolbar button{font-size:12px;padding:5px 10px}.links-caption{font-size:12px;color:var(--sub);margin:0 0 8px;line-height:1.45}
.offl{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:2px 10px;border-radius:999px;margin:0 0 10px;background:var(--card2);color:var(--sub,inherit);border:1px dashed var(--line)}
.tag{display:inline-block;font-size:11.5px;font-weight:600;padding:0 8px;border-radius:999px;line-height:1.7;background:var(--warn2);color:var(--warn)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

html.in-app header{padding-top:10px}
/* 安卓原生层已经按真实系统栏高度垫了上下色块，网页不再叠加 safe-area，避免底栏上方多出一截空白 */
.in-app body{padding-bottom:84px}.in-app nav{padding-bottom:4px}.in-app #toast{bottom:84px}
dialog#login{border:0;border-radius:16px;padding:20px;width:min(92vw,380px);background:var(--card,#fff);color:inherit;box-shadow:0 12px 40px rgba(0,0,0,.25)}
dialog#login::backdrop{background:rgba(0,0,0,.4)}
dialog#login label{display:block;margin:10px 0 4px;font-size:13px;opacity:.8}
dialog#login input[type=text],dialog#login input[type=password]{width:100%;box-sizing:border-box}
dialog#login .cap{display:flex;gap:8px;align-items:center}dialog#login .cap img{height:40px;image-rendering:pixelated;border-radius:6px;cursor:pointer;background:#fff}
dialog#login .err{color:#d4573b;font-size:13px;min-height:18px;margin:8px 0 0}
dialog#login .lg-pass-ok{display:block;color:var(--ok);font-size:15px;font-weight:700;letter-spacing:.2px}
dialog#login .vpn-hint{margin-top:10px;padding:10px 12px;border-radius:10px;background:var(--pri2);color:var(--txt);font-size:13px;line-height:1.5}
dialog#login .vpn-hint a{color:var(--pri);font-weight:600}
#oa-ch{display:flex;align-items:center;gap:6px;flex-wrap:nowrap}
#oa-ch .oa-chip{display:inline-flex;align-items:center;gap:2px;flex:none}
#oa-ch .oa-chip button.ch{white-space:nowrap;padding:7px 12px}
#oa-ch .oa-chip .mv{padding:4px 6px;font-size:12px;line-height:1;min-width:0}
#oa-ch .oa-add{flex:none;padding:7px 12px}
#oa-pick details{margin-top:8px;border:1px solid var(--line);border-radius:10px;padding:8px 10px}
#oa-pick details>summary{cursor:pointer;font-weight:600;font-size:13.5px}
#oa-pick .cols{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
#oa-pick .cols label{display:flex;align-items:center;gap:6px;font-size:13px;padding:6px 10px;border:1px solid var(--line);border-radius:999px;cursor:pointer;background:var(--card2)}
#oa-pick .cols label.on{border-color:var(--pri);background:var(--pri2);color:var(--pri);font-weight:600}
#oa-manage{margin-top:10px}
#oa-manage .row-acts{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
</style></head>
<body>
<header><svg class="logo" viewBox="0 0 1024 1024" aria-hidden="true" focusable="false"><g transform="translate(0 1024) scale(.1 -.1)" fill="currentColor"><path d="M4735 10230 c-3 -6 -50 -10 -105 -10 -55 0 -102 -4 -105 -10 -3 -5 -37 -10 -75 -10 -38 0 -72 -4 -75 -10 -3 -5 -32 -10 -65 -10 -40 0 -59 -4 -63 -14 -3 -8 -23 -14 -53 -14 -26 -1 -52 -6 -58 -12 -5 -5 -32 -10 -58 -10 -26 0 -48 -4 -48 -10 0 -5 -18 -10 -39 -10 -22 0 -43 -4 -46 -10 -3 -5 -24 -10 -46 -10 -21 0 -39 -4 -39 -10 0 -5 -13 -10 -30 -10 -16 0 -30 -4 -30 -10 0 -5 -18 -10 -39 -10 -22 0 -43 -4 -46 -10 -3 -5 -17 -10 -30 -10 -13 0 -27 -4 -30 -10 -3 -5 -20 -10 -36 -10 -17 0 -32 -6 -35 -15 -4 -8 -19 -15 -34 -15 -16 0 -32 -4 -35 -10 -3 -5 -15 -10 -25 -10 -11 0 -35 -9 -55 -20 -20 -11 -47 -20 -60 -20 -14 0 -25 -4 -25 -10 0 -5 -9 -10 -20 -10 -11 0 -20 -4 -20 -10 0 -5 -12 -10 -27 -11 -16 0 -41 -9 -58 -19 -59 -37 -88 -50 -112 -50 -12 0 -23 -4 -23 -10 0 -5 -9 -10 -20 -10 -11 0 -20 -4 -20 -10 0 -5 -9 -10 -20 -10 -11 0 -20 -4 -20 -10 0 -5 -6 -10 -12 -10 -22 0 -154 -69 -173 -90 -10 -11 -26 -20 -37 -20 -10 0 -18 -4 -18 -10 0 -5 -9 -10 -20 -10 -11 0 -20 -4 -20 -10 0 -5 -9 -10 -20 -10 -11 0 -20 -4 -20 -10 0 -5 -8 -10 -17 -10 -9 0 -25 -7 -35 -17 -19 -17 -49 -36 -83 -52 -12 -5 -27 -16 -34 -25 -7 -9 -19 -16 -26 -16 -6 0 -20 -9 -30 -20 -10 -11 -25 -20 -34 -20 -9 0 -23 -9 -31 -20 -8 -11 -20 -20 -27 -20 -6 0 -27 -16 -46 -35 -19 -19 -40 -35 -46 -35 -7 0 -26 -13 -41 -30 -15 -16 -34 -30 -42 -30 -8 0 -29 -16 -48 -35 -19 -19 -39 -35 -44 -35 -6 0 -31 -21 -57 -46 -26 -25 -57 -51 -69 -58 -60 -30 -57 -33 145 -236 104 -104 194 -190 200 -190 6 0 217 -207 470 -460 253 -253 465 -460 472 -460 6 0 293 -281 637 -625 343 -344 629 -625 635 -625 6 0 454 -443 996 -985 542 -542 990 -985 995 -985 17 0 170 -156 170 -173 0 -9 7 -17 16 -17 9 0 283 -268 611 -595 327 -327 600 -595 606 -595 7 0 262 -250 567 -555 311 -311 563 -555 572 -555 10 0 18 7 18 16 0 9 14 29 30 44 17 15 30 35 30 43 0 8 16 29 35 46 19 17 35 37 35 46 0 8 9 20 20 27 11 7 20 18 20 24 0 17 29 70 45 84 8 7 15 20 15 29 0 9 9 22 19 28 20 13 51 67 51 90 0 7 5 13 10 13 6 0 10 8 10 18 0 10 9 24 20 32 11 8 20 19 20 26 0 13 42 98 60 119 7 8 9 15 5 15 -5 0 -2 8 6 18 22 27 39 60 39 77 0 8 5 15 10 15 6 0 10 9 10 20 0 11 5 20 10 20 6 0 10 9 10 20 0 11 5 20 10 20 6 0 10 6 10 13 0 15 41 99 59 120 6 8 9 21 6 29 -3 8 1 21 10 28 8 7 15 21 15 31 0 11 5 19 10 19 6 0 10 14 10 30 0 17 5 30 10 30 6 0 10 9 10 19 0 11 5 23 10 26 6 3 10 17 10 30 0 13 5 27 10 30 6 3 10 19 10 36 0 16 5 29 10 29 6 0 10 13 10 29 0 16 7 34 15 41 9 7 13 21 10 30 -3 9 1 23 10 30 8 7 15 27 15 46 0 18 5 36 10 39 6 3 10 19 10 36 0 16 5 29 10 29 6 0 10 18 10 40 0 26 -5 40 -13 40 -7 0 -48 34 -90 75 -43 41 -82 75 -87 75 -5 0 -59 50 -120 110 -61 61 -115 110 -121 110 -6 0 -62 52 -125 115 -63 63 -120 115 -127 115 -7 0 -55 43 -107 95 -52 52 -99 95 -105 95 -6 0 -60 50 -120 110 -60 61 -114 110 -120 110 -6 0 -53 43 -105 95 -52 52 -99 95 -105 95 -6 0 -57 47 -115 105 -58 58 -109 105 -115 105 -6 0 -50 38 -97 85 -48 47 -91 85 -97 85 -5 0 -48 38 -95 85 -47 47 -91 85 -98 85 -6 0 -44 34 -84 75 -40 41 -78 75 -86 75 -7 0 -51 39 -97 85 -46 47 -89 85 -95 85 -6 0 -49 38 -96 85 -47 47 -89 85 -95 85 -6 0 -40 29 -75 65 -35 36 -69 65 -75 65 -6 0 -48 38 -95 85 -47 47 -89 85 -95 85 -6 0 -44 34 -85 75 -41 41 -80 75 -86 75 -7 0 -51 38 -98 85 -47 47 -90 85 -96 85 -7 0 -40 29 -75 65 -35 36 -69 65 -76 65 -7 0 -50 38 -95 85 -46 47 -89 85 -96 85 -7 0 -51 38 -98 85 -47 47 -89 85 -95 85 -6 0 -40 29 -75 65 -35 36 -69 65 -75 65 -6 0 -44 34 -85 75 -41 41 -79 75 -85 75 -6 0 -48 38 -95 85 -47 47 -90 85 -97 85 -7 0 -45 34 -84 75 -40 41 -78 75 -86 75 -8 0 -42 29 -77 65 -34 36 -68 65 -75 65 -6 0 -41 29 -77 65 -36 36 -70 65 -75 65 -5 0 -37 27 -71 60 -35 33 -68 60 -73 60 -6 0 -40 29 -75 65 -35 36 -69 65 -75 65 -6 0 -35 25 -65 55 -30 30 -59 55 -65 55 -12 1 -105 88 -105 99 0 5 24 9 52 10 29 0 54 5 56 11 2 6 53 10 127 10 72 0 126 4 130 10 4 6 75 10 180 10 105 0 176 -4 180 -10 4 -6 57 -10 125 -10 68 0 121 -4 125 -10 3 -5 37 -10 74 -10 49 0 72 -4 81 -15 8 -10 31 -15 71 -15 33 0 59 -4 59 -10 0 -5 22 -10 49 -10 28 0 53 -4 56 -10 3 -5 24 -10 46 -10 21 0 39 -4 39 -10 0 -5 13 -10 29 -10 17 0 33 -4 36 -10 3 -5 21 -10 40 -10 19 0 37 -4 40 -10 3 -5 24 -10 45 -10 21 0 42 -4 45 -10 3 -5 17 -10 30 -10 13 0 26 -4 30 -9 8 -14 65 -41 86 -41 10 0 21 -4 24 -10 3 -5 19 -10 36 -10 16 0 29 -4 29 -10 0 -5 9 -10 20 -10 11 0 20 -4 20 -10 0 -5 9 -10 19 -10 11 0 23 -4 26 -10 3 -5 14 -10 24 -10 20 0 118 -47 127 -61 3 -5 14 -9 25 -9 10 0 19 -4 19 -10 0 -5 9 -10 20 -10 11 0 20 -4 20 -10 0 -5 6 -10 13 -10 18 0 75 -28 82 -41 4 -5 25 -18 48 -28 24 -11 51 -29 61 -40 11 -12 24 -21 31 -21 7 0 20 -9 30 -20 10 -11 25 -20 34 -20 9 0 23 -9 31 -20 8 -11 22 -20 32 -20 10 0 18 -4 18 -9 0 -5 16 -16 35 -25 20 -10 41 -26 48 -37 6 -10 19 -19 27 -19 9 0 34 -18 55 -40 21 -22 44 -40 50 -40 6 0 35 -25 65 -55 30 -30 59 -55 65 -55 5 0 255 -245 555 -545 300 -300 550 -545 555 -545 6 0 78 -67 160 -150 82 -82 155 -150 162 -150 6 0 68 -56 137 -125 68 -69 129 -125 136 -125 6 0 74 -63 150 -140 76 -77 144 -140 150 -140 7 0 75 -63 152 -140 77 -77 145 -140 152 -140 7 0 50 -38 95 -85 46 -47 85 -85 87 -85 2 0 4 72 4 160 0 100 -4 160 -10 160 -6 0 -10 50 -10 130 0 80 -4 130 -10 130 -6 0 -10 33 -10 79 0 44 -4 83 -10 86 -5 3 -10 32 -10 64 0 38 -5 63 -14 70 -9 8 -12 24 -9 49 4 27 1 42 -11 51 -11 9 -16 30 -16 62 0 26 -4 51 -10 54 -5 3 -10 21 -10 40 0 19 -4 37 -10 40 -5 3 -10 24 -10 46 0 21 -4 39 -10 39 -5 0 -10 18 -10 39 0 22 -4 43 -10 46 -5 3 -10 24 -10 46 0 21 -4 39 -10 39 -5 0 -10 13 -10 29 0 17 -4 33 -10 36 -5 3 -10 21 -10 39 0 19 -7 39 -16 47 -8 7 -13 21 -11 31 3 10 -1 25 -9 32 -8 8 -14 26 -14 40 0 14 -4 26 -10 26 -5 0 -10 11 -10 25 0 13 -9 40 -20 60 -11 20 -20 47 -20 60 0 14 -4 25 -10 25 -5 0 -10 14 -10 30 0 17 -4 30 -10 30 -5 0 -10 8 -10 19 0 10 -7 24 -15 31 -9 7 -13 21 -10 31 3 9 1 20 -4 23 -13 8 -41 65 -41 83 0 7 -4 13 -10 13 -5 0 -10 9 -10 20 0 11 -4 20 -10 20 -5 0 -10 9 -10 20 0 11 -4 20 -10 20 -5 0 -10 9 -10 20 0 11 -4 20 -10 20 -5 0 -10 8 -11 18 0 9 -9 31 -19 47 -32 52 -70 128 -70 142 0 7 -4 13 -10 13 -5 0 -10 9 -10 20 0 11 -4 20 -10 20 -5 0 -10 8 -10 18 0 10 -9 24 -20 32 -11 8 -20 19 -20 26 0 17 -29 70 -46 85 -8 7 -24 31 -34 54 -10 23 -26 48 -35 55 -8 7 -15 20 -15 29 0 9 -9 22 -20 29 -11 7 -20 19 -20 28 0 9 -11 25 -25 36 -14 11 -25 26 -25 35 0 8 -14 28 -30 43 -16 15 -30 33 -30 40 0 6 -13 25 -30 43 -16 18 -30 37 -30 43 0 7 -16 26 -35 43 -19 17 -35 36 -35 44 0 7 -18 31 -40 52 -22 21 -40 44 -40 50 0 6 -45 55 -100 110 -55 55 -100 104 -100 110 0 13 -222 235 -235 235 -6 0 -48 38 -95 85 -47 47 -89 85 -95 85 -6 0 -29 18 -50 40 -21 22 -44 40 -50 40 -6 0 -26 16 -45 35 -19 19 -39 35 -44 35 -6 0 -25 14 -43 30 -18 17 -38 30 -45 30 -7 0 -26 16 -43 35 -16 19 -37 35 -45 35 -9 0 -22 9 -30 20 -8 11 -21 20 -30 20 -9 0 -22 9 -30 20 -8 11 -22 20 -31 20 -9 0 -22 7 -29 15 -7 9 -32 25 -55 35 -23 10 -47 26 -54 34 -15 18 -68 46 -88 46 -7 0 -13 5 -13 10 0 6 -8 10 -18 10 -10 0 -24 9 -32 20 -8 11 -21 20 -30 21 -8 0 -28 9 -45 19 -50 31 -169 90 -183 90 -6 0 -12 5 -12 10 0 6 -9 10 -20 10 -11 0 -20 5 -20 10 0 6 -9 10 -20 10 -11 0 -20 5 -20 10 0 6 -9 10 -19 10 -11 0 -23 5 -26 10 -3 6 -17 10 -30 10 -13 0 -26 4 -29 9 -10 16 -109 61 -133 61 -13 0 -23 5 -23 10 0 6 -11 10 -25 10 -13 0 -40 9 -60 20 -20 11 -44 20 -55 20 -10 0 -22 5 -25 10 -3 6 -19 10 -35 10 -15 0 -30 7 -34 15 -3 9 -18 15 -35 15 -16 0 -33 5 -36 10 -3 6 -17 10 -30 10 -13 0 -27 5 -30 10 -3 6 -17 10 -30 10 -13 0 -27 5 -30 10 -3 6 -24 10 -46 10 -21 0 -39 5 -39 10 0 6 -18 10 -39 10 -22 0 -43 5 -46 10 -3 6 -24 10 -46 10 -21 0 -39 5 -39 10 0 6 -22 10 -48 10 -26 0 -53 5 -58 10 -6 6 -32 11 -58 12 -30 0 -50 6 -53 14 -3 9 -22 14 -53 14 -27 0 -52 5 -55 10 -3 6 -42 10 -85 10 -43 0 -82 5 -85 10 -3 6 -50 10 -105 10 -55 0 -102 4 -105 10 -4 6 -143 10 -385 10 -242 0 -381 -4 -385 -10z M1177 8252 c-15 -15 -27 -34 -27 -41 0 -7 -13 -26 -30 -41 -16 -15 -30 -34 -30 -42 0 -7 -9 -20 -20 -28 -11 -8 -20 -22 -20 -31 0 -10 -11 -26 -25 -37 -14 -11 -25 -26 -25 -34 0 -8 -9 -23 -20 -33 -11 -10 -20 -24 -20 -30 0 -7 -7 -18 -15 -25 -9 -7 -24 -32 -35 -54 -10 -23 -28 -50 -39 -60 -12 -11 -21 -27 -21 -38 0 -10 -4 -18 -10 -18 -5 0 -10 -8 -10 -18 0 -10 -9 -24 -20 -32 -11 -8 -20 -22 -20 -32 0 -10 -4 -18 -10 -18 -5 0 -10 -6 -10 -13 0 -14 -38 -90 -70 -142 -10 -16 -19 -38 -19 -47 -1 -10 -5 -18 -11 -18 -5 0 -10 -9 -10 -20 0 -11 -4 -20 -10 -20 -5 0 -10 -9 -10 -20 0 -11 -4 -20 -10 -20 -5 0 -10 -9 -10 -20 0 -11 -4 -20 -10 -20 -5 0 -10 -8 -10 -19 0 -10 -6 -24 -14 -31 -8 -6 -12 -18 -9 -26 3 -8 -1 -22 -8 -32 -26 -32 -39 -62 -39 -87 0 -14 -4 -25 -10 -25 -5 0 -10 -9 -10 -20 0 -11 -4 -20 -10 -20 -5 0 -10 -9 -10 -20 0 -11 -4 -20 -10 -20 -5 0 -10 -13 -10 -29 0 -17 -4 -33 -10 -36 -5 -3 -10 -19 -10 -36 0 -16 -4 -29 -10 -29 -5 0 -10 -12 -10 -26 0 -14 -7 -32 -15 -40 -8 -8 -12 -21 -8 -30 3 -8 -2 -23 -12 -34 -10 -11 -15 -26 -12 -34 3 -8 -1 -20 -9 -26 -8 -7 -14 -30 -14 -51 0 -22 -4 -39 -10 -39 -5 0 -10 -13 -10 -30 0 -16 -4 -30 -10 -30 -5 0 -10 -18 -10 -39 0 -22 -4 -43 -10 -46 -5 -3 -10 -24 -10 -46 0 -21 -4 -39 -10 -39 -5 0 -10 -18 -10 -39 0 -22 -4 -43 -10 -46 -5 -3 -10 -32 -10 -64 0 -42 -5 -62 -16 -72 -12 -9 -15 -24 -11 -51 3 -25 0 -41 -9 -49 -8 -7 -14 -31 -14 -60 0 -27 -4 -49 -10 -49 -6 0 -10 -35 -10 -85 0 -50 -4 -85 -10 -85 -6 0 -10 -45 -10 -114 0 -66 -4 -117 -10 -121 -14 -8 -14 -725 0 -725 6 0 10 -45 10 -114 0 -66 4 -117 10 -121 6 -3 10 -42 10 -85 0 -43 5 -82 10 -85 6 -3 10 -33 10 -65 0 -36 5 -60 12 -62 7 -3 11 -24 9 -59 -1 -40 2 -59 14 -69 10 -8 15 -29 15 -61 0 -27 5 -49 10 -49 6 0 10 -18 10 -39 0 -22 4 -43 10 -46 5 -3 10 -24 10 -46 0 -21 5 -39 10 -39 6 0 10 -18 10 -39 0 -22 5 -43 10 -46 6 -3 10 -17 10 -30 0 -13 5 -27 10 -30 6 -3 10 -22 10 -41 0 -20 7 -42 15 -50 8 -8 12 -21 8 -30 -3 -8 2 -23 11 -33 9 -10 14 -25 11 -33 -3 -8 1 -21 10 -28 8 -7 15 -23 15 -36 0 -12 4 -26 10 -29 6 -3 10 -15 10 -26 0 -10 5 -19 10 -19 6 0 10 -13 10 -30 0 -22 5 -30 18 -30 18 0 76 52 72 65 -1 4 25 36 59 71 34 36 61 69 61 74 0 5 29 38 65 74 36 35 65 70 65 76 0 7 29 41 65 76 36 35 65 69 65 75 0 6 29 41 65 77 36 36 65 70 65 76 0 7 22 34 50 61 28 27 50 54 50 60 0 6 29 40 65 75 36 35 65 69 65 75 0 6 29 40 65 75 36 35 65 70 65 76 0 7 29 40 65 75 36 34 65 69 65 77 0 8 29 42 65 76 36 34 65 67 65 74 0 7 27 40 60 72 33 32 60 65 60 72 0 8 18 32 40 53 l40 39 16 -22 c8 -12 21 -22 28 -22 7 0 38 -25 69 -55 30 -30 61 -55 67 -55 7 0 31 -20 54 -45 24 -25 48 -45 55 -45 7 0 34 -22 61 -50 27 -27 55 -50 63 -50 8 0 38 -25 66 -55 29 -30 58 -55 64 -55 7 0 37 -25 67 -55 30 -30 59 -55 65 -55 6 0 29 -18 50 -40 21 -22 44 -40 50 -40 6 0 35 -25 65 -55 30 -30 59 -55 65 -55 6 0 34 -23 63 -50 29 -28 56 -50 61 -50 5 0 34 -25 65 -55 30 -30 60 -55 66 -55 7 0 32 -20 57 -45 24 -25 49 -45 55 -45 5 0 27 -18 48 -40 21 -22 45 -40 52 -40 8 0 34 -20 58 -45 24 -25 49 -45 55 -45 6 0 33 -23 60 -50 27 -28 54 -50 60 -50 6 0 31 -20 55 -45 24 -25 49 -45 55 -45 6 0 24 -13 40 -30 16 -17 35 -30 43 -30 8 0 32 -20 54 -45 22 -25 47 -45 55 -45 8 0 32 -18 53 -40 21 -22 45 -40 53 -40 7 0 31 -20 53 -45 21 -24 46 -45 54 -45 9 0 34 -18 55 -40 21 -22 44 -40 50 -40 6 0 31 -20 55 -45 24 -25 49 -45 55 -45 6 0 24 -13 40 -30 16 -16 34 -30 40 -30 6 0 31 -20 55 -45 24 -25 50 -45 58 -45 8 0 27 -13 42 -30 15 -16 33 -30 39 -30 6 0 31 -20 54 -45 24 -25 49 -45 56 -45 7 0 26 -13 41 -30 15 -16 35 -30 43 -30 8 0 33 -20 56 -45 23 -25 47 -45 54 -45 7 0 31 -18 52 -40 21 -22 44 -40 50 -40 6 0 31 -20 55 -45 24 -25 49 -45 55 -45 6 0 29 -18 50 -40 21 -22 44 -40 50 -40 6 0 31 -20 55 -45 24 -25 50 -45 58 -45 8 0 27 -13 42 -30 15 -16 33 -30 39 -30 7 0 31 -20 55 -45 25 -25 49 -45 55 -45 6 0 34 -22 63 -50 29 -27 57 -50 63 -50 6 0 31 -20 55 -45 24 -25 49 -45 55 -45 14 0 72 -60 59 -61 -5 -1 -23 0 -40 1 -17 0 -36 -5 -42 -13 -7 -8 -34 -15 -69 -16 -32 -1 -59 -6 -61 -11 -2 -6 -81 -10 -198 -10 -137 0 -200 -4 -215 -13 -17 -9 -23 -9 -26 1 -3 9 -43 12 -153 12 -86 0 -150 4 -152 10 -1 5 -33 10 -70 11 -43 1 -72 7 -79 15 -7 9 -33 14 -70 14 -32 0 -61 5 -64 10 -3 6 -28 10 -56 10 -27 0 -49 5 -49 10 0 6 -22 10 -49 10 -28 0 -53 5 -56 10 -3 6 -17 10 -30 10 -13 0 -27 5 -30 10 -3 6 -24 10 -46 10 -21 0 -39 5 -39 10 0 6 -9 10 -19 10 -11 0 -23 5 -26 10 -3 6 -21 10 -40 10 -19 0 -36 4 -40 9 -9 16 -66 41 -92 41 -12 0 -23 5 -23 10 0 6 -11 10 -24 10 -13 0 -50 14 -81 30 -31 17 -68 30 -81 30 -13 0 -24 5 -24 10 0 6 -9 10 -20 10 -11 0 -20 5 -20 10 0 6 -9 10 -20 10 -11 0 -23 7 -26 15 -4 8 -15 15 -25 15 -10 0 -19 5 -19 10 0 6 -8 10 -19 10 -10 0 -24 7 -31 15 -7 8 -40 29 -74 45 -34 16 -70 38 -81 50 -10 11 -23 20 -30 20 -7 0 -20 9 -30 20 -10 11 -25 20 -34 20 -9 0 -23 9 -31 20 -8 11 -22 20 -32 20 -10 0 -18 4 -18 9 0 5 -15 16 -32 24 -18 9 -46 29 -62 46 -17 17 -35 31 -41 31 -6 0 -24 13 -40 30 -16 17 -34 30 -40 30 -6 0 -33 23 -60 51 -28 28 -58 54 -67 58 -23 9 -388 372 -388 386 0 6 -25 35 -55 65 -30 29 -52 56 -50 59 8 7 -27 41 -42 41 -17 0 -403 -384 -403 -400 0 -7 -83 -95 -185 -196 -102 -101 -185 -189 -185 -195 0 -7 -65 -77 -145 -157 -80 -80 -145 -150 -145 -157 0 -6 -11 -22 -25 -35 -25 -24 -33 -50 -15 -50 6 0 10 -7 10 -15 0 -8 20 -35 45 -59 25 -25 45 -50 45 -56 0 -6 25 -36 55 -66 30 -31 55 -60 55 -66 0 -5 43 -53 95 -106 52 -53 95 -101 95 -107 0 -14 132 -145 146 -145 6 0 58 -47 116 -105 58 -58 110 -105 116 -105 6 0 31 -20 55 -45 25 -25 50 -45 56 -45 6 0 30 -18 52 -40 23 -22 47 -40 54 -40 6 0 29 -20 51 -45 21 -24 46 -45 55 -45 8 0 28 -14 44 -30 16 -17 34 -30 40 -30 6 0 22 -11 35 -25 13 -14 29 -25 35 -25 7 0 20 -9 30 -20 10 -11 23 -20 30 -20 7 0 20 -9 30 -20 10 -11 26 -20 37 -20 10 0 18 -4 18 -10 0 -5 7 -10 16 -10 9 0 27 -11 40 -25 13 -14 30 -25 39 -25 8 0 15 -4 15 -10 0 -5 8 -10 19 -10 10 0 24 -7 31 -15 7 -8 49 -33 94 -55 46 -22 91 -49 101 -60 10 -11 26 -20 37 -20 10 0 18 -4 18 -10 0 -5 9 -10 20 -10 11 0 20 -4 20 -10 0 -5 9 -10 20 -10 11 0 20 -4 20 -10 0 -5 7 -10 15 -10 8 0 30 -9 50 -20 20 -11 42 -20 49 -20 17 0 74 -28 81 -41 4 -5 15 -9 26 -9 10 0 19 -4 19 -10 0 -5 14 -10 30 -10 17 0 30 -4 30 -10 0 -5 9 -10 19 -10 11 0 23 -4 26 -10 3 -5 17 -10 30 -10 13 0 27 -5 30 -10 3 -6 15 -10 26 -10 10 0 19 -4 19 -10 0 -5 14 -10 30 -10 17 0 30 -4 30 -10 0 -5 13 -10 29 -10 16 0 34 -7 41 -15 7 -9 19 -14 26 -11 6 2 20 -2 31 -9 10 -8 28 -15 40 -15 12 0 25 -4 28 -10 3 -5 19 -10 36 -10 16 0 29 -4 29 -10 0 -5 18 -10 39 -10 22 0 43 -4 46 -10 3 -5 19 -10 36 -10 16 0 29 -4 29 -10 0 -5 18 -10 39 -10 22 0 43 -4 46 -10 3 -5 26 -10 50 -10 24 0 47 -5 50 -10 3 -6 28 -10 54 -10 31 0 53 -5 61 -15 8 -10 31 -15 71 -15 33 0 59 -4 59 -10 0 -6 30 -10 69 -10 39 0 73 -5 76 -10 3 -6 42 -10 85 -10 43 0 82 -5 85 -10 8 -14 815 -14 815 0 0 6 36 10 89 10 50 0 93 5 96 10 3 6 37 10 75 10 38 0 72 5 75 10 3 6 32 10 64 10 37 0 63 5 70 13 6 8 30 14 53 15 23 1 47 7 52 12 6 6 27 10 48 10 21 0 38 5 38 10 0 6 18 10 39 10 22 0 43 5 46 10 3 6 24 10 46 10 21 0 39 5 39 10 0 6 14 10 30 10 17 0 30 5 30 10 0 6 18 10 39 10 22 0 43 5 46 10 3 6 17 10 30 10 13 0 27 5 30 10 3 6 20 10 36 10 17 0 32 6 35 15 4 8 19 15 34 15 16 0 32 5 35 10 3 5 17 10 30 10 13 0 27 5 30 10 3 5 19 10 36 10 16 0 29 5 29 10 0 6 9 10 20 10 11 0 20 5 20 10 0 6 12 10 28 11 15 0 50 14 77 29 104 59 150 80 172 80 13 0 23 5 23 10 0 6 9 10 20 10 11 0 20 5 20 10 0 6 6 10 13 10 18 0 75 28 83 41 3 6 16 15 27 20 12 5 36 18 52 28 17 11 38 20 48 20 9 1 17 6 17 11 0 6 9 10 20 10 11 0 20 5 20 10 0 6 9 10 20 10 11 0 20 5 20 10 0 6 8 10 18 10 11 0 27 9 37 20 10 11 23 20 30 20 6 0 22 11 35 25 13 14 29 25 35 25 7 0 20 9 30 20 10 11 23 20 30 20 7 0 20 9 30 20 10 11 25 20 34 20 9 0 23 9 31 20 8 11 20 20 27 20 8 0 29 16 47 35 19 19 40 35 46 35 6 0 29 18 50 40 21 22 45 40 53 40 8 0 29 16 46 35 17 19 36 35 43 35 8 0 43 29 78 65 35 36 70 65 77 65 7 0 13 7 13 15 0 16 -1775 1795 -1792 1795 -6 0 -346 335 -756 745 -410 410 -750 745 -756 745 -6 0 -286 275 -621 610 -335 336 -614 610 -620 610 -6 0 -255 245 -555 545 -300 300 -549 545 -555 545 -6 0 -244 234 -530 520 -286 286 -526 520 -532 520 -15 0 -82 70 -83 85 0 14 -72 85 -85 85 -5 0 -64 54 -130 120 l-121 120 -27 -28z"/></g></svg><h1><span class="ttl">SuperJLU</span><small class="sub" style="font-weight:500">吉大人的一站式服务</small> <small id="upd"></small></h1>
<div class="thm" role="group" aria-label="外观"><button type="button" data-theme="system" aria-pressed="true" title="跟随系统">◐</button><button type="button" data-theme="light" aria-pressed="false" title="浅色">☀</button><button type="button" data-theme="dark" aria-pressed="false" title="深色">☾</button></div>
<span id="sync-ind" class="sync-ind" hidden title="正在刷新" aria-hidden="true"></span><button class="btn" id="refresh" title="强制重新获取全部数据，包括学业和培养方案；不会请求教务重算" aria-label="强制刷新">⟳<span class="lbl"> 强制刷新</span></button></header>
<main>
<div id="sess" hidden></div><div id="offl" hidden></div>
<div id="boot" class="card"><div class="state"><div class="spin"></div><b>正在读取本地数据…</b><div class="skel"></div><div class="skel" style="max-width:300px"></div></div></div>
<section class="tab on" id="t-kb">
 <div class="card" id="kb-issues" role="status" hidden></div>
 <div class="card kb">
  <div class="kb-next" id="kb-next" hidden></div>
  <div class="row wk"><button class="btn ghost" id="prev">‹</button><div class="n" id="wkn">第 1 周</div><button class="btn ghost" id="next">›</button><span class="sp"></span><button class="btn" id="today">本周</button></div>
  <div class="grid" id="grid"></div>
  <div class="kb-tools"><button type="button" class="btn" id="kb-add">＋ 添加课程</button><span class="sub" style="align-self:center">点一节课可以修改或隐藏，双击空白格添加这一节</span></div>
 </div>
</section>
<section class="tab" id="t-cj">
 <div class="grade-overview-slot" id="grade-overview-slot"><div class="card" id="grade-overview"><div class="row grade-overview-heading" style="margin-bottom:14px"><h2 style="margin:0">成绩与绩点</h2><span class="sp"></span><span class="chip" id="grade-source">教务成绩</span><button type="button" class="btn ghost grade-pin" id="grade-pin" data-grade-pin aria-label="成绩统计吸顶" aria-pressed="true" title="取消吸顶"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l-1 7 4 4v2H6v-2l4-4-1-7ZM12 16v6"/></svg><span>已吸顶</span></button><button class="btn ghost" id="grade-help" aria-label="成绩帮助" title="成绩帮助">?</button></div>
  <div class="gpa"><div><b id="g-score" data-grade-value="score">—</b><span>加权成绩</span><small class="grade-delta" data-grade-delta="score" hidden></small></div><div><b id="g-gpa" data-grade-value="point">—</b><span>加权绩点</span><small class="grade-delta" data-grade-delta="point" hidden></small></div><div><b id="g-cr" data-grade-value="credit">—</b><span>计入学分</span></div><div><b id="g-n" class="grade-count" aria-label="已选 0 门，共 0 门课程" title="已选 / 全部课程；通过类和零学分课程不参与加权"><span class="grade-count-selected" data-grade-selected>0</span><span class="grade-count-total">/<span data-grade-total>0</span></span></b><span>计入课程</span></div></div>
  <div class="grade-caption"><p class="sub" id="grade-calc-note"></p></div></div></div>
 <div class="card" id="grade-compact-live" aria-label="桌面实时成绩统计"><div class="gpa"><div><b data-grade-value="score">—</b><span>加权成绩</span><small class="grade-delta" data-grade-delta="score" hidden></small></div><div><b data-grade-value="point">—</b><span>加权绩点</span><small class="grade-delta" data-grade-delta="point" hidden></small></div><div><b data-grade-value="credit">—</b><span>计入学分</span></div><div><b class="grade-count" aria-label="已选 0 门，共 0 门课程"><span class="grade-count-selected" data-grade-selected>0</span><span class="grade-count-total">/<span data-grade-total>0</span></span></b><span>计入课程</span></div></div><button type="button" class="btn ghost grade-pin" data-grade-pin aria-label="成绩统计吸顶" aria-pressed="true" title="取消吸顶"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l-1 7 4 4v2H6v-2l4-4-1-7ZM12 16v6"/></svg><span>已吸顶</span></button></div>
 <div class="card grade-mobile-live" aria-label="实时成绩统计"><div class="gpa"><div><b data-grade-value="score">—</b><span>加权成绩</span><small class="grade-delta" data-grade-delta="score" hidden></small></div><div><b data-grade-value="point">—</b><span>加权绩点</span><small class="grade-delta" data-grade-delta="point" hidden></small></div></div><div class="grade-live-meta"><span>计入学分 <b data-grade-value="credit">—</b></span><span>计入课程 <b class="grade-count" aria-label="已选 0 门，共 0 门课程"><span class="grade-count-selected" data-grade-selected>0</span><span class="grade-count-total">/<span data-grade-total>0</span></span></b></span></div></div>
 <div class="card off-card" id="ogpa" hidden></div>
 <div class="card">
  <div class="grade-toolbar grade-template-toolbar"><select id="scheme" aria-label="计算模板"></select><button class="btn pri" id="saveas">另存为自定义模板</button><button class="btn ghost" id="grade-restore" disabled>恢复模板选择</button><button class="btn ghost" id="del">删除</button></div>
  <details class="grade-rules" id="grade-rules"><summary><span id="grade-rules-title"></span><span class="miss grade-unsaved" id="grade-template-dirty" hidden>未保存</span><span class="sub">查看规则与课程调整</span></summary><div class="grade-policy" id="grade-policy"></div><div class="grade-template-summary" id="grade-template-summary" hidden></div></details>
  <div class="grade-toolbar" style="margin-top:12px"><input id="grade-search" type="search" placeholder="搜索课程名称、性质或学期" aria-label="搜索课程"><select id="termf" aria-label="学期筛选"><option value="">全部学期</option></select><button class="btn" id="grade-sync">⟳ 同步教务成绩</button><button class="btn" id="grade-use-jwxt" hidden>返回教务成绩</button></div>
  <p class="sub grade-sync-status" id="grade-sync-status" role="status">默认显示当前登录账号的教务成绩。</p>
  <div class="grade-issues" id="grade-issues" role="region" aria-label="成绩数据核对" hidden></div>
  <details id="grade-filter"><summary>⚲ 高级筛选 <span id="grade-filter-count"></span></summary>
   <div class="sub" style="margin-top:12px">学期（可多选）</div><div class="grade-choices" id="grade-terms"></div>
   <div class="sub" style="margin-top:12px">课程性质（可多选）</div><div class="grade-choices" id="grade-natures"></div>
   <div class="rgrid"><label>成绩范围<span class="rng"><input type="number" id="grade-score-min" placeholder="最低" min="0" max="100" step="any" aria-label="最低成绩">–<input type="number" id="grade-score-max" placeholder="最高" min="0" max="100" step="any" aria-label="最高成绩"></span></label>
    <label>绩点范围<span class="rng"><input type="number" id="grade-point-min" placeholder="最低" min="0" step="any" aria-label="最低绩点">–<input type="number" id="grade-point-max" placeholder="最高" min="0" step="any" aria-label="最高绩点"></span></label>
    <label>学分范围<span class="rng"><input type="number" id="grade-credit-min" placeholder="最低" min="0" step="any" aria-label="最低学分">–<input type="number" id="grade-credit-max" placeholder="最高" min="0" step="any" aria-label="最高学分"></span></label>
    <label>计入状态<select id="grade-inclusion"><option value="">全部</option><option value="in">已计入</option><option value="out">已排除</option></select></label>
    <label>成绩状态<select id="grade-status"><option value="">全部</option><option value="pass">及格</option><option value="fail">不及格</option><option value="unknown">成绩无法换算</option><option value="missing-point">缺失绩点</option><option value="missing-nature">未标注性质</option></select></label></div>
   <div class="row" style="margin-top:10px"><span class="sp"></span><button class="btn ghost" id="grade-reset">重置筛选</button></div></details>
  <p class="sub grade-visible" id="grade-visible"></p><div class="grade-bulk" role="group" aria-label="批量调整全部课程，不受列表筛选影响"><button class="btn ghost" id="all" title="计入全部课程，不受列表筛选影响">全部计入</button><button class="btn ghost" id="none" title="排除全部课程，不受列表筛选影响">全部排除</button><button class="btn ghost" id="grade-required" title="追加计入所有有学分的必修课程">计入必修</button></div>
  <div class="sub" id="dirty" role="status" style="margin-top:6px"></div><div id="grade-notes" class="grade-import-notes"></div>
  <details class="grade-secondary"><summary>其他方式 · 文件导入（可选）</summary><p class="sub">无需登录即可导入 Excel / CSV 成绩单并在本地计算；重新打开页面会回到当前账号的教务成绩。</p><div class="row"><button class="btn ghost" id="grade-import">导入成绩单</button><button class="btn ghost" id="grade-view-import" hidden>查看已导入成绩</button><input type="file" id="grade-file" accept=".xlsx,.xls,.csv" hidden></div></details>
 </div>
 <div class="card grade-table"><table aria-label="成绩列表"><thead><tr><th style="width:38px">计入</th><th>课程</th><th data-grade-sort="nature" aria-sort="none"><button>性质 ↕</button></th><th class="n" data-grade-sort="credit" aria-sort="none"><button>学分 ↕</button></th><th class="n" data-grade-sort="numeric_score" aria-sort="none"><button>成绩 ↕</button></th><th class="n" data-grade-sort="point" aria-sort="none"><button>绩点 ↕</button></th><th data-grade-sort="term" aria-sort="none"><button>学期 ↕</button></th></tr></thead><tbody id="gt"></tbody></table></div>
 <p class="sub" style="text-align:center">筛选只改变列表显示；上方结果始终统计所有已勾选课程。</p>
</section>
<section class="tab" id="t-xy"><div id="prog"></div></section>
<section class="tab" id="t-js"><div class="card room-form"><h2>空教室</h2>
 <div class="rgrp"><div class="rgrp-h">校区</div><div class="seg rchips" id="rcs" role="radiogroup" aria-label="学校校区"></div><input type="hidden" id="rc"></div>
 <div class="rgrp"><div class="rgrp-h">时间</div>
  <div class="rgrid r2">
   <label class="m-date">日期<input type="date" id="rd"></label>
   <label class="m-week">星期<select id="rwd"><option value="1">周一</option><option value="2">周二</option><option value="3">周三</option><option value="4">周四</option><option value="5">周五</option><option value="6">周六</option><option value="7">周日</option></select></label>
   <label class="m-week">周次<input id="rw" placeholder="如 6 或 6-8"></label>
   <label>节次<span class="rng"><input type="number" id="rp1" min="1" max="14" value="1" aria-label="起始节次">–<input type="number" id="rp2" min="1" max="14" value="2" aria-label="结束节次"></span></label>
   <label class="m-study r-full">自习时间<span class="rng"><input type="time" id="rst" value="08:00" aria-label="开始时间">–<input type="time" id="ret" value="09:40" aria-label="结束时间"></span></label>
  </div>
  <div class="m-study rchips-row" id="rst-presets"><span class="sub">快捷</span><button type="button" class="chip" data-sp="1-4">上午</button><button type="button" class="chip" data-sp="5-8">下午</button><button type="button" class="chip" data-sp="9-12">晚上</button></div>
 </div>
 <div class="rgrp"><div class="rgrp-h">地点</div>
  <div class="rgrid r2">
   <label>教学楼<select id="rb"><option value="">全部</option></select></label>
   <label>教室类型<select id="rt"><option value="">全部</option></select></label>
  </div>
  <label class="rcheck" title="隐藏实验室、机房、语音室等专用教室"><input type="checkbox" id="rhs" checked>屏蔽特殊教室（实验室、机房等）</label>
 </div>
 <details id="rmore" class="rgrp"><summary>座位数与更多条件</summary>
  <div class="rgrid r2" style="margin-top:8px">
   <label>上课座位数<span class="rng"><input type="number" id="rs1" min="0" placeholder="不限" aria-label="上课座位数下限">–<input type="number" id="rs2" min="0" placeholder="不限" aria-label="上课座位数上限"></span></label>
   <label>考试座位数<span class="rng"><input type="number" id="re1" min="0" placeholder="不限" aria-label="考试座位数下限">–<input type="number" id="re2" min="0" placeholder="不限" aria-label="考试座位数上限"></span></label>
  </div>
  <div class="rgrid r2" id="rextra"><p class="sub">加载中…</p></div></details>
 <button class="btn pri rq-btn" id="rq">查询空教室</button>
 <p class="sub" id="rauto" role="status" style="margin:8px 0 0"></p>
 <p class="sub" id="rinfo" style="margin:8px 0 0">需要已保存会话；结果实时来自教务，自动翻页取全。</p></div>
 <div class="banner err room-error" id="room-error" role="alert" hidden><div><b>查询未成功</b><p class="sub" id="room-error-message"></p></div><button class="btn" id="room-switch-login" type="button">检查登录方式</button></div>
 <div class="card room-results" id="rres" tabindex="-1" aria-label="空教室查询结果" hidden></div></section>
<section class="tab" id="t-ks"><div class="card"><h2>考试倒计时</h2><div id="exams"></div></div></section>
<section class="tab" id="t-oa">
 <div id="oa-list-v">
 <div class="card" id="oa-pick" hidden>
  <h2 style="margin:0 0 6px">选你的学院</h2>
  <p class="sub" style="margin:0 0 8px">选一个学院后，顶部会自动加上它的通知入口；以后还能随时增减。也可以先跳过，只看校内通知。</p>
  <div id="oa-pick-b"></div>
  <div class="row" style="margin-top:12px"><button type="button" class="btn ghost" id="oa-pick-skip">先跳过</button><span class="sp"></span><button type="button" class="btn pri" id="oa-pick-ok" disabled>开始使用</button></div>
 </div>
 <div class="card"><div class="row"><h2 style="margin:0">通知 <span class="sub" id="oa-meta"></span></h2><span class="sp"></span><button class="btn" id="oa-ref" title="只取第 1 页">⟳ 更新</button></div>
  <div class="seg" id="oa-ch" style="margin:12px 0 0;overflow-x:auto" hidden></div>
  <div id="oa-manage" hidden></div>
  <div class="oaf" style="margin-top:12px"><input id="oa-kw" type="search" placeholder="搜索标题或发文单位（本地筛选）"><select id="oa-dept"><option value="">全部单位</option></select></div>
  <p class="sub" style="margin:10px 0 0" id="oa-src">学校 OA 可经校园网或学校 VPN 访问；校外可登录<a href="/api/oa/webvpn" target="_blank" rel="noopener noreferrer">学校 WebVPN ↗</a>查看原站。登录时选择「校外 WebVPN」后，OA 通知同步也会经应用内 WebVPN；校园网直连模式下走直连。学院官网通知可直接访问，独立更新；数据只读并保存在本机。</p></div>
 <div class="card" id="oa-box" style="padding:8px 14px"><div class="state"><div class="spin"></div><b>正在读取通知…</b></div></div>
 <div class="card" id="oa-sub"><h2>关键词订阅</h2><div id="oa-sub-b"><p class="sub" style="margin:0">读取中…</p></div></div>
 </div>
 <div id="oa-detail-v" hidden></div>
</section>
<section class="tab" id="t-sz">
 <div class="card" id="links"><h2>校园服务</h2><div class="row links-toolbar"><button id="links-refresh" class="btn ghost" type="button">刷新</button><button id="links-check" class="btn ghost" type="button">验证教务</button></div><p id="links-state" class="links-caption" role="status"></p><div id="links-b"><p class="sub" style="margin:0">读取中…</p></div></div>
 <div class="card sl"><h2>账号</h2>
  <p class="sub" id="lginfo">登录后同步课表、成绩和考试。</p><div class="seg" role="group" aria-label="连接方式"><button type="button" data-login-mode="direct" class="on" aria-pressed="true">校园网直连</button><button type="button" data-login-mode="webvpn" aria-pressed="false">校外 WebVPN</button></div>
  <p class="sub" id="login-method-hint">连着校园网时选这个。</p><p class="sub device-net-hint" id="device-net-hint" role="status" hidden></p>
  <div class="row"><button class="btn pri" id="lgbtn" type="button">登录并同步</button><span class="sp"></span><span id="network-route" role="status" class="sub">当前：<strong id="network-route-current">校园网直连</strong><span id="network-route-last" hidden></span></span></div>
  <p class="sub" id="login-feedback" role="status" hidden></p><p class="sub sl-note">目前仅支持本科生教务，研究生暂不支持。</p>
  <details class="srow"><summary>连接检测</summary><p class="sub" id="network-summary" role="status">看看现在能不能连上学校网站。</p><button class="btn" id="network-check">检测连接</button><div id="network-report" aria-live="polite"></div></details>
 </div>
 <div class="card sl"><h2>设置</h2>
  <div class="srow flat"><span>外观</span><div class="thm" role="group" aria-label="外观"><button type="button" data-theme="system" aria-pressed="true" title="跟随系统">跟随系统</button><button type="button" data-theme="light" aria-pressed="false" title="浅色">浅色</button><button type="button" data-theme="dark" aria-pressed="false" title="深色">深色</button></div></div>
  <details class="srow"><summary>学期与调课</summary><p class="sub" id="calinfo"></p><details><summary class="sub">手动设置开学日期</summary><div class="row" style="margin-top:8px"><input type="date" id="fm"><button class="btn pri" id="savefm">保存覆盖</button><button class="btn ghost" id="clrfm">恢复教务校历</button></div></details><label class="adj-toggle"><input type="checkbox" id="adj-on" checked> 自动应用调课/停课</label><p class="sub" id="adj-info" style="margin:4px 0 0"></p></details>
  <details class="srow" id="kb-edits-card"><summary>我的课表修改</summary><p class="sub" id="kb-edits-sum"></p><div id="kb-edits-list"></div>
  <div class="row" style="margin-top:10px"><a class="btn" id="kb-export" href="/api/schedule/overlay" download="superjlu-schedule-edits.json">导出备份</a><button type="button" class="btn" id="kb-import-btn">导入备份</button><input type="file" id="kb-import" accept=".json,application/json,text/plain" hidden><button type="button" class="btn ghost" id="kb-reset" hidden>恢复教务原样</button><button type="button" class="btn ghost" id="kb-undo" hidden>撤销恢复</button></div>
  <div id="kb-backup-box" hidden><p class="sub">把下面的内容复制下来保存好（比如发给自己），换手机后用「粘贴备份内容」恢复。</p><textarea id="kb-backup-text" readonly rows="5"></textarea><button type="button" class="btn" id="kb-copy">复制</button></div>
  <details style="margin-top:8px"><summary class="sub">粘贴备份内容</summary><textarea id="kb-paste" rows="4" placeholder="把之前复制的备份内容粘贴到这里"></textarea><button type="button" class="btn" id="kb-paste-ok">导入</button></details></details>
  <div class="srow flat"><span>导出到手机日历<small class="sub">课前 15 分钟提醒</small></span><a class="btn" id="ics" href="/api/ics" download>导出</a></div>
 </div>
 <!--BROWSER_PREFERENCES_CARD-->
 <!--ANDROID_EXTRAS_CARD-->
 <div class="card sl" id="ver-card"><h2>关于</h2>
  <div class="srow flat"><span id="upd-s" role="status">版本 v<span id="upd-v"></span><span id="upd-m"></span></span><a class="btn pri" id="upd-go" href="#" target="_blank" rel="noopener noreferrer" hidden>前往下载</a><button type="button" class="btn ghost" id="upd-chk">检查更新</button></div>
  <details class="sub" id="upd-tech" hidden><summary>详细原因</summary><code id="upd-why" style="word-break:break-all"></code></details>
  <label class="srow flat"><span>自动检查新版本</span><input type="checkbox" id="upd-auto" checked></label>
  <p class="sub sl-note">数据与隐私：所有数据只保存在本机，不会上传到任何服务器。</p>
 </div>
</section>
</main>
<nav><button class="on" data-t="kb"><b>▦</b>课表</button><button data-t="cj"><b>◎</b>成绩</button><button data-t="xy"><b>◔</b>学业</button><button data-t="js"><b>⌂</b>教室</button><button data-t="ks"><b>⏱</b>考试</button><button data-t="oa"><b>✉</b>通知</button><button data-t="sz"><b>☰</b>更多</button></nav>
<dialog id="login" aria-labelledby="lgt"><form method="dialog" id="lgf" autocomplete="on">
 <h2 id="lgt" style="margin:0 0 4px">登录统一身份认证</h2><p class="sub" id="lg-ug" style="margin:0 0 6px">目前仅支持本科生教务，研究生暂不支持。</p><p class="sub" id="lgok" style="margin:0 0 6px;color:var(--ok);font-weight:600" hidden>✓ SuperJLU 已登录，如需切换账号可直接修改</p><p class="sub device-net-hint" id="lg-device-net" role="status" style="margin:0 0 6px" hidden></p><p class="sub" style="margin:0">账号是邮箱前缀（不是学号）。登录状态加密保存在本机，下次打开不用重登。</p>
 <div id="lg1"><label for="lgu">账号</label><div id="lga" class="lga" hidden></div><input type="text" id="lgu" autocomplete="username" autocapitalize="off" spellcheck="false" placeholder="邮箱前缀">
  <label for="lgp">密码</label><input type="password" id="lgp" autocomplete="current-password" placeholder="密码">
  <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="lgr" checked>记住我（会话失效时免输密码）</label></div>
 <div id="lg2" hidden><p id="lgh" style="margin:8px 0 0"><b class="lg-pass-ok">✓ 账号密码已通过</b><span class="sub" style="display:block;margin-top:4px">微信验证码会发到「智慧吉大」的「统一身份认证」消息；若未收到可点「重新发送」。</span></p>
  <div id="lg3" hidden><label for="lgw">微信验证码（到「智慧吉大」查看「统一身份认证」消息）</label><input type="text" id="lgw" inputmode="numeric" autocomplete="one-time-code"><div class="row" style="margin-top:8px"><button type="button" class="btn ghost" id="lg-resend">重新发送</button><span class="sub" id="lg-resend-hint" role="status"></span></div></div></div>
 <p class="err" id="lge" role="alert"></p>
 <div class="vpn-hint" id="lgvpn" hidden></div>
 <button type="button" class="btn pri" id="lg-vpn-continue" hidden style="width:100%;margin-top:8px">通过应用内 WebVPN 继续</button>
 <div class="row" style="margin-top:8px"><button type="button" class="btn ghost" id="lgx">取消</button><span style="flex:1"></span><button type="submit" class="btn pri" id="lgo">登录</button></div>
</form></dialog>
<dialog id="kb-dlg" class="grade-dialog" aria-label="课程"><div id="kb-dlg-body"></div></dialog>
<dialog id="room-detail" class="grade-dialog room-dialog" aria-labelledby="room-detail-title"><div class="row room-detail-heading"><h2 id="room-detail-title"></h2><button type="button" class="btn ghost" id="room-detail-close" aria-label="关闭教室详情">✕</button></div><p class="sub" id="room-detail-hint">所选时段空闲 · 以本次教务查询结果为准</p><div id="room-detail-day"></div><details class="room-metadata"><summary>教室资料</summary><dl id="room-detail-fields" class="room-detail-fields"></dl></details></dialog>
<dialog id="grade-help-dialog" class="grade-dialog" aria-labelledby="grade-help-title"><div class="row"><h2 id="grade-help-title" style="margin:0">成绩帮助（适用于吉林大学）</h2><span class="sp"></span><button class="btn ghost" data-grade-close aria-label="关闭成绩帮助">✕</button></div>
 <p>不同学院保研政策和奖学金政策不同。请先核对本学院当年规则，调整计入课程，再点击「另存为自定义模板」。内置模板仅供起步参考，不代表官方统计。</p>
 <h3>内置模板</h3><p><strong class="grade-template-name">保研加权：</strong>排除选修、<span style="color:var(--bad)">限选</span>、通用学术英语、体育、军事理论、军事训练。<strong class="grade-template-name">奖学金加权：</strong>只计必修，排除英语、体育、军事训练；军事理论计入。<strong class="grade-template-name">所有课程：</strong>计入全部有学分课程。</p>
 <h3>计算与导入</h3><p>成绩、绩点分别按学分加权。等级成绩：优秀 95、良好 85、中等 75、及格 65、不及格 55。教务课程优先用单科绩点，缺失时按原程序规则估算并标注；导入成绩单缺少绩点时显示「—」。无法识别的成绩会标注，计入时按 0 分处理，请核对后再使用结果。</p>
 <p>支持 Excel / CSV（最多 5 MB），中英文表头、标题行和多工作表。导入数据只保存在本机，独立于教务数据，可随时返回教务成绩。自定义模板保留基础规则及手动选择，新增课程按基础规则计入。</p>
 <h3>核对与恢复模板</h3><p>「需要核对的数据」可筛选无法换算的成绩、缺失绩点或未标注性质的课程，点击已选条件可取消筛选，不改变计入状态。手动调整后，成绩和绩点下方显示相对当前模板已保存选择的差值；任一结果缺失时显示「—」。点击「恢复模板选择」撤销当前模板下的临时调整，自定义模板原有的增减课程会保留。</p>
 <h3>筛选与批量操作</h3><p>搜索、高级筛选和排序只控制显示。「全部计入」「全部排除」作用于整份成绩单，不受当前筛选影响；「计入必修」追加计入所有有学分的必修课程。点击列标题切换降序、升序和默认顺序。</p>
 <h3>学院官网与政策查询</h3><div class="college-links" id="grade-college-links"><span class="sub">正在读取学院官网…</span></div><p>到学院官网搜索以下关键词寻找方案，点击可复制：</p><div class="grade-keywords"><button class="btn ghost" data-grade-copy>免试</button><button class="btn ghost" data-grade-copy>推荐优秀应届本科毕业生免试攻读研究生</button><button class="btn ghost" data-grade-copy>推免</button></div><div class="row" style="margin-top:18px"><span class="sp"></span><button class="btn pri" data-grade-close>我知道了</button></div></dialog>
<dialog id="grade-save-dialog" class="grade-dialog" aria-labelledby="grade-save-title"><form id="grade-save-form"><h2 id="grade-save-title">另存为自定义模板</h2><p>保存基础规则与当前的手动计入 / 排除。新增课程按基础规则选择。</p><label for="grade-template-name" class="sub">模板名称</label><input id="grade-template-name" maxlength="40" required style="width:100%;margin:8px 0 16px" placeholder="例如：软件学院保研"><div class="row"><button type="button" class="btn ghost" id="grade-save-cancel">取消</button><span class="sp"></span><button class="btn pri" type="submit">保存模板</button></div></form></dialog>
<dialog id="academic-confirm" class="grade-dialog" aria-labelledby="academic-confirm-title"><form id="academic-confirm-form"><h2 id="academic-confirm-title">让教务重新计算？</h2><p>教务会重新统计你已修过的课程和学分。完成后，SuperJLU 会自动更新这里的数据。</p><p class="sub">如果你刚在教务网站上计算过，只需点「从教务更新」，不用再次计算。</p><div class="row"><button type="button" class="btn ghost" id="academic-confirm-cancel">暂不计算</button><span class="sp"></span><button type="submit" class="btn pri">确认重新计算</button></div></form></dialog>
<div id="toast" role="status" aria-live="polite"></div>
<script>
"use strict";
const $=s=>document.querySelector(s), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const LEVEL={"优秀":95,"良好":85,"中等":75,"及格":65,"不及格":0,"通过":null,"不通过":0};
const COLORS=["#3b6fd4","#d4573b","#2e9e6a","#9b51e0","#d48a1e","#1f8fa8","#c2416f","#5b6bd6","#6b8e23","#b8572b"];
let D=null, week=1, include=new Set(), current="__postgraduate__", dirty=false, gradeSessionState="unknown";
function toast(m,error=false){const t=$("#toast"),el=document.createElement("div");el.className="toast-item"+(error?" bad":"");el.setAttribute("role",error?"alert":"status");el.textContent=m;t.append(el);while(t.children.length>3)t.firstElementChild.remove();setTimeout(()=>el.classList.add("leaving"),3650);setTimeout(()=>el.remove(),4000)}
function point(s){s=String(s).trim();let v=/^\d+(\.\d+)?$/.test(s)?parseFloat(s):(s in LEVEL?LEVEL[s]:null);if(v===null)return null;return v<60?0:Math.min(4,Math.round((1+(v-60)*.1)*100)/100)}
async function api(path,body){const r=await fetch(path,body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{});const j=await r.json();if(j&&j.network_error===true&&$("#network-summary"))$("#network-summary").textContent="最近请求失败："+j.error;if(j&&j.session_expired===true){clearRoomCache();if(!j.site||j.site==="jwxt"){gradeSessionState="expired";lgInfo(false)}if(Array.isArray(j.courses)||Array.isArray(j.grades)||Array.isArray(j.exams)||j.completion||j.calendar){const next=gradeRefreshSnapshot(D,j);D=Object.assign({},next,{session_expired:true,offline:true,cached_at:j.cached_at||next.cached_at||next.updated},j.site?{session_site:String(j.site)}:{});try{renderAll()}catch(_){}}else{D=Object.assign(D||{},{session_expired:true},j.site?{session_site:String(j.site)}:{});if(D&&((D.courses||[]).length||(D.grades||[]).length)&&!D.offline){D.offline=true;D.cached_at=D.cached_at||D.updated}try{renderSession();renderOffline()}catch(_){}}}if(j&&j.offline===true&&j.ok!==false&&(r.ok||r.status===401))return j;if(!r.ok||j.ok===false){const err=new Error(j.error||(r.status===401?"登录会话已过期，请在「更多 → 登录」中重新登录":r.status));err.payload=j;err.connectionAction=!!(j.connection_action||j.session_expired);throw err}return j}
function weekOf(date){const fm=D.first_monday;if(!fm)return 1;const d0=new Date(fm+"T00:00:00");return Math.floor((date-d0)/864e5/7)+1}
function nextClass(courses,periods,firstMonday,now,maxW){
 const toM=t=>{const m=/^(\d{1,2}):(\d{2})/.exec(String(t||""));return m?+m[1]*60+ +m[2]:NaN};
 const pad=n=>String(n).padStart(2,"0"),ymd=d=>d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());
 const pm=periods||{},slot=(n,i)=>{const t=pm[n]!=null?pm[n]:pm[String(n)];return t&&t.length>i?toM(t[i]):NaN};
 if(!now||typeof now.getFullYear!=="function"||isNaN(+now)||!firstMonday)return null;
 const fm=new Date(String(firstMonday).slice(0,10)+"T00:00:00");
 if(isNaN(+fm))return null;
 const cap=+maxW>0?+maxW:30,cur=+now,today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
 const weekNow=Math.floor((today-fm)/864e5/7)+1;
 let best=null;
 for(const c of courses||[]){
  if(!c||c.src==="cancelled")continue;
  const wd=+c.weekday,a=+c.start,b=+c.end||a;
  if(!(wd>=1&&wd<=7&&a>=1&&b>=a))continue;
  const sm=slot(a,0),em=slot(b,1);
  if(!(sm>=0)||!(em>sm))continue;
  for(const raw of c.weeks||[]){
   const w=+raw;if(!(w>=1&&w<=cap))continue;
   const day=new Date(fm.getFullYear(),fm.getMonth(),fm.getDate()+(w-1)*7+wd-1);
   const st=+new Date(day.getFullYear(),day.getMonth(),day.getDate(),Math.floor(sm/60),sm%60,0,0);
   const en=+new Date(day.getFullYear(),day.getMonth(),day.getDate(),Math.floor(em/60),em%60,0,0);
   if(!(en>cur))continue;
   const item={kind:st<=cur?"now":"next",name:String(c.name||""),location:String(c.location||""),weekday:wd,start:a,end:b,week:w,hm:pad(Math.floor(sm/60))+":"+pad(sm%60),ymd:ymd(day),mins:st<=cur?Math.ceil((en-cur)/60000):Math.max(0,Math.round((st-cur)/60000)),thisWeek:w===weekNow,startAt:st,endAt:en};
   if(!best){best=item;continue}
   const nowWin=item.kind==="now",bestNow=best.kind==="now";
   if(nowWin!==bestNow){if(nowWin)best=item;continue}
   if(nowWin){if(item.endAt<best.endAt||(item.endAt===best.endAt&&item.name<best.name))best=item;continue}
   if(item.startAt<best.startAt||(item.startAt===best.startAt&&(item.endAt<best.endAt||(item.endAt===best.endAt&&item.name<best.name))))best=item;
  }
 }
 if(!best)return null;
 return {kind:best.kind,name:best.name,location:best.location,weekday:best.weekday,start:best.start,end:best.end,week:best.week,hm:best.hm,ymd:best.ymd,mins:best.mins,thisWeek:best.thisWeek};
 }
function nextClassLabel(hit,now){
 if(!hit)return {k:"课表",t:"本学期没有更多课程",sub:""};
 const wd="周"+("一二三四五六日"[hit.weekday-1]||"?");
 const per="第"+hit.start+(hit.end!==hit.start?"-"+hit.end:"")+"节";
 const tail=per+(hit.location?" · "+hit.location:"");
 if(hit.kind==="now")return {k:"正在上",t:hit.name||"未命名课程",sub:tail+(hit.mins>0?" · 还剩 "+hit.mins+" 分钟":"")};
 const p=n=>String(n).padStart(2,"0"),y=d=>d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate());
 let when=wd+" "+(hit.hm||"");
 if(now&&typeof now.getFullYear==="function"&&!isNaN(+now)&&hit.ymd){
  if(hit.ymd===y(now))when="今天 "+(hit.hm||"");
  else{const tmr=new Date(now.getFullYear(),now.getMonth(),now.getDate()+1);if(hit.ymd===y(tmr))when="明天 "+(hit.hm||"");else if(!hit.thisWeek)when="第"+hit.week+"周 "+wd+" "+(hit.hm||"")}
 }
 return {k:"下一节",t:hit.name||"未命名课程",sub:(when+" · "+tail).trim()};
 }
function maxWeek(){return Math.max((D.calendar&&D.calendar.total_weeks)||16,...D.courses.flatMap(c=>c.weeks))}
function color(name){let h=0;for(const ch of name)h=(h*31+ch.charCodeAt(0))>>>0;return COLORS[h%COLORS.length]}
function renderGrid(){
 $("#wkn").textContent=`第 ${week} 周`;
 const g=$("#grid"),days=["一","二","三","四","五","六","日"];let html='<div></div>';
 const fm=D.first_monday, now=new Date();
 days.forEach((d,i)=>{let lab="周"+d,today=false;if(fm){const dd=new Date(fm+"T00:00:00");dd.setDate(dd.getDate()+(week-1)*7+i);lab+=`<br>${dd.getMonth()+1}/${dd.getDate()}`;today=dd.toDateString()===now.toDateString()}html+=`<div class="h${today?" today":""}">${lab}</div>`});
 const cs=KB_CS=D.courses.filter(c=>c.weeks.includes(week)),PM=periodMap();
 const maxP=Math.max(11,...cs.map(c=>c.end));
 for(let p=1;p<=maxP;p++){const pt=PM[p]||PM[String(p)];html+=`<div class="p" style="grid-row:${p+1};grid-column:1;flex-direction:column">${p}${pt?`<em>${pt[0]}</em>${pt[1]?`<em class="pe">${pt[1]}</em>`:""}`:""}</div>`;for(let d=1;d<=7;d++)html+=`<div class="cell" style="grid-row:${p+1};grid-column:${d+1}"></div>`}
 cs.forEach((c,i)=>{html+=`<div class="cls${kbCls(c)}" data-i="${i}" role="button" tabindex="0" style="grid-row:${c.start+1}/${c.end+2};grid-column:${c.weekday+1};background:${c.src==="cancelled"?"#8a9099":color(c.name)}"><b>${esc(c.name)}</b><i>${esc(c.location)}</i>${kbTime(c,PM)?`<i class="tm">${kbTime(c,PM).split("–").map((t,k)=>`<span>${k?"–":""}${t}</span>`).join("")}</i>`:""}</div>`});

 g.innerHTML=html;
 if(!D.courses.length)g.insertAdjacentHTML("afterend",'<p class="empty" id="noc">还没有课表数据，点右上角「刷新」同步</p>');
}
/* 课表个人修改：增 / 隐藏 / 改，刷新不覆盖（后端 schedule_overlay.json） */
const KB_WD="一二三四五六日";let KB_CS=[];
const KB_FIELD={name:"课程名",location:"地点",teacher:"教师",weekday:"星期",start:"开始节",end:"结束节"};
/* 课程起止时间：首节开始 – 末节结束，如 08:00–09:40 */
function kbTime(c,m){m=m||{};const a=m[c.start]||m[String(c.start)],b=m[c.end]||m[String(c.end)];return a&&a[0]&&b&&b[1]?a[0]+"–"+b[1]:""}
function kbSlot(c){return "周"+(KB_WD[c.weekday-1]||"?")+" 第"+c.start+(c.end!==c.start?"-"+c.end:"")+"节"}
function kbOcc(cs){const s=new Set();for(const c of cs||[])for(let p=+c.start;p<=+c.end;p++)s.add((+c.weekday)+"-"+p);return s}
function kbBlankSeed(weekday,period,occupied,week,maxP){weekday=+weekday;period=+period;week=+week;maxP=+maxP||period;if(!(weekday>=1&&weekday<=7&&period>=1&&week>=1))return null;const occ=p=>occupied&&occupied.has&&occupied.has(weekday+"-"+p);if(occ(period))return null;let start=period,end=period,mate=period%2?period+1:period-1;if(mate>=1&&mate<=maxP&&!occ(mate)){start=Math.min(period,mate);end=Math.max(period,mate)}return {name:"",location:"",teacher:"",weekday,start,end,weeks:[week]}}
function kbWeeks(ws){ws=[...new Set(ws||[])].sort((a,b)=>a-b);if(!ws.length)return"";if(ws.length>=3&&ws.every((w,i)=>!i||w-ws[i-1]===2))return"第"+ws[0]+"-"+ws[ws.length-1]+"周（"+(ws[0]%2?"单":"双")+"周）";const out=[];let a=ws[0],p=ws[0];for(const w of ws.slice(1).concat([null])){if(w===p+1){p=w;continue}out.push(a===p?String(a):a+"-"+p);a=p=w}return"第"+out.join("、")+"周"}
function kbPreset(kind,max){const a=[];for(let w=1;w<=max;w++)if(kind==="all"||(kind==="odd"&&w%2===1)||(kind==="even"&&w%2===0))a.push(w);return a}
function kbTarget(t){const m=/^(.*)\|(\d+)\|(\d+)-(\d+)$/.exec(t||"");return m?{name:m[1],weekday:+m[2],start:+m[3],end:+m[4]}:{name:t||""}}
function kbOpText(o){if(o.op==="add"){const c=o.course||{};return"添加了「"+c.name+"」 "+kbSlot(c)+" "+kbWeeks(c.weeks)}const t=kbTarget(o.target),where="「"+t.name+"」"+(t.weekday?" "+kbSlot(t):""),when=o.weeks&&o.weeks.length?kbWeeks(o.weeks):"所有周";if(o.op==="hide")return where+" "+when+"不上";const s=o.set||{};return where+" "+when+"："+Object.keys(s).map(k=>(KB_FIELD[k]||k)+"改为"+(k==="weekday"?"周"+KB_WD[s[k]-1]:k==="start"||k==="end"?"第"+s[k]+"节":s[k])).join("，")}
function kbIssueTitle(i){return i.kind==="changed"?"教务更新了这门课":i.kind==="missing"?"这条修改暂未生效":"这条修改已损坏"}
function kbIssueActions(i){if(i.kind==="invalid")return[["remove","删掉这条修改"]];const a=[["ack","我知道了"]];if(i.kind==="missing"&&i.op==="edit")a.push(["detach","保留为自定义课"]);a.push(["remove","删掉这条修改"]);return a}
function kbCls(c){return c.src==="cancelled"?" cancelled":c.src==="custom"?" custom":c.src==="edited"?" edited":c.adj?" adjusted":""}
function kbSrcText(c){if(c.src==="cancelled")return"教务"+(c.adj||"停课");if(c.src==="custom")return"你自己添加的课";if(c.src==="official"&&c.adj)return"教务"+c.adj;if(c.src==="edited"){const t=kbTarget(c.from);return"你改过的课（教务原来是 "+(t.weekday?kbSlot(t):t.name)+"）"}return"教务课表"}
function kbCourse(c,patch){return Object.assign({name:c.name,teacher:c.teacher,location:c.location,weekday:c.weekday,start:c.start,end:c.end,weeks:c.weeks},patch||{})}
function kbOpSet(id){const o=((D&&D.schedule_ops)||[]).find(x=>x.id===id);return(o&&o.set)||{}}
function kbSkipReq(c,wk){if(c.src==="official")return{action:"hide",target:c.key,jxbid:c.jxbid||undefined,weeks:[wk]};if(c.src==="custom"){const rest=c.weeks.filter(w=>w!==wk);return rest.length?{action:"update",id:c.oid,course:kbCourse(c,{weeks:rest})}:{action:"remove",id:c.oid}}return null}
function kbDeleteReq(c){return c.src==="official"?{action:"hide",target:c.key,jxbid:c.jxbid||undefined}:{action:"remove",id:c.oid}}
function kbEditReq(c,vals,scope,wk){if(c.src==="custom")return{action:"update",id:c.oid,course:kbCourse(c,vals)};const set={};for(const k of Object.keys(KB_FIELD))if(vals[k]!==undefined&&String(vals[k])!==String(c[k]))set[k]=vals[k];if(c.src==="edited")return{action:"update",id:c.oid,set:Object.assign({},kbOpSet(c.oid),set)};return{action:"edit",target:c.key,jxbid:c.jxbid||undefined,weeks:scope==="week"?[wk]:null,set}}
async function kbPost(body,okMsg){try{const j=await api("/api/schedule/overlay",body);for(const k of Object.keys(j))if(k!=="ok")D[k]=j[k];renderGrid();renderKbExtras();if(okMsg)toast(okMsg);return true}catch(e){toast(e.message,true);return false}}
function kbOpen(c){if(!c)return;const b=$("#kb-dlg-body"),ed=c.src==="edited";if(c.src==="cancelled"){b.innerHTML=`<h2 style="margin:0 0 6px">${esc(c.name)} <span class="chip">本周停课</span></h2><p class="sub">${esc(kbSlot(c))} · ${esc(c.location)}${c.teacher?" · "+esc(c.teacher):""}<br>${esc(kbSrcText(c))}</p><p class="sub">这节课第 ${esc(c.weeks.join("、"))} 周不上，其他周照常。关闭「更多 → 学期」里的「自动应用调课/停课」可按原始安排显示。</p><div class="row" style="margin-top:12px"><span class="sp"></span><button type="button" class="btn ghost" data-k="close">关闭</button></div>`;b.onclick=e=>{if(e.target.dataset&&e.target.dataset.k==="close")$("#kb-dlg").close()};const d=$("#kb-dlg");if(!d.open)d.showModal();return}
 b.innerHTML=`<h2 style="margin:0 0 6px">${esc(c.name)}</h2><p class="sub">${esc(kbSlot(c))} · ${esc(c.location)}${c.teacher?" · "+esc(c.teacher):""}<br>${esc(kbWeeks(c.weeks))} · ${esc(kbSrcText(c))}</p>${c.hint?`<p class="sub">⚠ ${esc(c.hint)}</p>`:""}<div class="row" style="margin-top:12px"><button type="button" class="btn pri" data-k="edit">修改</button>${ed?"":'<button type="button" class="btn" data-k="skip">本周不上</button>'}<button type="button" class="btn ghost" data-k="del">${ed?"恢复教务原样":"删除这门课"}</button><span class="sp"></span><button type="button" class="btn ghost" data-k="close">关闭</button></div>`;
 b.onclick=async e=>{const k=e.target.dataset&&e.target.dataset.k;if(!k)return;if(k==="close")return $("#kb-dlg").close();if(k==="edit")return kbForm(c);
  if(k==="skip"){const r=kbSkipReq(c,week);if(r&&await kbPost(r,"第"+week+"周的「"+c.name+"」已标记为不上"))$("#kb-dlg").close();return}
  if(!confirm(ed?"撤销你对这门课的修改，恢复教务原样？":c.src==="custom"?"删除你添加的「"+c.name+"」？":"在你的课表里隐藏「"+c.name+"」的所有周？刷新课表也不会再出现，可以在「更多 → 我的课表修改」里恢复。"))return;
  if(await kbPost(kbDeleteReq(c),ed?"已恢复教务原样":"已删除"))$("#kb-dlg").close()};
 const d=$("#kb-dlg");if(!d.open)d.showModal()}
function kbForm(c,seed){const add=!c,custom=add||c.src==="custom",official=!!c&&c.src==="official",mx=maxWeek(),cur=c||Object.assign({name:"",location:"",teacher:"",weekday:1,start:1,end:2,weeks:kbPreset("all",mx)},seed||{});
 const opt=(n,v,lab)=>`<option value="${n}"${n==v?" selected":""}>${lab}</option>`,secs=Math.max(12,cur.end,...Object.keys(D.periods||{}).map(Number).filter(n=>n>0)),sel=(id,v)=>`<select id="${id}">${Array.from({length:secs},(_,i)=>opt(i+1,v,"第"+(i+1)+"节")).join("")}</select>`;
 const weeksHtml=custom?`<div class="sub" style="margin-top:10px">上课周</div><div class="row" style="margin:4px 0"><button type="button" class="btn ghost" data-p="all">全选</button><button type="button" class="btn ghost" data-p="odd">单周</button><button type="button" class="btn ghost" data-p="even">双周</button><button type="button" class="btn ghost" data-p="none">清空</button></div><div class="wkpick">${Array.from({length:mx},(_,i)=>`<label><input type="checkbox" value="${i+1}"${cur.weeks.includes(i+1)?" checked":""}>${i+1}</label>`).join("")}</div>`:official?`<div class="kb-scope" role="radiogroup" aria-label="修改范围"><label><input type="radio" name="kb-scope" value="week" checked> 只改本周（第${week}周）</label><label><input type="radio" name="kb-scope" value="all"> 所有周</label></div>`:"";
 const b=$("#kb-dlg-body");b.innerHTML=`<h2 style="margin:0 0 10px">${add?"添加课程":"修改「"+esc(c.name)+"」"}</h2>${add&&seed?`<p class="sub" style="margin:0 0 8px">已按空白格填好：${esc(kbSlot(cur))}，${esc(kbWeeks(cur.weeks))}。填写课程名即可保存，星期、节次和周次还能改。</p>`:""}<form id="kb-form" class="kb-form"><label>课程名<input id="kb-f-name" value="${esc(cur.name)}" maxlength="60" required></label><label>地点<input id="kb-f-location" value="${esc(cur.location==="待定"&&add?"":cur.location)}" maxlength="60"></label><label>教师<input id="kb-f-teacher" value="${esc(cur.teacher)}" maxlength="40"></label><div class="row"><label>星期 <select id="kb-f-weekday">${[1,2,3,4,5,6,7].map(d=>opt(d,cur.weekday,"周"+KB_WD[d-1])).join("")}</select></label><label>从 ${sel("kb-f-start",cur.start)}</label><label>到 ${sel("kb-f-end",cur.end)}</label></div>${weeksHtml}<div class="row" style="margin-top:14px"><span class="sp"></span><button type="button" class="btn ghost" id="kb-f-cancel">取消</button><button class="btn pri">保存</button></div></form>`;
 b.onclick=e=>{const p=e.target.dataset&&e.target.dataset.p;if(!p)return;const on=new Set(p==="none"?[]:kbPreset(p,mx));b.querySelectorAll(".wkpick input").forEach(x=>x.checked=on.has(+x.value))};
 $("#kb-f-cancel").onclick=()=>$("#kb-dlg").close();
 $("#kb-form").onsubmit=async e=>{e.preventDefault();const v={name:$("#kb-f-name").value.trim(),location:$("#kb-f-location").value.trim(),teacher:$("#kb-f-teacher").value.trim(),weekday:+$("#kb-f-weekday").value,start:+$("#kb-f-start").value,end:+$("#kb-f-end").value};if(!v.name)return toast("请填写课程名",true);if(v.end<v.start)return toast("结束节不能早于开始节",true);
  if(custom){v.weeks=[...b.querySelectorAll(".wkpick input:checked")].map(x=>+x.value);if(!v.weeks.length)return toast("请至少选择一周",true)}
  const sc=(b.querySelector('input[name="kb-scope"]:checked')||{}).value,req=add?{action:"add",course:v}:kbEditReq(c,v,sc,week);if(await kbPost(req,"已保存，刷新课表也不会覆盖"))$("#kb-dlg").close()};
 const d=$("#kb-dlg");if(!d.open)d.showModal();try{$("#kb-f-name").focus()}catch(_){}}
function adjInfoText(a){a=a||{};if(a.enabled===false)return"已关闭：课表按教务原始安排显示。";if(a.applied>0)return`本学期有 ${a.applied} 处调课/停课已经显示在课表上：带「调」字的是调过来的课，灰色带「停」字的是停掉的课，点开能看到原来的安排。`;if(a.count>0)return"本学期的调课已经包含在课表里了。";return"刷新课表时会一起读取调课、停课；读不到也不影响课表和登录。"}
function renderAdjToggle(){const a=(D&&D.schedule_adjust)||{enabled:true},el=$("#adj-on");if(!el)return;el.checked=a.enabled!==false;$("#adj-info").textContent=adjInfoText(a)}
function renderKbExtras(){const is=(D&&D.schedule_issues)||[],box=$("#kb-issues");if(!box)return;box.hidden=!is.length;
 box.innerHTML=is.length?`<h2>有 ${is.length} 条课表修改需要你看一下</h2>`+is.map(i=>`<div class="kb-iss"><b>${esc(kbIssueTitle(i))}</b> <span class="sub">「${esc(i.name||"")}」${i.weekday?" "+esc(kbSlot(i)):""}</span><div class="sub">${esc(i.message)}</div><div class="row" style="margin-top:6px">${kbIssueActions(i).map(([a,l])=>`<button type="button" class="btn${a==="remove"?" ghost":""}" data-a="${a}" data-id="${esc(i.oid)}">${l}</button>`).join("")}</div></div>`).join(""):"";
 const ops=(D&&D.schedule_ops)||[],n=ops.length,o=(D&&D.schedule_other_terms)||0;
 $("#kb-edits-sum").textContent=(n?`本学期你改了 ${n} 处课表，刷新课表不会覆盖这些修改。`:"你还没有修改过课表。在课表里点一节课就能修改或隐藏，也可以点「＋ 添加课程」，或双击空白格按这一节添加。")+(o?` 其他学期还有 ${o} 处修改，已经保存，不会显示在本学期课表里。`:"");
 $("#kb-edits-list").innerHTML=ops.map(x=>`<div class="kb-op"><span>${esc(kbOpText(x))}</span><button type="button" class="btn ghost" data-a="remove" data-id="${esc(x.id)}">撤销</button></div>`).join("");
 $("#kb-reset").hidden=!n;$("#kb-undo").hidden=!(D&&D.schedule_can_undo_reset)}
const KB_DONE={ack:"好的，不再提醒",detach:"已保留为自定义课",remove:"已删掉这条修改"};
function kbActionClick(e){const t=e.target.closest&&e.target.closest("button[data-a]");if(t)kbPost({action:t.dataset.a,id:t.dataset.id},KB_DONE[t.dataset.a])}
function kbImportText(text){let doc;try{doc=JSON.parse(text)}catch(_){return toast("这不是课表修改备份",true)}return kbPost({action:"import",doc},"备份已导入")}
const GRADE_BUILTINS={__postgraduate__:{base:"postgraduate",name:"保研加权（不含限选课程）"},__scholarship__:{base:"scholarship",name:"奖学金加权"},__all__:{base:"comprehensive",name:"所有课程"}};
let gradeBase="postgraduate",gradeSort={key:"",dir:0};
// Grade calculation helpers: no DOM, shared by rendering and regression checks.
function gradeTotals(grades,selected){const rows=grades.filter(g=>selected.has(g.key)&&g.credit>0&&!g.ungraded),credits=rows.reduce((n,g)=>n+g.credit,0);return{count:rows.length,credits,score:credits?rows.reduce((n,g)=>n+(g.numeric_score??0)*g.credit,0)/credits:null,point:credits&&rows.every(g=>g.point!=null)?rows.reduce((n,g)=>n+g.point*g.credit,0)/credits:null,invalid:rows.filter(g=>!g.score_valid).length,estimated:rows.filter(g=>g.point_source==="estimated"&&g.point!=null).length}}
function gradeMatches(g,f,selected){if(f.q&&!`${g.name} ${g.nature} ${g.term}`.toLocaleLowerCase().includes(f.q))return false;if(f.term&&g.term!==f.term)return false;if(f.terms.length&&!f.terms.includes(g.term))return false;if(f.natures.length&&!f.natures.includes(g.nature))return false;if(f.inclusion&&(selected.has(g.key)!==(f.inclusion==="in")))return false;if(["unknown","missing-point","missing-nature"].includes(f.status)&&!gradeIssue(g,f.status))return false;if(f.status==="fail"&&!(g.numeric_score!=null&&g.numeric_score<60))return false;if(f.status==="pass"&&!(g.numeric_score>=60))return false;for(const [key,min,max] of f.ranges){if(min!==""&&(g[key]==null||g[key]<Number(min)))return false;if(max!==""&&(g[key]==null||g[key]>Number(max)))return false}return true}
function gradeCompare(a,b,sort){if(!sort.dir)return b.term.localeCompare(a.term);const x=a[sort.key],y=b[sort.key];if(x==null)return y==null?0:1;if(y==null)return-1;return(typeof x==="number"?x-y:String(x).localeCompare(String(y),"zh-CN"))*sort.dir}
function gradeSelectionCount(grades,selected){return{selected:grades.filter(g=>selected.has(g.key)).length,total:grades.length}}
function gradeTemplateChanges(grades,selected,base){return{added:grades.filter(g=>selected.has(g.key)&&!g.builtin?.[base]),removed:grades.filter(g=>!selected.has(g.key)&&g.builtin?.[base])}}
function gradeSchemeSelection(grades,builtin,rule,keys=[]){const saved=new Set(keys),overrides=rule?.overrides||{};return new Set(grades.filter(g=>builtin?g.builtin?.[builtin.base]:rule?Object.prototype.hasOwnProperty.call(overrides,g.key)?overrides[g.key]:g.builtin?.[rule.base]:saved.has(g.key)||saved.has(g.legacy_key)).map(g=>g.key))}
function gradeSelectionChanged(grades,selected,saved){return grades.some(g=>selected.has(g.key)!==saved.has(g.key))}
function gradeBaseName(base){return({postgraduate:"保研加权",scholarship:"奖学金加权",comprehensive:"所有课程加权"})[base]||"所有课程加权"}
function gradePolicy(base,custom){if(custom)return`基于${gradeBaseName(base)}的自定义模板。 不同学院政策不同，请核对当年规则。`;const policy=base==="postgraduate"?'排除选修、<span style="color:var(--bad)">限选</span>、通用学术英语、体育、军事理论、军事训练。':base==="scholarship"?"只计必修，排除英语、体育、军事训练；军事理论计入。":"计入所有有学分课程。";return policy+" 不同学院政策不同，请核对当年规则，调整后另存为自定义模板。"}
function gradeStatusText(data,state){if(data?.grade_source==="import")return"正在预览文件："+(data.grade_filename||"成绩单")+"。无需登录即可计算，教务成绩已保留。";if(state==="expired"||state==="missing")return(state==="expired"?"登录会话已过期":"尚未登录")+"，无法同步教务成绩；仍可导入成绩单并在本地计算。";return"默认显示当前账号的教务成绩；登录后会自动同步，也可导入成绩单在本地计算。"}
function gradeRefreshSnapshot(previous,next){if(previous?.grade_source!=="import")return next;const kept={};for(const key of ["grades","grade_source","has_imported_grades","grade_filename","grade_notes"])kept[key]=previous[key];return Object.assign({},next,kept)}
function gradeIssue(g,kind){if(kind==="unknown")return g.credit>0&&!g.ungraded&&!g.score_valid;if(kind==="missing-point")return g.credit>0&&!g.ungraded&&g.point==null;if(kind==="missing-nature")return!String(g.nature||"").trim()||g.nature==="未标注";return false}
function gradeDataIssues(grades,selected){const counts={unknown:0,"missing-point":0,"missing-nature":0,selectedUnknown:0,selectedMissingPoint:0};for(const g of grades){for(const kind of ["unknown","missing-point","missing-nature"])if(gradeIssue(g,kind))counts[kind]++;if(selected.has(g.key)){if(gradeIssue(g,"unknown"))counts.selectedUnknown++;if(gradeIssue(g,"missing-point"))counts.selectedMissingPoint++}}return counts}
function gradeDelta(current,saved){const delta=key=>current[key]==null||saved[key]==null?null:current[key]-saved[key];return{score:delta("score"),point:delta("point")}}
function gradeSignedDifference(value){if(value==null||!Number.isFinite(value))return"—";const rounded=Math.round(value*1000)/1000;return(rounded>0?"+":"")+rounded.toFixed(3)}
// Grade rendering
let gradePinned=true,gradeCompact=false,gradeCompactFrame=0;try{gradePinned=localStorage.getItem("jlu-grade-pinned")!=="false"}catch(_){}
const gradeHeader=document.querySelector("header");
function updateGradeCompact(){
 const rect=$("#grade-overview").getBoundingClientRect(),bar=$("#grade-compact-live"),top=(gradeHeader?.getBoundingClientRect().height||76)+8;
 bar.style.left=rect.left+"px";bar.style.width=rect.width+"px";
 const metrics=$("#grade-overview>.gpa").getBoundingClientRect();
 gradeCompact=gradePinned&&window.innerWidth>520&&$("#t-cj").classList.contains("on")&&rect.top<top&&metrics.bottom<=top+bar.getBoundingClientRect().height;
 bar.classList.toggle("grade-compact-visible",gradeCompact);
}
function scheduleGradeCompact(){if(gradeCompactFrame)return;gradeCompactFrame=requestAnimationFrame(()=>{gradeCompactFrame=0;updateGradeCompact()})}
function renderGradePin(){document.querySelectorAll('[data-grade-pin]').forEach(b=>{b.setAttribute("aria-pressed",String(gradePinned));b.title=gradePinned?"取消吸顶":"开启吸顶";b.querySelector("span").textContent=gradePinned?"已吸顶":"吸顶"});$("#grade-overview").classList.toggle("grade-unpinned",!gradePinned);updateGradeCompact()}
document.querySelectorAll('[data-grade-pin]').forEach(b=>b.onclick=()=>{gradePinned=!gradePinned;try{localStorage.setItem("jlu-grade-pinned",String(gradePinned))}catch(_){}renderGradePin()});
function updateGradeStickyOffset(){if(gradeHeader)document.documentElement.style.setProperty("--app-header-height",Math.ceil(gradeHeader.getBoundingClientRect().height)+"px");scheduleGradeCompact()}
updateGradeStickyOffset();if(window.ResizeObserver&&gradeHeader)new ResizeObserver(updateGradeStickyOffset).observe(gradeHeader);window.addEventListener("resize",updateGradeStickyOffset);window.addEventListener("scroll",scheduleGradeCompact,{passive:true});renderGradePin();
function renderGradeIssues(){
 const box=$("#grade-issues"),issues=gradeDataIssues(D.grades,include),labels={unknown:"成绩无法换算","missing-point":"缺失绩点","missing-nature":"未标注性质"};
 const kinds=Object.keys(labels).filter(kind=>issues[kind]);box.hidden=!kinds.length;if(box.hidden){box.innerHTML="";return}
 const active=$("#grade-status").value;
 box.innerHTML='<h3>需要核对的数据</h3><div class="row">'+kinds.map(kind=>`<button class="btn ghost" type="button" data-grade-issue="${kind}" aria-pressed="${active===kind}" title="筛选查看，不改变课程计入状态">${labels[kind]} · ${issues[kind]} 门</button>`).join("")+'</div>'+(issues.selectedUnknown?`<p class="grade-issue-critical" role="status">已选 ${issues.selectedUnknown} 门成绩无法换算，当前按 0 分计入加权成绩，请先核对。</p>`:issues.unknown?'<p>无法换算的课程勾选后会按 0 分计入加权成绩，请先核对。</p>':"")+(issues.selectedMissingPoint?`<p>已选 ${issues.selectedMissingPoint} 门缺少绩点，加权绩点暂显示 —。</p>`:"")+(issues["missing-nature"]?'<p>部分课程未标注性质，请核对内置模板的计入范围。</p>':"");
}
function renderGradeDelta(result,saved){
 const delta=gradeDelta(result,gradeTotals(D.grades,saved)),name=GRADE_BUILTINS[current]?.name||current;
 document.querySelectorAll('[data-grade-delta]').forEach(el=>{const value=delta[el.dataset.gradeDelta];el.hidden=!dirty;el.textContent="较模板 "+gradeSignedDifference(value);el.title=`与当前模板「${name}」的已保存选择对比`+(value==null?"；当前或模板结果缺失，无法比较":"");el.dataset.direction=value==null||Math.abs(value)<.0005?"same":value>0?"up":"down"});
}
function restoreGradeSelection(){include=schemeSelection(current);dirty=false;renderGrades();toast("已恢复「"+(GRADE_BUILTINS[current]?.name||current)+"」的课程选择")}
function renderGradeRules(){
 const box=$("#grade-rules"),custom=!GRADE_BUILTINS[current];if(box.dataset.scheme!==current)box.open=false;box.dataset.scheme=current;
 $("#grade-rules-title").textContent=custom?`基于${gradeBaseName(gradeBase)}的自定义模板`:GRADE_BUILTINS[current].name;
 $("#grade-template-dirty").hidden=!dirty;
 $("#grade-policy").innerHTML=(custom?`基于${esc(gradeBaseName(gradeBase))}的自定义模板。 `:"")+gradePolicy(gradeBase,false)+(D.grades.some(g=>g.nature==="未标注")?' <strong>部分课程未标注性质，请手动核对计入范围。</strong>':"");
}
function renderTemplateSummary(){
 const box=$("#grade-template-summary"),custom=!GRADE_BUILTINS[current],rule=(D.scheme_rules||{})[current];box.hidden=!custom&&!dirty;if(box.hidden)return;
 const open=box.dataset.scheme===current?new Set([...box.querySelectorAll('details[open]')].map(d=>d.dataset.change)):new Set();
 const baseName=gradeBaseName(gradeBase),changes=gradeTemplateChanges(D.grades,include,gradeBase);
 const course=g=>`<span class="grade-change-course" title="${esc((g.term||"未标注学期")+" · "+g.nature)}">${esc(g.name)}</span>`;
 const line=(kind,label,items)=>!items.length?"":`<div><span class="grade-change-label ${kind}">${label}</span>${items.slice(0,5).map(course).join("、")}${items.length>5?`<details class="grade-change-more" data-change="${kind}" ${open.has(kind)?"open":""}><summary title="展开其余 ${items.length-5} 门课程">等 ${items.length} 门课</summary><span>${items.slice(5).map(course).join("、")}</span></details>`:""}</div>`;
 box.dataset.scheme=current;box.innerHTML=`<p class="grade-template-base">${custom?"基于":"当前选择基于"}<strong>${esc(baseName)}</strong>${custom?"的自定义模板":""}${custom&&!rule?' <span class="sub">（旧模板未记录基础规则，以所有课程对照）</span>':""}${dirty?' <span class="miss grade-unsaved">未保存</span>':""}</p>`+line("added","增加了",changes.added)+line("removed","减少了",changes.removed)+(!changes.added.length&&!changes.removed.length?'<p class="sub">与基础模板一致，暂无课程增减。</p>':"");
}
function schemeOptions(){const s=$("#scheme");s.innerHTML='<optgroup label="内置模板">'+Object.entries(GRADE_BUILTINS).map(([id,b])=>`<option value="${id}">${b.name}</option>`).join("")+'</optgroup>'+ (Object.keys(D.schemes).length?'<optgroup label="自定义模板">'+Object.keys(D.schemes).map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join("")+'</optgroup>':"");s.value=current in D.schemes||current in GRADE_BUILTINS?current:"__postgraduate__"}
function schemeSelection(name){return gradeSchemeSelection(D.grades,GRADE_BUILTINS[name],(D.scheme_rules||{})[name],D.schemes[name]||[])}
function applyScheme(name){current=name;const b=GRADE_BUILTINS[name],rule=(D.scheme_rules||{})[name];gradeBase=b?.base||rule?.base||"comprehensive";include=schemeSelection(name);dirty=false;renderGrades()}
function gradeFilters(){return{q:$("#grade-search").value.trim().toLocaleLowerCase(),term:$("#termf").value,terms:[...document.querySelectorAll('#grade-terms input:checked')].map(e=>e.value),natures:[...document.querySelectorAll('#grade-natures input:checked')].map(e=>e.value),inclusion:$("#grade-inclusion").value,status:$("#grade-status").value,ranges:[["numeric_score",$("#grade-score-min").value,$("#grade-score-max").value],["point",$("#grade-point-min").value,$("#grade-point-max").value],["credit",$("#grade-credit-min").value,$("#grade-credit-max").value]]}}
function visibleGrades(){const f=gradeFilters();return D.grades.filter(g=>gradeMatches(g,f,include)).sort((a,b)=>gradeCompare(a,b,gradeSort))}
function gradeFilterOptions(){for(const [id,key] of [["grade-terms","term"],["grade-natures","nature"]]){const box=$("#"+id),keep=new Set([...box.querySelectorAll('input:checked')].map(e=>e.value));box.innerHTML=[...new Set(D.grades.map(g=>g[key]))].sort().map(v=>`<label><input type="checkbox" value="${esc(v)}" ${keep.has(v)?"checked":""}>${esc(v||"未标注")}</label>`).join("")||'<span class="sub">暂无选项</span>'}}
function resetGradeFilters(render=true){document.querySelectorAll('#grade-filter input').forEach(e=>e.type==="checkbox"?e.checked=false:e.value="");$("#grade-search").value="";$("#termf").value="";$("#grade-inclusion").value="";$("#grade-status").value="";gradeSort={key:"",dir:0};if(render)renderGrades()}
function gradeReady(){if(D?.grades.length)return true;toast("还没有成绩数据，请先导入成绩单或从教务刷新",true);return false}
function renderGrades(){
 const saved=schemeSelection(current);dirty=gradeSelectionChanged(D.grades,include,saved);
 const result=gradeTotals(D.grades,include),rows=visibleGrades(),fmt=n=>n==null?"—":String(Math.round(n*1000)/1000);
 const values={score:result.score==null?"—":result.score.toFixed(3),point:result.point==null?"—":result.point.toFixed(3),credit:fmt(result.credits)},selection=gradeSelectionCount(D.grades,include);
 for(const [key,value] of Object.entries(values))document.querySelectorAll(`[data-grade-value="${key}"]`).forEach(el=>el.textContent=value);
 document.querySelectorAll('[data-grade-selected]').forEach(el=>el.textContent=selection.selected);document.querySelectorAll('[data-grade-total]').forEach(el=>el.textContent=selection.total);document.querySelectorAll('.grade-count').forEach(el=>el.setAttribute("aria-label",`已选 ${selection.selected} 门，共 ${selection.total} 门课程`));renderTemplateSummary();
 $("#grade-calc-note").textContent=`成绩与绩点按学分加权 · ${D.grade_source==="import"?"使用成绩单提供的绩点；缺失时显示 —":"优先使用教务单科绩点；标有「估算」的课程按原程序规则换算；通过类不参与加权"}${result.invalid?` · ${result.invalid} 门成绩无法换算，已按 0 分计入，请核对`:""}${result.estimated?` · ${result.estimated} 门使用估算绩点`:""}`;
 renderGradeRules();
 $("#grade-source").textContent=D.grade_source==="import"?"文件预览":"当前账号 · 教务成绩";$("#grade-source").title=D.grade_filename||"";$("#grade-use-jwxt").hidden=D.grade_source!=="import";$("#grade-sync").hidden=D.grade_source==="import";$("#grade-view-import").hidden=!D.has_imported_grades||D.grade_source==="import";$("#del").disabled=!!GRADE_BUILTINS[current];
 if(!gradeSyncing)$("#grade-sync-status").textContent=gradeStatusText(D,gradeSessionState);
 $("#dirty").textContent=dirty?"● 有未保存的修改，另存模板后可重复使用":"";$("#grade-visible").textContent=`显示 ${rows.length} / ${D.grades.length} 门`;
 $("#grade-restore").disabled=!dirty;renderGradeDelta(result,saved);renderGradeIssues();scheduleGradeCompact();
 const f=gradeFilters(),active=f.terms.length+f.natures.length+(f.inclusion?1:0)+(f.status?1:0)+f.ranges.filter(r=>r[1]!==""||r[2]!=="").length;$("#grade-filter-count").textContent=active?`· ${active} 项条件`:"";
 document.querySelectorAll('[data-grade-sort]').forEach(th=>{const active=th.dataset.gradeSort===gradeSort.key&&gradeSort.dir;th.setAttribute("aria-sort",active?(gradeSort.dir===1?"ascending":"descending"):"none");const b=th.querySelector("button"),label=b.textContent.replace(/ [↕↑↓]$/u,"");b.textContent=label+" "+(active?(gradeSort.dir===1?"↑":"↓"):"↕")});
 $("#gt").innerHTML=rows.map(g=>{const on=include.has(g.key),failed=g.numeric_score!=null&&g.numeric_score<60;return`<tr class="${on?"":"off"}${failed?" failed":""}"><td><input type="checkbox" data-k="${esc(g.key)}" aria-label="计入 ${esc(g.name)} ${esc(g.term)}" ${on?"checked":""}></td><td><span class="name">${esc(g.name)}</span>${g.ungraded?'<span class="grade-badge">通过类 · 不参与加权</span>':!g.score_valid?'<span class="grade-badge">成绩无法换算 · 计入时按 0 分</span>':""}</td><td><span class="sub">${esc(g.nature)}</span></td><td class="n">${fmt(g.credit)}</td><td class="n">${esc(g.score)}</td><td class="n">${g.point==null?"—":fmt(g.point)}${g.point_source==="estimated"&&g.point!=null?'<span class="grade-badge">估算</span>':""}</td><td><span class="sub">${esc(g.term||"未标注")}</span></td></tr>`}).join("")||`<tr><td colspan="7" class="empty">${D.grades.length?"没有符合筛选条件的课程，请调整或重置筛选":"还没有成绩数据，导入成绩单或从教务刷新后即可计算"}</td></tr>`;
 const notes=D.grade_notes||[];$("#grade-notes").innerHTML=notes.length?`<details><summary>导入说明 · ${notes.length} 项</summary>${notes.map(n=>`<p class="sub">${esc(n)}</p>`).join("")}</details>`:"";
}
function cd(e){if(!e.start)return{cls:"",big:"?",sm:"待定"};const ms=new Date(e.start)-new Date();if(ms<0)return{cls:"past",big:"✓",sm:"已结束"};const d=Math.floor(ms/864e5);if(d>=1)return{cls:d<=3?"soon":"",big:d,sm:"天"};return{cls:"soon",big:Math.ceil(ms/36e5),sm:"小时"}}
function fmtTime(e){if(!e.start)return"时间待定";const s=e.start.replace("T"," ");return s+(e.end?"–"+e.end.slice(11):"")}
function renderExams(){
 const L=D.exams.map(e=>{const c=cd(e);return`<div class="exam"><div class="cd ${c.cls}"><b>${c.big}</b><span>${c.sm}</span></div><div class="t"><b>${esc(e.name)}</b><span class="sub">${esc(fmtTime(e))}<br>${esc(e.location)}${e.seat?" · 座位 "+esc(e.seat):""}${e.kind?" · "+esc(e.kind):""}</span></div></div>`});
 $("#exams").innerHTML=L.join("")||'<p class="empty">暂无考试安排数据（刷新后若教务已发布会显示在这里）</p>';
}
function renderOfficial(){const o=D.official_gpa,box=$("#ogpa");if(D.grade_source==="import"){box.hidden=true;return}if(o&&o.available===false){box.hidden=false;box.innerHTML=`<h3>教务官方统计</h3><p class="sub" style="margin:0">吉大教务暂未提供「学分绩点统计」接口；成绩里若含教务单科绩点，会显示其学分加权结果。</p>`;return}if(!o||!o.items||!o.items.length){box.hidden=true;return}box.hidden=false;
 box.innerHTML=`<h3>教务官方统计 <span class="chip">只读</span></h3><div class="ogpa">${o.items.map(i=>`<div><span class="sub">${esc(i.label)}</span><b>${esc(i.value)}</b></div>`).join("")}</div><p class="sub" style="margin:8px 0 0">${o.source==="grades_jw_point"?"按教务单科绩点计算":"来自教务「学分绩点统计」"}${o.plan?" · "+esc(o.plan):""}</p>`}
function num(v){return v==null?"-":(Math.round(v*100)/100)}
function officialCard(){const o=D.official_gpa;if(!o||o.source!=="official"||!o.items)return"";return`<div class="card"><h2>教务官方 GPA <span class="chip">只读</span></h2><div class="ogpa">${o.items.map(i=>`<div><span class="sub">${esc(i.label)}</span><b>${esc(i.value)}</b></div>`).join("")}</div></div>`}
let PF={st:"",tm:"",nt:""};
function planCourses(){return(D.plan_courses&&D.plan_courses.courses)||[]}
function pfOk(c){return(!PF.st||c.status===PF.st)&&(!PF.tm||(c.term||"")===PF.tm)&&(!PF.nt||(c.nature||c.category||"")===PF.nt)}
function planFilters(){const cs=planCourses();if(!cs.length)return"";const u=k=>[...new Set(cs.map(k).filter(Boolean))].sort();const sel=(id,l,v,lab)=>`<label>${lab}<select id="${id}"><option value="">全部</option>${l.map(x=>`<option${x===v?" selected":""}>${esc(x)}</option>`).join("")}</select></label>`;
 const n=s=>cs.filter(c=>c.status===s).length;return`<div class="card"><h2>培养方案课程 <span class="sub">${cs.length} 门 · 已修 ${n("已修")} · 在修 ${n("在修")} · 未修 ${n("未修")}</span></h2><div class="rgrid">${sel("pf-st",["已修","在修","未修","未通过"],PF.st,"状态")}${sel("pf-tm",u(c=>c.term),PF.tm,"修读学期")}${sel("pf-nt",u(c=>c.nature||c.category),PF.nt,"课程性质/类别")}</div></div>`}
let PDEPT=false;
function courseRows(cs){PDEPT=planCourses().some(c=>c.dept);const tag={"已修":"done","在修":"chip","未修":"miss","未通过":"miss"};return cs.filter(pfOk).map(c=>`<tr><td><span class="${tag[c.status]||"chip"}">${esc(c.status)}</span></td><td>${esc(c.code)}</td><td>${esc(c.name)}</td><td>${c.credit??""}</td><td>${esc(c.hours||"")}</td><td>${esc(c.nature||c.category||"")}</td><td>${esc(c.exam_type||"")}</td><td>${esc(c.term||"")}</td>${PDEPT?`<td>${esc(c.dept||"")}</td>`:""}<td>${esc(c.score||"")}</td></tr>`).join("")}
function pch(){PDEPT=planCourses().some(c=>c.dept);return`<tr><th>状态</th><th>课程号</th><th>课程名</th><th>学分</th><th>学时</th><th>性质</th><th>考试类型</th><th>修读学期</th>${PDEPT?"<th>开课单位</th>":""}<th>成绩</th></tr>`}
function groupCourses(g){const cs=g.courses||[];if(!cs.length)return"";const rows=courseRows(cs);const k=cs.filter(pfOk).length;return`<details class="gc"${PF.st||PF.tm||PF.nt||cs.length<=8?" open":""}><summary>课程 ${k}/${cs.length}</summary><div style="overflow-x:auto"><table class="rt"><thead>${pch()}</thead><tbody>${rows||'<tr><td colspan="10" class="sub">无符合筛选的课程</td></tr>'}</tbody></table></div></details>`}
function ungrouped(){const c=D.completion,cs=planCourses();if(!cs.length)return"";const inG=new Set(((c&&c.groups)||[]).flatMap(g=>(g.courses||[]).map(x=>x.code+"|"+x.group_code)));const rest=cs.filter(x=>!inG.has(x.code+"|"+x.group_code));if(!rest.length)return"";return`<div class="card"><h2>${c&&c.groups&&c.groups.length?"未归入课组的课程":"全部课程"} <span class="sub">${rest.filter(pfOk).length} 门</span></h2><div style="overflow-x:auto"><table class="rt"><thead>${pch()}</thead><tbody>${courseRows(rest)}</tbody></table></div></div>`}
const isDone=c=>(c.status_code||({"已修":"done"})[c.status])==="done";
function doneCredits(n,seen=new Set()){if(seen.has(n.code))return 0;seen.add(n.code);return(n.courses||[]).filter(isDone).reduce((s,c)=>s+(+c.credit||0),0)+(n.children||[]).reduce((s,x)=>s+doneCredits(x,seen),0)}
function fixEarned(n){const e=Math.max(+n.earned>0?+n.earned:0,Math.round(doneCredits(n)*100)/100);n.earned=e;if(n.required!=null)n.missing=Math.max(0,Math.round((n.required-e)*100)/100);(n.children||[]).forEach(fixEarned);return n}
function nodeCount(n){return(n.courses||[]).length+(n.children||[]).reduce((s,x)=>s+nodeCount(x),0)}
function treeNode(n,d){const p=n.required?Math.min(100,(n.earned||0)/n.required*100):0;const ok=n.required!=null&&!n.missing;const cs=n.courses||[];const k=cs.filter(pfOk).length;
 const leaf=!(n.children||[]).length;return`<details class="tn"${d<1||(leaf&&cs.length<=3)?" open":""} style="margin-left:${Math.min(d,4)*10}px"><summary><b>${esc(n.name)}</b>${n.nature?` <span class="chip">${esc(n.nature)}</span>`:""} <span class="sub">${num(n.earned)}${n.required!=null?" / "+num(n.required):""} 学分${n.earned_source==="plan_courses"?" (按课程)":""} · ${nodeCount(n)} 门</span> ${ok?'<span class="done">✓</span>':n.missing?`<span class="miss">差 ${num(n.missing)}</span>`:""}</summary>${n.required?`<div class="bar"><i style="width:${p.toFixed(1)}%;${ok?"background:var(--ok)":""}"></i></div>`:""}${cs.length?`<div style="overflow-x:auto"><table class="rt"><thead>${pch()}</thead><tbody>${courseRows(cs)||'<tr><td colspan="10" class="sub">无符合筛选的课程</td></tr>'}</tbody></table></div>`:""}${(n.children||[]).map(ch=>treeNode(ch,d+1)).join("")}</details>`}
function unmatchedCard(c){const u=c.unmatched||[];if(!u.length)return"";const R={selected_now:"本学期已选（培养方案里没有列出，课组以教务为准）",substitute:"替代/认定课程",kzh_not_in_tree:"课组号不在方案课组树中",no_kzh:"无课组号"};const by={};u.forEach(x=>(by[x.unmatched_reason]=by[x.unmatched_reason]||[]).push(x));
 return`<div class="card"><h2>未归组课程 <span class="sub">${u.length} 门</span></h2>${Object.entries(by).map(([r,l])=>`<details><summary>${esc(R[r]||r)} · ${l.length} 门</summary><div style="overflow-x:auto"><table class="rt"><thead>${pch()}</thead><tbody>${courseRows(l)}</tbody></table></div></details>`).join("")}</div>`}
function hydrateGroups(c){const cs=planCourses();if(!c||!cs.length)return c;const gs=c.groups||[];const need=!c.tree||!c.tree.length||gs.some(g=>!(g.courses&&g.courses.length));if(!need)return c;const byC={},byN={};gs.forEach(g=>{if(g.code)byC[g.code]=g;if(g.name)byN[g.name]=g;g.courses=g.courses||[]});if(gs.every(g=>g.courses.length)){/* only fix earned */}else{cs.forEach(x=>{const g=byC[x.group_code]||byN[x.group];if(g&&!g.courses.some(y=>y.code===x.code&&y.group_code===x.group_code))g.courses.push(x)})}
 gs.forEach(g=>{const from=(g.courses||[]).filter(isDone).reduce((s,x)=>s+(+x.credit||0),0);const srv=(+g.earned>0)?+g.earned:null;if(srv==null||from>srv){g.earned=Math.round(from*100)/100;g.earned_source="plan_courses";if(g.required!=null){g.missing=Math.max(0,Math.round((g.required-g.earned)*100)/100);g.passed=!g.missing}}});return c}
/* 学业完成刷新失败时在页面上说明原因，不再只在提示条里一闪而过 */
let PROG_ERR="";
function progRefreshError(r){return [["completion","学业总览"],["plan_courses","培养方案明细"]].flatMap(([key,label])=>{const c=r&&r[key];if(!c||c.ok!==false)return[];const why=c.login_needed?"登录已过期，请到「更多 → 账号」重新登录后再刷新。":c.skipped?"登录已过期，这次没有更新。":(c.error||"教务暂时没有返回数据");return[label+"："+why]}).join("；")}
function progErrCard(){return PROG_ERR?`<div class="banner err progress-error" role="alert"><div><b>${PROG_ERR.startsWith("培养方案明细：")?"培养方案明细没有刷新成功":"学业完成没有刷新成功"}</b><p class="sub">${esc(PROG_ERR)}${D&&(D.completion||D.plan_courses)?" 部分内容可能是上次保存的数据。":""}</p></div><button class="btn" type="button" onclick="fullRefresh({forceAcademic:true}).catch(()=>{})">重试</button></div>`:""}
let academicBusy=false,academicJob={state:"idle"},academicNotice=null,academicUpdating=false,academicPollTimer=null;
function academicTime(value){if(!value)return"暂无记录";const d=new Date(typeof value==="number"?value*1000:String(value).trim().replace(" ","T"));if(Number.isNaN(d.getTime()))return"暂无记录";const p=v=>String(v).padStart(2,"0");return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}
function academicCard(){const m=D.academic_meta||{},c=D.completion||{},changed=m.school_calculated_at&&m.cached_calculated_at&&m.school_calculated_at!==m.cached_calculated_at,status=academicNotice||academicJob;return`<div class="card"><div class="academic-head"><h2>学业数据</h2><div class="academic-actions"><button class="btn ghost" id="academic-update" type="button" onclick="updateAcademicData()"${academicBusy?" disabled":""}>从教务更新</button><button class="btn ghost" id="academic-recalculate" type="button" onclick="startAcademicRecalculation()"${academicBusy?" disabled":""}>重新计算</button></div></div><dl class="academic-times"><div><dt>更新到本机</dt><dd>${esc(academicTime(m.local_synced_at))}</dd></div><div><dt>教务计算于</dt><dd>${esc(academicTime(m.school_calculated_at||c.calculated_at))}</dd></div></dl>${changed?'<p class="sub" style="color:var(--warn)">教务已有新的计算结果，点「从教务更新」即可查看。</p>':""}<p class="sub" style="margin-bottom:0">在教务网站计算过了？点「从教务更新」。课程仍不完整时，可让教务「重新计算」。</p><p id="academic-status" class="academic-status" data-state="${esc(status.state||"idle")}" role="status">${esc(status.state==="success"?"✓ "+(status.message||"学业数据已更新"):status.message||"")}</p></div>`}
async function pollAcademicRecalculation(){clearTimeout(academicPollTimer);if(academicUpdating)return;try{const j=await api("/api/academic/recalculate");if(academicUpdating)return;const finished=j.state==="success"&&academicJob.state!=="success"&&!academicNotice;academicJob=j;academicBusy=["submitting","running","syncing"].includes(j.state);if(finished){D=gradeRefreshSnapshot(D,await api("/api/data"));PROG_ERR="";renderAll()}else renderProgress();if(academicBusy)academicPollTimer=setTimeout(pollAcademicRecalculation,2000)}catch(e){academicBusy=false;academicJob={state:"unconfirmed",message:"暂时连不上程序，尚未确认计算结果。请稍后再打开学业页查看，不要重复提交。"};renderProgress()}}
function startAcademicRecalculation(){if(academicBusy||bootRefreshing)return;const dialog=$("#academic-confirm");if(!dialog.open)dialog.showModal()}
async function submitAcademicRecalculation(){if(academicBusy||bootRefreshing)return;$("#academic-confirm").close();academicNotice=null;academicBusy=true;academicJob={state:"submitting",message:"已请求教务重新计算，请稍候…"};renderProgress();try{await api("/api/academic/recalculate",{confirmed:true});await pollAcademicRecalculation()}catch(e){academicBusy=false;academicJob={state:"failed",message:e.message};renderProgress()}}
async function updateAcademicData(){if(academicBusy||bootRefreshing)return;academicUpdating=true;academicBusy=true;clearTimeout(academicPollTimer);academicNotice={state:"running",message:"正在从教务更新学业数据…"};renderProgress();try{const j=await api("/api/academic/refresh",{});D=gradeRefreshSnapshot(D,j);PROG_ERR="";academicNotice={state:"success",message:"已从教务更新学业数据。"};renderAll()}catch(e){academicNotice={state:"failed",message:"更新没有完成，已保留原有数据。请检查网络或重新登录后再试。"};try{D=gradeRefreshSnapshot(D,await api("/api/data"))}catch(_){} }finally{academicUpdating=false;academicBusy=false;renderProgress()}}
$("#academic-confirm-cancel").onclick=()=>$("#academic-confirm").close();
$("#academic-confirm-form").onsubmit=e=>{e.preventDefault();submitAcademicRecalculation()};
document.querySelector('nav button[data-t="xy"]').addEventListener("click",()=>pollAcademicRecalculation());
function renderProgress(){const c=hydrateGroups(D.completion),box=$("#prog");
 if(!c){box.innerHTML=academicCard()+progErrCard()+officialCard()+'<div class="card"><p class="empty">还没有学业完成数据，点右上角“刷新”</p></div>';return}
 const pct=c.required?Math.min(100,(c.earned||0)/c.required*100):0;
 let h=academicCard()+progErrCard()+officialCard()+`<div class="card"><h2>${esc(c.plan||"培养方案")}</h2><div class="row"><span class="big">${num(c.earned)}</span><span class="sub">/ ${num(c.required)} 学分</span><span class="sp"></span>${c.passed?'<span class="done">✓ 已满足毕业学分</span>':`<span class="miss">还差 ${num(c.missing)} 学分</span>`}</div><div class="bar"><i style="width:${pct.toFixed(1)}%"></i></div><p class="sub" style="margin:0">${c.selected!=null?"已选（含在修）"+num(c.selected)+" 学分 · ":""}${c.calculated_at?"教务计算于 "+esc(academicTime(c.calculated_at)):""}</p></div>`;
 const gs=c.groups||[];
 if(c.tree&&c.tree.length){const st=c.tree_stats||{};h+=planFilters()+`<div class="card"><h2>课组树 <span class="sub">${st.groups||0} 个课组 · 课程已归组 ${st.matched||0}/${st.courses||0}</span></h2>${c.tree.map(n=>treeNode(fixEarned(n),0)).join("")}</div>`+unmatchedCard(c);box.innerHTML=h;return}
 if(gs.length){const todo=gs.filter(g=>!g.passed&&(g.missing||0)>0);
  h+=planFilters()+`<div class="card"><h2>各类课程 <span class="sub">${todo.length?todo.length+" 类未完成":"全部完成"}</span></h2>`+gs.map(g=>{const p=g.required?Math.min(100,(g.earned||0)/g.required*100):0;return`<div class="grp"><div class="row"><b>${esc(g.name)}</b>${g.nature?`<span class="chip">${esc(g.nature)}</span>`:""}</div><div class="bar"><i style="width:${p.toFixed(1)}%;${g.passed?"background:var(--ok)":""}"></i></div><div class="row sub"><span>${num(g.earned)} / ${num(g.required)} 学分${g.courses_done?" · "+g.courses_done+" 门":""}${g.earned_source==="derived"?' <span class="chip">按成绩推算</span>':""}</span><span class="sp"></span>${g.passed||!g.missing?'<span class="done">已完成</span>':`<span class="miss">差 ${num(g.missing)}</span>`}</div>${groupCourses(g)}</div>`}).join("")+`</div>`}
 else h+='<div class="card"><p class="sub">暂时没有课组明细，只显示总学分。点右上角「刷新」重新同步培养方案；如仍不显示，说明教务没有返回你所在专业的课组数据。</p></div>';
 if(!gs.length)h+=planFilters();
 box.innerHTML=h+ungrouped()}
document.addEventListener("change",e=>{const id=e.target.id;if(id==="pf-st"||id==="pf-tm"||id==="pf-nt"){PF={st:$("#pf-st").value,tm:$("#pf-tm").value,nt:$("#pf-nt").value};renderProgress()}});
function fmtCached(t){if(!t)return"未知时间";const d=new Date(typeof t==="number"?t*1000:t);if(isNaN(d))return esc(String(t));const p=n=>String(n).padStart(2,"0");return `${d.getMonth()+1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`}
function offlineBadge(j){return j&&j.offline===true?`<span class="offl" title="登录失效或网络不通，显示的是本机缓存">⏏ 离线数据 · 更新于 ${fmtCached(j.cached_at)}</span>`:""}
function renderOffline(){const b=$("#offl");if(!b)return;const h=offlineBadge(D);b.hidden=!h;b.innerHTML=h}
function widgetExport(d){
 // 给安卓桌面小组件的精简课表快照（只含课表必要字段，不含成绩/账号）。
 if(!d||!Array.isArray(d.courses))return null;
 const per={};for(const [k,v] of Object.entries(d.periods||{}))if(Array.isArray(v)&&v.length>=2)per[String(k)]=[String(v[0]),String(v[1])];
 const cs=d.courses.filter(c=>c&&c.src!=="cancelled").map(c=>({name:String(c.name||""),location:String(c.location||""),teacher:String(c.teacher||""),weekday:+c.weekday||0,start:+c.start||0,end:+c.end||+c.start||0,weeks:(c.weeks||[]).map(Number).filter(w=>w>0)})).filter(c=>c.weekday>=1&&c.weekday<=7&&c.start>=1);
 return {v:1,first_monday:String(d.first_monday||"").slice(0,10),periods:per,courses:cs,updated:String(d.updated||"")};
 }
function widgetPush(){try{if(window.SuperJLU&&SuperJLU.saveWidgetData){const w=widgetExport(D);if(w)SuperJLU.saveWidgetData(JSON.stringify(w))}}catch(_){}}
function renderAll(){try{renderOffline();renderSession()}catch(_){}widgetPush();
 $("#upd").textContent=D.updated?"更新于 "+D.updated.replace("T"," "):"";
 $("#fm").value=D.first_monday||"";
 const terms=[...new Set(D.grades.map(g=>g.term))].sort().reverse();const tf=$("#termf"),keep=tf.value;
 tf.innerHTML='<option value="">全部学期</option>'+terms.map(t=>`<option>${esc(t)}</option>`).join("");tf.value=keep;
 document.getElementById("noc")?.remove();renderGrid();try{renderKbExtras();renderAdjToggle()}catch(_){}gradeFilterOptions();schemeOptions();if(!dirty)applyScheme($("#scheme").value);else renderGrades();renderExams();renderOfficial();renderProgress();
 const cal=D.calendar||{};$("#calinfo").innerHTML=D.first_monday?`第 1 周周一：<b>${esc(D.first_monday)}</b>（${D.first_monday_source==="manual"?"手动覆盖":"来自教务校历"}）${cal.term?" · "+esc(cal.term):""}${cal.total_weeks?" · 共 "+cal.total_weeks+" 周":""} · 今天第 ${weekOf(new Date())} 周`:"尚未读取校历：点右上角“刷新”自动获取开学日期。";
}
function refreshSummary(r){const c=k=>r&&r[k]&&r[k].ok?(r[k].cached?"缓存":(r[k].count??"✓")):"✗";return `课表 ${c("schedule")} · 成绩 ${c("grades")} · 考试 ${c("exams")} · 校历 ${c("calendar")} · 学业总览 ${c("completion")} · 培养方案明细 ${c("plan_courses")}`}
let bootRefreshing=false;
function setSyncInd(on){const ind=$("#sync-ind");if(!ind)return;ind.hidden=!on;ind.setAttribute("aria-hidden",on?"false":"true");if(on)ind.setAttribute("aria-label","正在刷新");else ind.removeAttribute("aria-label")}
async function subReq(m,path,body){const r=await fetch(path,body?{method:m,headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{method:m});let j=null;try{j=await r.json()}catch(_){}if(r.status===404&&(!j||j.ok===undefined)){const e=new Error("NOAPI");e.noapi=true;throw e}if(!r.ok||!j||j.ok===false)throw new Error((j&&j.error)||("HTTP "+r.status));return j}
const OACHN=id=>((OACHS||[]).find(c=>c.id===id)||{}).name||id;
async function loadSubs(){const b=$("#oa-sub-b");let j;try{j=await subReq("GET","/api/oa/subscriptions?limit=20")}catch(e){b.innerHTML=e.noapi?`<p class="sub" style="margin:0">当前版本还没有订阅功能，请更新 SuperJLU 后再试。</p>`:`<p class="sub" style="margin:0">读取订阅失败：${esc(e.message)}</p>`;return}
 const rules=j.rules||[],ms=(j.matches||[]).filter(m=>rules.some(r=>r.id===m.rule_id));
 b.innerHTML=`<p class="sub" style="margin:0 0 10px">按关键词（标题匹配）和发文单位订阅，只在本机保存。</p><div class="oaf"><input id="sub-kw" type="text" placeholder="关键词，逗号分隔，如 讲座,补考"><input id="sub-dp" type="text" placeholder="发文单位（可选，逗号分隔）"><button class="btn pri" id="sub-add">添加</button></div>`+
 (rules.length?`<ul class="oal" style="margin-top:8px">${rules.map(r=>`<li style="cursor:default"><div class="tt">${(r.keywords||[]).map(k=>`<span class="chip">${esc(k)}</span>`).join(" ")}<span class="mt">${(r.depts||[]).length?"单位："+esc(r.depts.join("、"))+" · ":""}${r.channel?esc(OACHN(r.channel)):"全部栏目"}</span></div><button class="btn ghost" data-del="${esc(r.id)}">删除</button></li>`).join("")}</ul>`:`<p class="sub" style="margin:12px 0 0">还没有订阅规则。</p>`)+
 `<h2 style="font-size:15px;margin:16px 0 4px">最近命中</h2>`+(ms.length?`<ul class="oal">${ms.map(m=>{const n=m.notice||{};return`<li data-id="${esc(n.id)}"><div class="tt">${n.top?'<span class="pin">置顶</span>':""}${esc(n.title)}<span class="mt">命中「${esc((m.keywords_hit||[]).join("、"))}」 · ${esc(n.dept||"")} · ${esc(n.time||"")}</span></div><span class="ar">›</span></li>`}).join("")}</ul>`:`<p class="sub" style="margin:0">暂无命中。添加订阅后，打开通知页或点「更新」时会检查是否有新消息。</p>`);
 $("#sub-add").onclick=async()=>{const kw=$("#sub-kw").value.trim();if(!kw)return toast("请填写关键词");const dp=$("#sub-dp").value.split(/[,，、]/).map(x=>x.trim()).filter(Boolean);try{await subReq("POST","/api/oa/subscriptions",{keywords:kw,depts:dp,channel:OACH});toast("已添加订阅");loadSubs()}catch(e){toast(e.noapi?"当前版本还没有订阅功能，请更新":e.message)}};
 b.querySelectorAll("[data-del]").forEach(x=>x.onclick=async()=>{/* 不用 confirm()：安卓 WebView 没有 WebChromeClient 时会静默返回 false，导致删不掉 */if(!x.dataset.armed){x.dataset.armed=1;x.textContent="确认删除";x.classList.add("pri");setTimeout(()=>{delete x.dataset.armed;x.textContent="删除";x.classList.remove("pri")},3000);return}try{await subReq("DELETE","/api/oa/subscriptions/"+encodeURIComponent(x.dataset.del))}catch(e){if(!/404/.test(e.message)&&!e.noapi)return toast(e.message)}loadSubs()});
 b.querySelectorAll("li[data-id]").forEach(li=>li.onclick=()=>openOA(li.dataset.id))}
async function fullRefresh({toastOnStart,okToast,failPrefix,forceAcademic=false}={}){if(bootRefreshing)return null;bootRefreshing=true;const b=$("#refresh");const prev=b?b.innerHTML:"";if(b){b.disabled=true;b.innerHTML='⟳<span class="lbl"> 刷新中…</span>'}setSyncInd(true);if(toastOnStart)toast(toastOnStart);try{const j=await api("/api/refresh",{force_academic:forceAcademic}),next=gradeRefreshSnapshot(D,j);if(D&&D.grade_source!==next.grade_source)dirty=false;D=next;if(typeof progRefreshError==="function")PROG_ERR=progRefreshError(j.result);renderAll();const msg=okToast||("已刷新："+refreshSummary(j.result));toast(msg,!!PROG_ERR);try{if(!window.__rm){window.__rm=1;roomsInit()}}catch(_){}loadOA().then(loadSubs).catch(()=>{});return j}catch(e){try{const has=D&&((D.courses||[]).length||(D.grades||[]).length||(D.exams||[]).length||D.completion);if(!has){const d=await fetch("/api/data").then(r=>r.json());if(d&&((d.courses||[]).length||(d.grades||[]).length||(d.exams||[]).length||d.completion)){D=gradeRefreshSnapshot(D,d);renderAll()}}}catch(_){}const partial=e&&e.payload&&e.payload.result;if(typeof progRefreshError==="function"){PROG_ERR=partial?progRefreshError(partial):(e&&e.message)||"刷新失败";try{renderProgress()}catch(_){}}const sum=partial?refreshSummary(partial):"";toast((failPrefix||"刷新失败：")+e.message+(sum?"（已显示部分："+sum+"）":""),true);throw e}finally{bootRefreshing=false;setSyncInd(false);if(b){b.disabled=false;b.innerHTML=prev||'⟳<span class="lbl"> 刷新</span>'}}}
async function load(){D=await api("/api/data");week=Math.min(Math.max(1,weekOf(new Date())),maxWeek());renderAll();try{rdToWeek()}catch(_){}api("/api/session").then(async s=>{gradeSessionState=s.state||(s.logged_in?"ok":s.needs_login?"missing":"unknown");lgInfo(s.logged_in===true);renderSession();if(!gradeSyncing)$("#grade-sync-status").textContent=gradeStatusText(D,gradeSessionState);if(s.logged_in===true&&D.grade_source!=="import"&&!gradeImporting){if(D.needs_bootstrap){try{await fullRefresh({toastOnStart:D.bootstrapped?"正在同步教务数据…":"首次同步教务数据中…",okToast:null,failPrefix:"自动同步失败："})}catch(_){}}else refreshGradeData(true)}}).catch(()=>{})}
let gradeSyncing=false;
async function refreshGradeData(automatic=false){if(gradeSyncing)return;gradeSyncing=true;const b=$("#grade-sync");b.disabled=true;b.textContent="⟳ 同步中…";$("#grade-sync-status").textContent="正在使用已保存的登录会话同步教务成绩…";try{const j=await api("/api/grades/refresh",{auto:automatic});if(D.grade_source!=="import"&&!gradeImporting){D=j;renderAll();$("#grade-sync-status").textContent=`已同步当前账号的 ${j.grade_result.count} 门教务课程。`}if(!automatic)toast("教务成绩已同步")}catch(e){if(D.grade_source!=="import")$("#grade-sync-status").textContent="同步失败，保留本机成绩缓存："+e.message;if(!automatic)toast("同步失败："+e.message,true)}finally{gradeSyncing=false;b.disabled=false;b.textContent="⟳ 同步教务成绩";if(D.grade_source==="import"||gradeSessionState==="expired"||gradeSessionState==="missing")$("#grade-sync-status").textContent=gradeStatusText(D,gradeSessionState)}}
function sessionInfo(d){const s=d&&d.session;const exp=(d&&d.session_expired===true)||(s&&(s.expired===true||s.valid===false||/^(expired|invalid)$/i.test(String(s.status||s.state||""))));if(exp||gradeSessionState==="expired")return s||{};return gradeSessionState==="missing"?{missing:true}:null}
function renderNextClass(){
 const box=$("#kb-next");if(!box)return;
 if(!D){box.hidden=true;return}
 const s=sessionInfo(D),courses=D.courses||[];
 let cap=30;try{cap=maxWeek()}catch(_){}
 const now=new Date(),hit=D.first_monday?nextClass(courses,periodMap(),D.first_monday,now,cap):null;
 let lab;
 if(!courses.length)lab={k:"课表",t:s&&s.missing?"登录后同步课表":"还没有课表",sub:s&&!s.missing?"点右上角刷新":""};
 else if(!D.first_monday)lab={k:"课表",t:"刷新后显示下一节课",sub:""};
 else lab=nextClassLabel(hit,now);
 const login=s?`<button class="btn" type="button" onclick="openLogin()">${s.missing?"登录":"重新登录"}</button>`:"";
 const html=`<span class="k${hit&&hit.kind==="now"?" now":""}">${esc(lab.k)}</span><button type="button" class="main" id="kb-next-go"${hit?"":" disabled"}><b>${esc(lab.t)}</b>${lab.sub?` <span class="sub">${esc(lab.sub)}</span>`:""}</button>${login}`;
 box.hidden=false;if(box.dataset.v===html)return;box.dataset.v=html;box.innerHTML=html;
 const go=$("#kb-next-go");if(go&&hit)go.onclick=()=>{week=Math.min(Math.max(1,hit.week),cap);renderGrid()};
}
function renderSession(){try{renderNextClass()}catch(_){}const box=$("#sess"),s=sessionInfo(D),onKb=!!document.querySelector("#t-kb.on");if(!s||onKb){box.hidden=true;box.innerHTML="";return}box.hidden=false;
 box.innerHTML=`<div class="banner slim" role="status"><span>${s.missing?"尚未登录":(D&&D.session_site?esc(SITEN(D.session_site))+" ":"")+"登录已过期"}</span><button class="btn" type="button" onclick="openLogin()">${s.missing?"登录":"重新登录"}</button></div>`}
setInterval(()=>{try{if(D)renderNextClass()}catch(_){}},60000);
document.addEventListener("visibilitychange",()=>{if(document.hidden)return;try{renderNextClass()}catch(_){}});
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("nav button,.tab").forEach(x=>x.classList.remove("on"));b.classList.add("on");$("#t-"+b.dataset.t).classList.add("on");scrollTo(0,0);scheduleGradeCompact();try{renderSession()}catch(_){}if(b.dataset.t==="cj"&&!gradeHelpSeen())openGradeHelp()});
$("#prev").onclick=()=>{if(week>1){week--;renderGrid()}};$("#next").onclick=()=>{if(week<maxWeek()){week++;renderGrid()}};
function kbAddAt(el){if(!el||!el.classList||!el.classList.contains("cell"))return;const now=Date.now();if(kbAddAt.lock&&now-kbAddAt.lock<500)return;const maxP=Math.max(11,...(KB_CS||[]).map(c=>+c.end||0));const seed=kbBlankSeed(+el.dataset.d,+el.dataset.p,kbOcc(KB_CS),week,maxP);if(!seed)return;kbAddAt.lock=now;kbForm(null,seed)}
$("#grid").addEventListener("click",e=>{const el=e.target.closest(".cls");if(el)return kbOpen(KB_CS[+el.dataset.i]);const c=e.target.closest(".cell");if(c&&e.detail<2)kbHint(c)});
$("#grid").addEventListener("dblclick",e=>{const el=e.target.closest&&e.target.closest(".cell");if(!el||(e.target.closest&&e.target.closest(".cls")))return;e.preventDefault();kbAddAt(el)});
$("#grid").addEventListener("keydown",e=>{const el=e.target.closest&&e.target.closest(".cls");if(el&&(e.key==="Enter"||e.key===" ")){e.preventDefault();kbOpen(KB_CS[+el.dataset.i])}});
$("#adj-on").onchange=async e=>{const on=e.target.checked;try{const j=await api("/api/settings",{apply_adjustments:on});D=gradeRefreshSnapshot(D,j);renderAll();toast(on?"已开启，调课会显示在课表上":"已关闭，课表按教务原始安排显示")}catch(err){e.target.checked=!on;toast(err.message,true)}};
$("#kb-add").onclick=()=>kbForm(null);$("#kb-issues").onclick=kbActionClick;$("#kb-edits-list").onclick=kbActionClick;
$("#kb-reset").onclick=()=>{if(confirm("把本学期课表恢复成教务原样？你的修改会先收起来，马上可以「撤销恢复」。"))kbPost({action:"reset"},"已恢复教务原样")};
$("#kb-undo").onclick=()=>kbPost({action:"undo_reset"},"已撤销，你的修改回来了");
$("#kb-import-btn").onclick=()=>$("#kb-import").click();
$("#kb-import").onchange=e=>{const f=e.target.files&&e.target.files[0];e.target.value="";if(!f)return;const r=new FileReader();r.onload=()=>kbImportText(String(r.result));r.onerror=()=>toast("无法读取这个文件",true);r.readAsText(f)};
$("#kb-paste-ok").onclick=()=>{const t=$("#kb-paste").value.trim();if(!t)return toast("请先粘贴备份内容",true);kbImportText(t).then(ok=>{if(ok)$("#kb-paste").value=""})};
$("#kb-export").onclick=async e=>{if(!/SuperJLU-Android/.test(navigator.userAgent))return;e.preventDefault();let t;try{t=await fetch("/api/schedule/overlay").then(r=>r.text())}catch(_){return toast("读取备份失败",true)}$("#kb-backup-text").value=t;$("#kb-backup-box").hidden=false;try{const f=new File([t],"superjlu-schedule-edits.json",{type:"application/json"});if(navigator.canShare&&navigator.canShare({files:[f]}))await navigator.share({files:[f],title:"SuperJLU 课表修改备份"})}catch(_){}};
$("#kb-copy").onclick=async()=>{const t=$("#kb-backup-text");t.select();let ok=false;try{await navigator.clipboard.writeText(t.value);ok=true}catch(_){try{ok=document.execCommand("copy")}catch(_){}}toast(ok?"已复制，可以粘贴到聊天或备忘录里保存":"复制失败，请长按文字手动复制",!ok)};
$("#today").onclick=()=>{week=Math.min(Math.max(1,weekOf(new Date())),maxWeek());renderGrid()};
function kbSwipe(dx,dy,dt,width){
 // 只认「明确、完整的左右滑」：水平位移 ≥ 视图宽度 35%（至少 120px），水平分量 > 2.5 倍竖直分量，且速度够快（≥0.3px/ms，≤900ms）。返回 1=下一周，-1=上一周，0=不切换。
 const w=+width>0?+width:360,ax=Math.abs(dx),ay=Math.abs(dy);
 if(!(dt>0)||dt>900)return 0;
 if(ax<Math.max(120,w*.35))return 0;
 if(ax<=2.5*ay)return 0;
 if(ax/dt<.3)return 0;
 return dx<0?1:-1;
 }
let tx=null,kbTap=null;$("#grid").addEventListener("touchstart",e=>{if(e.touches.length!==1){tx=null;return}const t=e.touches[0];tx={x:t.clientX,y:t.clientY,at:Date.now(),multi:false}},{passive:true});
$("#grid").addEventListener("touchmove",e=>{if(tx&&e.touches.length>1)tx.multi=true},{passive:true});
$("#grid").addEventListener("touchend",e=>{if(tx===null)return;const t=e.changedTouches[0],s=tx;tx=null;if(s.multi)return;const dx=t.clientX-s.x,dy=t.clientY-s.y,g=$("#grid"),sw=kbSwipe(dx,dy,Date.now()-s.at,(g&&g.clientWidth)||window.innerWidth);if(sw){kbTap=null;kbHint(null);(sw>0?$("#next"):$("#prev")).click();return}if(Math.abs(dx)>10||Math.abs(dy)>10){kbTap=null;return}const el=e.target.closest&&e.target.closest(".cell");if(!el||(e.target.closest&&e.target.closest(".cls"))){kbTap=null;return}const now=Date.now(),key=el.dataset.d+"|"+el.dataset.p;if(kbTap&&kbTap.key===key&&now-kbTap.at<450){kbTap=null;kbHint(null);kbAddAt(el)}else{kbTap={key,at:now};kbHint(el)}});
let kbHintT=0;function kbHint(el){document.querySelectorAll("#grid .cell.hint").forEach(c=>{if(c!==el)c.classList.remove("hint")});clearTimeout(kbHintT);if(!el)return;el.classList.add("hint");kbHintT=setTimeout(()=>el.classList.remove("hint"),1800)}
$("#grade-restore").onclick=restoreGradeSelection;
$("#grade-issues").onclick=e=>{const button=e.target.closest("[data-grade-issue]");if(!button||!gradeReady())return;const kind=button.dataset.gradeIssue,active=$("#grade-status").value===kind;resetGradeFilters(false);$("#grade-status").value=active?"":kind;$("#grade-filter").open=true;renderGrades()};
$("#gt").onchange=e=>{const k=e.target.dataset.k;if(!k)return;e.target.checked?include.add(k):include.delete(k);renderGrades()};
$("#scheme").onchange=e=>{if(dirty&&!confirm("当前选择尚未保存，切换模板会放弃这些修改。继续？")){e.target.value=current;return}applyScheme(e.target.value)};$("#termf").onchange=renderGrades;
$("#all").onclick=()=>{if(!gradeReady())return;D.grades.forEach(g=>include.add(g.key));renderGrades()};
$("#none").onclick=()=>{if(!gradeReady())return;include.clear();renderGrades()};
$("#grade-required").onclick=()=>{if(!gradeReady())return;D.grades.filter(g=>g.required&&g.credit>0).forEach(g=>include.add(g.key));renderGrades()};
$("#saveas").onclick=()=>{if(!gradeReady())return;$("#grade-template-name").value=GRADE_BUILTINS[current]?"":current;$("#grade-save-dialog").showModal();$("#grade-template-name").focus()};
$("#grade-save-cancel").onclick=()=>$("#grade-save-dialog").close();
$("#grade-save-form").onsubmit=async e=>{e.preventDefault();const n=$("#grade-template-name").value.trim(),button=e.submitter;if(!n)return;if(GRADE_BUILTINS[n])return toast("请使用其他模板名称",true);if(n in D.schemes&&!confirm("已存在同名模板，覆盖它？"))return;button.disabled=true;try{D=await api("/api/schemes",{name:n,include:[...include],base:gradeBase,grade_source:D.grade_source});current=n;dirty=false;$("#grade-save-dialog").close();renderAll();toast("已保存自定义模板："+current)}catch(err){toast(err.message,true)}finally{button.disabled=false}};
$("#del").onclick=async()=>{if(GRADE_BUILTINS[current])return;if(!confirm("删除自定义模板「"+current+"」？"))return;try{D=await api("/api/schemes/delete",{name:current,grade_source:D.grade_source});current="__postgraduate__";dirty=false;renderAll();toast("已删除模板")}catch(e){toast(e.message,true)}};
$("#grade-search").oninput=renderGrades;$("#grade-filter").oninput=renderGrades;$("#grade-reset").onclick=resetGradeFilters;
document.querySelectorAll('[data-grade-sort]').forEach(th=>th.querySelector('button').onclick=()=>{if(!gradeReady())return;const key=th.dataset.gradeSort;gradeSort=gradeSort.key!==key?{key,dir:-1}:gradeSort.dir===-1?{key,dir:1}:{key:"",dir:0};renderGrades()});
$("#grade-filter").querySelector('summary').addEventListener('click',e=>{if(!gradeReady())e.preventDefault()});
async function openGradeHelp(){
 $("#grade-help-dialog").showModal();
 const box=$("#grade-college-links");if(box.dataset.loaded)return;
 try{const j=await api("/api/grades/colleges");box.innerHTML=j.links.map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.name)} ↗</a>`).join("");box.dataset.loaded="1"}
 catch(_){box.innerHTML='<span class="sub">官网入口暂不可用，请到学院官网查询当年政策。</span>'}
}
$("#grade-help").onclick=()=>openGradeHelp();
$("#grade-help-dialog").querySelectorAll('[data-grade-close]').forEach(b=>b.onclick=()=>$("#grade-help-dialog").close());
function gradeHelpSeen(){if(window.__ghs||(D&&D.settings&&D.settings.grade_help_seen))return true;try{return!!localStorage.getItem("jlu-grade-policy-v1")}catch(_){return false}}
$("#grade-help-dialog").addEventListener('close',()=>{window.__ghs=1;try{localStorage.setItem("jlu-grade-policy-v1","1")}catch(_){}if(D){D.settings=Object.assign(D.settings||{},{grade_help_seen:true})}fetch("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({grade_help_seen:true})}).catch(()=>{})});
document.querySelectorAll('[data-grade-copy]').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.textContent.trim());b.title="已复制到剪贴板";let status=$("#grade-copy-status");if(!status){status=document.createElement("p");status.id="grade-copy-status";status.setAttribute("role","status");$(".grade-keywords").after(status)}status.textContent="已复制到剪贴板："+b.textContent.trim();toast("已复制到剪贴板")}catch(_){toast("复制失败，请手动复制关键词",true)}});
let gradeImporting=false;
async function importGradeFile(file){
 if(!file)return;
 if(gradeImporting)return toast("正在导入，请稍候",true);
 if(!D)return toast("页面正在读取本地数据，请稍后重试",true);
 if(!/\.(xlsx|xls|csv)$/i.test(file.name))return toast("请选择 .xlsx、.xls 或 .csv 成绩单",true);
 if(file.size>5*1024*1024)return toast("成绩单超过 5 MB",true);
 if((dirty||D.grade_source==="import")&&!confirm("将切换至新导入的成绩单，当前课程选择请先保存为模板。继续？"))return;
 const b=$("#grade-import");gradeImporting=true;b.disabled=true;b.textContent="导入中…";
 try{const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(",")[1]);reader.onerror=()=>reject(new Error("无法读取成绩单"));reader.readAsDataURL(file)});D=await api("/api/grades/import",{filename:file.name,data});dirty=false;renderAll();resetGradeFilters();toast(`已导入 ${D.grades.length} 门课程，无需登录即可在本地计算`)}
 catch(e){toast("导入失败："+e.message,true)}
 finally{gradeImporting=false;b.disabled=false;b.textContent="导入成绩单";$("#grade-file").value="";if(!gradeSyncing)$("#grade-sync-status").textContent=gradeStatusText(D,gradeSessionState)}
}
$("#grade-import").onclick=()=>$("#grade-file").click();$("#grade-file").onchange=e=>importGradeFile(e.target.files[0]);
function gradeFileDrag(event){return Array.from(event.dataTransfer?.types||[]).includes("Files")||!!event.dataTransfer?.files?.length}
function gradePageActive(){return $("#t-cj").classList.contains("on")}
function gradeDragOver(event){if(!gradeFileDrag(event))return;event.preventDefault();event.dataTransfer.dropEffect="copy"}
function gradeDrop(event){if(!gradeFileDrag(event))return;event.preventDefault();if(!gradePageActive())return toast("请切换到「成绩」页后导入成绩单",true);const files=event.dataTransfer.files;if(files.length!==1)return toast("请每次只导入一份成绩单",true);return importGradeFile(files[0])}
// One document-level handler also covers the header, margins and page background.
document.addEventListener("dragover",gradeDragOver);
document.addEventListener("drop",gradeDrop);
async function switchGradeSource(source){if(dirty&&!confirm("当前课程选择尚未保存，切换前请先保存为模板。继续？"))return;try{D=await api("/api/grades/source",{grade_source:source});dirty=false;renderAll();resetGradeFilters();toast(source==="import"?"正在预览导入文件":"已返回当前账号的教务成绩")}catch(e){toast(e.message,true)}}
$("#grade-use-jwxt").onclick=()=>switchGradeSource("jwxt");$("#grade-view-import").onclick=()=>switchGradeSource("import");$("#grade-sync").onclick=()=>refreshGradeData();
$("#clrfm").onclick=async()=>{D=await api("/api/settings",{first_monday:""});await load();toast("已恢复为教务校历")};
document.querySelectorAll(".thm button").forEach(b=>b.onclick=()=>window.__setTheme(b.dataset.theme));window.__setTheme(localStorage.getItem("jlu-theme")||"system");
$("#savefm").onclick=async()=>{try{D=await api("/api/settings",{first_monday:$("#fm").value});await load();toast("已保存")}catch(e){toast(e.message)}};
async function exportIcs(e){if(!D||!D.first_monday){e.preventDefault();toast("请先刷新以读取校历");return}if(!/SuperJLU-Android/.test(navigator.userAgent))return;e.preventDefault();if(exportIcs.busy)return;exportIcs.busy=1;const btn=e.currentTarget,prev=btn&&btn.textContent;if(btn){btn.textContent="导出中…";btn.setAttribute("aria-busy","true")}try{const r=await fetch("/api/ics"),text=await r.text();if(!r.ok||!text.startsWith("BEGIN:VCALENDAR")){let m="导出失败";try{const j=JSON.parse(text);if(j&&j.error)m=j.error}catch(_){}toast(m,true);return}if(window.SuperJLU&&typeof SuperJLU.shareIcs==="function"){SuperJLU.shareIcs(text);return}const f=new File([text],"jlu-schedule.ics",{type:"text/calendar"});if(navigator.canShare&&navigator.canShare({files:[f]})){await navigator.share({files:[f],title:"吉大课表"});return}toast("没有可以打开课表的应用",true)}catch(err){if(err&&err.name==="AbortError")return;toast("导出失败",true)}finally{exportIcs.busy=0;if(btn){btn.textContent=prev||"导出 iCal (.ics)";btn.removeAttribute("aria-busy")}}}
$("#ics").onclick=exportIcs;
$("#refresh").onclick=()=>fullRefresh({forceAcademic:true}).catch(()=>{});
/* 日期与「周次+星期」双向联动：改日期自动换算周次/星期，改周次/星期（单周）自动换算日期 */
function rdToWeek(){const v=$("#rd").value;if(!v)return;const d=new Date(v+"T00:00:00");$("#rwd").value=String(d.getDay()||7);if(D&&D.first_monday){const w=weekOf(d);if(w>=1)$("#rw").value=String(w)}}
function weekToRd(){const fm=D&&D.first_monday,raw=($("#rw").value||"").trim(),wm=/^(\d+)/.exec(raw),w=wm?+wm[1]:0,wd=+$("#rwd").value;if(!fm||!(w>=1)||!(wd>=1))return;const d=new Date(fm+"T00:00:00");d.setDate(d.getDate()+(w-1)*7+wd-1);$("#rd").value=new Date(d-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
$("#rd").addEventListener("change",rdToWeek);$("#rw").addEventListener("change",weekToRd);$("#rwd").addEventListener("change",weekToRd);
/* 自习时间 ↔ 空闲节次：按教务节次表（或内置默认）互相换算，查询仍走节次参数。
   DEF_PERIODS 必须在顶部 IIFE 调用 periodsToStudy() 之前初始化，否则 const TDZ 会让整页脚本中断，#boot 永远不消失。 */
const DEF_PERIODS={1:["08:00","08:45"],2:["08:55","09:40"],3:["10:00","10:45"],4:["10:55","11:40"],5:["13:30","14:15"],6:["14:25","15:10"],7:["15:30","16:15"],8:["16:25","17:10"],9:["18:30","19:15"],10:["19:25","20:10"],11:["20:20","21:05"]};
function periodMap(){const p=D&&D.periods;return(p&&Object.keys(p).length)?p:DEF_PERIODS}
function periodsToStudy(){const a=+$("#rp1").value,b=+$("#rp2").value,m=periodMap(),x=m[a]||m[String(a)],y=m[b]||m[String(b)];$("#rst").value=x&&x[0]?x[0]:"";$("#ret").value=y&&y[1]?y[1]:""}
function studyToPeriods(){const s=$("#rst").value,e=$("#ret").value,m=periodMap();if(!s||!e||s>=e)return;let lo=null,hi=null;Object.keys(m).forEach(k=>{const n=+k,t=m[k];if(!(n>=1)||!t||t.length<2)return;if(t[0]<e&&t[1]>s){if(lo===null||n<lo)lo=n;if(hi===null||n>hi)hi=n}});if(lo!==null){$("#rp1").value=lo;$("#rp2").value=hi}}
let _rSync=false;
/* 按当前时间自动选好「接下来两节」：正在上的或下一节开始，连续两节；当天课都结束了就选次日第 1-2 节。
   用户手动改过日期或节次后不再覆盖。 */
function roomNextSlot(map,now){const toM=t=>{const m=/^(\d{1,2}):(\d{2})/.exec(t||"");return m?+m[1]*60+ +m[2]:NaN};const ks=Object.keys(map).map(Number).filter(n=>n>=1&&map[n]&&map[n].length>=2&&!isNaN(toM(map[n][1]))).sort((a,b)=>a-b);const d=new Date(now.getFullYear(),now.getMonth(),now.getDate());if(!ks.length)return{date:d,a:1,b:2};const cur=now.getHours()*60+now.getMinutes();const k=ks.find(n=>toM(map[n][1])>cur);if(k===undefined){d.setDate(d.getDate()+1);return{date:d,a:ks[0],b:ks[Math.min(1,ks.length-1)]}}const i=ks.indexOf(k);return{date:d,a:k,b:ks[Math.min(i+1,ks.length-1)]}}
let _rTouched=false;
function roomAutoSlot(){if(_rTouched)return;const s=roomNextSlot(periodMap(),new Date()),dd=s.date;$("#rd").value=dd.getFullYear()+"-"+String(dd.getMonth()+1).padStart(2,"0")+"-"+String(dd.getDate()).padStart(2,"0");$("#rp1").value=s.a;$("#rp2").value=s.b;rdToWeek();periodsToStudy();const n=new Date(),tomorrow=dd.getDate()!==n.getDate(),h=$("#rauto");if(h)h.textContent=`已按现在的时间选好${tomorrow?"明天":"今天"}第 ${s.a}${s.b!==s.a?"-"+s.b:""} 节，可以直接查询，也可以自己改。`}
roomAutoSlot();
["#rd","#rp1","#rp2","#rst","#ret","#rw","#rwd"].forEach(q=>{const e=$(q);if(e)["input","change"].forEach(ev=>e.addEventListener(ev,()=>{_rTouched=true;const h=$("#rauto");if(h)h.textContent=""}))});
$("#rp1").addEventListener("change",()=>{if(_rSync)return;_rSync=true;try{if(+$("#rp2").value<+$("#rp1").value)$("#rp2").value=$("#rp1").value;periodsToStudy()}finally{_rSync=false}});
$("#rp2").addEventListener("change",()=>{if(_rSync)return;_rSync=true;try{if(+$("#rp1").value>+$("#rp2").value)$("#rp1").value=$("#rp2").value;periodsToStudy()}finally{_rSync=false}});
$("#rst").addEventListener("change",()=>{if(_rSync)return;_rSync=true;try{studyToPeriods()}finally{_rSync=false}});
$("#ret").addEventListener("change",()=>{if(_rSync)return;_rSync=true;try{studyToPeriods()}finally{_rSync=false}});
document.querySelectorAll("#rst-presets [data-sp]").forEach(b=>b.onclick=()=>{_rTouched=true;const[a,c]=b.dataset.sp.split("-").map(Number);$("#rp1").value=a;$("#rp2").value=c;periodsToStudy()});
let RM="date",RR=[],RS={k:"name",d:1};
/* 空教室只有一张表单：日期、周次/星期、自习时间、节次一起显示、互相联动。
   最后改的是日期就按日期查；改的是周次/星期就按周次查（支持 6-8 这样的多周）。 */
$("#rd").addEventListener("change",()=>{RM="date"});$("#rw").addEventListener("change",()=>{RM="week"});$("#rwd").addEventListener("change",()=>{RM="week"});
function roomQueryMode(){const w=($("#rw").value||"").trim();if(RM==="week"&&w&&!/^\d+$/.test(w))return"week";if(!$("#rd").value&&w)return"week";return RM==="week"&&!(D&&D.first_monday)&&w?"week":"date"}
const opts=(l,all)=>(all?`<option value="">${all}</option>`:"")+l.map(c=>`<option value="${esc(c.code)}">${esc(c.name)}</option>`).join("");
let ROOM_BUILDINGS_REQUEST=0,ROOM_BUILDINGS_READY=Promise.resolve();
async function loadBuildings(){const c=$("#rc").value,generation=++ROOM_BUILDINGS_REQUEST;if(!c){$("#rb").innerHTML=opts([],"全部");return}try{const j=await api("/api/rooms/buildings",{campus:c});if(generation===ROOM_BUILDINGS_REQUEST&&$("#rc").value===c)$("#rb").innerHTML=opts(j.buildings,"全部")}catch(e){toast(e.message)}}
// 六个校区固定（教务代码表 01–06，已与真实 campuses.json 核对），不再需要「加载」
const CAMPUSES=[{code:"01",name:"前卫校区"},{code:"02",name:"南岭校区"},{code:"03",name:"新民校区"},{code:"04",name:"朝阳校区"},{code:"05",name:"南湖校区"},{code:"06",name:"和平校区"}];
const RCKEY="superjlu.room.campus";
function lsGet(k){try{return localStorage.getItem(k)}catch(_){return null}}
function lsSet(k,v){try{localStorage.setItem(k,v)}catch(_){}}
function pickCampus(code){$("#rc").value=code;lsSet(RCKEY,code);document.querySelectorAll("#rcs button").forEach(b=>{const on=b.dataset.c===code;b.classList.toggle("on",on);b.setAttribute("aria-checked",on?"true":"false")});ROOM_BUILDINGS_READY=loadBuildings();if(window.__rm)roomFormChanged()}
$("#rcs").innerHTML=CAMPUSES.map(c=>`<button type="button" role="radio" data-c="${esc(c.code)}">${esc(c.name.replace(/校区$/,""))}</button>`).join("");
document.querySelectorAll("#rcs button").forEach(b=>b.onclick=()=>pickCampus(b.dataset.c));
let RMETA=false;
async function roomsInit(){const last=lsGet(RCKEY);pickCampus(CAMPUSES.some(c=>c.code===last)?last:CAMPUSES[0].code);if(RMETA)return;RMETA=true;try{const t=await api("/api/rooms/types",{});$("#rt").innerHTML=opts(t.types,"全部");const f=await api("/api/rooms/fields",{});$("#rextra").innerHTML=f.fields.map(x=>`<label>${esc(x.caption||x.name)}<input data-f="${esc(x.name)}" placeholder="${esc(x.name)}"></label>`).join("")||'<p class="sub">元数据中没有其它检索字段</p>'}catch(e){RMETA=false;showRoomFailure(e)}}
document.querySelector('nav button[data-t="js"]').addEventListener("click",()=>{roomAutoSlot();if(!window.__rm){window.__rm=1;roomsInit()}});
const RCOLS=[["building","教学楼"],["kind","教室类型"],["name","教室名称"],["seats","上课座位数"],["exam_seats","考试座位数"]];
// Room presentation helpers: shared by desktop and the Android WebView.
function roomCardName(room){
 const full=String(room.name||"").trim();if(!full)return"未命名教室";let name=full;
 const clean=s=>s.replace(/^[\s\-—–_·]+/u,"").trim(),campus=String(room.campus||"").trim(),shortCampus=campus.replace(/(?:校区|校园)$/u,""),building=String(room.building||"").trim();
 const strip=prefix=>{if(prefix&&name.startsWith(prefix)){const rest=clean(name.slice(prefix.length));if(rest){name=rest;return true}}return false};
 // Match supplied location names first; never delete an entire special-room name.
 strip(building);strip(campus)||strip(shortCampus);strip(building);
 let shortBuilding=building;for(const prefix of [campus,shortCampus])if(prefix&&shortBuilding.startsWith(prefix)){const rest=shortBuilding.slice(prefix.length);if(!rest||/^[\s\-—–_·]/u.test(rest))shortBuilding=clean(rest)}strip(shortBuilding);
 // Some JWXT rows only identify the building as "前卫-". A building ending in
 // 楼 followed by a room code / separator is still an unambiguous name prefix.
 const inferred=/^.+?(?:教学楼|综合楼|实验楼|楼)(?=[\s\-—–_·]*[A-Za-z0-9]|[\s\-—–_·]+[^\s\-—–_·])/u.exec(name);if(inferred)strip(inferred[0]);
 return name||full;
}
function roomIsTiered(room){const kind=String(room.kind||"");if(/阶梯|阶教/.test(kind))return true;if(/普通|平面/.test(kind))return false;return /阶梯|阶教/.test(String(room.name||""))}
function roomColorLayout(rooms,columns,palette=10){
 columns=Math.max(1,Math.floor(columns)||1);palette=Math.max(8,Math.floor(palette)||10);
 const cells=[],used=Array(palette).fill(0),layout=[];
 for(const room of rooms){const span=roomIsTiered(room)?Math.min(2,columns):1;let row=0,col=0;
  // Match grid-auto-flow:row dense, including normal tiles filling earlier gaps.
  for(;;row++){if(!cells[row])cells[row]=[];let found=false;for(col=0;col<=columns-span;col++){let free=true;for(let c=col;c<col+span;c++)if(cells[row][c]!=null)free=false;if(free){found=true;break}}if(found)break}
  const avoid=new Set(),take=(r,c)=>{if(cells[r]&&cells[r][c]!=null)avoid.add(cells[r][c])};take(row,col-1);take(row,col+span);for(let c=col;c<col+span;c++){take(row-1,c);take(row+1,c)}
  let tone=-1;for(let n=0;n<palette;n++){const candidate=(layout.length+n)%palette;if(!avoid.has(candidate)&&(tone<0||used[candidate]<used[tone]))tone=candidate}
  used[tone]++;for(let c=col;c<col+span;c++)cells[row][c]=tone;layout.push({tone,row,col,span});
 }return layout;
}
function roomQueryLabel(j){const day="一二三四五六日"[j.weekday-1]||"";return j.mode==="week"?`第${j.weeks}周 周${day}`:`${j.date}${j.week>0?" · 第"+j.week+"周":""} 周${day}`}
function roomViewPreference(){try{return localStorage.getItem("jlu-room-view")==="table"?"table":"cards"}catch(_){return"cards"}}

// Every block has four periods. Never invent clock times absent from school data.
const ROOM_DAY_BLOCKS=[{name:"上午",periods:[1,2,3,4]},{name:"下午",periods:[5,6,7,8]},{name:"晚上",periods:[9,10,11,12]}];
function roomKey(room){return JSON.stringify([String(room.building||""),String(room.name||"")])}
function roomFavoriteKey(room,j){return JSON.stringify([String(j.query&&j.query.campus||room.campus||""),roomKey(room)])}
function roomDayState(room,p,j){
 const record=j.day&&j.day.records[p];
 if(record)return(record.freeSet?record.freeSet.has(roomKey(room)):record.free.includes(roomKey(room)))?"free":"unavailable";
 return p>=j.periods[0]&&p<=j.periods[1]?"free":"unknown";
}
function roomDayStats(room,j){
 let total=0,unknown=0,start=0,best={start:0,end:0,length:0};
 for(let p=1;p<=12;p++){
  const state=roomDayState(room,p,j);if(state==="unknown")unknown++;
  if(state==="free"){total++;if(!start)start=p;if(p-start+1>best.length)best={start,end:p,length:p-start+1}}else start=0;
 }return{total,unknown,best};
}
function roomDayTime(p,map){const t=map[p];return Array.isArray(t)&&t[0]&&t[1]?t.join("–"):"时间未提供"}
function roomDayArc(a,b){const pt=d=>{const r=d*Math.PI/180;return[108-78*Math.cos(r),108-78*Math.sin(r)]},x=pt(a),y=pt(b);return`M${x[0].toFixed(2)} ${x[1].toFixed(2)} A78 78 0 0 1 ${y[0].toFixed(2)} ${y[1].toFixed(2)}`}
function roomDayMatches(room,j,filter,min,onlyFav,favorites){
 if(onlyFav&&!favorites.has(roomFavoriteKey(room,j)))return false;
 if(!j.day)return !filter&&!min;
 return roomDayStats(room,j).best.length>=min&&(!filter||ROOM_DAY_BLOCKS[+filter-1].periods.some(p=>roomDayState(room,p,j)==="free"));
}


function roomDayRecord(rooms,source){const free=rooms.map(roomKey),parsed=Date.parse(source);return{rooms,free,freeSet:new Set(free),source,expires:(Number.isFinite(parsed)?Math.min(parsed,Date.now()):Date.now())+300000}}
function roomFollowup(room,j){
 if(!j.day)return{state:"unknown",label:"所选时段空闲",title:"跨周结果不推断单日后续状态"};
 const p=j.periods[1]+1;if(p>12)return{state:"end",label:"今日无后续",title:"所选时段后，今日已无第 1–12 节以内的后续节次"};
 const state=roomDayState(room,p,j);
 return state==="free"?{state,label:"下节空闲",title:`第 ${p} 节空闲；全天信息可点开查看`}:state==="unavailable"?{state,label:"下节无空闲",title:`第 ${p} 节未查到空闲记录，不等同于确认正在上课`}:{state,label:"后续待查",title:`第 ${p} 节尚未获取，点开卡片可查看并重试`};
}
function roomGroupColors(count,columns,tiered){const span=tiered?Math.min(2,columns):1,perRow=Math.max(1,Math.floor(columns/span));return Array.from({length:count},(_,i)=>(Math.floor(i/perRow)*3+i%perRow+(tiered?4:0))%10)}

// Room presentation rendering.
let ROOM_VIEW=roomViewPreference(),ROOM_OBSERVER=null;
const ROOM_ICON={normal:'<path d="M4 7h6v4H4zm10 0h6v4h-6zM4 16h6v4H4zm10 0h6v4h-6zM5 4h14"/>',tiered:'<path d="M3 20h5v-5h5v-5h5V5h3M3 12V9h3m3-2V4h3M3 23h18"/>',unknown:'<path d="M4 21V4h16v17M8 8h2m4 0h2M8 12h2m4 0h2M9 21v-5h6v5"/>'};
function roomIcon(r){const tiered=roomIsTiered(r),known=/普通|平面/.test(String(r.kind||""));return`<svg class="room-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ROOM_ICON[tiered?"tiered":known?"normal":"unknown"]}</svg>`}

let ROOM_RESULT=null,ROOM_REQUEST=0,ROOM_DAY_ONLY_FAV=false,ROOM_DETAIL=null;
const ROOM_FAV_KEY="jlu-room-favorites";
function roomFavorites(){try{const a=JSON.parse(localStorage.getItem(ROOM_FAV_KEY)||"[]");return new Set(Array.isArray(a)?a.filter(k=>typeof k==="string").slice(0,500):[])}catch(_){return new Set()}}
function paintRoomColors(){
 document.querySelectorAll("#rres .room-grid").forEach(grid=>{
  if(!grid.clientWidth)return;const columns=getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).length,tiles=[...grid.querySelectorAll("[data-room-card]")];
  const colors=roomGroupColors(tiles.length,columns,grid.classList.contains("tiered"));tiles.forEach((tile,i)=>tile.dataset.tone=String(colors[i]));
 });
}
function roomScrollTo(selector){requestAnimationFrame(()=>{const el=$(selector);if(!el)return;const reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;el.scrollIntoView({behavior:reduce?"auto":"smooth",block:"start"});if(selector==="#rres")el.focus({preventScroll:true})})}
function showRoomDetail(room,j,block=-1){
 ROOM_DETAIL={room,j,block};$("#room-detail-title").textContent=roomCardName(room);
 $("#room-detail-hint").textContent=j.day?"全天 12 节分别显示：绿色为空闲，灰色为无空闲记录，虚线为尚未确认。":"所选时段空闲 · 以本次教务查询结果为准";
 const fields=[["教室全名",room.name],["校区",room.campus],["教学楼",room.building],["教室类型",room.kind],["上课座位数",room.seats],["考试座位数",room.exam_seats],["查询日期",roomQueryLabel(j)],["查询节次",`第 ${j.periods[0]}–${j.periods[1]} 节`],["空闲日期",room.free_date],["空闲节次",room.free_periods],["空闲时间",room.free_time]];
 $("#room-detail-fields").innerHTML=fields.map(([label,value])=>`<dt>${esc(label)}</dt><dd>${esc(value==null||value===""?"未提供":String(value))}</dd>`).join("");
 $("#room-detail .room-metadata").open=!j.day;renderRoomDayDetail();if(!$("#room-detail").open)$("#room-detail").showModal();
 if(j.day)loadRoomDay(j,ROOM_REQUEST);
}
function renderRoomDayDetail(){
 const info=ROOM_DETAIL;if(!info)return;const{room,j,block}=info;if(!j.day){$("#room-detail-day").innerHTML="";return}
 const stats=roomDayStats(room,j),count=12-stats.unknown;
 $("#room-detail-day").innerHTML=`<div class="room-detail-overview">${roomDayGauge(room,j,-1)}</div><div class="room-day-status" role="status">${j.day.loading?`正在确认各节状态 · ${count}/12 节已确认`:j.day.error?esc(j.day.error):count===12?"全天 12 节状态已确认":`${count}/12 节已确认，剩余节次尚未获取`}${!j.day.loading&&count<12?'<button type="button" class="btn ghost" id="room-day-retry">重试未获取节次</button>':""}</div>`+ROOM_DAY_BLOCKS.map((b,i)=>{const states=b.periods.map(p=>roomDayState(room,p,j)),unknown=states.filter(s=>s==="unknown").length;return`<section class="room-day-detail-block ${i===block?"active":""}" data-detail-block="${i}"><div class="room-day-detail-head">${b.name}<span>${states.filter(s=>s==="free").length} / 4 节空闲${unknown?` · ${unknown} 节未确认`:""}</span></div><div class="room-day-periods">${b.periods.map((p,k)=>{const state=states[k];return`<div class="room-day-period ${state}" data-room-period="${p}"><b>第 ${p} 节</b><small>${esc(roomDayTime(p,periodMap()))}</small>${state==="free"?"空闲":state==="unavailable"?"无空闲记录":j.day.loading?"确认中…":"未获取"}</div>`}).join("")}</div></section>`}).join("");
 if($("#room-day-retry"))$("#room-day-retry").onclick=()=>loadRoomDay(j,ROOM_REQUEST);
 document.querySelectorAll("#room-detail-day [data-room-day-block]").forEach(b=>b.onclick=()=>{ROOM_DETAIL.block=+b.dataset.roomDayBlock;renderRoomDayDetail();$(`#room-detail-day [data-detail-block="${ROOM_DETAIL.block}"]`).scrollIntoView({block:"nearest",behavior:"auto"})});
}
$("#room-detail-close").onclick=()=>$("#room-detail").close();
let roomBackdropStart=null;
function roomDetailOutside(e){const dialog=$("#room-detail"),r=dialog.getBoundingClientRect();return e.target===dialog&&(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)}
$("#room-detail").addEventListener("pointerdown",e=>{roomBackdropStart=roomDetailOutside(e)?{x:e.clientX,y:e.clientY}:null});
$("#room-detail").addEventListener("pointercancel",()=>{roomBackdropStart=null});
$("#room-detail").addEventListener("click",e=>{const start=roomBackdropStart;roomBackdropStart=null;if(start&&roomDetailOutside(e)&&Math.hypot(e.clientX-start.x,e.clientY-start.y)<12)$("#room-detail").close()});
$("#room-detail").addEventListener("close",()=>{ROOM_DETAIL=null;roomBackdropStart=null});
window.addEventListener("resize",paintRoomColors);
function roomDayGauge(r,j,index){
 const stats=roomDayStats(r,j);
 return`<div class="room-day-gauge"><svg viewBox="0 0 216 132" aria-hidden="true">${ROOM_DAY_BLOCKS.map((b,i)=>b.periods.map((p,k)=>`<path d="${roomDayArc(i*60+4+k*13.5,i*60+15.5+k*13.5)}" fill="none" stroke-width="14" class="room-day-${roomDayState(r,p,j)}"/>`).join("")).join("")}<text x="19" y="55" text-anchor="middle">上午</text><text x="108" y="10" text-anchor="middle">下午</text><text x="197" y="55" text-anchor="middle">晚上</text><text x="108" y="88" text-anchor="middle" class="room-day-total">${stats.total}<tspan font-size="12" font-weight="500"> 节</tspan></text><text x="108" y="107" text-anchor="middle" class="room-day-total-note">当日已确认空闲</text></svg><div class="room-day-blocks">${ROOM_DAY_BLOCKS.map((b,i)=>`<button type="button" data-room-day-block="${i}" aria-label="${esc(roomCardName(r))} ${b.name}，查看具体节次">${b.name}<strong>${b.periods.filter(p=>roomDayState(r,p,j)==="free").length}/4</strong></button>`).join("")}</div></div>`;
}
function roomDayCard(r,j,index,favorites){
 const tiered=roomIsTiered(r),fav=favorites.has(roomFavoriteKey(r,j)),next=roomFollowup(r,j),location=[r.campus,r.building].filter(Boolean).join(" · ");
 return`<article class="room-tile room-day-card" data-room-card data-room-index="${index}" data-tone="${index%10}" data-wide="${tiered}" data-kind="${esc(r.kind||"")}" data-name="${esc(r.name||"")}" aria-label="${esc(roomCardName(r))}"><div class="room-tile-top">${roomIcon(r)}<div class="room-day-identity"><button type="button" class="room-day-name" data-room="${index}" title="${esc(r.name||"")}">${esc(roomCardName(r))}</button></div><button type="button" class="btn room-day-star" data-room-fav="${index}" aria-label="${esc((fav?"取消收藏 ":"收藏 ")+roomCardName(r))}" aria-pressed="${fav}">${fav?"★":"☆"}</button></div>${j.showBuilding?`<div class="room-compact-location" title="${esc(location)}">${esc(r.building||location)}</div>`:""}<div class="room-compact-meta"><span>${r.seats!==""&&r.seats!=null?esc(String(r.seats))+" 座":"座位未提供"}</span><span class="room-next" data-room-followup="${esc(roomKey(r))}" data-state="${next.state}" title="${esc(next.title)}">${next.label}</span></div></article>`;
}
function renderRooms(j){
 const box=$("#rres");if(ROOM_OBSERVER)ROOM_OBSERVER.disconnect();box.hidden=false;ROOM_RESULT=j;
 const favorites=roomFavorites(),numeric=k=>["seats","exam_seats"].includes(k);
 const rs=[...RR].sort((a,b)=>RS.d*(numeric(RS.k)?(+a[RS.k]||0)-(+b[RS.k]||0):String(a[RS.k]||"").localeCompare(String(b[RS.k]||""),"zh",{numeric:true}))||String(a.name).localeCompare(String(b.name),"zh",{numeric:true}));
 const indices=new Map(rs.map((r,i)=>[r,i])),visible=ROOM_VIEW==="cards"&&ROOM_DAY_ONLY_FAV?rs.filter(r=>favorites.has(roomFavoriteKey(r,j))):rs;
 const toggle=`<div class="room-view" data-view="${ROOM_VIEW}" role="group" aria-label="查询结果展示方式"><button type="button" data-room-view="table" aria-pressed="${ROOM_VIEW==="table"}">表格</button><button type="button" data-room-view="cards" aria-pressed="${ROOM_VIEW==="cards"}">卡片</button></div>`;
 const sort=`<div class="room-sort"><label for="room-sort">排序</label><select id="room-sort">${RCOLS.map(([k,l])=>`<option value="${k}" ${RS.k===k?"selected":""}>${l}</option>`).join("")}</select><button type="button" class="btn ghost" id="room-sort-dir" aria-label="${RS.d>0?"改为降序":"改为升序"}">${RS.d>0?"升序 ↑":"降序 ↓"}</button></div>`;
 const toolbar=`<div class="room-list-tools"><label class="room-day-fav-only"><input type="checkbox" id="room-day-fav-only" ${ROOM_DAY_ONLY_FAV?"checked":""}>只看收藏</label>${sort}</div>`;
 const cards=ROOM_VIEW!=="cards"?" ":[true,false].map(tiered=>{const group=visible.filter(r=>roomIsTiered(r)===tiered);return group.length?`<section class="room-day-group"><h3>${roomIcon({kind:tiered?"阶梯教室":"普通教室"})}${tiered?"阶梯教室":group.every(r=>/普通|平面/.test(r.kind||""))?"普通教室":"普通及其他教室"}<span class="sub">${group.length} 间</span></h3><div class="room-grid room-day-grid ${tiered?"tiered":""}">${group.map(r=>roomDayCard(r,j,indices.get(r),favorites)).join("")}</div></section>`:""}).join("");
 const table=ROOM_VIEW!=="table"?"":`<div class="room-table-wrap"><table class="rt" aria-label="空教室查询结果"><thead><tr>${RCOLS.map(([k,l])=>`<th aria-sort="${RS.k===k?(RS.d>0?"ascending":"descending"):"none"}"><button type="button" data-room-sort="${k}">${l}${RS.k===k?(RS.d>0?" ▲":" ▼"):""}</button></th>`).join("")}</tr></thead><tbody>${rs.map((r,i)=>`<tr>${RCOLS.map(([k])=>`<td>${k==="name"?`<button type="button" class="room-name-button" data-room="${i}">${esc(r[k]||"未命名教室")}</button>`:esc(r[k]==null||r[k]===""?"—":String(r[k]))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
 const heading=`${esc(roomQueryLabel(j))} <span class="room-query-period">第 ${j.periods[0]}–${j.periods[1]} 节</span><span class="sub">${visible.length!==rs.length?`显示 ${visible.length} / `:""}${rs.length} 间空教室${j.hidden_special?" · 已屏蔽特殊教室 "+j.hidden_special+" 间":""}</span>`;
 const content=!rs.length?'<p class="empty" role="status">没有符合条件的空教室</p>':ROOM_VIEW==="table"?table:toolbar+(visible.length?cards:'<p class="empty">没有收藏的教室</p>')+`<p class="room-list-note">${j.day?"所选时段空闲 · 外部状态仅指下一节；全天仪表盘点开查看。":"所选多周均空闲 · 点开查看教室资料。"}</p>`;
 const focused=document.activeElement,focusToken=focused&&box.contains(focused)?{id:focused.id,key:focused.dataset.roomKey,fav:focused.dataset.roomFav!=null}:null;
 if(box.querySelector(".room-results-head")){box.querySelector("h2").innerHTML=heading;box.querySelector(".room-view").dataset.view=ROOM_VIEW;box.querySelectorAll("[data-room-view]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.roomView===ROOM_VIEW)));box.querySelector(".room-results-body").innerHTML=content}
 else box.innerHTML=`<div class="room-results-head"><h2>${heading}</h2>${toggle}</div><div class="room-results-body">${content}</div>`;
 box.querySelectorAll("[data-room-view]").forEach(b=>b.onclick=()=>{ROOM_VIEW=b.dataset.roomView;try{localStorage.setItem("jlu-room-view",ROOM_VIEW)}catch(_){}renderRooms(j);box.querySelector(`[data-room-view="${ROOM_VIEW}"]`).focus({preventScroll:true})});
 const changeSort=k=>{RS=RS.k===k?{k,d:-RS.d}:{k,d:1};renderRooms(j)};
 box.querySelectorAll("[data-room-sort]").forEach(b=>b.onclick=()=>changeSort(b.dataset.roomSort));
 if($("#room-sort"))$("#room-sort").onchange=e=>{RS={k:e.target.value,d:1};renderRooms(j)};
 if($("#room-sort-dir"))$("#room-sort-dir").onclick=()=>changeSort(RS.k);
 box.querySelectorAll("[data-room]").forEach(b=>{b.dataset.roomKey=roomKey(rs[+b.dataset.room]);b.onclick=()=>showRoomDetail(rs[+b.dataset.room],j)});
 box.querySelectorAll("article[data-room-card]").forEach(card=>card.onclick=e=>{if(!e.target.closest("button,a,input,select,[data-room]"))showRoomDetail(rs[+card.dataset.roomIndex],j)});
 box.querySelectorAll("[data-room-fav]").forEach(b=>{b.dataset.roomKey=roomKey(rs[+b.dataset.roomFav]);b.onclick=()=>{const fav=roomFavorites(),key=roomFavoriteKey(rs[+b.dataset.roomFav],j);fav.has(key)?fav.delete(key):fav.add(key);try{localStorage.setItem(ROOM_FAV_KEY,JSON.stringify([...fav].slice(-500)))}catch(_){}renderRooms(j);if(!box.contains(document.activeElement))$("#room-day-fav-only").focus({preventScroll:true})}});
 if($("#room-day-fav-only"))$("#room-day-fav-only").onchange=e=>{ROOM_DAY_ONLY_FAV=e.target.checked;renderRooms(j)};
 paintRoomColors();if(typeof ResizeObserver!=="undefined"){ROOM_OBSERVER=new ResizeObserver(paintRoomColors);box.querySelectorAll(".room-grid").forEach(g=>ROOM_OBSERVER.observe(g))}
 if(focusToken){const target=focusToken.id?document.getElementById(focusToken.id):[...box.querySelectorAll(focusToken.fav?"[data-room-fav]":"[data-room]")].find(b=>b.dataset.roomKey===focusToken.key);if(target)target.focus({preventScroll:true})}
}
function updateRoomNextBadges(j){
 if(ROOM_RESULT!==j)return;if(!j.roomLookup)j.roomLookup=new Map(j.rooms.map(r=>[roomKey(r),r]));
 document.querySelectorAll("#rres [data-room-followup]").forEach(b=>{const room=j.roomLookup.get(b.dataset.roomFollowup);if(!room)return;const next=roomFollowup(room,j);b.textContent=next.label;b.dataset.state=next.state;b.title=next.title});
}
function refreshRoomDetail(j){if(ROOM_DETAIL&&ROOM_DETAIL.j===j&&$("#room-detail").open)renderRoomDayDetail()}
// Memory-only inventories: no account data is persisted in browser storage.
const ROOM_DAY_CACHE=new Map();let ROOM_DAY_TASK=null,ROOM_DAY_QUEUE=Promise.resolve(),ROOM_FORM_REVISION=0,ROOM_QUERY_PENDING=null;
function roomReadQuery(){
 const extra={};document.querySelectorAll("#rextra [data-f]").forEach(i=>{if(i.value.trim())extra[i.dataset.f]=i.value.trim()});
 return{mode:roomQueryMode(),campus:$("#rc").value,building:$("#rb").value,kind:$("#rt").value,date:$("#rd").value,weeks:$("#rw").value,weekday:$("#rwd").value,hide_special:$("#rhs").checked,periods:`${$("#rp1").value}-${$("#rp2").value}`,seat_min:$("#rs1").value,seat_max:$("#rs2").value,exam_min:$("#re1").value,exam_max:$("#re2").value,extra};
}
function roomScopeKey(q){return JSON.stringify([q.mode,q.date,q.campus,q.building,q.kind,q.seat_min||"",q.seat_max||"",q.exam_min||"",q.exam_max||"",Object.entries(q.extra||{}).sort()])}
function stopRoomPrefetch(){if(ROOM_DAY_TASK)ROOM_DAY_TASK.cancelled=true;ROOM_DAY_TASK=null}
function clearRoomCache(){stopRoomPrefetch();ROOM_DAY_CACHE.clear();ROOM_FORM_REVISION++;ROOM_REQUEST++;ROOM_QUERY_PENDING=null;const b=$("#rq");if(b){b.disabled=false;b.textContent="查询空教室"}}
function freshRoomRecords(day){const now=Date.now();for(const[p,r]of Object.entries(day.records))if(r.expires<=now)delete day.records[p];return day.records}
function roomCacheEntry(query){
 const key=roomScopeKey(query);let entry=ROOM_DAY_CACHE.get(key);
 if(!entry){entry={day:{records:{},loading:false,error:"",request:null},meta:null};ROOM_DAY_CACHE.set(key,entry);if(ROOM_DAY_CACHE.size>3)ROOM_DAY_CACHE.delete(ROOM_DAY_CACHE.keys().next().value)}
 freshRoomRecords(entry.day);return entry;
}
function roomCachedResult(query){
 if(query.mode!=="date")return null;const entry=ROOM_DAY_CACHE.get(roomScopeKey(query));if(!entry||!entry.meta)return null;
 const records=freshRoomRecords(entry.day),[a,b]=query.periods.split("-").map(Number);if(!(a>=1&&b>=a&&b<=12))return null;
 for(let p=a;p<=b;p++)if(!records[p])return null;
 const candidates=records[a].rooms.filter(r=>{for(let p=a+1;p<=b;p++)if(!records[p].freeSet.has(roomKey(r)))return false;return true});
 const kept=query.hide_special?candidates.filter(r=>!r.special):candidates,m=periodMap();
 const rooms=kept.map(r=>({...r,free_date:query.date,free_periods:Array.from({length:b-a+1},(_,i)=>a+i).join(","),free_time:m[a]?.[0]&&m[b]?.[1]?m[a][0]+"–"+m[b][1]:""}));
 return{...entry.meta,periods:[a,b],rooms,total:candidates.length,hidden_special:candidates.length-kept.length,day:entry.day,from_cache:true};
}
function mergeRoomRecords(j,r,batch){
 if(r.date!==j.date||!Array.isArray(r.records))throw new Error("全天空闲记录未获取完整");const seen=new Set();
 for(const record of r.records){const p=record.period;if(record.complete!==true||record.date!==j.date||!batch.includes(p)||seen.has(p)||!Array.isArray(record.rooms))throw new Error("全天空闲记录未获取完整");seen.add(p);j.day.records[p]=roomDayRecord(record.rooms,record.fetched_at)}
 if(r.partial||seen.size!==batch.length)throw new Error("部分节次未获取");
}
function refreshRoomDayUsers(day){const j=ROOM_RESULT;if(j&&j.day===day){updateRoomNextBadges(j);refreshRoomDetail(j)}}
function loadRoomDay(j,generation){
 if(!j.day)return Promise.resolve();if(j.day.request){if(!j.day.task?.cancelled)return j.day.request;return j.day.request.then(()=>ROOM_RESULT?.day===j.day?loadRoomDay(j,ROOM_REQUEST):undefined)}
 freshRoomRecords(j.day);const key=roomScopeKey(j.query);
 if(ROOM_DAY_TASK&&ROOM_DAY_TASK.key!==key)stopRoomPrefetch();
 const missing=Array.from({length:12},(_,i)=>i+1).filter(p=>!j.day.records[p]);if(!missing.length)return Promise.resolve();
 missing.sort((a,b)=>(a<=j.periods[1])-(b<=j.periods[1])||a-b);
 const task={key,cancelled:false};ROOM_DAY_TASK=task;j.day.task=task;j.day.loading=true;j.day.error="";refreshRoomDayUsers(j.day);
 // Queue batches across scope changes: an old in-flight batch may finish,
 // but cannot overlap a new batch or schedule further old-scope requests.
 const work=async()=>{let incomplete=false;try{
  for(let start=0;start<missing.length;start+=4){
   if(task.cancelled)return;const batch=missing.slice(start,start+4).filter(p=>!j.day.records[p]||j.day.records[p].expires<=Date.now());if(!batch.length)continue;
   const r=await api("/api/rooms/day",{...j.query,mode:"date",date:j.date,day_periods:batch});if(task.cancelled)return;
   try{mergeRoomRecords(j,r,batch)}catch(error){incomplete=true;if(r.session_expired)throw error}
   refreshRoomDayUsers(j.day);
  }
  if(incomplete)throw new Error("部分节次未获取");
 }catch(_){if(!task.cancelled)j.day.error="部分节次未获取，未确认的节次已单独标出，可重试。"}
 finally{j.day.loading=false;j.day.request=null;if(ROOM_DAY_TASK===task)ROOM_DAY_TASK=null;refreshRoomDayUsers(j.day)}};
 const pending=ROOM_DAY_QUEUE.then(work,work);j.day.request=pending;ROOM_DAY_QUEUE=pending.catch(()=>{});return pending;
}
function roomFormChanged(){
 ROOM_FORM_REVISION++;
 const query=roomReadQuery();if(ROOM_DAY_TASK&&ROOM_DAY_TASK.key!==roomScopeKey(query))stopRoomPrefetch();
}
$("#t-js").addEventListener("change",e=>{if(e.target.matches("input,select")&&!e.target.closest("#rres"))roomFormChanged()});
document.querySelectorAll("#rst-presets [data-sp]").forEach(b=>b.addEventListener("click",roomFormChanged));
function showRoomFailure(error){const original=String(error?.message||"查询未成功，请稍后重试。"),technical=/HTTP\s*\d{3}|尝试：|cxkxjs|Traceback/i.test(original)||original.length>160;$("#room-error-message").textContent=(technical?"空教室查询失败，请检查网络或在「更多 → 登录」切换登录方式后重试。":original)+(RR.length?" 已保留上次查询结果。":"");$("#room-switch-login").hidden=!(technical||error?.connectionAction);$("#room-error").hidden=false}
$("#room-switch-login").onclick=()=>{document.querySelector('nav button[data-t="sz"]').click();location.hash="sz";$("#network-route").scrollIntoView({behavior:"smooth",block:"center"})};
async function runRoomQuery(){
 await ROOM_BUILDINGS_READY;const query=roomReadQuery(),signature=JSON.stringify(query);
 if(ROOM_QUERY_PENDING&&ROOM_QUERY_PENDING.signature===signature)return ROOM_QUERY_PENDING.promise;
 const b=$("#rq"),generation=++ROOM_REQUEST,revision=ROOM_FORM_REVISION;b.disabled=true;b.textContent="查询中…";$("#room-error").hidden=true;
 if(ROOM_DAY_TASK&&ROOM_DAY_TASK.key!==roomScopeKey(query))stopRoomPrefetch();
 const work=async()=>{
 try{
  const j=roomCachedResult(query)||await api("/api/rooms",query);if(generation!==ROOM_REQUEST||revision!==ROOM_FORM_REVISION)return;
  j.query=query;if(j.mode==="date"&&j.periods[1]<=12){
   const entry=roomCacheEntry(query);entry.meta={mode:j.mode,date:j.date,week:j.week,weeks:j.weeks,weekday:j.weekday};j.day=entry.day;
   // Selected-interval positives are only a fallback for displayed rooms.
   // They must never masquerade as complete single-period inventories.
  }
  RR=j.rooms;j.showBuilding=new Set(RR.map(r=>r.building||"")).size>1;ROOM_DAY_ONLY_FAV=false;if(["day_run","day_total"].includes(RS.k))RS={k:"name",d:1};
  if(ROOM_DETAIL&&ROOM_DETAIL.j!==j)$("#room-detail").close();renderRooms(j);roomScrollTo("#rres");if(j.day)loadRoomDay(j,generation);
 }catch(e){if(generation===ROOM_REQUEST&&revision===ROOM_FORM_REVISION){showRoomFailure(e);if(ROOM_RESULT)renderRooms(ROOM_RESULT);roomScrollTo("#room-error")}}
 finally{if(generation===ROOM_REQUEST){b.disabled=false;b.textContent="查询空教室";ROOM_QUERY_PENDING=null}}
 };
 const promise=Promise.resolve().then(work);ROOM_QUERY_PENDING={signature,promise};return promise;
}
$("#rq").onclick=()=>runRoomQuery();
let OA=null,OAQ={kw:"",dept:""},OAERR="",OACH="179577",OACHS=null,OAPREFS=null,OACAT=null,OAMANAGE=false,OAPICK=null;
function oaFilter(items,q){const k=(q.kw||"").trim().toLowerCase();return items.filter(i=>(!q.dept||i.dept===q.dept)&&(!k||(i.title+" "+i.dept).toLowerCase().includes(k)))}
function oaLink(u,label){try{const p=new URL(u||"");if(!/^https?:$/.test(p.protocol))return"";const h=p.hostname;if(!(h==="jlu.edu.cn"||h.endsWith(".jlu.edu.cn")||/\.(jdyy\.cn|jdey\.com\.cn|zrlyyy\.com)$/.test(h)))return""}catch(_){return""}return`<a class="btn ghost" href="${esc(u)}" target="_blank" rel="noopener noreferrer">${label}</a>`}
function renderOA(){const box=$("#oa-box");queueMicrotask(()=>{if(OA&&OA.offline===true&&!box.querySelector(".offl"))box.insertAdjacentHTML("afterbegin",offlineBadge(OA))});if(OAERR&&!OA){box.innerHTML=`<div class="state"><b>读取通知失败</b>${esc(OAERR)}<div class="sub" style="margin-top:6px">学校 OA 可经校园网或学校 VPN 访问；当前通道为校外 WebVPN 时同步也会走应用内 WebVPN。学院通知可独立更新。</div><div style="margin-top:14px"><button class="btn pri" id="oa-retry">重试</button></div></div>`;$("#oa-retry").onclick=loadOA;return}
 if(!OA)return;const all=OA.items||[];const ds=[...new Set(all.map(i=>i.dept).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"zh"));const sel=$("#oa-dept");sel.innerHTML='<option value="">全部单位</option>'+ds.map(d=>`<option${d===OAQ.dept?" selected":""}>${esc(d)}</option>`).join("");
 const needNet=OA.source==="college"&&["network_error","need_campus"].includes(OA.status);
 const linkOnly=OA.source==="college"&&OA.status==="link_only";
 const hint=needNet?`<div class="state" style="padding:10px 4px"><b>学院官网暂未连通</b>${esc(OA.hint||"")}</div>`:"";
 $("#oa-meta").textContent=all.length?`${all.length} 条${OA.fetched_at?" · 更新于 "+String(OA.fetched_at).replace("T"," ").slice(0,16):""}`:(linkOnly?"官网入口":"");
 if(linkOnly){const u=OA.source_url||"";box.innerHTML=`<div class="state"><b>打开学院官网查看通知</b><div class="sub" style="margin-top:6px">${esc(OA.hint||"该学院暂不支持自动抓取列表。")}</div><div style="margin-top:14px">${oaLink(u,"打开官网 ↗")||'<span class="sub">暂无可用链接</span>'}</div></div>`;return}
 if(!all.length){box.innerHTML=hint||(OA.source==="college"?`<div class="state"><b>还没有消息</b>点右上角「更新」从学院官网取第一页。</div>`:`<div class="state"><b>还没有通知</b>点右上角「更新」从校内通知取第一页。</div>`);return}
 const it=oaFilter(all,OAQ);if(!it.length){box.innerHTML=`<div class="state"><b>没有符合条件的通知</b>换个关键词或单位试试。</div>`;return}
 box.innerHTML=hint+`<ul class="oal">${it.map(i=>`<li data-id="${esc(i.id)}" tabindex="0"><div class="tt">${i.top?'<span class="pin">置顶</span>':""}${esc(i.title)}<span class="mt">${esc(i.dept||"未知单位")} · ${esc(i.time||"")}</span></div><span class="ar">›</span></li>`).join("")}</ul>`;
 box.querySelectorAll("li").forEach(li=>{li.onclick=()=>openOA(li.dataset.id);li.onkeydown=e=>{if(e.key==="Enter")openOA(li.dataset.id)}})}
function renderOACh(){const box=$("#oa-ch"),l=OACHS||[];const show=l.length>=1;box.hidden=!show;if(!show){box.innerHTML="";return}
 const canEdit=!!(OAPREFS&&OAPREFS.onboarded);
 box.innerHTML=l.map((c,i)=>`<span class="oa-chip"><button type="button" class="ch${c.id===OACH?" on":""}" data-ch="${esc(c.id)}">${esc(c.name||c.id)}</button>${canEdit?`<button type="button" class="btn ghost mv" data-mv="-1" data-i="${i}" title="前移" aria-label="前移">‹</button><button type="button" class="btn ghost mv" data-mv="1" data-i="${i}" title="后移" aria-label="后移">›</button>`:""}</span>`).join("")+(canEdit?`<button type="button" class="btn ghost oa-add" id="oa-add">＋</button>`:"");
 box.querySelectorAll("button.ch").forEach(b=>b.onclick=()=>{OACH=b.dataset.ch;OA=null;OAQ.dept="";renderOACh();$("#oa-box").innerHTML=`<div class="state"><div class="spin"></div><b>正在读取通知…</b></div>`;loadOA()});
 box.querySelectorAll("button.mv").forEach(b=>b.onclick=()=>oaMove(+b.dataset.i,+b.dataset.mv));
 const add=$("#oa-add");if(add)add.onclick=()=>{OAMANAGE=!OAMANAGE;renderOAManage()}}
async function oaMove(i,dir){if(!OAPREFS||!OAPREFS.order)return;const order=OAPREFS.order.slice();const j=i+dir;if(j<0||j>=order.length)return;[order[i],order[j]]=[order[j],order[i]];try{const r=await api("/api/oa/prefs",{order,enabled:OAPREFS.enabled,onboarded:true});OAPREFS=r.prefs;OACHS=r.channels;renderOACh();renderOAManage()}catch(e){toast(e.message)}}
async function renderOAManage(){const box=$("#oa-manage");if(!OAMANAGE){box.hidden=true;box.innerHTML="";return}box.hidden=false;
 if(!OACAT){try{OACAT=(await api("/api/oa/catalog")).catalog}catch(e){box.innerHTML=`<p class="sub">读取学院目录失败：${esc(e.message)}</p>`;return}}
 const en=new Set((OAPREFS&&OAPREFS.enabled)||[]);
 const cats=(OACAT.categories||[]).map(g=>{const cols=(g.colleges||[]).map(c=>{const ids=c.scrape?Object.keys(c.cols||{}).map(k=>c.id+"-"+k):[c.id+"-site"];const on=ids.some(id=>en.has(id));return`<label class="${on?"on":""}" data-cid="${esc(c.id)}"><input type="checkbox" ${on?"checked":""}>${esc(c.name)}${c.scrape?"":" · 官网"}</label>`}).join("");return`<details ${g.id==="cs"?"open":""}><summary>${esc(g.name)}</summary><div class="cols">${cols}</div></details>`}).join("");
 box.innerHTML=`<p class="sub" style="margin:0 0 6px">勾选学院以加入顶部快捷栏；可抓取的学院会加入通知栏目，其余以官网入口显示。</p>${cats}<div class="row-acts"><button type="button" class="btn ghost" id="oa-man-close">收起</button><button type="button" class="btn pri" id="oa-man-save">保存</button></div>`;
 box.querySelectorAll("label").forEach(lb=>lb.querySelector("input").onchange=e=>lb.classList.toggle("on",e.target.checked));
 $("#oa-man-close").onclick=()=>{OAMANAGE=false;renderOAManage()};
 $("#oa-man-save").onclick=async()=>{const picked=[...box.querySelectorAll("label")].filter(l=>l.querySelector("input").checked).map(l=>l.dataset.cid);const enabled=["179577"];const order=(OAPREFS.order||[]).filter(x=>x==="179577"||x.startsWith("179"));
  // keep campus OA ids already enabled
  (OAPREFS.enabled||[]).forEach(id=>{if(/^\d+$/.test(id)&&!enabled.includes(id))enabled.push(id)});
  picked.forEach(cid=>{const col=(OACAT.categories||[]).flatMap(g=>g.colleges||[]).find(c=>c.id===cid);if(!col)return;const ids=col.scrape?Object.keys(col.cols||{}).slice(0,2).map(k=>col.id+"-"+k):[col.id+"-site"];ids.forEach(id=>{if(!enabled.includes(id))enabled.push(id)})});
  const newOrder=[...enabled];
  try{const r=await api("/api/oa/prefs",{enabled,order:newOrder,onboarded:true,home_college:(OAPREFS&&OAPREFS.home_college)||picked[0]||""});OAPREFS=r.prefs;OACHS=r.channels;OAMANAGE=false;renderOAManage();renderOACh();if(!OACHS.some(c=>c.id===OACH))OACH=(OACHS[0]||{}).id;OA=null;loadOA();toast("已更新信息源")}catch(e){toast(e.message)}}}
function renderOAPick(){const card=$("#oa-pick");if(!card)return;if(!OAPREFS||OAPREFS.onboarded){card.hidden=true;return}card.hidden=false;
 if(!OACAT){api("/api/oa/catalog").then(j=>{OACAT=j.catalog;renderOAPick()}).catch(()=>{});$("#oa-pick-b").innerHTML='<p class="sub">正在加载学院列表…</p>';return}
 OAPICK=OAPICK||"";
 const html=(OACAT.categories||[]).map(g=>`<details ${g.id==="cs"?"open":""}><summary>${esc(g.name)}</summary><div class="cols">${(g.colleges||[]).map(c=>`<label class="${OAPICK===c.id?"on":""}" data-cid="${esc(c.id)}"><input type="radio" name="oa-home" value="${esc(c.id)}" ${OAPICK===c.id?"checked":""}>${esc(c.name)}</label>`).join("")}</div></details>`).join("");
 $("#oa-pick-b").innerHTML=html||'<p class="sub">暂无学院目录</p>';
 $("#oa-pick-b").querySelectorAll("label").forEach(lb=>lb.onclick=()=>{OAPICK=lb.dataset.cid;$("#oa-pick-ok").disabled=!OAPICK;renderOAPick()});
 $("#oa-pick-ok").disabled=!OAPICK}
async function oaFinishPick(skip){try{const r=await api("/api/oa/prefs",{apply_home:true,home_college:skip?"":(OAPICK||"")});OAPREFS=r.prefs;OACHS=r.channels;$("#oa-pick").hidden=true;renderOACh();if(!OACHS.some(c=>c.id===OACH))OACH=(OACHS[0]||{id:"179577"}).id;OA=null;await loadOA();toast(skip?"已跳过，可随时点 ＋ 添加学院":"已保存你的学院")}catch(e){toast(e.message)}}
async function loadOA(){OAERR="";try{const j=await api("/api/oa/channels");OACHS=j.channels;OAPREFS=j.prefs||OAPREFS;if(j.prefs&&!j.prefs.onboarded)renderOAPick()}catch(e){OACHS=OACHS||[{id:"179577",name:"校内通知"}]}if(!OACHS.some(c=>c.id===OACH))OACH=(OACHS[0]||{id:"179577"}).id;renderOACh();try{OA=await api("/api/oa/notices?category="+encodeURIComponent(OACH))}catch(e){OA=null;OAERR=e.message}renderOA()}
$("#oa-pick-skip").onclick=()=>oaFinishPick(true);
$("#oa-pick-ok").onclick=()=>oaFinishPick(false);
function oaBack(){$("#oa-detail-v").hidden=true;$("#oa-list-v").hidden=false}
async function openOA(id){const v=$("#oa-detail-v");$("#oa-list-v").hidden=true;v.hidden=false;v.innerHTML=`<div class="card"><div class="state"><div class="spin"></div><b>正在读取…</b></div></div>`;scrollTo(0,0);
 let i;try{i=(await api("/api/oa/notice?id="+encodeURIComponent(id))).item}catch(e){v.innerHTML=`<div class="card"><button class="btn ghost" id="oa-back">‹ 返回</button><div class="state"><b>读取失败</b>${esc(e.message)}</div></div>`;$("#oa-back").onclick=oaBack;return}
 const atts=i.attachments||[];
 v.innerHTML=`<div class="card oad"><div class="row" style="margin-bottom:10px"><button class="btn ghost" id="oa-back">‹ 返回</button><span class="sp"></span>${oaLink(i.url,i.source==="college"?"打开原文 ↗":"在 OA 中打开 ↗")}</div><h2>${i.top?'<span class="pin">置顶</span>':""}${esc(i.title)}</h2><div class="sub">${esc(i.dept||"未知单位")} · ${esc(i.time||"")}</div>`+
  (i.text?`<div class="body">${esc(i.text)}</div>`:`<div class="state" style="padding:28px 8px">${i.source==="college"?"<b>学院新闻只保存标题</b>点“打开原文”在新标签页查看。":"<b>本地没有正文</b>点“在 OA 中打开”查看原文；校外可校外登录 · WebVPN 与教务 访问 OA。"}</div>`)+
  (atts.length?`<h2 style="font-size:15px;margin-top:6px">附件 <span class="sub">${atts.length}</span></h2><div class="att">${atts.map(a=>`<a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">📎 ${esc(a.name)}</a>`).join("")}</div>`:"")+`</div>`;
 $("#oa-back").onclick=oaBack}
$("#oa-kw").oninput=e=>{OAQ.kw=e.target.value;renderOA()};$("#oa-dept").onchange=e=>{OAQ.dept=e.target.value;renderOA()};
$("#oa-ref").onclick=async()=>{const b=$("#oa-ref");b.disabled=true;b.textContent="更新中…";try{OA=await api("/api/oa/refresh",{category:OACH});OAERR="";renderOA();const bad=["network_error","need_campus"].includes(OA.status);toast(OA.status==="link_only"?"请打开学院官网查看":bad?"学院官网暂未连通，已保留本地通知":"已更新第一页",bad)}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent="⟳ 更新"}};
document.querySelector('nav button[data-t="oa"]').addEventListener("click",()=>{(OA?Promise.resolve():loadOA()).then(loadSubs)});
let SITES=null,LINKN={};const SITEN=id=>(SITES&&SITES[id]&&SITES[id].name)||LINKN[id]||id;
const SST={ok:["已登录","done"],expired:["已过期","miss"],missing:["未登录","chip"],unknown:["未知","chip"]};
async function loadSessions(){try{const r=await fetch("/api/sessions");if(!r.ok)return null;const j=await r.json();if(!j||j.ok===false||!Array.isArray(j.sites))return null;const m={};j.sites.forEach(s=>{if(s&&s.id)m[s.id]=s});return m}catch(_){return null}}
function siteHasLoginStatus(id){return !["xsxk","lib","ilearn"].includes(id)}
function stBadge(s){if(!s||!siteHasLoginStatus(s.id))return"";const t=s.state==="ok"?[s.id==="vpn"?"VPN 登录状态已保存":"登录状态已保存","chip"]:s.external_browser?["需在浏览器登录","chip"]:s.id==="pay"&&s.state==="missing"?["网站独立登录","chip"]:SST[s.state]||SST.unknown;return`<span class="${t[1]}" title="${esc(s.message||"")}">${t[0]}</span>`}
let LOGIN_MODE=null,ACTIVE_LOGIN_MODE="direct";
function syncLoginChoice(){const selected=LOGIN_MODE||ACTIVE_LOGIN_MODE;document.querySelectorAll("[data-login-mode]").forEach(b=>{const on=b.dataset.loginMode===selected;b.classList.toggle("on",on);b.setAttribute("aria-pressed",String(on))});$("#login-method-hint").textContent=selected==="webvpn"?"在家、用流量或热点时选这个。":"连着校园网时选这个。";if(typeof renderDeviceNet==="function")renderDeviceNet();$("#lgbtn").textContent=selected!==ACTIVE_LOGIN_MODE?"切换方式并登录":LOGGED?"重新登录 / 切换账号":"登录并同步"}
document.querySelectorAll("[data-login-mode]").forEach(b=>b.onclick=()=>{LOGIN_MODE=b.dataset.loginMode;syncLoginChoice()});
function loginFeedback(message){const p=$("#login-feedback");p.textContent=message||"";p.hidden=!message}
function renderNetworkState(state){if(ACTIVE_LOGIN_MODE!==(state.mode==="webvpn"?"webvpn":"direct"))clearRoomCache();ACTIVE_LOGIN_MODE=state.mode==="webvpn"?"webvpn":"direct";if(LOGIN_MODE===null)LOGIN_MODE=ACTIVE_LOGIN_MODE;const last=state.last_connection?.route;$("#network-route-current").textContent=ACTIVE_LOGIN_MODE==="webvpn"?"校外 WebVPN":"校园网直连";$("#network-route-last").hidden=!last;$("#network-route-last").textContent=last?"最近成功连接："+(last==="webvpn"?"WebVPN":"直连"):"";syncLoginChoice()}
// Android 直连时提示「当前走移动数据 / Wi-Fi 未通过网关认证」；桌面端接口无提示，不改变任何行为
let DEVICE_NET_HINT="";function renderDeviceNet(){const sel=LOGIN_MODE||ACTIVE_LOGIN_MODE,c=$("#device-net-hint");if(c){c.hidden=!(DEVICE_NET_HINT&&sel!=="webvpn");c.textContent=DEVICE_NET_HINT}let lgTarget="";try{lgTarget=LG&&LG.target}catch(_){}const d=$("#lg-device-net");if(d){d.hidden=!(DEVICE_NET_HINT&&lgTarget==="jwxt");d.textContent=DEVICE_NET_HINT}}
async function loadDeviceNet(){try{const j=await (await fetch("/api/network/device")).json();DEVICE_NET_HINT=(j&&j.direct_hint)||""}catch(_){DEVICE_NET_HINT=""}renderDeviceNet()}
async function loadNetworkState(){loadDeviceNet();try{renderNetworkState(await api("/api/network/state"))}catch(_){}const bp=$("#browser-preferences");if(bp)bp.hidden=!/SuperJLU-Android/.test(navigator.userAgent)}
function axInit(){const c=$("#android-extras");if(!c)return;const ok=!!(window.SuperJLU&&SuperJLU.setLockNotify);c.hidden=!ok;if(!ok)return;const n=$("#ax-notify");try{n.checked=!!SuperJLU.lockNotifyEnabled()}catch(_){}n.onchange=()=>{try{SuperJLU.setLockNotify(n.checked)}catch(_){}};$("#ax-battery").onclick=()=>{try{SuperJLU.requestBatteryExemption()}catch(_){}};$("#ax-autostart").onclick=()=>{try{SuperJLU.openAutostartSettings()}catch(_){}};try{const pr=$("#ax-pin");if(pr&&SuperJLU.canPinWidget&&SuperJLU.canPinWidget()){pr.hidden=false;pr.querySelectorAll("[data-pin]").forEach(b=>b.onclick=()=>{try{SuperJLU.pinWidget(+b.dataset.pin)}catch(_){}})}}catch(_){}try{const h=SuperJLU.backgroundHint();if(h)$("#ax-hint").textContent=h}catch(_){}}
try{axInit()}catch(_){}
function networkCheckFooter(data){const dev=data&&data.device_hint?`<p class="sub" id="network-device-hint" role="status"><b>手机网络</b> ${esc(data.device_hint)}</p>`:"";const hint=data&&data.hint;if(hint)return dev+`<p class="sub" id="network-check-hint" role="status"><b>校外提示</b> ${esc(hint)}</p><p class="sub">检测不验证登录状态，也不会切换「校园网直连／校外 WebVPN」。学校 OA 直连未通不影响学院通知。</p>`;return dev+`<p class="sub">检测不验证登录状态。学校 OA 未连通不会影响学院通知。若教务直连失败而 WebVPN 门户可达，可到「更多 → 登录」改选「校外 WebVPN」。</p>`}
$("#network-check").onclick=async()=>{const b=$("#network-check");b.disabled=true;$("#network-summary").textContent="正在检测实际 HTTPS 入口，不读取账号或改变登录状态…";try{const data=await api("/api/network/check",{});$("#network-summary").textContent="检测于 "+data.checked_at.replace("T"," ");$("#network-report").innerHTML='<div style="overflow-x:auto"><table><thead><tr><th>服务</th><th>连接</th><th>说明</th></tr></thead><tbody>'+data.services.map(s=>`<tr><td>${esc(s.name)}<br><span class="sub">${esc(s.host)}:${s.port}</span></td><td>${s.reachable?"可达":"未连通"}</td><td class="sub">${esc(s.error||("HTTP "+s.http_status+" · "+(s.transport==="system"?"系统 HTTPS":"Python HTTPS")+" · "+s.milliseconds+"ms"))}</td></tr>`).join("")+'</tbody></table></div>'+networkCheckFooter(data)+`<details class="sub" id="network-tech"><summary>技术信息（反馈问题时可附上）</summary>Python ${esc(data.python)} · ${esc(data.tls_library)}</details>`}catch(e){$("#network-summary").textContent=e.message}finally{b.disabled=false}};
const LKOK=u=>{try{const p=new URL(u);return p.protocol==="https:"&&/(^|\.)jlu\.edu\.cn$/.test(p.hostname)}catch(_){return false}};
const lkA=(u,t,c)=>LKOK(u)?`<a class="btn ${c}" href="${esc(u)}" target="_blank" rel="noopener noreferrer">${t}</a>`:"";
function serviceTime(value){if(value===null||value===undefined||value==="")return"";const n=typeof value==="number"||/^\d+(\.\d+)?$/.test(String(value))?Number(value):NaN;const date=new Date(Number.isFinite(n)?(n<1e12?n*1000:n):value);return Number.isFinite(date.getTime())?date.toLocaleString("zh-CN",{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hour12:false}):""}
function serviceLink(url,text,cls){if(!/^\/api\/sso\/jump\?/.test(url||""))return lkA(url,text,cls);const target=/SuperJLU-Android/.test(navigator.userAgent)?"":' target="_blank"';return`<a class="btn ${cls}" href="${esc(url)}"${target} rel="noopener noreferrer">${text}</a>`}
function serviceActions(x,route){const vpn=!!(x.vpn_url&&LKOK(x.vpn_url)),via=vpn&&route==="webvpn";return serviceLink(x.sso_url||x.url,x.id==="vpn"?"打开 VPN 网页 ↗":x.campus_only?"直接打开 ↗":"打开 ↗",via?"ghost":"pri")+(vpn?serviceLink(x.vpn_sso_url||x.vpn_url,"经 WebVPN 打开 ↗",via?"pri":"ghost"):"")}
function serviceHelp(x){if(!/^\/api\/sso\/jump\?/.test(x.vpn_help_url||""))return"";const target=/SuperJLU-Android/.test(navigator.userAgent)?"":' target="_blank"';return`<div class="lg"><a class="service-help" href="${esc(x.vpn_help_url)}"${target} rel="noopener noreferrer">浏览器 VPN 登录说明</a></div>`}
function serviceResult(x){const r=x.handoff;if(!r||!r.state)return"";const failed=r.state!=="issued",time=serviceTime(r.checked_at);return`<div class="handoff-result${failed?" failed":""}" role="status">上次${r.route==="webvpn"?" WebVPN":""}免登${time?"（"+esc(time)+"）":""}：${esc(r.message||"结果待确认")}</div>`}
function servicePrimary(x,route){const vpn=!!(x.vpn_url&&LKOK(x.vpn_url)),via=vpn&&route==="webvpn";const url=via?(x.vpn_sso_url||x.vpn_url):(x.sso_url||x.url);const sso=/^\/api\/sso\/jump\?/.test(url||"");const target=/SuperJLU-Android/.test(navigator.userAgent)?"":' target="_blank"';const rel=sso?' rel="noopener noreferrer"':' rel="noopener noreferrer"';return{url,sso,attrs:`href="${esc(url)}"${target}${rel}`}}
function serviceVpnAlt(x,route){const vpn=!!(x.vpn_url&&LKOK(x.vpn_url));if(!vpn)return"";const via=route==="webvpn";if(via){const u=x.sso_url||x.url;if(!u)return"";const sso=/^\/api\/sso\/jump\?/.test(u);const target=/SuperJLU-Android/.test(navigator.userAgent)?"":' target="_blank"';return`<a class="vpn" href="${esc(u)}"${target} rel="noopener noreferrer">直连</a>`}const u=x.vpn_sso_url||x.vpn_url;const sso=/^\/api\/sso\/jump\?/.test(u||"");const target=/SuperJLU-Android/.test(navigator.userAgent)?"":' target="_blank"';return`<a class="vpn" href="${esc(u)}"${target} rel="noopener noreferrer">经 WebVPN</a>`}
function serviceTip(x,s,route){const bits=[x.purpose,x.login];if(x.campus_only)bits.push(x.vpn_url?"校外可点「经 WebVPN」":"校外需先连校园 VPN");if(s&&siteHasLoginStatus(x.id)){const t=s.state==="ok"?(s.id==="vpn"?"VPN 已登录":"已登录"):(SST[s.state]||SST.unknown)[0];bits.push("应用内："+t+(s.checked_at?" · "+serviceTime(s.checked_at):""))}const r=x.handoff;if(r&&r.state)bits.push("上次免登："+(r.message||r.state)+(r.checked_at?" · "+serviceTime(r.checked_at):""));if(x.vpn_help_url)bits.push("有浏览器 VPN 登录说明");return bits.filter(Boolean).join(" · ")}
function serviceDot(x,s){const r=x.handoff;if(r&&r.state&&r.state!=="issued")return`<span class="dot fail" title="${esc(r.message||"免登未成功")}" aria-label="${esc(r.message||"免登未成功")}"></span>`;if(!s||!siteHasLoginStatus(x.id)||s.external_browser)return"";const k=s.state==="ok"?"ok":s.state==="expired"?"bad":"";if(!k)return"";const t=(SST[s.state]||SST.unknown)[0];return`<span class="dot ${k}" title="${esc(t)}" aria-label="${esc(t)}"></span>`}
function renderServiceLinks(j){const b=$("#links-b"),L=(j.links||[]).filter(x=>LKOK(x.url)),S=id=>SITES&&SITES[id],route=j.route||"direct";L.forEach(x=>{LINKN[x.id]=x.name;const s=S(x.id);if(!x.vpn_url&&s&&typeof s.vpn_url==="string"&&LKOK(s.vpn_url))x.vpn_url=s.vpn_url});if(!L.length){b.innerHTML='<p class="sub" style="margin:0">没有可显示的入口。</p>';return}b.innerHTML=`<div class="lgrid">${L.map(x=>{const s=S(x.id),pri=servicePrimary(x,route);return`<div class="lk" title="${esc(serviceTip(x,s,route))}">${serviceDot(x,s)}<a class="go" ${pri.attrs}><span class="ic" aria-hidden="true">${esc(x.icon||"↗")}</span><b>${esc(x.name)}</b></a>${serviceVpnAlt(x,route)}</div>`}).join("")}</div>`+(j.warning?`<p class="sub" style="margin:10px 0 0">⚠ ${esc(j.warning)}</p>`:"")}
let LINKS_LAST=0,LINKS_PENDING=null;
async function loadLinks(force=true){if(LINKS_PENDING)return LINKS_PENDING;if(!force&&Date.now()-LINKS_LAST<30000)return;LINKS_PENDING=(async()=>{const btn=$("#links-refresh");if(btn)btn.disabled=true;try{const j=await api("/api/links");SITES=await loadSessions();renderServiceLinks(j);LINKS_LAST=Date.now();$("#links-state").textContent=""}catch(e){$("#links-state").textContent="读取失败："+e.message+"；保留原显示，可点击刷新重试。"}finally{if(btn)btn.disabled=false}})();try{return await LINKS_PENDING}finally{LINKS_PENDING=null}}
$("#links-refresh").onclick=()=>loadLinks();
$("#links-check").onclick=async()=>{const b=$("#links-check");b.disabled=true;b.textContent="验证中…";try{const j=await api("/api/sessions/check",{site:"jwxt"});await loadLinks();const s=j.site;$("#links-state").textContent=s.state==="ok"?"应用内教务会话验证通过；外部浏览器登录仍需在打开网站后确认。":s.message||"未能验证应用内会话"}catch(e){$("#links-state").textContent=e.message}finally{b.disabled=false;b.textContent="验证应用内教务会话"}};
document.querySelector('nav button[data-t="sz"]').addEventListener("click",()=>{loadLinks(false);loadNetworkState()});
window.addEventListener("focus",()=>{if(document.querySelector('nav button[data-t="sz"].on'))loadLinks()});
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&document.querySelector('nav button[data-t="sz"].on'))loadLinks()});


// ---- 新版本提醒：不弹窗、不强制，只在「更多」里显示，并在导航上加一个小圆点 ----
let UPD=null;
function updAuto(){try{return localStorage.getItem("jlu-update-auto")!=="off"}catch(_){return true}}
const UPD_TXT={ok:"当前已是最新版本哦！",fail:"暂时连不上 GitHub，稍后再试",page:"页面没拿到版本信息，请稍后重试"};
// 版本号放在独立的 #upd-v 里，状态只写 #upd-m，避免覆盖掉版本号（#122 之前点「检查更新」会清掉 #upd-v 导致报错）
function updVer(j){const v=$("#upd-v");if(!v)return;let c=j&&j.current;if(!c){try{c=window.SuperJLU&&SuperJLU.appVersion&&SuperJLU.appVersion()}catch(_){}}if(c)v.textContent=String(c).replace(/^v/i,"");}
function updMsg(html){const m=$("#upd-m");if(m)m.innerHTML=html?" · "+html:""}
function updWhy(r){const t=$("#upd-tech"),w=$("#upd-why");if(!t||!w)return;w.textContent=r||"";t.hidden=!r}
function updRender(j,manual){const go=$("#upd-go"),nav=document.querySelector('nav button[data-t="sz"]');updVer(j);const has=!!(j&&j.has_update&&j.latest);go.hidden=!has;if(has)go.href=j.url;let seen=null;try{seen=localStorage.getItem("jlu-update-seen")}catch(_){}if(nav)nav.classList.toggle("upd-dot",has&&seen!==j.latest);updWhy(j&&j.unavailable?(j.reason||"unavailable")+(j.checked_at?" @ "+j.checked_at:""):"");if(has)updMsg(`<b style="color:var(--pri)">有新版本 v${esc(j.latest)}</b>，可随时下载，不更新也能照常使用。`);else if(manual){updMsg(esc(j&&j.unavailable?UPD_TXT.fail:"已是最新版本"));toast(j&&j.unavailable?UPD_TXT.fail:UPD_TXT.ok,!!(j&&j.unavailable))}}
async function updCheck(manual){let j;try{const ctl=typeof AbortController=="function"?new AbortController():null;const tm=ctl&&setTimeout(()=>ctl.abort(),25000);try{const r=await fetch("/api/update"+(manual?"?force=1":""),ctl?{signal:ctl.signal}:{});j=await r.json()}finally{if(tm)clearTimeout(tm)}}catch(e){if(manual){updVer(null);updMsg(esc(UPD_TXT.page));updWhy("page "+((e&&e.name)||"error")+": "+((e&&e.message)||"").slice(0,80));toast(UPD_TXT.page,true)}return}UPD=j;try{updRender(j,manual)}catch(e){updWhy("render "+((e&&e.message)||e))}}
updVer(null);
$("#upd-auto").checked=updAuto();$("#upd-auto").onchange=e=>{try{localStorage.setItem("jlu-update-auto",e.target.checked?"on":"off")}catch(_){}if(!e.target.checked)document.querySelector('nav button[data-t="sz"]').classList.remove("upd-dot")};
$("#upd-chk").onclick=()=>{updMsg("正在检查…");updCheck(true)};
document.querySelector('nav button[data-t="sz"]').addEventListener("click",()=>{if(UPD&&UPD.has_update&&UPD.latest){try{localStorage.setItem("jlu-update-seen",UPD.latest)}catch(_){}document.querySelector('nav button[data-t="sz"]').classList.remove("upd-dot")}});
setTimeout(()=>{if(updAuto())updCheck(false);else fetch("/api/update?local=1").then(r=>r.json()).then(j=>updRender(j,false)).catch(()=>{})},4000);
fetch("/api/update?local=1").then(r=>r.json()).then(updVer).catch(()=>{});

function fromHash(){const h=new URLSearchParams(location.hash.slice(1));const tab=[...h.keys()][0];const b=document.querySelector(`nav button[data-t="${tab}"]`);if(b)b.click();const s=h.get("scheme");if(s&&D.schemes[s]){$("#scheme").value=s;applyScheme(s)}}
const _ra=renderAll;renderAll=function(){_ra();renderSession()};
load().then(()=>{$("#boot").remove();fromHash()}).catch(e=>{$("#boot").innerHTML=`<div class="state"><b>加载失败</b>${esc(e.message)}<div style="margin-top:14px"><button class="btn pri" onclick="location.reload()">重试</button></div></div>`});
// ---- 应用内登录（统一身份认证：账号密码 → 微信验证码；图形验证码由服务端自动识别，界面不显示） ----
let LG={step:"pw"};
function lgErr(m){$("#lge").textContent=m||"";const v=$("#lgvpn");if(v&&!m){v.hidden=true;v.innerHTML=""}}
function lgVpnHint(j,opts){const v=$("#lgvpn");if(!v)return;opts=opts||{};if(opts.canConnectVpn){v.hidden=false;v.innerHTML="统一认证已通过，教务直连不可达。请点下方「通过应用内 WebVPN 继续」，无需重发验证码；校外请改用「校外 WebVPN」登录。";return;}const url=j&&j.vpn_url;v.hidden=false;v.innerHTML=url?`连不上教务或统一认证时，请先在浏览器打开 <a href="${esc(url)}" target="_blank" rel="noopener noreferrer">校园 VPN</a> 登录，连上后再点「登录」重试。本工具不会代填 VPN 账号。`:`连不上教务或统一认证时，请先到「更多 → 校园服务」打开校园 VPN 并登录，连上后再点「登录」重试。本工具不会代填 VPN 账号。`;}
// Once credentials pass, keep them visible but outside the focus order until a password retry.
function lgResendView(){const b=$("#lg-resend"),h=$("#lg-resend-hint");if(!b||!h)return;const left=Math.max(0,Math.ceil(((LG.resendAt||0)-Date.now())/1000));b.disabled=!!LG.busy||left>0||LG.step!=="code";b.textContent=left?`重新发送（${left}s）`:"重新发送";h.textContent=left?"验证码未收到？倒计时结束后可重发。":"未收到或已过期时可重新发送。"}
function lgView(){$("#lg1").inert=LG.step!=="pw";$("#lg2").hidden=LG.step==="pw";$("#lg3").hidden=LG.step!=="code";$("#lgo").textContent=LG.step==="pw"?"登录":LG.step==="cap"?(LG.retry?"重新发送":"发送微信验证码"):"完成登录";lgResendView()}
const PW_MASK="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022";
function lgAcc(list){const box=$("#lga");box.innerHTML="";LG.acc=list||[];const cur=$("#lgu").value.trim();box.hidden=!LG.acc.length;LG.acc.forEach(u=>{const s=document.createElement("span");if(u===cur)s.className="on";const b=document.createElement("button");b.type="button";b.textContent=u;b.onclick=()=>{$("#lgu").value=u;$("#lgp").value=PW_MASK;lgSync();$("#lgp").focus()};const x=document.createElement("button");x.type="button";x.className="x";x.textContent="×";x.title="删除该账号及其保存的密码";x.setAttribute("aria-label","删除账号 "+u);x.onclick=async()=>{if(!confirm("删除已保存的账号 "+u+"（连同密码）？"))return;try{const j=await (await fetch("/api/login/accounts/"+encodeURIComponent(u),{method:"DELETE"})).json();if($("#lgu").value.trim()===u)$("#lgu").value=j.accounts&&j.accounts[0]||"";lgAcc(j.accounts||[]);toast("已删除 "+u)}catch(_){toast("删除失败")}};s.append(b,x);box.append(s)});const a=document.createElement("button");a.type="button";a.className="add";a.textContent="＋ 其他账号";a.onclick=()=>{$("#lgu").value="";$("#lgp").value="";lgSync();$("#lgu").focus()};if(LG.acc.length)box.append(a)}
function lgSync(){const u=$("#lgu").value.trim();const has=(LG.acc||[]).includes(u);if(has){if(!$("#lgp").value||$("#lgp").value===PW_MASK)$("#lgp").value=PW_MASK;$("#lgp").placeholder=""}else{if($("#lgp").value===PW_MASK)$("#lgp").value="";$("#lgp").placeholder="密码"}document.querySelectorAll("#lga span").forEach(s=>s.classList.toggle("on",s.firstChild.textContent===u))}
$("#lgu").addEventListener("input",lgSync);$("#lgp").addEventListener("focus",e=>{if(e.target.value===PW_MASK)e.target.select()});
let LOGGED=false;function lgInfo(ok){LOGGED=!!ok;if(ok)gradeSessionState="ok";const i=$("#lginfo");if(i)i.textContent=ok?"✓ 已登录":gradeSessionState==="expired"?"登录已过期，请重新登录。":"登录后同步课表、成绩和考试。";syncLoginChoice()}
async function openLogin(target){const flow=LG={step:"pw",target};if(LOGIN_MODE===null)await loadNetworkState();if(LG!==flow)return;target=target==="vpn"||target==="jwxt"?target:LOGIN_MODE==="webvpn"?"vpn":"jwxt";flow.target=target;$("#lgo").disabled=false;if(typeof loadDeviceNet==="function"){renderDeviceNet();loadDeviceNet()}const _vc=$("#lg-vpn-continue");_vc.hidden=true;if(_vc.classList)_vc.classList.remove("pri");const _go=$("#lgo");if(_go.classList){_go.classList.add("pri");_go.classList.remove("ghost")};$("#lgt").textContent=target==="vpn"?"校外登录 · WebVPN 与教务":"校园网登录 · 直连教务";lgErr("");$("#lgp").value="";$("#lgok").hidden=!LOGGED;if(LOGGED)$("#lgp").value=PW_MASK;$("#lgw").value="";lgView();try{const j=await (await fetch("/api/login")).json();if(LG!==flow)return;if(j.saved_username&&!$("#lgu").value)$("#lgu").value=j.saved_username;lgAcc(j.accounts||(j.saved_username?[j.saved_username]:[]));lgSync();const ok=LOGGED||!!(j.session&&j.session.logged_in);if(ok)LOGGED=true;$("#lgok").hidden=!ok;if((ok||(LG.acc||[]).includes($("#lgu").value.trim()))&&(!$("#lgp").value||$("#lgp").value===PW_MASK))$("#lgp").value=PW_MASK}catch(_){}if(LG!==flow)return;const d=$("#login");if(d.showModal)d.showModal();else d.setAttribute("open","");$("#lgu").value?$("#lgp").focus():$("#lgu").focus()}
async function lgPost(path,body){let r;try{r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})})}catch(e){let alive=false;try{alive=(await fetch("/api/session",{cache:"no-store"})).ok}catch(_){}throw new Error(alive?"和 SuperJLU 后台的连接中断了（教务响应慢或被安全软件拦截），请再点一次重试":"SuperJLU 后台已经退出，请从托盘或开始菜单重新打开 SuperJLU 后再登录")}let j={};try{j=await r.json()}catch(_){}if(!r.ok||j.ok===false){const error=new Error(j.error||("HTTP "+r.status));error.canConnectVpn=!!j.can_connect_vpn;error.payload=j;throw error}return j}
async function lgDone(result={}){const flow=LG;clearRoomCache();$("#login").close();LOGIN_MODE=LG.target==="vpn"?"webvpn":"direct";await loadNetworkState();if(LG!==flow)return;await loadLinks();if(LG!==flow)return;if(LG.target==="vpn"&&!result.jwxt_ready){const message=result.warning||"WebVPN 已连接，但教务尚未验证，请重试登录或同步。";loginFeedback(message);toast(message,true);return}loginFeedback("");lgInfo(true);D=Object.assign(D||{},{session_expired:false,session:null,needs_bootstrap:true});try{renderSession()}catch(_){}try{await fullRefresh({toastOnStart:"登录成功，正在刷新各页面…",okToast:null,failPrefix:"登录成功，刷新失败："})}catch(_){}await loadNetworkState()}
async function lgSendCode(flow=LG){const j=await lgPost((flow.target==="vpn"?"/api/vpn/login/":"/api/login/")+"send_code",{});if(LG!==flow)return false;if(j.step==="code_sent"){LG.step="code";LG.retry=false;LG.resendAt=Date.now()+60000;lgView();$("#lgw").value="";toast("微信验证码已发送");return true}LG.step="cap";LG.retry=true;lgErr(j.error||"发送失败，请重试");return false}
async function lgSubmit(ev,resend=false){ev.preventDefault();const flow=LG,b=$("#lgo");if(flow.busy||b.disabled||resend&&(flow.step!=="code"||Date.now()<(flow.resendAt||0)))return;lgErr("");let focusCode=false;flow.busy=true;b.disabled=true;lgResendView();try{
 if(LG.step==="pw"){const j=await lgPost((LG.target==="vpn"?"/api/vpn/login/":"/api/login/")+"start",{username:$("#lgu").value.trim(),password:$("#lgp").value===PW_MASK?"":$("#lgp").value,remember:$("#lgr").checked});if(LG!==flow)return;$("#lgp").value=PW_MASK;if(j.step==="success"){await lgDone(j);return}LG.step="cap";LG.retry=false;lgView();b.textContent="发送中…";focusCode=await lgSendCode(flow)}
 else if(LG.step==="cap"||resend){focusCode=await lgSendCode(flow)}
 else{const j=await lgPost((LG.target==="vpn"?"/api/vpn/login/":"/api/login/")+"verify",{wechat_code:$("#lgw").value.trim()});if(LG!==flow)return;if(j.step==="success"){await lgDone(j);return}lgErr(j.error||"验证码不正确")}
}catch(e){if(LG!==flow)return;LG.retry=true;lgErr(e.message);const cont=$("#lg-vpn-continue");cont.hidden=!e.canConnectVpn;if(e.canConnectVpn){if(b.classList){b.classList.remove("pri");b.classList.add("ghost")}if(cont.classList)cont.classList.add("pri");}else{if(cont.classList)cont.classList.remove("pri");if(b.classList){b.classList.add("pri");b.classList.remove("ghost")}}const p=e.payload||{};if(e.canConnectVpn||p.vpn_hint||p.network||/无法连接|连接超时|网络连接|NetworkError|校外|VPN/i.test(e.message||"")){try{lgVpnHint(p,{canConnectVpn:!!e.canConnectVpn})}catch(_){}}if(/重新输入账号密码|已失效/.test(e.message))LG.step="pw"}finally{flow.busy=false;if(LG===flow){b.disabled=false;lgView();if(focusCode&&LG.step==="code"&&$("#login").open)$("#lgw").focus()}}}
$("#lg-vpn-continue").onclick=async()=>{const flow=LG;const b=$("#lg-vpn-continue");b.disabled=true;try{const result=await api("/api/network/vpn",{});if(LG!==flow)return;LG.target="vpn";await lgDone(result);if(LG!==flow)return;fetch("/api/login/cancel",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).catch(()=>{})}catch(e){if(LG===flow)lgErr(e.message)}finally{if(LG===flow)b.disabled=false}};
$("#lgf").addEventListener("submit",lgSubmit);
function lgCancel(){const target=LG.target;LG={step:"pw"};fetch((target==="vpn"?"/api/vpn/login/cancel":"/api/login/cancel"),{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).catch(()=>{});$("#login").close()}
$("#lgx").onclick=lgCancel;
$("#login").addEventListener("cancel",e=>{e.preventDefault();lgCancel()});
$("#lg-resend").onclick=ev=>lgSubmit(ev,true);
setInterval(()=>{if($("#login").open)lgResendView()},1000);
async function startLogin(){await openLogin()}
$("#lgbtn").onclick=startLogin;
</script></body></html>
"""

# Android 原生设置保存应用内默认；桌面端保持 hidden，由 loadNetworkState 按 UA 显示。
SHOW_BROWSER_PREFERENCES = True
ANDROID_EXTRAS_CARD = '<div class="card" id="android-extras" hidden><h2>小组件与后台</h2><p class="sub">长按桌面 → 小组件 → SuperJLU</p><div class="row" id="ax-pin" hidden><button type="button" class="btn ghost" data-pin="0">添加今日</button><button type="button" class="btn ghost" data-pin="1">添加本周</button><button type="button" class="btn ghost" data-pin="2">添加下一节</button></div><label class="adj-toggle"><input type="checkbox" id="ax-notify"> 锁屏显示下一节课</label><div class="row" style="margin-top:12px"><button type="button" class="btn ghost" id="ax-battery">允许后台运行</button><button type="button" class="btn ghost" id="ax-autostart">自启动设置</button></div><details style="margin-top:10px"><summary class="sub">说明</summary><p class="sub" style="margin:6px 0 0">桌面列表里找不到小组件时，用上方「添加」按钮。</p><p class="sub" style="margin:6px 0 0">锁屏显示是一条常驻通知，不是锁屏小组件。</p><p class="sub" id="ax-hint" style="margin:4px 0 0">最近任务里给本应用加锁需手动操作。</p></details></div>'
BROWSER_PREFERENCES_CARD = '<div class="card" id="browser-preferences" hidden><h2>外部浏览器</h2><p class="sub" id="browser-preferences-hint">跟随系统默认浏览器，或指定一个应用。仅影响本应用。</p><a class="btn ghost" id="browser-settings-button" href="superjlu://browser-settings" aria-describedby="browser-preferences-hint">设置默认浏览器</a></div>'
PAGE = PAGE.replace("<!--ANDROID_EXTRAS_CARD-->", ANDROID_EXTRAS_CARD, 1)
PAGE = PAGE.replace("<!--BROWSER_PREFERENCES_CARD-->", BROWSER_PREFERENCES_CARD if SHOW_BROWSER_PREFERENCES else "", 1)
