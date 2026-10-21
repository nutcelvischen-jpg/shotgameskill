"""
build_example.py — 範例「辦公室紙團投籃」的完整 Blender 建模管線
房間（烘焙光影）＋ 4 種目標（垃圾桶、小垃圾桶、資源回收桶、馬克杯）→ GLB + targets.json

兩種跑法：
  A) 命令列（最穩，推薦給 agent）：
     /Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/blender/build_example.py -- example/models
  B) Blender MCP（execute_blender_code）：
     exec(open("/絕對路徑/scripts/blender/build_example.py").read(), {"__file__": "/絕對路徑/scripts/blender/build_example.py", "__name__": "__main__"})
"""
import sys, os, math, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bl_helpers as H
importlib.reload(H)
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.join(HERE, "..", "..", "example", "models")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ 1. 清場
H.reset_scene()

# ------------------------------------------------------------------ 2. 材質
floor_m = H.tile_material("Floor", (0.62, 0.6, 0.56), (0.58, 0.56, 0.52), (0.3, 0.29, 0.27), scale=5, grime=0.5)
wall_m  = H.tile_material("Wall", (0.86, 0.86, 0.82), (0.83, 0.83, 0.79), (0.7, 0.7, 0.66), scale=3, vertical=True)
metal   = H.pbr("BinMetal", (0.55, 0.57, 0.6), rough=0.35, metal=0.9)
green   = H.pbr("BinGreen", (0.18, 0.55, 0.3), rough=0.4, coat=0.5)
mug_m   = H.pbr("MugCeramic", (0.95, 0.94, 0.9), rough=0.15, coat=1.0)
coffee  = H.pbr("Coffee", (0.12, 0.06, 0.03), rough=0.05)
wood    = H.pbr("Wood", (0.45, 0.3, 0.18), rough=0.6)
pot_m   = H.pbr("Pot", (0.7, 0.35, 0.22), rough=0.7)
leaf_m  = H.pbr("Leaf", (0.2, 0.5, 0.2), rough=0.5)

# ------------------------------------------------------------------ 3. 房間（靜態，要烘焙）
# 座標約定：玩家在 y=0 往 +Y 看，目標放在 y≈1.8
room = H.group("Room")
floor = H.quad("Floor", 2.4, 3.2, loc=(0, 1.3, 0), mat=floor_m, parent=room)
back  = H.quad("WallBack", 2.4, 2.4, loc=(0, 2.9, 1.2), vertical=True, mat=wall_m, parent=room)
left  = H.quad("WallLeft", 3.2, 2.4, loc=(-1.2, 1.3, 1.2), vertical=True, mat=wall_m, parent=room)
left.rotation_euler = (0, 0, math.radians(90))      # 法線 -Y 轉 90° → 朝 +X（朝向房間內）
right = H.quad("WallRight", 3.2, 2.4, loc=(1.2, 1.3, 1.2), vertical=True, mat=wall_m, parent=room)
right.rotation_euler = (0, 0, math.radians(-90))
# 不烘焙、保留 PBR 的小擺設（會吃 three.js 即時光）
H.box("Cabinet", (0.5, 0.4, 0.9), loc=(0.85, 2.65, 0.45), mat=wood, bevel=0.01, parent=room)
H.lathe("PlantPot", [(0.0, 0.0), (0.11, 0.0), (0.14, 0.28), (0.15, 0.3), (0.13, 0.3), (0.0, 0.27)],
        mat=pot_m, parent=room, loc=(-0.9, 2.6, 0))
H.sphere("PlantLeaves", 0.2, loc=(-0.9, 2.6, 0.45), mat=leaf_m, scale=(1, 1, 1.3), parent=room)

# ------------------------------------------------------------------ 4. 目標（會換的道具）
# 變體沿 X 軸排開，匯出時 export_glb 會暫時移回原點
BIN = [(0.0, 0.01), (0.125, 0.01), (0.14, 0.32), (0.15, 0.34), (0.162, 0.336), (0.15, 0.0), (0.0, 0.0)]
meta = {}

g = H.group("Bin_Basic", loc=(3, 0, 0))
H.lathe("Bin_Basic_Body", BIN, mat=metal, parent=g, subsurf=1)
meta["Bin_Basic"] = dict(file="bin_basic.glb", rimY=0.34, r=0.14, outerR=0.165, label="標準垃圾桶")

g = H.group("Bin_Small", loc=(4.5, 0, 0)); g.scale = (0.62, 0.62, 0.62)
H.lathe("Bin_Small_Body", BIN, mat=metal, parent=g, subsurf=1)
meta["Bin_Small"] = dict(file="bin_small.glb", rimY=0.34 * 0.62, r=0.14 * 0.62, outerR=0.165 * 0.62, label="迷你垃圾桶")

g = H.group("Bin_Recycle", loc=(6, 0, 0))
H.lathe("Bin_Recycle_Body", [(0.0, 0.01), (0.11, 0.01), (0.12, 0.48), (0.13, 0.5), (0.142, 0.495), (0.13, 0.0), (0.0, 0.0)],
        mat=green, parent=g, subsurf=1)
meta["Bin_Recycle"] = dict(file="bin_recycle.glb", rimY=0.5, r=0.12, outerR=0.142, label="資源回收桶")

g = H.group("Mug", loc=(7.5, 0, 0))
H.lathe("Mug_Body", [(0.0, 0.006), (0.04, 0.006), (0.042, 0.1), (0.047, 0.104), (0.05, 0.1), (0.048, 0.0), (0.0, 0.0)],
        mat=mug_m, parent=g, subsurf=1)
handle_prof = [(0.03 + 0.007 * math.cos(a), 0.007 * math.sin(a)) for a in [i / 12 * 2 * math.pi for i in range(13)]]
hd = H.lathe("Mug_Handle", handle_prof, mat=mug_m, parent=g, steps=24, subsurf=0)
hd.rotation_euler = (math.radians(90), 0, 0); hd.location = (0.05, 0, 0.052)
cf = H.cylinder("Mug_Coffee", 0.04, 0.004, loc=(0, 0, 0.08), mat=coffee, parent=g)
meta["Mug"] = dict(file="mug.glb", rimY=0.104, r=0.04, outerR=0.05, label="老闆的馬克杯")

# ------------------------------------------------------------------ 5. 燈光／相機
H.world((0.2, 0.2, 0.22), 0.5)
H.area_light("OfficeLight", (0, 1.6, 2.35), energy=38, size=1.2, color=(1, 0.97, 0.9))
H.camera("Cam_POV", loc=(0, -0.3, 1.3), look_at=(0, 1.8, 0.2), lens=26)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "..", "example_scene.blend"))

# ------------------------------------------------------------------ 6. 預覽（agent 自我檢查用）
H.preview(os.path.join(OUT, "..", "_preview.png"))

# ------------------------------------------------------------------ 7. 烘焙靜態光影（目標先藏起來）
targets = [o for o in bpy.data.objects if o.name.split("_")[0] in ("Bin", "Mug")]
H.bake_lighting([floor, back, left, right], OUT, res=1024, samples=48, hide=targets)

# ------------------------------------------------------------------ 8. 匯出
H.export_glb(room, os.path.join(OUT, "room.glb"))
for name, m in meta.items():
    H.export_glb(bpy.data.objects[name], os.path.join(OUT, m["file"]))
H.write_meta(os.path.join(OUT, "targets.json"), meta)

# 烘焙的 PNG 已經以 JPEG 包進 GLB，可刪掉中間檔
for f in os.listdir(OUT):
    if f.endswith("_bake.png"):
        os.remove(os.path.join(OUT, f))
bpy.ops.wm.save_mainfile()
print("DONE ->", OUT)
