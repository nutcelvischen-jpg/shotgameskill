# 測試與上線

## 本機預覽
```bash
cd example && python3 -m http.server 18431 --bind 127.0.0.1
# 開 http://127.0.0.1:18431/   （不能直接雙擊 index.html：file:// 會擋掉 fetch 和 GLB）
```
Port 被占用（`Address already in use`）或開到別的網站 → 換一個冷門的 port，**先 `curl` 看一下內容對不對**。

## 無頭測試（agent 自己驗收）
```bash
cd scripts && npm i playwright-core          # 第一次
node scripts/test_headless.mjs "http://127.0.0.1:18431/?lv=0" ./_shots 300,400,350
```
- 用系統 Chrome，不用下載瀏覽器；`--use-gl=angle` 讓 WebGL 在無頭模式也能畫。
- 會截圖 `00_menu`、`01_start`、每次動作後一張、`99_end`，**一定要打開截圖看**：模型有沒有出現、光是不是過曝、UI 有沒有擋住。
- 輸出 `NO ERRORS` 才算過；`HTTP 404 voice/*.mp3` 代表配音還沒產生。
- 事件很難碰到時用參數強制：`?lv=3&ev=dog,ghost,snake`。
- 測不到的東西（陀螺儀、iOS 權限、實際手感、聲音）要明講，請使用者用手機試。

## 上線：GitHub Pages
```bash
touch .nojekyll                               # 不讓 Jekyll 處理檔案
printf '*.blend\n*.blend1\n_shots/\nnode_modules/\n.DS_Store\n' > .gitignore
git init -b main && git add -A && git commit -m "first playable"
git remote add origin https://github.com/<帳號>/<repo>.git && git push -u origin main
gh api -X POST repos/<帳號>/<repo>/pages -f "source[branch]=main" -f "source[path]=/"
# 約 1 分鐘後：https://<帳號>.github.io/<repo>/
curl -s -o /dev/null -w "%{http_code}" https://<帳號>.github.io/<repo>/models/room.glb   # 確認模型也上去了
```
- 遊戲放在子資料夾時，網址要加路徑（例如 `/<repo>/example/`）。
- 更新：改完 `git push`，約 1 分鐘生效；手機看不到新版就重新整理（快取）。
- 上線前檢查：沒有 API 金鑰、沒有 `.blend`、GLB 總量 < 3MB。
