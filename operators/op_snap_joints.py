# MasterSK - Step 6: Snap Joints & Lock Roll Operator
import bpy
from .. import config
from ..core import bone_math

class MASTERSK_OT_snap_joints(bpy.types.Operator):
    """Step 6: Snap ALS joints to Genesis 9 anatomy while mathematically preserving exact UE local axes"""
    bl_idname = "mastersk.snap_joints"
    bl_label = "Step 6: Snap Joints & Lock Roll"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        als_arm = scene.mastersk_als_armature
        daz_arm = scene.mastersk_daz_armature

        # Auto-find ALS Armature in scene if not explicitly set
        if not als_arm or als_arm.type != 'ARMATURE':
            for obj in scene.objects:
                if obj.type == 'ARMATURE' and "als" in obj.name.lower():
                    als_arm = obj
                    scene.mastersk_als_armature = obj
                    break

        if not daz_arm or daz_arm.type != 'ARMATURE':
            bpy.ops.mastersk.auto_detect()
            daz_arm = scene.mastersk_daz_armature

        if not als_arm or als_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "ALS Armature not found. Please run 'Step 5: Append Base Skeleton' first.")
            return {'CANCELLED'}

        if not daz_arm or daz_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Genesis 9 Armature not selected.")
            return {'CANCELLED'}

        try:
            snapped_count = bone_math.snap_als_skeleton_to_daz(
                als_arm,
                daz_arm,
                config.BONE_NAME_MAPPING
            )
        except Exception as e:
            self.report({'ERROR'}, f"Joint snapping failed: {str(e)}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Step 6 Complete: Snapped {snapped_count} ALS bones while preserving original UE axes.")
        scene.mastersk_progress_step = 7
        return {'FINISHED'}
