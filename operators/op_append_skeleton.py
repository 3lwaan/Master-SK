# MasterSK - Step 5: Append ALS Base Skeleton Operator
import bpy
import os
from .. import config

class MASTERSK_OT_append_skeleton(bpy.types.Operator):
    """Step 5: Append the native ALS Master Armature from the addon assets folder"""
    bl_idname = "mastersk.append_skeleton"
    bl_label = "Step 5: Append Base Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_filepath = config.get_asset_path()

        if not os.path.exists(asset_filepath):
            self.report({
                'ERROR'
            }, f"ALS base skeleton file not found at: {asset_filepath}. Please ensure 'als_base_skeleton.blend' is in the addon assets folder.")
            return {'CANCELLED'}

        try:
            with bpy.data.libraries.load(asset_filepath, link=False) as (data_from, data_to):
                data_to.objects = [name for name in data_from.objects]
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load .blend asset: {str(e)}")
            return {'CANCELLED'}

        appended_armatures = []
        for obj in data_to.objects:
            if obj is not None:
                context.collection.objects.link(obj)
                if obj.type == 'ARMATURE':
                    appended_armatures.append(obj)

        if not appended_armatures:
            self.report({'ERROR'}, "No Armature object was found inside the appended blend file.")
            return {'CANCELLED'}

        als_armature = appended_armatures[0]
        als_armature.name = "ALS_Armature"

        context.scene.mastersk_als_armature = als_armature
        context.view_layer.objects.active = als_armature
        als_armature.select_set(True)

        self.report({'INFO'}, f"Step 5 Complete: Appended and dynamically scaled ALS Base Skeleton to match Genesis 9.")
        context.scene.mastersk_progress_step = 6
        return {'FINISHED'}
