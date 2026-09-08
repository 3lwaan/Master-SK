import bpy
import os
import json
import bmesh
import mathutils
from .. import config
from ..core import mesh_utils
from .op_split_meshes import clean_body_shape_keys, clean_empty_shape_keys, bake_arkit_shape_keys

class MASTERSK_OT_unified_optimize(bpy.types.Operator):
    """Step 7: Optimize geometry, shift UVs, and join into a single unified mesh"""
    bl_idname = "mastersk.unified_optimize"
    bl_label = "Step 7: Optimize & Join Unified Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mesh_obj = scene.mastersk_mesh_obj
        mouth_obj = scene.mastersk_mouth_mesh
        eyes_obj = scene.mastersk_eyes_mesh
        arm_obj = scene.mastersk_daz_armature

        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Mesh object.")
            return {'CANCELLED'}

        # ---------------------------------------------------------------------
        # 1. OPTIMIZE MATERIALS & UVS ON MAIN MESH (CUSTOM UNIFIED)
        # ---------------------------------------------------------------------
        try:
            # First, clean unused slots
            mesh_utils.clean_unused_material_slots(mesh_obj)
            
            # Identify indices
            head_idx, arms_idx = -1, -1
            mouth_indices, nail_indices = set(), set()
            for i, slot in enumerate(mesh_obj.material_slots):
                if not slot.material: continue
                name = slot.material.name.lower()
                if "head" in name or "face" in name: head_idx = i
                elif "arm" in name: arms_idx = i
                elif "mouth" in name or "cavity" in name: mouth_indices.add(i)
                elif "nail" in name: nail_indices.add(i)
                
            import json
            uv_data = {}
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "nail_uv_data.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as jf:
                    try: uv_data = {int(k): v for k, v in json.load(jf).items()}
                    except: pass

            mesh = mesh_obj.data
            uv_layer = mesh.uv_layers.active
            for poly in mesh.polygons:
                if poly.material_index in mouth_indices and head_idx != -1:
                    poly.material_index = head_idx
                elif poly.material_index in nail_indices and arms_idx != -1:
                    poly.material_index = arms_idx
                    if uv_layer and uv_data:
                        for loop_idx in poly.loop_indices:
                            if loop_idx in uv_data:
                                uv_layer.data[loop_idx].uv = uv_data[loop_idx]
                    
            mesh_utils.clean_unused_material_slots(mesh_obj)
            
            # UDIM Shift for UNIFIED mesh
            # Head: [0,0], Body: [1,0], Legs: [2,0], Arms: [3,0]
            uv_layer = mesh.uv_layers.active
            if uv_layer:
                for poly in mesh.polygons:
                    mat_idx = poly.material_index
                    if mat_idx >= len(mesh_obj.material_slots) or not mesh_obj.material_slots[mat_idx].material:
                        continue
                        
                    mat_name = mesh_obj.material_slots[mat_idx].material.name.lower()
                    shift_x = 0.0
                    if "body" in mat_name or "torso" in mat_name: shift_x = 1.0
                    elif "leg" in mat_name: shift_x = 2.0
                    elif "arm" in mat_name or "nail" in mat_name: shift_x = 3.0
                    
                    for loop_idx in poly.loop_indices:
                        current_u = uv_layer.data[loop_idx].uv[0]
                        uv_layer.data[loop_idx].uv[0] = (current_u % 1.0) + shift_x
        except Exception as e:
            self.report({'WARNING'}, f"Material/UV optimization failed: {e}")

        # ---------------------------------------------------------------------
        # 2. MOUTH MESH PREPARATION
        # ---------------------------------------------------------------------
        if mouth_obj and mouth_obj.type == 'MESH':
            if mouth_obj.name not in context.view_layer.objects:
                try: context.collection.objects.link(mouth_obj)
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

            pass # Mouth will be deleted later

        # ---------------------------------------------------------------------
        # 3. EYES MESH PREPARATION
        # ---------------------------------------------------------------------
        if eyes_obj and eyes_obj.type == 'MESH':
            if eyes_obj.name not in context.view_layer.objects:
                try: context.collection.objects.link(eyes_obj)
                except: pass
                
            eyes_obj.hide_set(False)
            eyes_obj.hide_viewport = False
            
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
                    
            if moisture_idx != -1:
                context.view_layer.objects.active = eyes_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(eyes_obj.data)
                
                verts_to_scale = set()
                for f in bm.faces:
                    if f.material_index == moisture_idx:
                        for v in f.verts: verts_to_scale.add(v)
                        
                left_eye_verts = []
                right_eye_verts = []
                for v in verts_to_scale:
                    if v.co.x > 0: left_eye_verts.append(v)
                    else: right_eye_verts.append(v)
                        
                if left_eye_verts:
                    center_l = sum((v.co for v in left_eye_verts), mathutils.Vector()) / len(left_eye_verts)
                    for v in left_eye_verts: v.co = center_l + (v.co - center_l) * 1.05
                        
                if right_eye_verts:
                    center_r = sum((v.co for v in right_eye_verts), mathutils.Vector()) / len(right_eye_verts)
                    for v in right_eye_verts: v.co = center_r + (v.co - center_r) * 1.05
                        
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

            # Shift Eyes UVs to [0,1]
            if eyes_obj.data.uv_layers.active:
                for loop in eyes_obj.data.loops:
                    current_u = eyes_obj.data.uv_layers.active.data[loop.index].uv[0]
                    current_v = eyes_obj.data.uv_layers.active.data[loop.index].uv[1]
                    eyes_obj.data.uv_layers.active.data[loop.index].uv[0] = (current_u % 1.0)
                    eyes_obj.data.uv_layers.active.data[loop.index].uv[1] = (current_v % 1.0) + 1.0


        # ---------------------------------------------------------------------
        # 4. SHAPE KEY PROCESSING
        # ---------------------------------------------------------------------
        if scene.mastersk_unified_keep_shapekeys:
            # Bake ARKit and clean body just like modular
            bake_arkit_shape_keys(mesh_obj)
            clean_empty_shape_keys(mesh_obj)
            clean_body_shape_keys(mesh_obj)

            if mouth_obj and mouth_obj.type == 'MESH' and mouth_obj.data.shape_keys:
                mouth_obj.shape_key_clear()

            if eyes_obj and eyes_obj.type == 'MESH' and eyes_obj.data.shape_keys:
                kb = eyes_obj.data.shape_keys.key_blocks
                keys_to_remove = []
                for key in kb:
                    if key.name != "Basis":
                        if key.name == "facs_bs_EyePupilsDilate":
                            key.name = "EyePupilsDilate"
                        else:
                            keys_to_remove.append(key)
                bpy.ops.object.select_all(action='DESELECT')
                eyes_obj.select_set(True)
                context.view_layer.objects.active = eyes_obj
                for k in keys_to_remove: eyes_obj.shape_key_remove(k)
        else:
            # Purge all shape keys everywhere
            if mesh_obj.data.shape_keys: mesh_obj.shape_key_clear()
            if mouth_obj and mouth_obj.type == 'MESH' and mouth_obj.data.shape_keys: mouth_obj.shape_key_clear()
            if eyes_obj and eyes_obj.type == 'MESH' and eyes_obj.data.shape_keys: eyes_obj.shape_key_clear()

        # ---------------------------------------------------------------------
        # 5. JOIN MESHES AND CLEANUP
        # ---------------------------------------------------------------------
        # Remove orphaned facial vertex groups from the mesh
        from .op_split_meshes import clean_vertex_groups
        clean_vertex_groups(mesh_obj, arm_obj)
        if eyes_obj: clean_vertex_groups(eyes_obj, arm_obj)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        if eyes_obj and eyes_obj.type == 'MESH': eyes_obj.select_set(True)
        
        bpy.ops.object.join()
        
        if mouth_obj and mouth_obj.type == 'MESH':
            # Do nothing, leave it in the scene as requested
            pass

        # Re-apply Armature Modifier
        for mod in mesh_obj.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = arm_obj

        # Final assignments
        mesh_obj.name = "G9_Unified_Mesh"
        arm_obj.name = "G9_Unified_Armature"

        scene.mastersk_body_mesh = mesh_obj
        scene.mastersk_head_mesh = None # Clear this since it's unified

        self.report({'INFO'}, "Step 7 Complete: Unified geometry optimized and joined.")
        scene.mastersk_progress_step = 8
        return {'FINISHED'}
