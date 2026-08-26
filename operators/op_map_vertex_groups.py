# MasterSK - Step 3: Rename Bones & Vertex Groups Operator
# Renames both armature bones AND mesh vertex groups from Genesis 9 names
# to ALS / Unreal Engine standard names simultaneously.
import bpy
from .. import config
from ..core import weight_utils

class MASTERSK_OT_map_vertex_groups(bpy.types.Operator):
    """Step 3: Rename G9 bones and vertex groups to ALS / UE standard names"""
    bl_idname = "mastersk.map_vertex_groups"
    bl_label = "Step 3: Rename Bones & Vertex Groups"
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

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # --- Phase 1: Rename Armature Bones ---
        renamed_bones = self.rename_armature_bones(arm_obj, config.BONE_NAME_MAPPING)

        # --- Phase 2: Rename Mesh Vertex Groups ---
        renamed_vgroups = weight_utils.rename_vertex_groups(
            mesh_obj,
            config.BONE_NAME_MAPPING
        )

        # --- Phase 3: Dynamic Prefix to Suffix Renaming ---
        # Converts remaining bones like 'l_ear' to 'ear_l' for Unreal compliance
        dynamic_bones = self.rename_dynamic_prefixes(arm_obj)
        dynamic_vgroups = weight_utils.rename_dynamic_vertex_groups(mesh_obj)

        self.report({'INFO'}, f"Step 3 Complete: Renamed {renamed_bones + dynamic_bones} bones and {renamed_vgroups + dynamic_vgroups} vertex groups.")
        scene.mastersk_progress_step = 4
        return {'FINISHED'}

    @staticmethod
    def rename_armature_bones(arm_obj, mapping):
        """
        Renames bones in the armature according to the mapping.
        Must be done in Edit Mode to modify bone names.
        Skips bones where old_name == new_name or old_name doesn't exist.
        """
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_obj.data.edit_bones

        renamed_count = 0
        for old_name, new_name in mapping.items():
            if old_name == new_name:
                continue
            eb = edit_bones.get(old_name)
            if eb:
                # If a bone with the target name already exists, skip
                # (shouldn't happen after cleanup, but safety check)
                if edit_bones.get(new_name):
                    continue
                eb.name = new_name
                renamed_count += 1

        bpy.ops.object.mode_set(mode='OBJECT')
        return renamed_count

    @staticmethod
    def rename_dynamic_prefixes(arm_obj):
        """
        Catches any remaining bones with 'l_' or 'r_' prefixes (like facial bones)
        and converts them to Unreal Engine '_l' / '_r' suffixes.
        """
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_obj.data.edit_bones

        renamed_count = 0
        for eb in edit_bones:
            if eb.name.startswith("l_"):
                new_name = eb.name[2:] + "_l"
                if not edit_bones.get(new_name):
                    eb.name = new_name
                    renamed_count += 1
            elif eb.name.startswith("r_"):
                new_name = eb.name[2:] + "_r"
                if not edit_bones.get(new_name):
                    eb.name = new_name
                    renamed_count += 1

        bpy.ops.object.mode_set(mode='OBJECT')
        return renamed_count
