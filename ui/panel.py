# MasterSK - 3D Viewport Sidebar Panel
import bpy
import os
from .. import config

class MASTERSK_OT_auto_detect(bpy.types.Operator):
    """Automatically detect Genesis 9 Mesh and Armature in the active selection or scene"""
    bl_idname = "mastersk.auto_detect"
    bl_label = "Auto-Detect Character"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # Check active and selected objects first
        for obj in context.selected_objects:
            if obj.type == 'MESH' and not scene.mastersk_mesh_obj:
                scene.mastersk_mesh_obj = obj
            elif obj.type == 'ARMATURE' and not scene.mastersk_daz_armature:
                if "als" not in obj.name.lower():
                    scene.mastersk_daz_armature = obj

        # Check all scene objects if still unset
        for obj in scene.objects:
            if not scene.mastersk_mesh_obj and obj.type == 'MESH':
                if any(kw in obj.name.lower() for kw in ["genesis", "g9", "mesh", "lawrence", "body"]):
                    scene.mastersk_mesh_obj = obj
            if not scene.mastersk_daz_armature and obj.type == 'ARMATURE':
                if not any(kw in obj.name.lower() for kw in ["als", "mannequin", "ue"]):
                    scene.mastersk_daz_armature = obj

        # Apply scale on detected objects to prevent mesh deformation issues
        self._apply_scale(context, scene.mastersk_daz_armature)
        self._apply_scale(context, scene.mastersk_mesh_obj)

        self.report({'INFO'}, "Genesis 9 character objects auto-detected (scale applied).")
        return {'FINISHED'}

    @staticmethod
    def _apply_scale(context, obj):
        """Applies the scale transform on the object so scale becomes (1,1,1)."""
        if not obj:
            return
        # Skip if scale is already (1,1,1)
        s = obj.scale
        if abs(s.x - 1.0) < 0.0001 and abs(s.y - 1.0) < 0.0001 and abs(s.z - 1.0) < 0.0001:
            return
        # Must be in object mode and select only this object
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

class MASTERSK_OT_reset_progress(bpy.types.Operator):
    """Reset the pipeline progress back to Step 1"""
    bl_idname = "mastersk.reset_progress"
    bl_label = "Reset Progress"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.mastersk_progress_step = 1
        self.report({'INFO'}, "Pipeline progress has been reset.")
        return {'FINISHED'}

class MASTERSK_PT_main_panel(bpy.types.Panel):
    """Main UI Panel for MasterSK Addon"""
    bl_label = "MasterSK - Genesis 9 to ALS"
    bl_idname = "MASTERSK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MasterSK'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 1. ALS Asset Status Box
        asset_path = config.get_asset_path()
        asset_exists = os.path.exists(asset_path)

        box_asset = layout.box()
        row_asset = box_asset.row(align=True)
        if asset_exists:
            row_asset.label(text="ALS Skeleton Asset: Ready", icon='CHECKMARK')
        else:
            row_asset.label(text="Asset Missing: assets/als_base_skeleton.blend", icon='ERROR')

        # 2. Character Selection Box (Genesis 9 Mesh & Armature)
        box_cfg = layout.box()
        box_cfg.label(text="Genesis 9 Character", icon='OUTLINER_OB_ARMATURE')

        col_cfg = box_cfg.column(align=True)
        col_cfg.prop_search(scene, "mastersk_mesh_obj", bpy.data, "objects", text="Mesh")
        col_cfg.prop_search(scene, "mastersk_daz_armature", bpy.data, "objects", text="Armature")

        box_cfg.separator(factor=0.3)
        box_cfg.operator("mastersk.auto_detect", text="Auto-Detect Character", icon='VIEWZOOM')

        layout.separator(factor=0.8)

        # 3. Pre-Requisite Reminder
        box_import = layout.box()
        box_import.label(text="Pre-Requisite: Daz Import", icon='INFO')
        col_import = box_import.column(align=True)
        col_import.label(text="Keep the default flexes morphs.")
        col_import.label(text="Do NOT import any FACS or JCM morphs.")
        
        layout.separator(factor=0.8)

        # 4. Pipeline Steps Box
        box_steps = layout.box()
        box_steps.label(text="Pipeline Steps:", icon='MOD_ARMATURE')
        
        # Draw Visual Progress Bar
        step_val = scene.mastersk_progress_step
        row_prog = box_steps.row(align=True)
        for i in range(1, 9):
            if i < step_val:
                row_prog.label(text="", icon='CHECKBOX_HLT')
            elif i == step_val:
                row_prog.label(text="", icon='PLAY')
            else:
                row_prog.label(text="", icon='CHECKBOX_DEHLT')

        if step_val > 8:
            box_steps.label(text="Pipeline Complete!", icon='FILE_TICK')
        
        box_steps.separator()

        col = box_steps.column(align=True)
        col.scale_y = 1.2

        # Step 1: Merge Weights
        r = col.row()
        r.enabled = (step_val == 1)
        r.operator("mastersk.merge_weights", text="1. Merge Complex Weights", icon='GROUP_VERTEX')
        col.separator(factor=0.4)

        # Step 2: Clean Armature
        r = col.row()
        r.enabled = (step_val == 2)
        r.operator("mastersk.clean_armature", text="2. Clean Armature", icon='BONE_DATA')
        col.separator(factor=0.4)

        # Step 3: Rename Bones & Vertex Groups
        r = col.row()
        r.enabled = (step_val == 3)
        r.operator("mastersk.map_vertex_groups", text="3. Rename Bones & VGroups", icon='OUTLINER_DATA_ARMATURE')
        col.separator(factor=0.4)

        # Step 4: Match Rest Pose (A-Pose)
        r = col.row()
        r.enabled = (step_val == 4)
        r.operator("mastersk.match_rest_pose", text="4. Match Rest Pose (A-Pose)", icon='ARMATURE_DATA')
        col.separator(factor=0.4)

        # Step 5: Append Base Skeleton
        r = col.row()
        r.enabled = (step_val == 5)
        r.operator("mastersk.append_skeleton", text="5. Append Base Skeleton", icon='APPEND_BLEND')
        col.separator(factor=0.4)

        # Step 6: Snap Joints & Lock Roll
        r = col.row()
        r.enabled = (step_val == 6)
        r.operator("mastersk.snap_joints", text="6. Snap Joints & Lock Roll", icon='SNAP_ON')
        col.separator(factor=0.4)

        # Step 7: Split Head & Body Meshes
        r = col.row()
        r.enabled = (step_val == 7)
        r.operator("mastersk.split_meshes", text="7. Split Head & Body Meshes", icon='MOD_EXPLODE')
        col.separator(factor=0.4)

        # Step 8: Finalize & Dual Rig Setup
        r = col.row()
        r.enabled = (step_val == 8)
        r.operator("mastersk.finalize_rigs", text="8. Finalize & Dual Rig Setup", icon='CHECKMARK')
        col.separator(factor=0.4)

        # Step 9: Generate ROM Animation (Optional)
        r = col.row()
        r.enabled = (step_val >= 8) # Can run after 8

        # 5. Post-Processing Reminder
        layout.separator(factor=1.0)
        box_post = layout.box()
        box_post.label(text="Pre-Export Checklist:", icon='ERROR')
        col_post = box_post.column(align=True)
        col_post.label(text="1. Manually align spine_01, 02, 03 to match weight paint.")
        col_post.label(text="2. Smooth crotch weights for pelvis and thigh_twist_01_l/r.")
        col_post.label(text="3. Verify armatures are named exactly 'root' (Object & Data).")
        col_post.label(text="4. Verify meshes are 'Char_Head_Mesh' / 'Char_Body_Mesh'.")

        layout.separator(factor=1.0)
        row_reset = layout.row()
        row_reset.operator("mastersk.reset_progress", text="Reset Progress", icon='FILE_REFRESH')




