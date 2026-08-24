bl_info = {
    "name": "MasterSK - Genesis 9 to ALS Pipeline",
    "author": "Gate Studio / Antigravity",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MasterSK Tab",
    "description": "Automated Daz Genesis 9 to ALS skeleton replacement, roll-locked joint snapping, and modular Body/Face dual-rig generation for Unreal Engine 5.",
    "category": "Rigging",
}

import sys
import bpy

from . import config
from .core import weight_utils, bone_math, mesh_utils
from .operators.op_merge_weights import MASTERSK_OT_merge_weights
from .operators.op_clean_armature import MASTERSK_OT_clean_armature
from .operators.op_map_vertex_groups import MASTERSK_OT_map_vertex_groups
from .operators.op_match_rest_pose import MASTERSK_OT_match_rest_pose
from .operators.op_split_meshes import MASTERSK_OT_split_meshes
from .operators.op_append_skeleton import MASTERSK_OT_append_skeleton
from .operators.op_snap_joints import MASTERSK_OT_snap_joints
from .operators.op_finalize_rigs import MASTERSK_OT_finalize_rigs, MASTERSK_OT_spine_warning_popup
from .ui.panel import MASTERSK_OT_auto_detect, MASTERSK_OT_reset_progress, MASTERSK_PT_main_panel

classes = (
    MASTERSK_OT_auto_detect,
    MASTERSK_OT_merge_weights,
    MASTERSK_OT_clean_armature,
    MASTERSK_OT_map_vertex_groups,
    MASTERSK_OT_match_rest_pose,
    MASTERSK_OT_split_meshes,
    MASTERSK_OT_append_skeleton,
    MASTERSK_OT_snap_joints,
    MASTERSK_OT_finalize_rigs,
    MASTERSK_OT_spine_warning_popup,
    MASTERSK_OT_reset_progress,
    MASTERSK_PT_main_panel,
)

def poll_mesh(self, object):
    return object.type == 'MESH'

def poll_armature(self, object):
    return object.type == 'ARMATURE'

def register():
    bpy.types.Scene.mastersk_mesh_obj = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Genesis 9 Mesh",
        description="Active Genesis 9 Character Mesh object",
        poll=poll_mesh
    )

    bpy.types.Scene.mastersk_daz_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Genesis 9 Armature",
        description="Original Genesis 9 Armature object",
        poll=poll_armature
    )

    bpy.types.Scene.mastersk_als_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="ALS Armature",
        description="Target ALS / Epic Mannequin Armature object",
        poll=poll_armature
    )

    bpy.types.Scene.mastersk_body_mesh = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="G9 Body Mesh",
        poll=poll_mesh
    )

    bpy.types.Scene.mastersk_head_mesh = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="G9 Head Mesh",
        poll=poll_mesh
    )

    bpy.types.Scene.mastersk_progress_step = bpy.props.IntProperty(
        name="Pipeline Progress",
        description="Current step in the MasterSK pipeline",
        default=1,
        min=1,
        max=9
    )

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.mastersk_head_mesh
    del bpy.types.Scene.mastersk_body_mesh
    del bpy.types.Scene.mastersk_als_armature
    del bpy.types.Scene.mastersk_daz_armature
    del bpy.types.Scene.mastersk_mesh_obj
    del bpy.types.Scene.mastersk_progress_step

if __name__ == "__main__":
    register()
