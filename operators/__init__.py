# MasterSK Operators package initialization
import bpy
from .op_merge_weights import MASTERSK_OT_merge_weights
from .op_clean_armature import MASTERSK_OT_clean_armature
from .op_map_vertex_groups import MASTERSK_OT_map_vertex_groups
from .op_match_rest_pose import MASTERSK_OT_match_rest_pose
from .op_split_meshes import MASTERSK_OT_split_meshes
from .op_append_skeleton import MASTERSK_OT_append_skeleton
from .op_snap_joints import MASTERSK_OT_snap_joints
from .op_finalize_rigs import MASTERSK_OT_finalize_rigs

classes = (
    MASTERSK_OT_merge_weights,
    MASTERSK_OT_clean_armature,
    MASTERSK_OT_map_vertex_groups,
    MASTERSK_OT_match_rest_pose,
    MASTERSK_OT_split_meshes,
    MASTERSK_OT_append_skeleton,
    MASTERSK_OT_snap_joints,
    MASTERSK_OT_finalize_rigs,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
