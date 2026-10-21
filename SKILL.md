---
name: blender-threejs-minigame
description: Build a funny 3D browser mini-game (aim/drop/throw style, like 烙賽模擬器 or a paper-toss game) with Blender for the art (procedural props, baked lighting, GLB export) and three.js for the game (physics, hit tests, events, procedural music, TTS voice lines), then test headless and deploy to GitHub Pages. Use when someone asks for a 3D web mini-game, a "simulator" joke game, or Blender → three.js assets.
---

# Blender × three.js 搞笑小遊戲 Skill

做法拆成兩條線：**Blender 只負責「看起來」**（靜態場景＋道具＋烘焙光影），**three.js 負責「玩起來」**（物理、判定、事件、聲音）。會動、會變形的東西（便便、紙團、液體、角色）一律在 three.js 用程式生成，不要在 Blender 做。

## 先讀什麼
| 時機 | 檔案 |
|---|---|
| 開始前，定玩法與難度 | `references/game-design.md` |
| 第一次碰 Blender 前（**必讀**） | `references/blender-pitfalls.md` |
| 寫 three.js 時 | `references/threejs-patterns.md` |
| 做音樂、音效、配音 | `references/voice-and-audio.md` |
| 測試、上線 | `references/testing-deploy.md` |
| 要範例程式 | `example/index.html`（紙團投籃，約 200 行，全部功能都有） |

## 工作流程（照順序，每一步都要「看一眼」再往下）

1. **定玩法（5 分鐘）**：寫出一句話核心動作＋一個操作＋難度旋鈕表＋事件清單。格式見 `game-design.md`。
2. **Blender 建場景**：複製 `scripts/blender/build_example.py` 改內容，`import bl_helpers as H` 用它的函式。
   - 一個道具一個 Empty 根節點（`Bin_Small`、`Toilet_Squat`…），變體沿 X 軸排開
   - 每建完一批就預覽（MCP 的 look／screenshot，或 `H.preview()`），**有看到才算做完**
   - 每一步存 `.blend`
3. **烘焙＋匯出**：`H.bake_lighting(靜態面, out, hide=會動的道具)` → `H.export_glb()` → `H.write_meta()` 輸出碰撞資料 JSON。
4. **three.js 遊戲**：從 `example/index.html` 改。先只做「一關＋核心動作」，手感對了才加關卡。
5. **加料**：電子配樂（程式合成）→ 音效 → 突發事件 → 結算評分 → TTS 配音。
6. **測試**：`node scripts/test_headless.mjs URL 截圖資料夾`，看截圖、確認 `NO ERRORS`。
7. **上線**：GitHub Pages（加 `.nojekyll`），給使用者連結。

## 跑 Blender 的兩種方式
- **命令列（最穩，優先）**：`/Applications/Blender.app/Contents/MacOS/Blender -b -P build.py -- 輸出資料夾`
- **Blender MCP**：適合邊做邊看。腳本用 `exec(open(path).read(), {"__file__": path, "__name__": "__main__"})` 執行，避免一次貼幾百行程式。MCP 斷線時改走命令列。

## 鐵則
- 用 `bl_helpers` 的 bmesh 函式建物件，**不要用 `bpy.ops.mesh.primitive_*`**，也不要假設預設的 Cube/Light/Camera 存在。
- 烘焙過的材質名稱結尾 `_Bake` → three.js 換成 `MeshBasicMaterial({map, toneMapped:false})`，再加一片 `ShadowMaterial` 平面接動態影子。
- 命中判定在**目標的區域座標**做（`target.worldToLocal`），目標會動、會歪都不用改公式。
- 碰撞數字（杯口高度、半徑）由 Blender 腳本寫進 JSON，**不要在兩邊各寫一份**。
- 每個遊戲都要：`?lv=`、`?ev=` 除錯參數、`window.__errs`、`window.__ok`、`window.game` 狀態，給無頭測試用。
- API 金鑰只能放環境變數；配音先離線產生 mp3 再放進網站。
- 不畫有版權的角色（貞子、Sonic、迪士尼…），改成原創角色並說明原因。
- 配音避免喘氣、呻吟類聲音（容易變得很猥褻），用「台詞」代替「聲音」，詳見 `voice-and-audio.md`。
- GLB 總量控制在 3MB 內：烘焙面只做看得到的大小、貼圖輸出 JPEG。
