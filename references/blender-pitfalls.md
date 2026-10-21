# Blender 踩雷清單（給 agent 看的）

這份清單來自實際做「烙賽模擬器」時一個一個踩到的雷。照著做，Blender 部分可以一次成功。

## 1. 物件建立
| ❌ 常見錯誤 | ✅ 正確做法 |
|---|---|
| `bpy.ops.mesh.primitive_cube_add()` 然後 `bpy.context.object` | `H.box()`／`H.cylinder()`／`H.lathe()`（bmesh＋bpy.data，不吃 context） |
| `bpy.data.objects["Light"]` 改燈光 → KeyError | 清場後自己建：`H.area_light()`、`H.camera()` |
| 物件連到 `bpy.context.collection` → 跑到隱藏的 collection | `H.link()` 一律連到 `scene.collection` |
| 複製物件後名稱變 `Toilet_Seat.001` | 複製完立刻改名；或乾脆用函式重建一份 |
| 圓形物件中間有一條黑縫 | lathe 後要 `remove_doubles`（`H.lathe` 已處理） |
| 方塊加 bevel 後 smooth shading 變得很醜 | 方塊保持 flat（`H.box` 預設） |

## 2. 形狀怎麼做才像
- **圓的東西一律用 `H.lathe(profile)`**：馬桶、杯子、垃圾桶、花盆、小便斗。profile 從內底 → 內壁 → 杯緣 → 外壁 → 外底連成一條線。
- 橢圓（例如馬桶）：`sx`／`sy` 參數壓扁。
- 半個殼（例如小便斗）：lathe 的 `angle=180`，再加 Solidify modifier。
- 「歪掉的」「迷你的」變體：同一個建模函式，改根節點的 `rotation_euler`／`scale` 就好。
- 細節靠材質、不靠多邊形：亮面陶瓷用 `coat=1, rough=0.12`；金屬用 `metal=0.9, rough=0.35`。

## 3. 材質
- Principled BSDF 輸入名稱跨版本不同（`Coat Weight` vs `Clearcoat`、`Emission Color` vs `Emission`）→ 用 `H.set_input(node, [名稱1, 名稱2], 值)`。
- **水面不要用 Transmission**：EEVEE 下會變成一片黑。改成不透明、低 roughness、加 coat 的淡藍色。
- 程式磁磚（Brick Texture）用 Object 座標：**牆面一定要 `vertical=True`**，否則磁磚會被拉成直條紋。
- 髒污：Noise → ColorRamp → Multiply 混進底色（`tile_material(grime=0.5)`）。

## 4. 烘焙（最容易出事的一段）
| 症狀 | 原因 | 解法 |
|---|---|---|
| 貼圖幾乎全黑，只有一小塊有畫面 | 地板面積比看得到的範圍大很多，UV 被縮小 | 地板／牆只做「鏡頭看得到的大小」的單一 quad，用 `uv.unwrap` 撐滿 |
| 一片白、過曝 | 燈太亮；three.js 的 MeshBasic 不會壓亮部 | 小房間面光 35~60W；烘完用 `look` 看一下貼圖 |
| 地上有道具的影子，但道具換掉了影子還在 | 烘焙時沒藏道具 | `bake_lighting(..., hide=道具們)` |
| three.js 貼圖錯位 | 物件有多組 UV | `bake_lighting` 會先清掉所有 UV 只留 BakeUV |
| `Baking map saved to internal image` 然後檔案不見 | 沒有 `img.save()` | 用 `H.bake_lighting`（已處理） |

## 5. 匯出 GLB
- 一律 `H.export_glb(root, path)`：只匯出該根節點、暫時移回原點、套用 modifier、貼圖轉 JPEG。
- **座標換算**：Blender `(x, y, z)` → three.js `(x, z, -y)`。玩家站在 Blender 的 y=0 往 +Y 看 = three.js 往 -Z 看。
- 碰撞資料（杯口高 `rimY`、內徑 `r`、外徑 `outerR`）用 `H.write_meta()` 一起輸出，數字直接寫成 three.js 座標。
- GLB 太大（> 3MB）：通常是烘焙 PNG。用 JPEG（預設）、牆面 512px 就夠。

## 6. 驗證習慣
- 每建完一個道具：截圖看（MCP `look`／`get_screenshot`，或 `H.preview()` 然後讀圖片）。
- 匯出後：在瀏覽器實際載入一次（`scripts/test_headless.mjs`），因為 Blender 裡好看 ≠ three.js 裡好看。
- 隨時 `bpy.ops.wm.save_mainfile()`，MCP 斷線不會白做。
