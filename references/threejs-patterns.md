# three.js 遊戲模式（直接抄）

所有程式片段在 `example/index.html` 都有完整版本。

## 0. 骨架
- 單一 `index.html`＋`models/`＋`voice/`，importmap 載入 `three@0.170.0`（鎖版本）。
- 直式手機優先：`aspect<1` 時 fov 調大；UI 用 `env(safe-area-inset-bottom)`。
- 頂層 `await` 載入模型，載完才顯示開始按鈕（測試腳本就靠 `#go` 判斷載入完成）。

## 1. 載入 Blender 模型
```js
async function glb(f){const g=(await loader.loadAsync('models/'+f)).scene;
 g.traverse(o=>{if(!o.isMesh)return;
  if(o.material.name.endsWith('_Bake'))                       // 烘焙過 → 不吃燈
    o.material=new THREE.MeshBasicMaterial({map:o.material.map,toneMapped:false});
  else{o.castShadow=o.receiveShadow=true;}});return g;}
```
- 動態影子：烘焙地板上方放 `ShadowMaterial({opacity:.3})` 平面接影子。
- 反光：`scene.environment = PMREM(RoomEnvironment)`，陶瓷/金屬才會亮。
- 模型快取：同一個 GLB 用好幾次就 `cache[f].scene.clone(true)`。

## 2. 程式生成的「軟東西」
| 東西 | 做法 |
|---|---|
| 便便／麵條／繩子 | Verlet 粒子鏈（每段等長約束）→ 每幀用 `CatmullRomCurve3` ＋ `TubeGeometry` 重建，半徑加 sin 雜訊 |
| 紙團／石頭 | `IcosahedronGeometry` 頂點隨機推拉＋`flatShading` |
| 桃子屁股 | 兩顆球＋頂點色漸層＋`MeshPhysicalMaterial({sheen:1})` 絨毛感；出力時 scale 擠扁＋抖動 |
| 水花 | 預先建 40 顆小球的物件池，重複使用 |
| 角色（狗、阿飄） | 用基本形狀組合（Sphere/Cone/Cylinder/Lathe/Tube），一個 Group，動畫用 sin 擺動 |

## 3. 物理：固定步長＋子步
```js
phAcc+=dt; while(phAcc>=H){physics(); phAcc-=H;}   // H=1/120
// 或簡單版：for(k<4) stepBall(b, dt/4)
```
快的東西一定要子步，不然會穿過杯緣。

## 4. 命中判定：在目標的區域座標做
```js
const lv = node.worldToLocal(p.clone());            // 目標會動、會歪都沒差
if (prevY > rimY && lv.y <= rimY) {                 // 從上方穿過杯口平面
  const e = (lv.x/rx)**2 + ((lv.z-cz)/rz)**2;       // 橢圓（馬桶）／圓（杯子）
  if (e < 1) 進了; else if (在外緣環內) 撞到邊;
}
```
- 碰撞數字從 `targets.json` 讀（Blender 端輸出），不要手抄。
- 撞杯緣：算點到「杯緣圓環」的最近點 → 法線反彈 `v -= (1+彈性)*(v·n)*n`。
- 進去之後：把物體「黏」在目標的區域座標（存 `local`，每幀 `localToWorld`），目標移動時才會一起走。

## 5. 輸入
- 滑鼠：位置 → 射線打到「瞄準高度的平面」或直接換算角度。
- 觸控：拖曳用相對位移（`dx/innerWidth`），另外給一顆大按鈕做「按住」。
- 鍵盤：空白鍵＝主要動作（測試腳本也用它）。
- 陀螺儀：`DeviceOrientationEvent.requestPermission()`（iOS 必須在點擊事件內呼叫），**每關開始時的角度當 0 點**。

## 6. 狀態機與除錯
```js
state: 'menu' → 'doors'(選擇) → 'play' → 'wipe'(加碼小遊戲) → 'result'
window.game = {state, made, left, level, ev}      // 每幀更新，測試讀這個
const QS = new URLSearchParams(location.search);  // ?lv=3 跳關  ?ev=dog,snake 強制事件
```

## 7. 事件系統
```js
evQueue = types.map((type,i)=>({type, at: 觸發進度}));
function updateEvent(dt){ if(!ev){ if(進度到了) startEvent(evQueue.shift()); return; } ev.t+=dt; ...各事件分支... }
```
- 一次只跑一個事件；每個事件自己管 `phase`（預告 → 進行 → 結束）。
- 事件期間音樂加速（音樂 `mood()` 讀 `ev`）。
- 燈光事件：場景燈 intensity×係數，烘焙材質換成 Lambert 才會跟著變暗，再補一盞跟著鏡頭的 SpotLight 當手電筒。

## 8. 效能
- `renderer.setPixelRatio(Math.min(devicePixelRatio,2))`
- 影子貼圖 1024、只有一盞投影燈
- TubeGeometry 只在「還在動」的物體上重建
