# MasterSK - Bone Math, Kinematics & Roll Preservation Utilities
# Pipeline v5.3: Kinematic Vector Alignment with Auto-Grounding & Auto-Pitch
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion

# ---------------------------------------------------------------------------
# Bone Position Utilities
# ---------------------------------------------------------------------------

def get_bone_world_positions(armature_obj):
    if armature_obj.type != 'ARMATURE':
        raise ValueError(f"Object {armature_obj.name} is not an armature.")

    world_mat = armature_obj.matrix_world
    bone_data = {}

    if armature_obj.data.is_editmode:
        for b in armature_obj.data.edit_bones:
            head_w = world_mat @ b.head
            tail_w = world_mat @ b.tail
            mat_w = world_mat @ b.matrix
            bone_data[b.name] = (head_w, tail_w, mat_w)
    else:
        for b in armature_obj.data.bones:
            head_w = world_mat @ b.head_local
            tail_w = world_mat @ b.tail_local
            mat_w = world_mat @ b.matrix_local
            bone_data[b.name] = (head_w, tail_w, mat_w)

    return bone_data

def remove_all_bone_constraints(arm_obj):
    removed = 0
    if arm_obj.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for pb in arm_obj.pose.bones:
        for constraint in list(pb.constraints):
            pb.constraints.remove(constraint)
            removed += 1
    return removed

# ---------------------------------------------------------------------------
# ALS Skeleton Temporary Loading
# ---------------------------------------------------------------------------

def load_als_skeleton_temp(filepath):
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]

    als_arm = None
    loaded_objects = []
    for obj in data_to.objects:
        if obj is not None:
            loaded_objects.append(obj)
            bpy.context.collection.objects.link(obj)
            if obj.type == 'ARMATURE' and als_arm is None:
                als_arm = obj

    if not als_arm:
        for obj in loaded_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        raise ValueError(f"Could not find Armature object in {filepath}")

    als_arm.location = (0, 0, 0)
    als_arm.rotation_euler = (0, 0, 0)
    als_arm.scale = (1, 1, 1)
    bpy.context.view_layer.update()

    return als_arm, loaded_objects

def cleanup_temp_als_skeleton(als_arm, loaded_objects):
    for obj in loaded_objects:
        if obj is not None:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

# ---------------------------------------------------------------------------
# V5.3 Pose Solver: Kinematic Vector Alignment with Auto-Grounding & Pitch
# ---------------------------------------------------------------------------

ALIGN_CHAINS = [
    # Left Arm
    ("clavicle_l", "upperarm_l"),
    ("upperarm_l", "lowerarm_l"),
    ("lowerarm_l", "hand_l"),
    ("hand_l", "middle_01_l"),
    # Right Arm
    ("clavicle_r", "upperarm_r"),
    ("upperarm_r", "lowerarm_r"),
    ("lowerarm_r", "hand_r"),
    ("hand_r", "middle_01_r"),
    # Left Leg
    ("thigh_l", "calf_l"),
    ("calf_l", "foot_l"),
    # Right Leg
    ("thigh_r", "calf_r"),
    ("calf_r", "foot_r"),
]

for side in ["_l", "_r"]:
    for f in ["thumb", "index", "middle", "ring", "pinky"]:
        ALIGN_CHAINS.append((f"{f}_01{side}", f"{f}_02{side}"))
        ALIGN_CHAINS.append((f"{f}_02{side}", f"{f}_03{side}"))

def get_bone_direction(arm_obj, bone_name, child_name=None):
    pb = arm_obj.pose.bones.get(bone_name)
    if not pb:
        return None
        
    world_mat = arm_obj.matrix_world
    head_world = world_mat @ pb.head
    
    if child_name:
        child_pb = arm_obj.pose.bones.get(child_name)
        if not child_pb:
            return None
        target_world = world_mat @ child_pb.head
    else:
        target_world = world_mat @ pb.tail

    vec = (target_world - head_world)
    if vec.length < 0.0001:
        return None
    return vec.normalized()

def correct_foot_pitch(arm_obj, foot_name, ball_name, target_toe_z):
    """
    Iteratively rotates the foot around its local X-axis (pitch) until
    the toe (ball head) reaches the exact target Z-height.
    """
    pb_foot = arm_obj.pose.bones.get(foot_name)
    pb_ball = arm_obj.pose.bones.get(ball_name)
    if not pb_foot or not pb_ball:
        return
        
    world_mat = arm_obj.matrix_world
    
    for _ in range(10):
        bpy.context.view_layer.update()
        
        A = world_mat @ pb_foot.head
        T = world_mat @ pb_ball.head
        
        current_toe_z = T.z
        error_z = target_toe_z - current_toe_z
        
        if abs(error_z) < 0.0001:
            break
            
        V = T - A
        # The local X-axis of the foot bone in world space
        Axis = pb_foot.matrix.to_3x3() @ Vector((1, 0, 0))
        Axis.normalize()
        
        cross_z = Axis.cross(V).z
        
        # Avoid division by zero
        if abs(cross_z) < 0.0001:
            break
            
        theta = error_z / cross_z
        # Clamp theta to prevent wild spinning in a single iteration
        theta = max(min(theta, 0.5), -0.5)
        
        # Apply local X rotation to pitch the foot up/down
        q_rot = Quaternion(Vector((1, 0, 0)), theta)
        pb_foot.rotation_mode = 'QUATERNION'
        pb_foot.rotation_quaternion = pb_foot.rotation_quaternion @ q_rot

def solve_als_named_apose(arm_obj, als_arm):
    bpy.context.view_layer.objects.active = arm_obj
    if arm_obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    remove_all_bone_constraints(arm_obj)
    bpy.ops.object.mode_set(mode='POSE')

    # 1. Reset pose
    for pb in arm_obj.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)

    bpy.context.view_layer.update()
    
    # --- AUTO-GROUNDING PRE-CALCULATION ---
    foot_l = arm_obj.pose.bones.get("foot_l")
    ball_l = arm_obj.pose.bones.get("ball_l")
    ball_r = arm_obj.pose.bones.get("ball_r")
    
    z_before_ankle = None
    z_before_toe_l = None
    z_before_toe_r = None
    
    if foot_l and ball_l:
        z_before_ankle = (arm_obj.matrix_world @ foot_l.head).z
        z_before_toe_l = (arm_obj.matrix_world @ ball_l.head).z
        
    if ball_r:
        z_before_toe_r = (arm_obj.matrix_world @ ball_r.head).z
    # --------------------------------------

    matched = 0

    # 2. Iterate down the kinematic chains
    for parent_name, target_name in ALIGN_CHAINS:
        pb = arm_obj.pose.bones.get(parent_name)
        if not pb:
            continue

        v_als = get_bone_direction(als_arm, parent_name, target_name)
        if not v_als:
            continue

        v_g9 = get_bone_direction(arm_obj, parent_name, target_name)
        if not v_g9:
            continue

        q_diff = v_g9.rotation_difference(v_als)
        
        if q_diff.angle < 0.001:
            continue
            
        loc = pb.head.copy()
        R_mat = q_diff.to_matrix().to_4x4()
        
        M_current = pb.matrix.copy()
        M_new = Matrix.Translation(loc) @ R_mat @ Matrix.Translation(-loc) @ M_current
        
        pb.matrix = M_new
        matched += 1
        
        bpy.context.view_layer.update()

    # --- AUTO-GROUNDING POST-CALCULATION ---
    if z_before_ankle is not None:
        bpy.context.view_layer.update()
        z_after_ankle = (arm_obj.matrix_world @ foot_l.head).z
        delta_z = z_after_ankle - z_before_ankle
        
        pelvis = arm_obj.pose.bones.get("pelvis")
        if pelvis:
            loc, rot, scale = pelvis.matrix.decompose()
            loc.z -= delta_z
            pelvis.matrix = Matrix.LocRotScale(loc, rot, scale)
            bpy.context.view_layer.update()
            
    # --- AUTO-PITCH CORRECTION ---
    if z_before_toe_l is not None:
        correct_foot_pitch(arm_obj, "foot_l", "ball_l", z_before_toe_l)
    if z_before_toe_r is not None:
        correct_foot_pitch(arm_obj, "foot_r", "ball_r", z_before_toe_r)
    # -----------------------------

    bpy.ops.object.mode_set(mode='OBJECT')
    return matched

def fix_pelvis_location(arm_obj):
    """
    Mathematically translates the G9 pelvis in Edit Mode to match the precise
    Unreal Engine pivot point (horizontally aligned with the thighs),
    preventing the character from sinking during root motion.
    """
    from .. import config
    
    # Temporarily load ALS to extract exact mathematical offsets
    als_path = config.get_asset_path()
    try:
        als_arm, loaded_objs = load_als_skeleton_temp(als_path)
    except Exception as e:
        print(f"Pelvis fix failed to load ALS: {e}")
        return
        
    als_mat = als_arm.matrix_world
    als_p = als_arm.pose.bones.get("pelvis")
    als_tl = als_arm.pose.bones.get("thigh_l")
    als_tr = als_arm.pose.bones.get("thigh_r")
    
    if not (als_p and als_tl and als_tr):
        cleanup_temp_als_skeleton(als_arm, loaded_objs)
        return
        
    als_p_head = als_mat @ als_p.head
    als_mid = (als_mat @ als_tl.head + als_mat @ als_tr.head) / 2
    als_offset = als_p_head - als_mid
    
    # Calculate ALS thigh width for proportional scaling
    als_width = (als_mat @ als_tl.head - als_mat @ als_tr.head).length
    
    cleanup_temp_als_skeleton(als_arm, loaded_objs)
    
    # Now fix the G9 pelvis in Edit Mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    ebs = arm_obj.data.edit_bones
    p = ebs.get("pelvis")
    tl = ebs.get("thigh_l")
    tr = ebs.get("thigh_r")
    
    if p and tl and tr:
        daz_mat = arm_obj.matrix_world
        daz_inv = daz_mat.inverted()
        
        daz_tl_head = daz_mat @ tl.head
        daz_tr_head = daz_mat @ tr.head
        
        daz_mid = (daz_tl_head + daz_tr_head) / 2
        daz_width = (daz_tl_head - daz_tr_head).length
        
        # Scale the ALS offset by the difference in thigh width
        scale_factor = daz_width / als_width if als_width > 0.001 else 1.0
        scaled_offset = als_offset * scale_factor
        
        target_world_head = daz_mid + scaled_offset
        target_local_head = daz_inv @ target_world_head
        
        # Translate the pelvis bone without altering its orientation
        orig_vec = p.tail - p.head
        p.head = target_local_head
        p.tail = target_local_head + orig_vec
        
    bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------------------
# Shape Key Safe Baking (NumPy C-Speed)
# ---------------------------------------------------------------------------

def fast_bake_armature_with_shapekeys(context, mesh_obj, arm_obj):
    context.view_layer.objects.active = mesh_obj

    arm_mod = None
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object == arm_obj:
            arm_mod = mod
            break

    if not arm_mod:
        return

    other_mods_vis = {}
    for m in mesh_obj.modifiers:
        if m != arm_mod:
            other_mods_vis[m.name] = m.show_viewport
            m.show_viewport = False

    context.view_layer.update()

    if not mesh_obj.data.shape_keys or len(mesh_obj.data.shape_keys.key_blocks) <= 1:
        bpy.ops.object.modifier_apply(modifier=arm_mod.name)
        for m_name, vis in other_mods_vis.items():
            if m_name in mesh_obj.modifiers:
                mesh_obj.modifiers[m_name].show_viewport = vis
        return

    key_blocks = mesh_obj.data.shape_keys.key_blocks
    num_verts = len(mesh_obj.data.vertices)
    num_floats = num_verts * 3

    orig_basis_arr = np.empty(num_floats, dtype=np.float32)
    key_blocks[0].data.foreach_get('co', orig_basis_arr)

    sk_deltas = []
    temp_arr = np.empty(num_floats, dtype=np.float32)
    for sk in key_blocks[1:]:
        sk.data.foreach_get('co', temp_arr)
        sk_deltas.append((temp_arr - orig_basis_arr).copy())

    orig_values = [sk.value for sk in key_blocks]
    for sk in key_blocks:
        sk.value = 0.0

    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()

    new_basis_arr = np.empty(num_floats, dtype=np.float32)
    eval_mesh.vertices.foreach_get('co', new_basis_arr)
    eval_obj.to_mesh_clear()

    mesh_obj.data.vertices.foreach_set('co', new_basis_arr)
    key_blocks[0].data.foreach_set('co', new_basis_arr)

    for i, sk in enumerate(key_blocks[1:]):
        new_sk_coords = new_basis_arr + sk_deltas[i]
        sk.data.foreach_set('co', new_sk_coords)

    for sk, val in zip(key_blocks, orig_values):
        sk.value = val

    mesh_obj.modifiers.remove(arm_mod)

    for m_name, vis in other_mods_vis.items():
        if m_name in mesh_obj.modifiers:
            mesh_obj.modifiers[m_name].show_viewport = vis

# ---------------------------------------------------------------------------
# ALS Reference Data Extraction (Step 7)
# ---------------------------------------------------------------------------

def extract_als_bone_data(filepath):
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]

    arm = None
    for obj in data_to.objects:
        if obj and obj.type == 'ARMATURE':
            arm = obj
            break

    if not arm:
        raise ValueError(f"Could not find Armature object in {filepath}")

    als_data = {}
    for bone in arm.data.bones:
        als_data[bone.name] = {
            'matrix_local': bone.matrix_local.copy(),
            'parent': bone.parent.name if bone.parent else None,
        }

    for obj in data_to.objects:
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    return als_data

# ---------------------------------------------------------------------------
# Joint Snapping with Roll Lock (Step 7)
# ---------------------------------------------------------------------------

def snap_als_bone_to_daz(edit_bone, daz_head_w, armature_world_inv):
    """
    Translates the ALS bone to the Daz joint position while mathematically
    preserving the EXACT Unreal Engine bone vector (length and orientation).
    This guarantees that UE animations play perfectly without spaghetti twisting.
    """
    # Calculate target local position
    local_head = armature_world_inv @ daz_head_w
    
    # Preserve the EXACT Unreal Engine bone vector (maintaining perfect local rotation)
    orig_vector = edit_bone.tail - edit_bone.head
    
    # Translate the bone without rotating or scaling it
    edit_bone.head = local_head
    edit_bone.tail = local_head + orig_vector

def snap_als_skeleton_to_daz(als_armature_obj, daz_armature_obj, bone_mapping):
    if als_armature_obj.type != 'ARMATURE' or daz_armature_obj.type != 'ARMATURE':
        raise ValueError("Both objects must be armatures.")

    daz_bones = get_bone_world_positions(daz_armature_obj)
    als_inv_mat = als_armature_obj.matrix_world.inverted()

    bpy.context.view_layer.objects.active = als_armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = als_armature_obj.data.edit_bones

    snapped_count = 0

    for als_bone_name in bone_mapping.values():
        if als_bone_name in edit_bones and als_bone_name in daz_bones:
            eb = edit_bones[als_bone_name]
            daz_head_w, daz_tail_w, _ = daz_bones[als_bone_name]
            snap_als_bone_to_daz(eb, daz_head_w, als_inv_mat)
            snapped_count += 1

    snap_als_ik_bones(edit_bones)
    bpy.ops.object.mode_set(mode='OBJECT')
    return snapped_count

def snap_als_ik_bones(edit_bones):
    ik_map = {
        "ik_foot_l": "foot_l",
        "ik_foot_r": "foot_r",
        "ik_hand_l": "hand_l",
        "ik_hand_r": "hand_r",
        "ik_hand_gun": "hand_r",
    }
    for ik_name, src_name in ik_map.items():
        if src_name in edit_bones and ik_name in edit_bones:
            src = edit_bones[src_name]
            ik = edit_bones[ik_name]
            ik.head = src.head.copy()
            # Make the IK bone visually 50% larger to avoid overlapping in Blender,
            # while keeping its mathematical rotation (Y-axis direction) perfectly identical for UE.
            direction = src.tail - src.head
            ik.tail = src.head + (direction * 1.5)
            ik.roll = src.roll
