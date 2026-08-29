# MasterSK - Step 8: Shape Key Purge & Mesh Integration
import bpy
from .op_split_meshes import clean_vertex_groups, bake_arkit_shape_keys, clean_empty_shape_keys, clean_body_shape_keys

class MASTERSK_OT_purge_and_join(bpy.types.Operator):
    """Step 8: Purge shape keys and join modular facial meshes into Head"""
    bl_idname = "mastersk.purge_and_join"
    bl_label = "Step 8: Shape Key Purge & Integration"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        body_obj = scene.mastersk_body_mesh
        head_obj = scene.mastersk_head_mesh
        head_arm = bpy.data.objects.get("G9_Head_Armature")
        body_arm = bpy.data.objects.get("G9_Body_Armature")

        if not body_obj or not head_obj:
            self.report({'ERROR'}, "Missing separated Head/Body meshes. Run Step 7 first.")
            return {'CANCELLED'}

        # 1. Clean Vertex Groups
        if head_arm and body_arm:
            clean_vertex_groups(head_obj, head_arm)
            clean_vertex_groups(body_obj, body_arm)

        # 2. Clean and Bake Shape Keys
        baked, deleted = bake_arkit_shape_keys(head_obj)
        clean_empty_shape_keys(body_obj)
        renamed = clean_body_shape_keys(body_obj)
        
        # Mouth Shape Keys
        mouth_obj = scene.mastersk_mouth_mesh
        if mouth_obj and mouth_obj.type == 'MESH':
            if mouth_obj.data.shape_keys:
                mouth_obj.shape_key_clear()
                
        # Eyes Shape Keys
        eyes_obj = scene.mastersk_eyes_mesh
        if eyes_obj and eyes_obj.type == 'MESH':
            if eyes_obj.data.shape_keys:
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
                
                for k in keys_to_remove:
                    eyes_obj.shape_key_remove(k)

        # 3. Join Meshes
        bpy.ops.object.select_all(action='DESELECT')
        
        if head_obj.name not in context.view_layer.objects:
            context.collection.objects.link(head_obj)
        head_obj.hide_set(False)
        head_obj.hide_viewport = False
        
        context.view_layer.objects.active = head_obj
        head_obj.select_set(True)
        
        if mouth_obj and mouth_obj.type == 'MESH':
            mouth_obj.select_set(True)
            
        if eyes_obj and eyes_obj.type == 'MESH':
            eyes_obj.select_set(True)
            
        bpy.ops.object.join()
        
        # Re-apply Head Armature Modifier (sometimes lost on join)
        for mod in head_obj.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = head_arm

        self.report({'INFO'}, f"Step 8 Complete: Baked {baked} ARKit, Purged {deleted} FACS, Joined meshes.")
        scene.mastersk_progress_step = 9
        return {'FINISHED'}
