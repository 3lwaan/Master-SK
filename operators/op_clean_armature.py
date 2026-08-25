# MasterSK - Step 2: Clean Armature Operator
# Deletes extra Genesis 9 bones, reparents children, removes bone
# collections and constraints. The character-named root bone and "hip"
# are DELETED. Pelvis becomes the top-level bone matching ALS.
#
# CRITICAL: After deletion, spine1 must be reparented to pelvis.
# In G9, spine1 is a sibling of pelvis (both children of hip).
# In ALS, spine_01 is a CHILD of pelvis. Without this fixup,
# the COPY_ROTATION solver in Step 4 would produce wrong results
# because the parent chains don't match.
import bpy
from .. import config
from ..core import weight_utils

class MASTERSK_OT_clean_armature(bpy.types.Operator):
    """Step 2: Remove extra G9 bones, reparent children, match ALS hierarchy"""
    bl_idname = "mastersk.clean_armature"
    bl_label = "Step 2: Clean Armature"
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

        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Armature.")
            return {'CANCELLED'}

        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid Genesis 9 Mesh object.")
            return {'CANCELLED'}

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # --- Phase 1: Identify the character-named root bone (parentless) ---
        char_root_name = None
        for bone in arm_obj.data.bones:
            if bone.parent is None:
                char_root_name = bone.name
                break

        if not char_root_name:
            self.report({'ERROR'}, "Could not find root bone (parentless bone) in the armature.")
            return {'CANCELLED'}

        # --- Phase 2: Collect all facial bones (children of 'head') ---
        facial_bones = set()
        head_bone = arm_obj.data.bones.get("head")
        if head_bone:
            self._collect_all_children(head_bone, facial_bones)

        # --- Phase 3: Build the whitelist of bones to keep ---
        # char_root_name and "hip" are NOT in keep_set — they get deleted
        keep_set = set(config.BONES_TO_KEEP)
        keep_set.update(facial_bones)

        # --- Phase 4: Remove ALL bone constraints ---
        constraints_removed = 0
        for pb in arm_obj.pose.bones:
            for constraint in list(pb.constraints):
                pb.constraints.remove(constraint)
                constraints_removed += 1

        # --- Phase 5: Enter Edit Mode and process bones ---
        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_obj.data.edit_bones

        # Identify ALL bones to delete (not in whitelist)
        bones_to_delete = []
        for eb in edit_bones:
            if eb.name not in keep_set:
                bones_to_delete.append(eb.name)

        delete_set = set(bones_to_delete)

        # Reparent children of deleted bones to nearest surviving ancestor
        for bone_name in bones_to_delete:
            eb = edit_bones.get(bone_name)
            if not eb:
                continue

            surviving_parent = self._find_surviving_parent(eb, delete_set, edit_bones)

            for child in list(eb.children):
                child.parent = surviving_parent
                child.use_connect = False

        # Delete the extra bones
        deleted_count = 0
        for bone_name in bones_to_delete:
            eb = edit_bones.get(bone_name)
            if eb:
                edit_bones.remove(eb)
                deleted_count += 1

        # --- Phase 5b: CRITICAL hierarchy fixup to match ALS ---
        # In G9, both pelvis and spine1 are children of "hip".
        # After deleting "hip", both become top-level (no parent).
        # But in ALS, spine_01 is a CHILD of pelvis, not a sibling.
        # Without this fix, the COPY_ROTATION solver in Step 4 would
        # apply pelvis-relative rotations to a bone with no parent,
        # causing the entire upper body to spaghetti.
        pelvis_eb = edit_bones.get("pelvis")
        if pelvis_eb:
            # Reparent spine1 to pelvis (matches ALS: spine_01 parent = pelvis)
            spine1_eb = edit_bones.get("spine1")
            if spine1_eb and spine1_eb.parent is None:
                spine1_eb.parent = pelvis_eb
                spine1_eb.use_connect = False

        bpy.ops.object.mode_set(mode='OBJECT')

        # --- Phase 6: Rename armature OBJECT and DATA to "root" ---
        old_obj_name = arm_obj.name
        arm_obj.name = "root"
        arm_obj.data.name = "root"

        # --- Phase 7: Remove all bone collections ---
        collections_removed = self._remove_bone_collections(arm_obj)

        # --- Phase 8: Merge character root vertex group into pelvis ---
        if mesh_obj:
            char_root_vg = mesh_obj.vertex_groups.get(char_root_name)
            if char_root_vg:
                pelvis_vg = mesh_obj.vertex_groups.get("pelvis")
                if pelvis_vg:
                    weight_utils.merge_vertex_groups(
                        mesh_obj,
                        {"pelvis": [char_root_name]},
                        remove_sources=True
                    )
                else:
                    char_root_vg.name = "pelvis"

            # Clean up any "hip" VG remnant
            hip_vg = mesh_obj.vertex_groups.get("hip")
            if hip_vg:
                pelvis_vg = mesh_obj.vertex_groups.get("pelvis")
                if pelvis_vg:
                    weight_utils.merge_vertex_groups(
                        mesh_obj,
                        {"pelvis": ["hip"]},
                        remove_sources=True
                    )
                else:
                    hip_vg.name = "pelvis"

        # --- Phase 9: Clean up orphan vertex groups ---
        orphan_removed = weight_utils.prune_unweighted_groups(mesh_obj)

        # --- Phase 10: Verify hierarchy matches ALS ---
        pelvis_bone = arm_obj.data.bones.get("pelvis")
        spine1_bone = arm_obj.data.bones.get("spine1")

        hierarchy_ok = True
        if pelvis_bone and pelvis_bone.parent is not None:
            self.report({'WARNING'}, "Pelvis is not the top-level bone.")
            hierarchy_ok = False
        if spine1_bone and (not spine1_bone.parent or spine1_bone.parent.name != "pelvis"):
            self.report({'WARNING'}, "spine1 is not a child of pelvis.")
            hierarchy_ok = False

        status = "OK" if hierarchy_ok else "WARNING: hierarchy mismatch"
        self.report({'INFO'},
            f"Step 2 Complete: Deleted {deleted_count} bones "
            f"(including '{char_root_name}'), "
            f"removed {constraints_removed} constraints, "
            f"removed {collections_removed} collections, "
            f"renamed '{old_obj_name}' -> 'root', "
            f"pruned {orphan_removed} orphan VGs. "
            f"Hierarchy: {status}"
        )
        scene.mastersk_progress_step = 3
        return {'FINISHED'}
    @staticmethod
    def _collect_all_children(bone, result_set):
        """Recursively collects all children bone names into result_set (excluding drv bones)."""
        for child in bone.children:
            if not child.name.endswith("(drv)"):
                result_set.add(child.name)
            MASTERSK_OT_clean_armature._collect_all_children(child, result_set)


    @staticmethod
    def _find_surviving_parent(edit_bone, delete_set, edit_bones):
        """
        Walks up the parent chain to find the first ancestor NOT in delete_set.
        Returns None if no surviving ancestor (bone becomes top-level).
        """
        parent = edit_bone.parent
        while parent is not None:
            if parent.name not in delete_set:
                return parent
            parent = parent.parent
        return None

    @staticmethod
    def _remove_bone_collections(arm_obj):
        """Removes all bone collections from the armature."""
        removed = 0
        arm_data = arm_obj.data

        if hasattr(arm_data, 'collections'):
            colls = list(arm_data.collections)
            for coll in colls:
                try:
                    arm_data.collections.remove(coll)
                    removed += 1
                except Exception:
                    pass

        return removed
