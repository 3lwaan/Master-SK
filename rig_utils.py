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
    """
    if mesh_objs:
        mesh_name = mesh_objs[0].name.replace(".001", "").strip()
        if not mesh_name.startswith("SKM_") and not mesh_name.startswith("SKM "):
            target_obj_name = f"SKM_{mesh_name}"
        else:
            target_obj_name = mesh_name
        armature_obj.name = target_obj_name

    armature_obj.data.name = "root"


def purge_all_bone_collections(armature_obj):
    """
    Completely wipes/clears all bone collections from armature.data.collections (Blender 4.4+).
    Ensures bone list is completely un-grouped and clean.
    """
    arm_data = armature_obj.data
    if hasattr(arm_data, "collections"):
        while arm_data.collections:
            arm_data.collections.remove(arm_data.collections[0])


def purge_bones_and_restructure_hierarchy(armature_obj, reference_data):
    """
    Step 2 Rig Processing (Edit Mode):
    - Purges extra physical 'root' bone, anchor bones, and driven bones (*(drv)*).
    - Resolves 'pelvis_temp_conflict': deletes pre-existing helper 'pelvis' or 'root' bones first before renaming 'hip' -> 'pelvis'.
    - Restructures hierarchy per MASTER_SK_HIERARCHY:
      - Top-level bone is 'pelvis' (parent is None).
      - spine_04 is parent of neck01, clavicle_l, clavicle_r, pectoral_l, pectoral_r.
      - Metacarpals are parented to hand_l/hand_r, and finger 01 bones parented to metacarpals.
    """
    daz_map = reference_data.get("DAZ_TO_MASTER_MAP", {})
    hierarchy = reference_data.get("MASTER_SK_HIERARCHY", {})
    bones_to_delete_list = reference_data.get("BONES_TO_DELETE", [])

    with ArmatureModeGuard(armature_obj, 'EDIT'):
        edit_bones = armature_obj.data.edit_bones

        # 1. First, delete physical 'root' / 'Root' bones and explicitly marked bones
        explicit_delete = set(bones_to_delete_list) | {"root", "Root", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"}
        
        for eb in list(edit_bones):
            b_name = eb.name
            b_name_lower = b_name.lower()
            
            if b_name in explicit_delete or b_name_lower in ["root", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"]:
                edit_bones.remove(eb)
            elif "(drv)" in b_name_lower or fnmatch.fnmatch(b_name_lower, "*(drv)*"):
                edit_bones.remove(eb)

        # 2. Resolve pelvis_temp_conflict:
        hip_bone = edit_bones.get("hip")
        pre_pelvis = edit_bones.get("pelvis")
        
        if hip_bone and pre_pelvis and pre_pelvis != hip_bone:
            edit_bones.remove(pre_pelvis)

        if hip_bone:
            hip_bone.name = "pelvis"

        # 3. Perform bone mapping & renaming for remaining bones cleanly
        for eb in list(edit_bones):
            orig_name = eb.name
            if orig_name in daz_map:
                target_name = daz_map[orig_name]
                if orig_name != target_name:
                    if target_name in edit_bones and edit_bones[target_name] != eb:
                        edit_bones.remove(edit_bones[target_name])
                    eb.name = target_name

        # 4. Enforce Top-Level Hierarchy Rules
        pelvis_eb = edit_bones.get("pelvis")
        if pelvis_eb:
            pelvis_eb.parent = None

        # 5. Restructure remaining bones according to MASTER_SK_HIERARCHY with fallback handling
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
    deleted_names = set(bones_to_delete_list) | {"root", "Root", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"}

    all_armature_bone_names = set(b.name for b in armature_obj.data.bones)

    for mesh_obj in mesh_objs:
        if not mesh_obj or mesh_obj.name not in bpy.data.objects or mesh_obj.type != 'MESH':
            continue

        vgroups = mesh_obj.vertex_groups
        groups_to_remove = []

        for vg in list(vgroups):
            vg_name = vg.name
            vg_name_lower = vg_name.lower()

            # Check if this group corresponds to a deleted bone or driven pattern
            is_deleted = (
                vg_name in deleted_names or
                vg_name_lower in ["root", "l_hand_anchor", "r_hand_anchor", "l_foot_anchor", "r_foot_anchor"] or
                "(drv)" in vg_name_lower or
                fnmatch.fnmatch(vg_name_lower, "*(drv)*")
            )

            if is_deleted:
                groups_to_remove.append(vg)
                continue

            # Rename matching vertex groups
            if vg_name in daz_map:
                new_vg_name = daz_map[vg_name]
                vg.name = new_vg_name

            # Re-check updated group name against active bones
            if vg.name not in all_armature_bone_names:
                groups_to_remove.append(vg)

        # Remove orphaned vertex groups
        for vg in groups_to_remove:
            try:
                vgroups.remove(vg)
            except Exception as e:
                print(f"[MasterSK] Error removing vertex group '{vg.name}': {e}")

        # Purge Zero-Weight Vertex Assignments
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
    - Creates UE5 / ALS standard top-level IK bones (parent is None):
      ik_foot_root -> Parent: None (Top-level bone)
      ik_foot_l    -> Parent: ik_foot_root (Snaps matrix to foot_l, roll offset 0 deg)
      ik_foot_r    -> Parent: ik_foot_root (Snaps matrix to foot_r, roll offset 0 deg)
      ik_hand_root -> Parent: None (Top-level bone)
      ik_hand_l    -> Parent: ik_hand_root (Snaps matrix to hand_l, roll offset 0 deg)
      ik_hand_r    -> Parent: ik_hand_root (Snaps matrix to hand_r, roll offset 0 deg)
    """
    with ArmatureModeGuard(armature_obj, 'EDIT'):
        edit_bones = armature_obj.data.edit_bones

        def get_or_create_bone(name):
            if name in edit_bones:
                return edit_bones[name]
            return edit_bones.new(name)

        # 1. Foot IK Hierarchy (Top-level root)
        ik_foot_root = get_or_create_bone("ik_foot_root")
        ik_foot_root.head = (0.0, 0.0, 0.0)
        ik_foot_root.tail = (0.0, 0.2, 0.0)
        ik_foot_root.roll = 0.0
        ik_foot_root.parent = None

        # ik_foot_l
        foot_l = edit_bones.get("foot_l") or edit_bones.get("l_foot")
        ik_foot_l = get_or_create_bone("ik_foot_l")
        ik_foot_l.parent = ik_foot_root
        if foot_l:
            ik_foot_l.head = foot_l.head.copy()
            ik_foot_l.tail = foot_l.tail.copy()
            ik_foot_l.matrix = foot_l.matrix.copy()
        else:
            ik_foot_l.head = (0.2, 0.0, 0.1)
            ik_foot_l.tail = (0.2, 0.2, 0.1)
        ik_foot_l.roll = 0.0

        # ik_foot_r
        foot_r = edit_bones.get("foot_r") or edit_bones.get("r_foot")
        ik_foot_r = get_or_create_bone("ik_foot_r")
        ik_foot_r.parent = ik_foot_root
        if foot_r:
            ik_foot_r.head = foot_r.head.copy()
            ik_foot_r.tail = foot_r.tail.copy()
            ik_foot_r.matrix = foot_r.matrix.copy()
        else:
            ik_foot_r.head = (-0.2, 0.0, 0.1)
            ik_foot_r.tail = (-0.2, 0.2, 0.1)
        ik_foot_r.roll = 0.0

        # 2. Hand IK Hierarchy (Top-level root)
        ik_hand_root = get_or_create_bone("ik_hand_root")
        ik_hand_root.head = (0.0, 0.0, 0.0)
        ik_hand_root.tail = (0.0, 0.2, 0.0)
        ik_hand_root.roll = 0.0
        ik_hand_root.parent = None

        # ik_hand_l
        hand_l = edit_bones.get("hand_l") or edit_bones.get("l_hand")
        ik_hand_l = get_or_create_bone("ik_hand_l")
        ik_hand_l.parent = ik_hand_root
        if hand_l:
            ik_hand_l.head = hand_l.head.copy()
            ik_hand_l.tail = hand_l.tail.copy()
            ik_hand_l.matrix = hand_l.matrix.copy()
        else:
            ik_hand_l.head = (0.6, 0.0, 1.4)
            ik_hand_l.tail = (0.6, 0.2, 1.4)
        ik_hand_l.roll = 0.0

        # ik_hand_r
        hand_r = edit_bones.get("hand_r") or edit_bones.get("r_hand")
        ik_hand_r = get_or_create_bone("ik_hand_r")
        ik_hand_r.parent = ik_hand_root
        if hand_r:
            ik_hand_r.head = hand_r.head.copy()
            ik_hand_r.tail = hand_r.tail.copy()
            ik_hand_r.matrix = hand_r.matrix.copy()
        else:
            ik_hand_r.head = (-0.6, 0.0, 1.4)
            ik_hand_r.tail = (-0.6, 0.2, 1.4)
        ik_hand_r.roll = 0.0
