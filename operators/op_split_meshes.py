# MasterSK - Step 7: Split Head & Body Meshes Operator
import bpy
from .. import config
from ..core import mesh_utils

def get_recursive_children(bone):
    children = list(bone.children)
    for c in bone.children:
        children.extend(get_recursive_children(c))
    return children

def clean_vertex_groups(mesh_obj, armature_obj):
    """Deletes vertex groups from mesh if the corresponding bone doesn't exist in armature."""
    if not mesh_obj or not armature_obj:
        return
        
    valid_bone_names = {b.name for b in armature_obj.data.bones}
    
    # We must iterate backwards or collect to list when deleting
    vgs_to_delete = []
    for vg in mesh_obj.vertex_groups:
        if vg.name not in valid_bone_names:
            vgs_to_delete.append(vg)
            
    for vg in vgs_to_delete:
        mesh_obj.vertex_groups.remove(vg)

def clean_empty_shape_keys(obj):
    """Deletes shape keys that have zero geometric effect on the remaining mesh vertices."""
    if not obj.data.shape_keys:
        return 0
    
    import numpy as np
    
    basis = obj.data.shape_keys.key_blocks[0]
    v_count = len(basis.data)
    if v_count == 0:
        return 0
        
    basis_co = np.zeros(v_count * 3, dtype=np.float32)
    basis.data.foreach_get("co", basis_co)
    target_co = np.zeros(v_count * 3, dtype=np.float32)
    
    removed_count = 0
    blocks = obj.data.shape_keys.key_blocks
    
    for i in range(len(blocks)-1, 0, -1):
        kb = blocks[i]
        kb.data.foreach_get("co", target_co)
        
        diff = np.abs(target_co - basis_co)
        if np.max(diff) < 0.0001:
            obj.shape_key_remove(kb)
            removed_count += 1
            
    return removed_count

def bake_arkit_shape_keys(obj):
    """Bakes Daz FACS shape keys into the 52 standard Apple ARKit shape keys and deletes the rest."""
    if not obj.data.shape_keys:
        return 0
        
    import numpy as np
    
    existing_kbs = {kb.name: kb for kb in obj.data.shape_keys.key_blocks}
    basis = obj.data.shape_keys.key_blocks[0]
    v_count = len(basis.data)
    if v_count == 0:
        return 0
        
    basis_co = np.zeros(v_count * 3, dtype=np.float32)
    basis.data.foreach_get("co", basis_co)
    
    # 1. Bake ARKit Keys
    baked_count = 0
    for arkit_name, facs_list in config.ARKIT_BAKING_MAP.items():
        if arkit_name in existing_kbs:
            continue # Already exists
            
        has_any = any(facs_name in existing_kbs for facs_name in facs_list)
        if not has_any:
            continue
            
        new_kb = obj.shape_key_add(name=arkit_name, from_mix=False)
        blended_co = np.copy(basis_co)
        
        for facs_name in facs_list:
            if facs_name in existing_kbs:
                source_kb = existing_kbs[facs_name]
                source_co = np.zeros(v_count * 3, dtype=np.float32)
                source_kb.data.foreach_get("co", source_co)
                # FACS fragments are additive
                blended_co += (source_co - basis_co)
                
        new_kb.data.foreach_set("co", blended_co)
        baked_count += 1
        
    # 2. Prune all non-ARKit keys (except Basis)
    deleted_count = 0
    blocks = obj.data.shape_keys.key_blocks
    for i in range(len(blocks)-1, 0, -1):
        kb = blocks[i]
        if kb.name not in config.ARKIT_BAKING_MAP:
            obj.shape_key_remove(kb)
            deleted_count += 1
            
    return baked_count, deleted_count

def clean_body_shape_keys(obj):
    """Strips Daz prefixes from body JCMs."""
    if not obj.data.shape_keys:
        return 0
        
    renamed = 0
    for kb in obj.data.shape_keys.key_blocks:
        old_name = kb.name
        if kb.name.startswith("body_bs_"):
            kb.name = kb.name.replace("body_bs_", "")
        elif kb.name.startswith("body_cbs_"):
            kb.name = kb.name.replace("body_cbs_", "")
            
        if old_name != kb.name:
            renamed += 1
            
    return renamed

class MASTERSK_OT_split_meshes(bpy.types.Operator):
    """Step 7: Separate the character mesh and rig into Head and Body components"""
    bl_idname = "mastersk.split_meshes"
    bl_label = "Step 7: Split Head & Body Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mesh_obj = scene.mastersk_mesh_obj
        arm_obj = scene.mastersk_daz_armature

        if not mesh_obj or mesh_obj.type != 'MESH':
            bpy.ops.mastersk.auto_detect()
            mesh_obj = scene.mastersk_mesh_obj
            arm_obj = scene.mastersk_daz_armature

        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Mesh object.")
            return {'CANCELLED'}
            
        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Armature object.")
            return {'CANCELLED'}

        # ---------------------------------------------------------------------
        # 1. OPTIMIZE MATERIALS & UVS
        # ---------------------------------------------------------------------
        try:
            mesh_utils.optimize_materials_and_uvs(mesh_obj)
        except Exception as e:
            self.report({'WARNING'}, f"Material/UV optimization failed: {e}")

        # ---------------------------------------------------------------------
        # 2. SPLIT MESHES
        # ---------------------------------------------------------------------
        # Save original character name before splitting
        original_mesh_name = mesh_obj.name
        
        try:
            body_obj, head_obj = mesh_utils.split_mesh_by_materials(
                mesh_obj,
                config.HEAD_MATERIAL_KEYWORDS,
                config.BODY_MATERIAL_KEYWORDS
            )
        except Exception as e:
            self.report({'ERROR'}, f"Failed to split meshes: {str(e)}")
            return {'CANCELLED'}
            
        # Rename meshes dynamically using original character name
        body_obj.name = f"{original_mesh_name}_Body_Mesh"
        head_obj.name = f"{original_mesh_name}_Head_Mesh"

        # ---------------------------------------------------------------------
        # 2. SPLIT ARMATURES
        # ---------------------------------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        context.view_layer.objects.active = arm_obj
        
        # Duplicate armature for the head
        bpy.ops.object.duplicate(linked=False)
        head_arm = context.active_object
        head_arm.name = "G9_Head_Armature"
        
        # Original armature becomes body
        arm_obj.name = "G9_Body_Armature"
        body_arm = arm_obj

        # ---------------------------------------------------------------------
        # 3. PRUNE HEAD ARMATURE (Keep Spine, Clavicle, Face. Delete Limbs)
        # ---------------------------------------------------------------------
        context.view_layer.objects.active = head_arm
        bpy.ops.object.mode_set(mode='EDIT')
        
        bones_to_delete = []
        # Target top-level limb bones
        limb_roots = ["thigh_l", "thigh_r", "lowerarm_l", "lowerarm_r", "l_pectoral", "r_pectoral", "l_pectoral(drv)", "r_pectoral(drv)"]
        
        for root_name in limb_roots:
            b = head_arm.data.edit_bones.get(root_name)
            if b:
                bones_to_delete.append(b)
                bones_to_delete.extend(get_recursive_children(b))
                
        # Unique list and delete
        bones_to_delete = list(set(bones_to_delete))
        for b in bones_to_delete:
            head_arm.data.edit_bones.remove(b)
            
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # ---------------------------------------------------------------------
        # 4. PRUNE BODY ARMATURE (Keep Body. Delete Face)
        # ---------------------------------------------------------------------
        context.view_layer.objects.active = body_arm
        bpy.ops.object.mode_set(mode='EDIT')
        
        bones_to_delete = []
        head_bone = body_arm.data.edit_bones.get("head")
        if head_bone:
            # Delete all children of head, but KEEP the head bone itself
            bones_to_delete.extend(get_recursive_children(head_bone))
            
        bones_to_delete = list(set(bones_to_delete))
        for b in bones_to_delete:
            body_arm.data.edit_bones.remove(b)
            
        bpy.ops.object.mode_set(mode='OBJECT')

        # ---------------------------------------------------------------------
        # 5. RE-LINK ARMATURE MODIFIERS
        # ---------------------------------------------------------------------
        # Head Mesh -> Head Armature
        for mod in head_obj.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = head_arm
                
        # Body Mesh -> Body Armature
        for mod in body_obj.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = body_arm

        # ---------------------------------------------------------------------
        # 6. CLEAN VERTEX GROUPS
        # ---------------------------------------------------------------------
        clean_vertex_groups(head_obj, head_arm)
        clean_vertex_groups(body_obj, body_arm)

        # ---------------------------------------------------------------------
        # 7. CLEAN AND BAKE SHAPE KEYS
        # ---------------------------------------------------------------------
        # Empty cleaner ensures body JCMs are purged from head, and FACS from body
        clean_empty_shape_keys(head_obj)
        clean_empty_shape_keys(body_obj)
        
        # Bake ARKit for Head, Rename JCMs for Body
        baked, deleted = bake_arkit_shape_keys(head_obj)
        renamed = clean_body_shape_keys(body_obj)

        # Update scene variables
        scene.mastersk_mesh_obj = body_obj
        scene.mastersk_body_mesh = body_obj
        scene.mastersk_head_mesh = head_obj
        scene.mastersk_daz_armature = body_arm

        self.report({'INFO'}, f"Step 7 Complete: Baked {baked} ARKit keys, Purged {deleted} FACS keys, Renamed {renamed} JCMs.")
        scene.mastersk_progress_step = 8
        return {'FINISHED'}
