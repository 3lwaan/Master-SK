import bpy
import mathutils
import fnmatch

class ArmatureModeGuard:
    """
    Context manager to safely switch object modes and restore original context/mode on exit,
    even if an exception occurs.
    """
    def __init__(self, target_obj, target_mode='EDIT'):
        self.target_obj = target_obj
        self.target_mode = target_mode
        self.original_active = None
        self.original_mode = 'OBJECT'

    def __enter__(self):
        if bpy.context.view_layer:
            self.original_active = bpy.context.view_layer.objects.active
        if bpy.context.object:
            self.original_mode = bpy.context.object.mode

        if self.target_obj and bpy.context.view_layer:
            self.target_obj.hide_set(False)
            self.target_obj.select_set(True)
            bpy.context.view_layer.objects.active = self.target_obj
            if self.target_obj.mode != self.target_mode:
                bpy.ops.object.mode_set(mode=self.target_mode)
        return self.target_obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.target_obj and self.target_obj.name in bpy.data.objects:
                if self.target_obj.mode != self.original_mode:
                    bpy.ops.object.mode_set(mode='OBJECT')
            if self.original_active and self.original_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = self.original_active
        except Exception as e:
            print(f"[MasterSK ModeGuard] Exception during mode restoration: {e}")
        return False


def validate_selection(context):
    """
    Validates that both a DAZ Armature (ARMATURE) and associated Character Mesh (MESH) are selected.
    Returns tuple: (armature_obj, list_of_mesh_objs, error_message)
    """
    selected = context.selected_objects
    if not selected:
        return None, [], "No objects selected. Please select your DAZ Armature and Character Mesh."

    armature_obj = None
    mesh_objs = []

    for obj in selected:
        if obj.type == 'ARMATURE':
            if armature_obj is None:
                armature_obj = obj
            else:
                return None, [], "Multiple Armatures selected. Please select only ONE DAZ Armature."
        elif obj.type == 'MESH':
            mesh_objs.append(obj)

    if not armature_obj:
        return None, [], "No Armature object selected. Please select a DAZ Armature."

    if not mesh_objs:
        for child in armature_obj.children:
            if child.type == 'MESH' and child not in mesh_objs:
                mesh_objs.append(child)

    if not mesh_objs:
        return None, [], "No Character Mesh object selected or associated with the Armature."

    return armature_obj, mesh_objs, ""


def apply_transforms(armature_obj, mesh_objs):
    """
    Applies location, rotation, and scale transforms to the armature and mesh objects.
    """
    objects_to_apply = [armature_obj] + mesh_objs
    orig_active = bpy.context.view_layer.objects.active
    
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')

    for obj in objects_to_apply:
        if obj and obj.name in bpy.data.objects:
            obj.hide_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            obj.select_set(False)

    if orig_active:
        bpy.context.view_layer.objects.active = orig_active
        orig_active.select_set(True)


def rename_armature_and_datablock(armature_obj, mesh_objs):
    """
    1. Armature Object Name (Orange Icon): Renames to 'SKM_' + mesh_name (e.g. 'SKM Nina' / 'SKM_Nina').
    2. Armature Data Block Name (Green Icon): Renames armature.data.name directly to 'root'.
       Frees up conflicting datablocks in bpy.data.armatures so the active datablock receives the exact name 'root'.
    """
    if mesh_objs:
        mesh_name = mesh_objs[0].name.replace(".001", "").strip()
        if not mesh_name.startswith("SKM_") and not mesh_name.startswith("SKM "):
            target_obj_name = f"SKM_{mesh_name}"
        else:
            target_obj_name = mesh_name
        armature_obj.name = target_obj_name

    # Free up 'root' name in bpy.data.armatures if another datablock holds it
    current_data = armature_obj.data
    for other_arm in list(bpy.data.armatures):
        if other_arm != current_data and other_arm.name in ["root", "root.001", "root.002", "root.003"]:
            if other_arm.users == 0:
                try:
                    bpy.data.armatures.remove(other_arm)
                except Exception:
                    other_arm.name = f"old_{other_arm.name}"
            else:
                other_arm.name = f"old_{other_arm.name}"

    current_data.name = "root"


def purge_all_bone_collections(armature_obj):
    """
    Completely wipes/clears all bone collections from armature.data.collections (Blender 4.4+).
    Ensures bone list is completely un-grouped and clean.
    """
    arm_data = armature_obj.data
    if hasattr(arm_data, "collections"):
        while arm_data.collections:
            arm_data.collections.remove(arm_data.collections[0])


def merge_hip_weights_to_pelvis(mesh_objs):
    """
    Merges vertex group weights from 'hip' into 'pelvis' on all mesh objects
    before deleting the 'hip' bone, preventing weight paint skinning issues.
    """
    for mesh_obj in mesh_objs:
        if not mesh_obj or mesh_obj.type != 'MESH':
            continue

        vgroups = mesh_obj.vertex_groups
        hip_vg = vgroups.get("hip")
        if not hip_vg:
            continue

        pelvis_vg = vgroups.get("pelvis")
        if not pelvis_vg:
            hip_vg.name = "pelvis"
            continue

        # Both hip and pelvis vertex groups exist: merge hip weights into pelvis
        mesh_data = mesh_obj.data
        for v in mesh_data.vertices:
            hip_w = 0.0
            pelvis_w = 0.0
            for g in v.groups:
                if g.group == hip_vg.index:
                    hip_w = g.weight
                elif g.group == pelvis_vg.index:
                    pelvis_w = g.weight

            if hip_w > 0.0:
                combined_w = min(1.0, hip_w + pelvis_w)
                pelvis_vg.add([v.index], combined_w, 'REPLACE')
                hip_vg.remove([v.index])

        try:
            vgroups.remove(hip_vg)
        except Exception as e:
            print(f"[MasterSK] Could not remove hip vertex group: {e}")


def purge_bones_and_restructure_hierarchy(armature_obj, reference_data):
    """
    Step 2 Rig Processing (Edit Mode):
    - Deletes 'root', 'hip', anchor bones, and driven bones (*(drv)*).
    - Top-level deformation bone is 'pelvis' (parent is None).
    """
    daz_map = reference_data.get("DAZ_TO_MASTER_MAP", {})
    hierarchy = reference_data.get("MASTER_SK_HIERARCHY", {})
    bones_to_delete_list = reference_data.get("BONES_TO_DELETE", [])

    with ArmatureModeGuard(armature_obj, 'EDIT'):
        edit_bones = armature_obj.data.edit_bones

        # 1. Delete physical 'root' / 'Root' / 'hip' bones and explicitly marked anchor/driven bones
        explicit_delete = set(bones_to_delete_list) | {"root", "Root", "hip", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"}
        
        for eb in list(edit_bones):
            b_name = eb.name
            b_name_lower = b_name.lower()
            
            if b_name in explicit_delete or b_name_lower in ["root", "hip", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"]:
                edit_bones.remove(eb)
            elif "(drv)" in b_name_lower or fnmatch.fnmatch(b_name_lower, "*(drv)*"):
                edit_bones.remove(eb)

        # 2. Perform bone mapping & renaming for remaining bones cleanly
        for eb in list(edit_bones):
            orig_name = eb.name
            if orig_name in daz_map:
                target_name = daz_map[orig_name]
                if orig_name != target_name:
                    if target_name in edit_bones and edit_bones[target_name] != eb:
                        edit_bones.remove(edit_bones[target_name])
                    eb.name = target_name

        # 3. Ensure pelvis is top-level (parent is None)
        pelvis_eb = edit_bones.get("pelvis")
        if pelvis_eb:
            pelvis_eb.parent = None

        # 4. Restructure remaining bones according to MASTER_SK_HIERARCHY with fallback handling
        for child_target, parent_target in hierarchy.items():
            child_eb = edit_bones.get(child_target)
            if child_eb:
                if parent_target is None:
                    child_eb.parent = None
                else:
                    parent_eb = edit_bones.get(parent_target)
                    
                    # Smart fallbacks if specific optional parent bone is absent
                    if not parent_eb:
                        if parent_target.startswith("indexmetacarpal"):
                            parent_eb = edit_bones.get("hand_l" if parent_target.endswith("_l") else "hand_r")
                        elif parent_target.startswith("midmetacarpal"):
                            parent_eb = edit_bones.get("hand_l" if parent_target.endswith("_l") else "hand_r")
                        elif parent_target.startswith("ringmetacarpal"):
                            parent_eb = edit_bones.get("hand_l" if parent_target.endswith("_l") else "hand_r")
                        elif parent_target.startswith("pinkymetacarpal"):
                            parent_eb = edit_bones.get("hand_l" if parent_target.endswith("_l") else "hand_r")
                        elif parent_target == "neck02":
                            parent_eb = edit_bones.get("neck01")
                        elif parent_target == "spine_04":
                            parent_eb = edit_bones.get("spine_03")

                    if parent_eb and parent_eb != child_eb:
                        child_eb.parent = parent_eb


def sync_bone_and_vertex_group_names(armature_obj, mesh_objs, reference_data):
    """
    Renames armature edit bones to Master SK names and concurrently syncs vertex groups on mesh objects.
    Deletes orphaned vertex groups and purges zero-weight vertex assignments.
    """
    daz_map = reference_data.get("DAZ_TO_MASTER_MAP", {})
    bones_to_delete_list = reference_data.get("BONES_TO_DELETE", [])
    deleted_names = set(bones_to_delete_list) | {"root", "Root", "hip", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"}

    all_armature_bone_names = set(b.name for b in armature_obj.data.bones)

    for mesh_obj in mesh_objs:
        if not mesh_obj or mesh_obj.name not in bpy.data.objects or mesh_obj.type != 'MESH':
            continue

        vgroups = mesh_obj.vertex_groups
        groups_to_remove = []

        for vg in list(vgroups):
            vg_name = vg.name
            vg_name_lower = vg_name.lower()

            is_deleted = (
                vg_name in deleted_names or
                vg_name_lower in ["root", "hip", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"] or
                "(drv)" in vg_name_lower or
                fnmatch.fnmatch(vg_name_lower, "*(drv)*")
            )

            if is_deleted:
                groups_to_remove.append(vg)
                continue

            if vg_name in daz_map:
                new_vg_name = daz_map[vg_name]
                vg.name = new_vg_name

            if vg.name not in all_armature_bone_names:
                groups_to_remove.append(vg)

        for vg in groups_to_remove:
            try:
                vgroups.remove(vg)
            except Exception as e:
                print(f"[MasterSK] Error removing vertex group '{vg.name}': {e}")

        purge_zero_weight_assignments(mesh_obj)


def purge_zero_weight_assignments(mesh_obj, threshold=0.0001):
    """
    Iterates through mesh vertices and removes vertex group assignments with weight <= threshold.
    """
    if not mesh_obj or mesh_obj.type != 'MESH':
        return

    mesh_data = mesh_obj.data
    vgroups = mesh_obj.vertex_groups

    if not vgroups:
        return

    for v in mesh_data.vertices:
        for g in list(v.groups):
            if g.weight <= threshold:
                try:
                    vgroup = vgroups[g.group]
                    vgroup.remove([v.index])
                except Exception:
                    pass


def inject_ue5_als_ik_bones(armature_obj):
    """
    Step 3 Operator Logic:
    - Root IK Bones (ik_foot_root, ik_hand_root):
        Head: (0.0, 0.0, 0.0), Tail: (0.0, 0.0, 0.2), length = 0.2 meters.
        Parent: None (Top-level IK roots, no physical root edit bone).
    - Foot IK Bones (ik_foot_l, ik_foot_r):
        Snap head to foot_l/r.head, copy matrix, length = target_foot_bone.length (or 0.15).
        Parent: ik_foot_root.
    - Hand IK Bones (ik_hand_l, ik_hand_r):
        Snap head to hand_l/r.head, copy matrix, length = target_hand_bone.length (or 0.15).
        Parent: ik_hand_root.
    """
    with ArmatureModeGuard(armature_obj, 'EDIT'):
        edit_bones = armature_obj.data.edit_bones

        def get_or_create_bone(name):
            if name in edit_bones:
                return edit_bones[name]
            return edit_bones.new(name)

        # 0. Ensure physical 'root' / 'Root' edit bone is deleted if present
        for r_name in ["root", "Root"]:
            if r_name in edit_bones:
                edit_bones.remove(edit_bones[r_name])

        # 1. Root IK Bones (ik_foot_root, ik_hand_root - Top-Level)
        ik_foot_root = get_or_create_bone("ik_foot_root")
        ik_foot_root.head = (0.0, 0.0, 0.0)
        ik_foot_root.tail = (0.0, 0.0, 0.2)
        ik_foot_root.length = 0.2
        ik_foot_root.parent = None

        ik_hand_root = get_or_create_bone("ik_hand_root")
        ik_hand_root.head = (0.0, 0.0, 0.0)
        ik_hand_root.tail = (0.0, 0.0, 0.2)
        ik_hand_root.length = 0.2
        ik_hand_root.parent = None

        # 2. Foot IK Bones (ik_foot_l, ik_foot_r)
        foot_l = edit_bones.get("foot_l") or edit_bones.get("l_foot")
        ik_foot_l = get_or_create_bone("ik_foot_l")
        ik_foot_l.parent = ik_foot_root
        if foot_l:
            ik_foot_l.head = foot_l.head.copy()
            ik_foot_l.matrix = foot_l.matrix.copy()
            ik_foot_l.length = max(0.12, foot_l.length)
        else:
            ik_foot_l.head = (0.2, 0.0, 0.1)
            ik_foot_l.tail = (0.2, 0.0, 0.25)
            ik_foot_l.length = 0.15

        foot_r = edit_bones.get("foot_r") or edit_bones.get("r_foot")
        ik_foot_r = get_or_create_bone("ik_foot_r")
        ik_foot_r.parent = ik_foot_root
        if foot_r:
            ik_foot_r.head = foot_r.head.copy()
            ik_foot_r.matrix = foot_r.matrix.copy()
            ik_foot_r.length = max(0.12, foot_r.length)
        else:
            ik_foot_r.head = (-0.2, 0.0, 0.1)
            ik_foot_r.tail = (-0.2, 0.0, 0.25)
            ik_foot_r.length = 0.15

        # 3. Hand IK Bones (ik_hand_l, ik_hand_r)
        hand_l = edit_bones.get("hand_l") or edit_bones.get("l_hand")
        ik_hand_l = get_or_create_bone("ik_hand_l")
        ik_hand_l.parent = ik_hand_root
        if hand_l:
            ik_hand_l.head = hand_l.head.copy()
            ik_hand_l.matrix = hand_l.matrix.copy()
            ik_hand_l.length = max(0.15, hand_l.length)
        else:
            ik_hand_l.head = (0.6, 0.0, 1.4)
            ik_hand_l.tail = (0.6, 0.0, 1.55)
            ik_hand_l.length = 0.15

        hand_r = edit_bones.get("hand_r") or edit_bones.get("r_hand")
        ik_hand_r = get_or_create_bone("ik_hand_r")
        ik_hand_r.parent = ik_hand_root
        if hand_r:
            ik_hand_r.head = hand_r.head.copy()
            ik_hand_r.matrix = hand_r.matrix.copy()
            ik_hand_r.length = max(0.15, hand_r.length)
        else:
            ik_hand_r.head = (-0.6, 0.0, 1.4)
            ik_hand_r.tail = (-0.6, 0.0, 1.55)
            ik_hand_r.length = 0.15
