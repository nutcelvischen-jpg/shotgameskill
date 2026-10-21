// test_headless.mjs — 無頭瀏覽器冒煙測試（不用開視窗、agent 也能自己看截圖）
// 安裝：  cd scripts && npm i playwright-core
// 執行：  node scripts/test_headless.mjs "http://localhost:8765/?lv=0" out_dir [按住毫秒,按住毫秒,...]
// 前提：  遊戲要有 #go 開始按鈕、空白鍵＝主要動作，並設定 window.__errs / window.__ok / window.game
// Chrome： 預設用系統 Chrome（macOS 路徑），其他環境設 CHROME=/path/to/chrome
import { chromium } from 'playwright-core';
import fs from 'fs';

const url = process.argv[2] || 'http://localhost:8765/';
const out = process.argv[3] || './_shots';
const holds = (process.argv[4] || '900,1100,800,1000,950,1050').split(',').map(Number);
fs.mkdirSync(out, { recursive: true });
const exe = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const browser = await chromium.launch({ executablePath: exe, headless: true, args: ['--use-gl=angle', '--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 420, height: 820 } });  // 手機直式
const errs = [];
page.on('pageerror', e => errs.push('PAGEERR ' + e.message));
page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) errs.push('HTTP ' + r.status() + ' ' + r.url()); });

await page.goto(url);
try { await page.waitForSelector('#go', { timeout: 20000 }); }
catch (e) { await page.screenshot({ path: `${out}/00_fail.png` }); console.log('START BUTTON NEVER APPEARED\n' + errs.join('\n')); await browser.close(); process.exit(1); }
await page.screenshot({ path: `${out}/00_menu.png` });
await page.click('#go');
await page.waitForTimeout(1500);
await page.screenshot({ path: `${out}/01_start.png` });

for (let i = 0; i < holds.length; i++) {
  await page.keyboard.down('Space');
  await page.waitForTimeout(holds[i]);
  await page.keyboard.up('Space');
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${out}/${String(i + 2).padStart(2, '0')}_action.png` });
  await page.waitForTimeout(1800);
  const g = await page.evaluate(() => window.game);
  console.log('step', i, JSON.stringify(g));
  if (g && g.state !== 'play') break;
}
await page.screenshot({ path: `${out}/99_end.png` });
const ok = await page.evaluate(() => ({ ok: window.__ok, errs: window.__errs, msg: document.querySelector('#msg')?.innerText }));
console.log('ok:', ok.ok, '| msg:', (ok.msg || '').replace(/\s+/g, ' ').slice(0, 120));
const all = errs.concat(ok.errs || []);
console.log(all.length ? all.join('\n') : 'NO ERRORS');
await browser.close();
process.exit(all.length ? 1 : 0);
