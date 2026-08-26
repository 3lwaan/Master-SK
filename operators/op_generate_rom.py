import bpy
import math
import mathutils
from .. import config

class MASTERSK_OT_generate_rom(bpy.types.Operator):
    """Generate a ROM (Range of Motion) animation for Pose Assets using World Matrices and Quaternions"""
    bl_idname = "mastersk.generate_rom"
    bl_label = "Step 9: Generate JCM ROM"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        als_arm = scene.mastersk_als_armature
        
        daz_arm = None
        data_col = bpy.data.collections.get("MasterSK_Data")
        if data_col:
            for obj in data_col.objects:
                if obj.type == 'ARMATURE':
                    daz_arm = obj
                    break

        if not als_arm or not daz_arm:
            self.report({'ERROR'}, "Could not find ALS rig or hidden Daz rig. Ensure Step 8 was completed.")
            return {'CANCELLED'}

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

        # Use QUATERNION for ALS to prevent Euler Gimbal Lock spinning
        for pb in als_arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            
        # Daz uses XYZ Euler inherently in our map
        for pb in daz_arm.pose.bones:
            pb.rotation_mode = 'XYZ'

        self.clear_pose(als_arm)
        self.clear_pose(daz_arm)
        
        frame = 1
        
        # Keyframe Basis (Frame 1)
        self.keyframe_all_rotations(als_arm, frame)
        frame += 1

        dg = context.evaluated_depsgraph_get()

        # Iterate through JCM Map and create poses
        for jcm_key, jcm_data in config.JCM_AAA_NAMING_MAP.items():
            daz_bone_name = jcm_data.get("daz_bone")
            
            # Skip if bone is None
            if daz_bone_name == "None" or not daz_bone_name:
                continue
                
            daz_pb = daz_arm.pose.bones.get(daz_bone_name)
            als_pb = als_arm.pose.bones.get(daz_bone_name)
            
            if not daz_pb or not als_pb:
                print(f"MasterSK ROM: Bone {daz_bone_name} not found for {jcm_key}")
                continue
                
            # Clear previous poses
            self.clear_pose(daz_arm)
            self.clear_pose(als_arm)
            
            # 1. Get Daz Rest Matrix (3x3 Rotation)
            daz_rest_rot = daz_pb.bone.matrix_local.to_3x3()
            
            # Apply Daz native local rotations
            rotations = jcm_data.get("rotations", {})
            x_rot = math.radians(rotations.get("X", 0))
            y_rot = math.radians(rotations.get("Y", 0))
            z_rot = math.radians(rotations.get("Z", 0))
            daz_pb.rotation_euler = (x_rot, y_rot, z_rot)
            
            # Update Depsgraph so Blender calculates the new world matrix for the Daz bone
            dg.update()
            
            # 2. Get Daz Posed Matrix (3x3 Rotation)
            daz_posed_rot = daz_pb.matrix.to_3x3()
            
            # 3. Calculate Delta Rotation in World Space
            # R_delta = R_posed @ R_rest_inverted
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
            
            # MATHEMATICALLY PERFECT FIX 2: 
            # Force shortest path interpolation to prevent Euler spinning
            q = als_pb.rotation_quaternion.copy()
            if q.w < 0:
                q.negate()
            als_pb.rotation_quaternion = q
            
            # Insert keyframe for the ALS bone
            als_pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Keyframe all other ALS bones at rest pose to prevent interpolation
            for other_pb in als_arm.pose.bones:
                if other_pb.name != daz_bone_name:
                    other_pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    
            frame += 1
            
        # Reset to basis at end
        self.clear_pose(als_arm)
        self.clear_pose(daz_arm)
        self.keyframe_all_rotations(als_arm, frame)

        # Set timeline range
        scene.frame_start = 1
        scene.frame_end = frame

        self.report({'INFO'}, f"Generated {frame-1}-frame ROM Animation (Quaternion Corrected): {action_name}")
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
