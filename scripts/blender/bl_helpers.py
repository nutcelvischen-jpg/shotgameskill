"""
bl_helpers.py — 給 AI agent 用的 Blender 小遊戲建模工具（Blender 4.2 ~ 5.x 測試過）

設計原則（這些都是 agent 最常在 Blender 出錯的地方）：
  1. 一律用 bpy.data / bmesh 建物件，不用 bpy.ops.mesh.primitive_*（ops 依賴 context，MCP / 背景模式常失敗）
  2. 不假設預設物件存在（"Cube" "Light" "Camera" 可能早就被刪了）→ 先 reset_scene() 再自己建
  3. Principled BSDF 的輸入名稱各版本不同 → 用 set_input() 安全設定，名字不存在就跳過
  4. 每個「可替換道具」都包在一個 Empty 根節點下（命名 PREFIX_Variant），export 時整組匯出
  5. 單位 = 公尺，Blender Z 朝上；匯出 glTF 後 three.js 座標 = (x, z, -y)

用法（MCP execute_blender_code 或 blender -b -P 皆可）：
    import sys; sys.path.insert(0, "/絕對路徑/scripts/blender")
    import importlib, bl_helpers as H; importlib.reload(H)
"""
import bpy, bmesh, math, os, json
from mathutils import Vector

# ================================================================ scene
def reset_scene():
    """刪掉所有物件與孤兒資料。比 'select all + delete' 穩定。"""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.images, bpy.data.curves):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def link(obj, parent=None):
    """連到場景根 collection（不要用 context.collection，它可能是隱藏的）。"""
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def group(name, loc=(0, 0, 0), parent=None):
    """Empty 根節點。道具所有零件 parent 到它，匯出時整組帶走。"""
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    e.location = loc
    return link(e, parent)


# ================================================================ materials
def set_input(node, names, value):
    """依序嘗試多個輸入名稱（跨版本相容），成功回傳 True。"""
    for n in ([names] if isinstance(names, str) else names):
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def pbr(name, color, rough=0.5, metal=0.0, coat=0.0, emit=None, emit_strength=1.0, alpha=1.0):
    """建立／更新 Principled 材質。coat>0 = 亮面陶瓷、烤漆；glTF 會轉成 KHR_materials_clearcoat。"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    set_input(b, "Base Color", (*color, 1))
    set_input(b, "Roughness", rough)
    set_input(b, "Metallic", metal)
    set_input(b, ["Coat Weight", "Clearcoat"], coat)
    if emit:
        set_input(b, ["Emission Color", "Emission"], (*emit, 1))
        set_input(b, "Emission Strength", emit_strength)
    if alpha < 1:
        set_input(b, "Alpha", alpha)
        try:
            m.surface_render_method = 'BLENDED'   # 4.2+
        except Exception:
            m.blend_method = 'BLEND'              # 舊版
    return m


def tile_material(name, c1, c2, mortar, scale=6.0, rough=0.3, vertical=False, grime=0.0):
    """程式磁磚（Brick Texture）＋溝縫凹凸＋可選髒污。
    vertical=True 給牆面用（物件在 XZ 平面），會自動旋轉貼圖座標，不然磁磚會被拉成條紋。"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Lk = nt.links
    b = N.get("Principled BSDF")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    if vertical:
        mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    Lk.new(tc.outputs["Object"], mp.inputs["Vector"])
    br = N.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = scale
    br.inputs["Mortar Size"].default_value = 0.015
    br.inputs["Brick Width"].default_value = 0.5
    br.inputs["Row Height"].default_value = 0.5
    Lk.new(mp.outputs["Vector"], br.inputs["Vector"])
    color_out = br.outputs["Color"]
    if grime > 0:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 2.5
        nz.inputs["Detail"].default_value = 8
        Lk.new(mp.outputs["Vector"], nz.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.5
        ramp.color_ramp.elements[1].position = 0.75
        Lk.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = grime
        Lk.new(ramp.outputs["Color"], mul.inputs[0])
        mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        Lk.new(mul.outputs[0], mix.inputs["Factor"])
        Lk.new(color_out, mix.inputs[6])
        mix.inputs[7].default_value = (0.75, 0.68, 0.5, 1)
        color_out = mix.outputs[2]
    Lk.new(color_out, b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs[3].default_value = 0.9
    mr.inputs[4].default_value = rough
    Lk.new(br.outputs["Fac"], mr.inputs[0])
    Lk.new(mr.outputs[0], b.inputs["Roughness"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.3
    Lk.new(br.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ================================================================ meshes (bmesh, no ops)
def _mesh_obj(name, bm, mat=None, smooth=True, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if mat:
        me.materials.append(mat)
    return link(bpy.data.objects.new(name, me), parent)


def box(name, size, loc=(0, 0, 0), mat=None, bevel=0.0, parent=None):
    """size = (寬X, 深Y, 高Z) 公尺，loc = 中心點。"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    o = _mesh_obj(name, bm, mat, smooth=False, parent=parent)
    o.location = loc
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel; md.segments = 3; md.limit_method = 'ANGLE'
    return o


def quad(name, w, h, loc=(0, 0, 0), vertical=False, mat=None, parent=None):
    """單一四邊形（地板／牆面）。vertical=True → 立在 XZ 平面、法線朝 -Y。
    烘焙用的面請只做「看得到的範圍」大小，不然貼圖解析度會浪費在看不到的地方。"""
    bm = bmesh.new()
    if vertical:
        pts = [(-w/2, 0, -h/2), (w/2, 0, -h/2), (w/2, 0, h/2), (-w/2, 0, h/2)]
    else:
        pts = [(-w/2, -h/2, 0), (w/2, -h/2, 0), (w/2, h/2, 0), (-w/2, h/2, 0)]
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    o = _mesh_obj(name, bm, mat, smooth=False, parent=parent)
    o.location = loc
    return o


def cylinder(name, r, h, loc=(0, 0, 0), mat=None, segs=32, r_top=None, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r,
                          radius2=r if r_top is None else r_top, depth=h)
    o = _mesh_obj(name, bm, mat, smooth=True, parent=parent)
    o.location = loc
    return o


def sphere(name, r, loc=(0, 0, 0), mat=None, scale=(1, 1, 1), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    o = _mesh_obj(name, bm, mat, smooth=True, parent=parent)
    o.location = loc; o.scale = scale
    return o


def lathe(name, profile, mat=None, steps=64, sx=1.0, sy=1.0, subsurf=2, parent=None, loc=(0, 0, 0)):
    """旋轉成形：馬桶、杯子、垃圾桶、花瓶等「圓的東西」最好用。
    profile = [(半徑, 高度), ...] 由內底 → 內壁 → 杯緣 → 外壁 → 外底，連成一條線。
    sx/sy 可以把圓壓成橢圓（例如馬桶 sy=1.28）。"""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i+1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.radians(360), steps=steps, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)   # 縫合接縫，否則會有一條黑線
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy
    o = _mesh_obj(name, bm, mat, smooth=True, parent=parent)
    o.location = loc
    if subsurf:
        md = o.modifiers.new("sub", "SUBSURF"); md.levels = subsurf; md.render_levels = subsurf
    return o


# ================================================================ lights / camera / world
def area_light(name, loc, energy=60, size=0.6, color=(1, 1, 1)):
    """面光（預設朝 -Z 往下照）。室內小空間 50~120W 就夠，太亮烘焙會過曝。"""
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.size = size; ld.color = color
    o = link(bpy.data.objects.new(name, ld)); o.location = loc
    return o


def camera(name, loc, look_at, lens=24, portrait=True):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    o = link(bpy.data.objects.new(name, cd)); o.location = loc
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc = bpy.context.scene; sc.camera = o
    sc.render.resolution_x, sc.render.resolution_y = (1080, 1920) if portrait else (1920, 1080)
    return o


def world(color=(0.15, 0.16, 0.15), strength=0.6):
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    return w


# ================================================================ bake
def _select_only(o):
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def bake_lighting(objects, out_dir, res=1024, samples=48, hide=()):
    """把「靜態場景」的光影（含陰影、反彈光）烘到貼圖。
    - hide: 會動的東西（道具、角色）先藏起來，避免陰影被烤死在地上
    - 每個物件換成 <name>_Bake 材質：只剩一張 Base Color 圖
    - three.js 端看到材質名稱結尾 _Bake → 換成 MeshBasicMaterial（不再吃燈光）"""
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    prev_engine = sc.render.engine
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    for h in hide:
        h.hide_render = True
    try:
        for o in objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            _select_only(o)
            me = o.data
            while len(me.uv_layers):          # 只留一組 UV，避免 glTF/three 用錯 UV
                me.uv_layers.remove(me.uv_layers[0])
            me.uv_layers.new(name="BakeUV")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            if len(me.polygons) == 1:
                bpy.ops.uv.unwrap(margin=0.0)              # 單一四邊形：撐滿整張圖
            else:
                bpy.ops.uv.smart_project(island_margin=0.02)
            bpy.ops.object.mode_set(mode='OBJECT')

            iname = f"{o.name}_bake"
            if iname in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[iname])
            img = bpy.data.images.new(iname, res, res)
            src = me.materials[0] if me.materials else pbr(o.name + "_mat", (0.8, 0.8, 0.8))
            mat = src.copy(); mat.name = f"{o.name}_Bake"
            me.materials.clear(); me.materials.append(mat)
            nt = mat.node_tree
            tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
            nt.nodes.active = tn
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT', 'COLOR'}, margin=8)
            img.filepath_raw = os.path.join(out_dir, f"{iname}.png")
            img.file_format = 'PNG'
            img.save()
            # 重新接線：只留 image → Base Color
            b = nt.nodes.get("Principled BSDF")
            for key in ("Base Color", "Normal", "Roughness"):
                for l in list(b.inputs[key].links):
                    nt.links.remove(l)
            nt.links.new(tn.outputs["Color"], b.inputs["Base Color"])
            print("baked", o.name)
    finally:
        for h in hide:
            h.hide_render = False
        sc.render.engine = prev_engine


# ================================================================ export
def export_glb(root, path, jpeg=True):
    """把 root（Empty 或單一物件）連同所有子物件匯出成 GLB。
    匯出時會暫時把 root 移到原點，所以建模時可以把變體排成一列方便看。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    old = root.location.copy()
    root.location = (0, 0, 0)
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    root.select_set(True)
    for c in root.children_recursive:
        c.select_set(True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True,
              export_apply=True, export_yup=True)
    if jpeg:   # 貼圖轉 JPEG，GLB 大小通常降 70~80%
        kw.update(export_image_format='JPEG', export_jpeg_quality=85)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        for k in ('export_image_format', 'export_jpeg_quality'):
            kw.pop(k, None)
        bpy.ops.export_scene.gltf(**kw)
    root.location = old
    kb = os.path.getsize(path) // 1024
    print(f"exported {os.path.basename(path)} {kb} KB")
    return kb


def write_meta(path, data):
    """道具的「碰撞資料」（杯口高度、半徑…）跟 GLB 一起輸出，遊戲端直接讀，不用手抄數字。
    注意：輸出時就換成 three.js 座標（Y 朝上）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("meta ->", path)


# ================================================================ preview
def preview(path, engine='BLENDER_EEVEE_NEXT', samples=16):
    """從目前相機渲染一張預覽圖，讓 agent 用眼睛確認（MCP 有 look 工具時用 look 更快）。
    背景模式下 EEVEE 不可用時自動退回 Workbench。"""
    sc = bpy.context.scene
    prev = sc.render.engine
    for eng in (engine, 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_percentage = 40
    sc.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as e:
        print("preview failed with", sc.render.engine, e, "→ fallback Workbench")
        sc.render.engine = 'BLENDER_WORKBENCH'
        bpy.ops.render.render(write_still=True)
    sc.render.engine = prev
    sc.render.resolution_percentage = 100
    print("preview ->", path)
