# MasterSK - Step 1: Merge Complex Weights Operator
# Consolidates Genesis 9 extra twists, drivers, metacarpals, toes, and hip
# into their primary ALS-equivalent target bones.
import bpy
from .. import config
from ..core import weight_utils

class MASTERSK_OT_merge_weights(bpy.types.Operator):
    """Step 1: Consolidate Genesis 9 extra twists, driver bones, spines, toes, and metacarpals"""
    bl_idname = "mastersk.merge_weights"
    bl_label = "Step 1: Merge Complex Weights"
    bl_options = {'REGISTER', 'UNDO'}

    remove_sources: bpy.props.BoolProperty(
        name="Remove Merged Source Groups",
        default=True,
        description="Delete redundant vertex groups after merging weights into target groups"
    )

    @staticmethod
    def find_root_bone_name(arm_obj):
        """
        Finds the root bone of the Genesis 9 armature.
        The root bone is the one with no parent - it is named after the character
        (e.g. 'Anice', 'Sara', 'Lawrence').
        """
        if not arm_obj or arm_obj.type != 'ARMATURE':
            return None
        for bone in arm_obj.data.bones:
            if bone.parent is None:
                return bone.name
        return None

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

        # Resolve the ROOT_BONE_SENTINEL to the actual character root bone name
        root_bone_name = self.find_root_bone_name(arm_obj)
        if not root_bone_name:
            self.report({'ERROR'}, "Could not find root bone (parentless bone) in the armature.")
            return {'CANCELLED'}

        # Build the resolved consolidation map by replacing the sentinel
        resolved_map = {}
        for target, sources in config.WEIGHT_CONSOLIDATION_MAP.items():
            if target == config.ROOT_BONE_SENTINEL:
                resolved_map[root_bone_name] = sources
            else:
                resolved_map[target] = sources

        total_merged, removed_groups = weight_utils.merge_vertex_groups(
            mesh_obj,
            resolved_map,
            remove_sources=self.remove_sources
        )

        weight_utils.normalize_all_weights(mesh_obj)

        self.report({'INFO'},
            f"Step 1 Complete: Merged {total_merged} vertex weights across "
            f"{removed_groups} redundant groups. Root bone: '{root_bone_name}'."
        )
        return {'FINISHED'}
