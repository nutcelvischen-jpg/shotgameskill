# 🎮 shotgameskill — 用 AI 做搞笑 3D 網頁小遊戲

**Blender 畫場景 × three.js 做遊戲 × Gemini TTS 配音**，讓 AI agent 一次做對的 Skill。

這個 Skill 是從實際做出來的遊戲整理而成：
- 💩 [烙賽模擬器](https://nutcelvischen-jpg.github.io/shotgame/)：對準馬桶、推門、停電、阿飄、馬桶蛇、吉娃娃、擦屁股評分
- 🗑️ [紙團投籃王（本 repo 範例）](https://nutcelvischen-jpg.github.io/shotgameskill/example/)：約 200 行、所有技巧都有

---

## 🚀 三步上手

### 1. 先玩範例
打開 👉 https://nutcelvischen-jpg.github.io/shotgameskill/example/
滑鼠瞄準，按住空白鍵蓄力、放開丟出。手機可以左右拖曳瞄準，再按住右下角的按鈕蓄力。

### 2. 把 Skill 裝進你的 AI agent
```bash
git clone https://github.com/nutcelvischen-jpg/shotgameskill.git
# Claude Code：
cp -r shotgameskill ~/.claude/skills/blender-threejs-minigame
# 其他 agent（Antigravity、Cursor…）：把整個資料夾放進該工具的 skills／rules 目錄，
# 或在對話開頭說「請先讀 shotgameskill/SKILL.md」
```
需要的工具：Blender 4.2 以上（建議裝 Blender MCP）、Python 3、Node.js、ffmpeg（只有配音會用到）。

### 3. 跟 AI 說你要做什麼（提示詞範本）
```
請用 blender-threejs-minigame skill 幫我做一個搞笑 3D 網頁小遊戲：
- 核心動作：＿＿＿＿（例：把餃子丟進滾水鍋、把貓推下桌、用吸管對準珍珠）
- 場景：＿＿＿＿（例：夜市攤位、辦公室、教室）
- 目標的變化：＿＿＿＿（例：鍋子越來越小、會移動）
- 突發事件 3 個：＿＿＿＿（例：老闆來了、停電、狗衝進來）
- 全破台詞：＿＿＿＿（例：「我是夜市之王！讚！」）
先做第 1 關讓我試玩，手感對了再加關卡和配音。
```

---

## 📁 內容
```
SKILL.md                      ← agent 入口：流程＋鐵則
references/
  game-design.md              ← 一頁企劃、難度表、好笑的來源、事件模板
  blender-pitfalls.md         ← Blender 踩雷清單（AI 最常錯的地方）
  threejs-patterns.md         ← 載模型、軟物體、物理、命中判定、事件系統
  voice-and-audio.md          ← 程式電子配樂、合成音效、搞笑配音 prompt 寫法
  testing-deploy.md           ← 無頭測試、GitHub Pages 上線
scripts/
  blender/bl_helpers.py       ← 建模／材質／烘焙／匯出工具函式（不靠 bpy.ops 建物件）
  blender/build_example.py    ← 範例的完整建模管線（一行指令重建所有模型）
  tts_openrouter.py           ← 批次產生配音 mp3
  test_headless.mjs           ← 無頭瀏覽器自動試玩＋截圖
example/
  index.html                  ← 紙團投籃王（可直接改成你的遊戲）
  models/                     ← room.glb、4 種目標 GLB、targets.json（碰撞資料）
  voice/ + voice_lines.json   ← 配音與台詞 prompt
```

## 🛠️ 自己重建範例
```bash
# 1) 重建 3D 模型（約 1 分鐘，含烘焙）
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/blender/build_example.py -- example/models
# 2) 重做配音（要自己的 OpenRouter 金鑰）
export OPENROUTER_API_KEY=sk-or-v1-...
python3 scripts/tts_openrouter.py example/voice_lines.json example/voice
# 3) 本機試玩
cd example && python3 -m http.server 18431 --bind 127.0.0.1   # 開 http://127.0.0.1:18431/
# 4) 自動測試
cd scripts && npm i playwright-core && cd ..
node scripts/test_headless.mjs "http://127.0.0.1:18431/" ./_shots
```
Windows 的 Blender 路徑通常是 `"C:\Program Files\Blender Foundation\Blender 4.x\blender.exe"`。

## 🧪 課堂練習（由易到難）
1. **改數字**：在 `example/index.html` 的 `LEVELS` 加第 5 關（更遠、目標移動更快）。
2. **改台詞**：改寫 `voice_lines.json`，用 `voice-and-audio.md` 的語氣標籤配出你自己的聲音。
3. **加事件**：照 `startEvent`／`updateEvent` 的格式加一個「同事來借釘書機」事件。
4. **換道具**：在 `build_example.py` 用 `H.lathe()` 做一個新目標（例：花瓶、安全帽），重新匯出。
5. **做自己的遊戲**：用上面的提示詞範本，讓 AI 從零做一個。

## ⚠️ 注意
- API 金鑰只放環境變數，**不要 commit**、不要寫進網頁。
- 不要畫有版權的角色，改用原創角色。
- 配音避免喘氣、呻吟類聲音，改用有字的喊聲（原因見 `voice-and-audio.md`）。

---
製作：陳俊智 Elvis Chen｜國立臺中科技大學 國際貿易與經營系 · 智慧商務多代理人實驗室 (ICMA Lab)
