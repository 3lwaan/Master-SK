import bpy
import math
import mathutils
import os
import json
from .. import config

class MASTERSK_OT_generate_rom(bpy.types.Operator):
    """Generate a ROM animation using Full Native Daz Matrix/ShapeKey Extraction"""
    bl_idname = "mastersk.generate_rom"
    bl_label = "Step 9: Generate JCM ROM"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        als_arm = scene.mastersk_als_armature
        mesh_obj = scene.mastersk_body_mesh
        if not mesh_obj:
            mesh_obj = scene.mastersk_mesh_obj
            
        daz_arm = None
        data_col = bpy.data.collections.get("MasterSK_Data")
        if data_col:
            for obj in data_col.objects:
                if obj.type == 'ARMATURE':
                    daz_arm = obj
                    break

        if not als_arm or not daz_arm or not mesh_obj:
            self.report({'ERROR'}, "Could not find ALS rig, Daz rig, or Mesh. Ensure Step 8 was completed.")
            return {'CANCELLED'}
            
        # Load daz_rom_full.json
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "daz_rom_full.json")
        if not os.path.exists(json_path):
            self.report({'ERROR'}, "daz_rom_full.json not found in addon data folder!")
            return {'CANCELLED'}
            
        with open(json_path, 'r') as f:
            rom_frames = json.load(f)

        # Ensure object mode
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Create or clear action for ALS
        if not als_arm.animation_data:
            als_arm.animation_data_create()
        action_name = "MasterSK_JCM_ROM"
        action = bpy.data.actions.get(action_name)
        if action:
            bpy.data.actions.remove(action)
        action = bpy.data.actions.new(name=action_name)
        als_arm.animation_data.action = action

        # Create or clear action for Mesh (Shape Keys)
        if mesh_obj.data.shape_keys:
            if not mesh_obj.data.shape_keys.animation_data:
                mesh_obj.data.shape_keys.animation_data_create()
            sk_action_name = "MasterSK_JCM_ROM_Mesh"
            sk_action = bpy.data.actions.get(sk_action_name)
            if sk_action:
                bpy.data.actions.remove(sk_action)
            sk_action = bpy.data.actions.new(name=sk_action_name)
            mesh_obj.data.shape_keys.animation_data.action = sk_action

        # Use QUATERNION for ALS to prevent Euler Gimbal Lock spinning
        for pb in als_arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            
        # Daz uses XYZ Euler inherently in our map
        for pb in daz_arm.pose.bones:
            pb.rotation_mode = 'XYZ'

        self.clear_pose(als_arm)
        self.clear_pose(daz_arm)
        if mesh_obj.data.shape_keys:
            self.clear_shape_keys(mesh_obj)
        
        frame = 1
        
        # Keyframe Basis (Frame 1)
        self.keyframe_all_rotations(als_arm, frame)
        if mesh_obj.data.shape_keys:
            self.keyframe_all_shape_keys(mesh_obj, frame)
        frame += 1

        dg = context.evaluated_depsgraph_get()

        # Iterate through Native Daz Frame Clusters
        for frame_key, frame_data in rom_frames.items():
            # Clear previous poses
            self.clear_pose(daz_arm)
            self.clear_pose(als_arm)
            if mesh_obj.data.shape_keys:
                self.clear_shape_keys(mesh_obj)
                
            active_sks = {}
            valid_frame = False
            
            # Parse Shape Keys for this frame
            for sk_data in frame_data.get("shape_keys", []):
                sk_name = sk_data["name"]
                sk_value = sk_data["value"]
                
                # Strip prefixes to match config keys (body_bs_FlexHamstringL -> FlexHamstringL)
                search_key = sk_name.replace("body_cbs_", "").replace("body_bs_", "")
                
                # Check if it exists in our mapping
                if search_key in config.JCM_AAA_NAMING_MAP:
                    jcm_data = config.JCM_AAA_NAMING_MAP[search_key]
                    
                    # Verify shape key actually exists on the mesh
                    if mesh_obj.data.shape_keys:
                        if jcm_data["new_name"] in mesh_obj.data.shape_keys.key_blocks:
                            active_sks[jcm_data["new_name"]] = sk_value
                            valid_frame = True
            
            # If no valid shape keys mapped for this cluster, we could skip it to save frames,
            # BUT wait: some frames might be used for bone movement testing without shape keys?
            # Actually, we want a compact ROM, so skipping frames that trigger NO valid shape keys is good.
            if not valid_frame:
                continue

            # Now parse and rotate all bones involved in this cluster
            for original_bone_name, rot in frame_data.get("bones", {}).items():
                # Daz bone in the JSON is the original name (e.g. l_shin). 
                # We must translate it to the new name (e.g. calf_l) using Step 3 map.
                mapped_bone_name = config.BONE_NAME_MAPPING.get(original_bone_name, original_bone_name)
                
                daz_pb = daz_arm.pose.bones.get(mapped_bone_name)
                als_pb = als_arm.pose.bones.get(mapped_bone_name)
                
                # If bone is not mapped to ALS, or was deleted in Step 2, skip it
                if not daz_pb or not als_pb:
                    continue
                    
                # 1. Get Daz Rest Matrix
                daz_rest_rot = daz_pb.bone.matrix_local.to_3x3()
                
                # Apply EXACT Extracted Rotations from the JSON
                x_rot = math.radians(rot["X"])
                y_rot = math.radians(rot["Y"])
                z_rot = math.radians(rot["Z"])
                daz_pb.rotation_euler = (x_rot, y_rot, z_rot)
                
                # Update Depsgraph
                dg.update()
                
                # 2. Get Daz Posed Matrix
                daz_posed_rot = daz_pb.matrix.to_3x3()
                
                # 3. Calculate Delta Rotation in World Space
                daz_rest_inv = daz_rest_rot.copy()
                daz_rest_inv.invert()
                delta_rot = daz_posed_rot @ daz_rest_inv
                
                # 4. Apply Delta Rotation to ALS Rest Matrix
                als_rest_rot = als_pb.bone.matrix_local.to_3x3()
                als_posed_rot = delta_rot @ als_rest_rot
                
                # 5. Build full 4x4 Matrix for ALS
                als_posed_mat = als_posed_rot.to_4x4()
                als_posed_mat.translation = als_pb.matrix.translation
                
                # Set the pose Matrix
                als_pb.matrix = als_posed_mat
                
                # Force shortest path interpolation
                q = als_pb.rotation_quaternion.copy()
                if q.w < 0:
                    q.negate()
                als_pb.rotation_quaternion = q
                
            # Insert keyframe for ALL ALS bones
            self.keyframe_all_rotations(als_arm, frame)
                    
            # Set shape keys to exact extracted values and keyframe it, others at 0.0
            if mesh_obj.data.shape_keys:
                for kb in mesh_obj.data.shape_keys.key_blocks:
                    if kb.name == "Basis": continue
                    if kb.name in active_sks:
                        kb.value = active_sks[kb.name]
                    else:
                        kb.value = 0.0
                    kb.keyframe_insert(data_path="value", frame=frame)
                    
            frame += 1
            
        # Reset to basis at end
        self.clear_pose(als_arm)
        self.clear_pose(daz_arm)
        if mesh_obj.data.shape_keys:
            self.clear_shape_keys(mesh_obj)
            
        self.keyframe_all_rotations(als_arm, frame)
        if mesh_obj.data.shape_keys:
            self.keyframe_all_shape_keys(mesh_obj, frame)

        # Set timeline range
        scene.frame_start = 1
        scene.frame_end = frame

        self.report({'INFO'}, f"Generated {frame}-frame ROM Animation matching Native Daz Clusters & Rotations!")
        return {'FINISHED'}

    def clear_pose(self, arm_obj):
        for pb in arm_obj.pose.bones:
            pb.matrix_basis.identity()

    def keyframe_all_rotations(self, arm_obj, frame):
        for pb in arm_obj.pose.bones:
            if pb.rotation_mode == 'QUATERNION':
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            else:
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    def clear_shape_keys(self, mesh_obj):
        for kb in mesh_obj.data.shape_keys.key_blocks:
            kb.value = 0.0

    def keyframe_all_shape_keys(self, mesh_obj, frame):
        for kb in mesh_obj.data.shape_keys.key_blocks:
            kb.keyframe_insert(data_path="value", frame=frame)

