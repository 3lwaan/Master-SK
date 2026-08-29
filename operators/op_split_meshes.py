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
        return 0, 0
        
    import numpy as np
    
    existing_kbs = {kb.name: kb for kb in obj.data.shape_keys.key_blocks}
    basis = obj.data.shape_keys.key_blocks[0]
    v_count = len(basis.data)
    if v_count == 0:
        return 0, 0
        
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

def clean_body_shape_keys(body_obj):
    """
    Cleans the body shape keys by renaming them to AAA standards.
    Strips prefixes and applies professional naming conventions (e.g. Foot_PitchDown_L)
    Also permanently deletes any leftover drivers, as UE5 will use Pose Assets.
    """
    if not body_obj.data.shape_keys:
        return 0
        
    # Delete drivers from the body mesh shape keys
    if body_obj.data.shape_keys.animation_data:
        body_obj.data.shape_keys.animation_data_clear()

    # Explicitly delete neck flexes from body mesh
    keys_to_delete = []
    for sk in body_obj.data.shape_keys.key_blocks:
        if "NeckFlex" in sk.name or "FlexNeck" in sk.name:
            keys_to_delete.append(sk)
            
    for sk in keys_to_delete:
        body_obj.shape_key_remove(sk)

    # Apply x2 multiplier and -1 range
    basis = body_obj.data.shape_keys.key_blocks.get("Basis")
    if not basis:
        basis = body_obj.data.shape_keys.key_blocks[0]
        
    basis_co = [v.co.copy() for v in basis.data]
    
    for sk in body_obj.data.shape_keys.key_blocks:
        if sk == basis:
            continue
            
        sk.slider_min = -1.0
            
        # Multiply vertex coordinates by 2.0
        for i in range(len(sk.data)):
            delta = sk.data[i].co - basis_co[i]
            sk.data[i].co = basis_co[i] + (delta * 2.0)

    cleaned_count = 0
    for sk in body_obj.data.shape_keys.key_blocks:
        if sk.name == "Basis":
            continue

        # Clear invalid vertex group masks that were broken by renaming
        sk.vertex_group = ""

        # Map to AAA names
        original_name = sk.name
        # If the original name starts with body_bs_ or body_cbs_, we might need to strip it first to match the config
        # Wait, our config map uses keys like "body_cbs_foot_x45n_l", so we should check exactly.
        # But the map generator used "foot_x45n_l" and "FlexBicepsL".
        # Let's clean the prefix for the lookup.
        lookup_name = original_name
        if lookup_name.startswith("body_bs_"):
            lookup_name = lookup_name.replace("body_bs_", "")
        elif lookup_name.startswith("body_cbs_"):
            lookup_name = lookup_name.replace("body_cbs_", "")
            
        if lookup_name in config.JCM_AAA_NAMING_MAP:
            new_sk_name = config.JCM_AAA_NAMING_MAP[lookup_name]["new_name"]
            if new_sk_name == "DELETE_ME":
                # Do not rename, just mark for deletion later, or delete right now?
                # We can't delete while iterating. Mark original name for deletion!
                pass # it will just keep its original name and we delete it in the next loop
            else:
                sk.name = new_sk_name
            cleaned_count += 1
        else:
            # Fallback just strip prefixes if somehow missed
            if original_name.startswith("body_bs_"):
                sk.name = original_name.replace("body_bs_", "")
                cleaned_count += 1
            elif original_name.startswith("body_cbs_"):
                sk.name = original_name.replace("body_cbs_", "")
                cleaned_count += 1

    keys_to_delete_final = []
    for sk in body_obj.data.shape_keys.key_blocks:
        # Check if this shape key maps to DELETE_ME in config!
        original_name = sk.name
        lookup_name = original_name
        if lookup_name.startswith("body_bs_"):
            lookup_name = lookup_name.replace("body_bs_", "")
        elif lookup_name.startswith("body_cbs_"):
            lookup_name = lookup_name.replace("body_cbs_", "")
            
        if lookup_name in config.JCM_AAA_NAMING_MAP:
            if config.JCM_AAA_NAMING_MAP[lookup_name]["new_name"] == "DELETE_ME":
                keys_to_delete_final.append(sk)
                continue
                
        # Also check for exact string DELETE_ME just in case
        if "DELETE_ME" in sk.name:
            keys_to_delete_final.append(sk)
            
    for sk in keys_to_delete_final:
        body_obj.shape_key_remove(sk)

    return cleaned_count

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
        # 6. MOUTH MESH PREPARATION (No joining)
        # ---------------------------------------------------------------------
        mouth_obj = scene.mastersk_mouth_mesh
        if mouth_obj and mouth_obj.type == 'MESH':
            if mouth_obj.name not in context.view_layer.objects:
                try: context.collection.objects.link(mouth_obj)
                except: pass
            try: context.view_layer.active_layer_collection.collection.objects.link(mouth_obj)
            except: pass
                
            mouth_obj.hide_set(False)
            mouth_obj.hide_viewport = False
            
            mouth_mat_idx = -1
            teeth_mat_idx = -1
            for i, slot in enumerate(mouth_obj.material_slots):
                if slot.material:
                    name_lower = slot.material.name.lower()
                    if "mouth" in name_lower: mouth_mat_idx = i
                    elif "teeth" in name_lower: teeth_mat_idx = i
                        
            if mouth_mat_idx != -1 and teeth_mat_idx != -1:
                for poly in mouth_obj.data.polygons:
                    if poly.material_index == teeth_mat_idx:
                        poly.material_index = mouth_mat_idx
                
                bpy.ops.object.select_all(action='DESELECT')
                mouth_obj.select_set(True)
                context.view_layer.objects.active = mouth_obj
                mouth_obj.active_material_index = teeth_mat_idx
                bpy.ops.object.material_slot_remove()

            if mouth_obj.data.uv_layers.active:
                for loop in mouth_obj.data.loops:
                    current_u = mouth_obj.data.uv_layers.active.data[loop.index].uv[0]
                    mouth_obj.data.uv_layers.active.data[loop.index].uv[0] = (current_u % 1.0) + 1.0

        # ---------------------------------------------------------------------
        # 7. EYES MESH PREPARATION (No joining)
        # ---------------------------------------------------------------------
        eyes_obj = scene.mastersk_eyes_mesh
        if eyes_obj and eyes_obj.type == 'MESH':
            if eyes_obj.name not in context.view_layer.objects:
                try: context.collection.objects.link(eyes_obj)
                except: pass
            try: context.view_layer.active_layer_collection.collection.objects.link(eyes_obj)
            except: pass
                
            eyes_obj.hide_set(False)
            eyes_obj.hide_viewport = False
            
            import os
            import json
            import bmesh
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "eye_optimization_data.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as jf:
                    opt_data = json.load(jf)
                    
                context.view_layer.objects.active = eyes_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(eyes_obj.data)
                
                bm.faces.ensure_lookup_table()
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                
                faces_to_delete = []
                if "delete_face_indices" in opt_data:
                    for f_idx in opt_data["delete_face_indices"]:
                        if f_idx < len(bm.faces):
                            faces_to_delete.append(bm.faces[f_idx])
                            
                edges_to_dissolve = []
                if "dissolve_edge_vertex_pairs" in opt_data:
                    for v1_idx, v2_idx in opt_data["dissolve_edge_vertex_pairs"]:
                        if v1_idx < len(bm.verts) and v2_idx < len(bm.verts):
                            v1 = bm.verts[v1_idx]
                            v2 = bm.verts[v2_idx]
                            edge = bm.edges.get((v1, v2))
                            if edge:
                                # Ensure this edge doesn't belong to a face we are about to delete
                                if not any(f in faces_to_delete for f in edge.link_faces):
                                    edges_to_dissolve.append(edge)
                
                if edges_to_dissolve:
                    bmesh.ops.dissolve_edges(bm, edges=edges_to_dissolve, use_verts=True)
                    
                valid_faces = [f for f in faces_to_delete if f.is_valid]
                if valid_faces:
                    bmesh.ops.delete(bm, geom=valid_faces, context='FACES')
                    
                bmesh.update_edit_mesh(eyes_obj.data)
                bpy.ops.object.mode_set(mode='OBJECT')

            moisture_idx = -1
            eye_idx = -1
            
            for i, slot in enumerate(eyes_obj.material_slots):
                if not slot.material: continue
                name_lower = slot.material.name.lower()
                if "moisture" in name_lower: moisture_idx = i
                elif "eye" in name_lower or "sclera" in name_lower or "cornea" in name_lower:
                    eye_idx = i
                    
            # Scale Moisture Up by 1.05
            if moisture_idx != -1:
                context.view_layer.objects.active = eyes_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(eyes_obj.data)
                
                verts_to_scale = set()
                for f in bm.faces:
                    if f.material_index == moisture_idx:
                        for v in f.verts: verts_to_scale.add(v)
                        
                import mathutils
                left_eye_verts = []
                right_eye_verts = []
                
                for v in verts_to_scale:
                    if v.co.x > 0:
                        left_eye_verts.append(v)
                    else:
                        right_eye_verts.append(v)
                        
                if left_eye_verts:
                    center_l = sum((v.co for v in left_eye_verts), mathutils.Vector()) / len(left_eye_verts)
                    for v in left_eye_verts:
                        v.co = center_l + (v.co - center_l) * 1.05
                        
                if right_eye_verts:
                    center_r = sum((v.co for v in right_eye_verts), mathutils.Vector()) / len(right_eye_verts)
                    for v in right_eye_verts:
                        v.co = center_r + (v.co - center_r) * 1.05
                        
                bmesh.update_edit_mesh(eyes_obj.data)
                bpy.ops.object.mode_set(mode='OBJECT')
                
            if moisture_idx != -1 and eye_idx != -1:
                for poly in eyes_obj.data.polygons:
                    if poly.material_index == moisture_idx:
                        poly.material_index = eye_idx
                bpy.ops.object.select_all(action='DESELECT')
                eyes_obj.select_set(True)
                context.view_layer.objects.active = eyes_obj
                eyes_obj.active_material_index = moisture_idx
                bpy.ops.object.material_slot_remove()

            # Force all Eye UVs into the exact [2, 3] UDIM tile
            if eyes_obj.data.uv_layers.active:
                for loop in eyes_obj.data.loops:
                    current_u = eyes_obj.data.uv_layers.active.data[loop.index].uv[0]
                    eyes_obj.data.uv_layers.active.data[loop.index].uv[0] = (current_u % 1.0) + 2.0

        scene.mastersk_mesh_obj = body_obj
        scene.mastersk_body_mesh = body_obj
        scene.mastersk_head_mesh = head_obj
        scene.mastersk_daz_armature = body_arm

        self.report({'INFO'}, "Step 7 Complete: Geometry isolated and topology optimized safely.")
        scene.mastersk_progress_step = 8
        return {'FINISHED'}