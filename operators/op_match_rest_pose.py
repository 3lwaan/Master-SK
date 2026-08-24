# MasterSK - Step 4: Match Rest Pose Operator (Kinematic Vector Alignment)
import bpy
import os
from .. import config
from ..core import bone_math

class MASTERSK_OT_match_rest_pose(bpy.types.Operator):
    """Step 4: Align character pose to ALS Master Skeleton and bake as new rest pose"""
    bl_idname = "mastersk.match_rest_pose"
    bl_label = "Step 4: Match Rest Pose (A-Pose)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mesh_obj = scene.mastersk_mesh_obj
        arm_obj = scene.mastersk_daz_armature

        # Auto-detect if not set
        if not mesh_obj or not arm_obj:
            bpy.ops.mastersk.auto_detect()
            mesh_obj = scene.mastersk_mesh_obj
            arm_obj = scene.mastersk_daz_armature

        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Mesh object.")
            return {'CANCELLED'}

        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Armature.")
            return {'CANCELLED'}

        # Validation: check that bones have been renamed (Step 3 should have run)
        has_als_names = any(
            b.name in ("spine_01", "upperarm_l", "calf_l")
            for b in arm_obj.data.bones
        )
        if not has_als_names:
            self.report({'ERROR'},
                "Armature bones do not appear to be renamed yet. "
                "Please run Steps 1-3 first."
            )
            return {'CANCELLED'}

        asset_filepath = config.get_asset_path()
        if not os.path.exists(asset_filepath):
            self.report({'ERROR'}, f"ALS base skeleton asset not found at: {asset_filepath}")
            return {'CANCELLED'}

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 1. Load ALS skeleton into scene temporarily
        try:
            als_arm, loaded_objects = bone_math.load_als_skeleton_temp(asset_filepath)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load ALS skeleton: {str(e)}")
            return {'CANCELLED'}

        # 2. Ensure G9 armature is at origin with identity transform
        arm_obj.location = (0, 0, 0)
        arm_obj.rotation_euler = (0, 0, 0)
        context.view_layer.update()

        # 3. Kinematic Vector Alignment (v5)
        # Rotates G9 bones in world space to visually match ALS limb directions
        try:
            matched = bone_math.solve_als_named_apose(arm_obj, als_arm)
        except Exception as e:
            bone_math.cleanup_temp_als_skeleton(als_arm, loaded_objects)
            self.report({'ERROR'}, f"Pose matching failed: {str(e)}")
            return {'CANCELLED'}

        # 4. Remove temporary ALS skeleton
        bone_math.cleanup_temp_als_skeleton(als_arm, loaded_objects)

        # 5. Bake the Armature Deformed Pose into the Mesh & All Shape Keys
        bone_math.fast_bake_armature_with_shapekeys(context, mesh_obj, arm_obj)

        # 6. Apply Current Pose as Armature Rest Pose
        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.object.mode_set(mode='OBJECT')

        # 6.5 Mathematically calculate and correct the Pelvis root motion pivot point
        try:
            bone_math.fix_pelvis_location(arm_obj)
        except Exception as e:
            self.report({'WARNING'}, f"Pelvis fix failed: {str(e)}")

        # 7. Re-link Armature Modifier
        has_mod = any(m.type == 'ARMATURE' and m.object == arm_obj for m in mesh_obj.modifiers)
        if not has_mod:
            new_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
            new_mod.object = arm_obj

        self.report({'INFO'}, "Step 4 Complete: Kinematic matching solved. New ALS A-Pose baked as default rest pose.")
        scene.mastersk_progress_step = 5
        return {'FINISHED'}
