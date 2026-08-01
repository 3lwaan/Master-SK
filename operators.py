import bpy
from .reference_loader import load_reference_data
from .rig_utils import (
    validate_selection,
    apply_transforms,
    rename_armature_and_datablock,
    purge_all_bone_collections,
    purge_bones_and_restructure_hierarchy,
    sync_bone_and_vertex_group_names,
    inject_ue5_als_ik_bones,
)

class MSK_OT_prepare_character(bpy.types.Operator):
    """Select your DAZ Armature and Character Mesh in the viewport, then press this button."""
    bl_idname = "master_sk.prepare_character"
    bl_label = "1. Prepare Active Character"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props
        
        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, 'Please select both the DAZ Armature and Character Mesh.')
            props.status_message = "Error: Please select both the DAZ Armature and Character Mesh."
            return {'CANCELLED'}

        try:
            apply_transforms(armature_obj, mesh_objs)
            
            props.active_armature_name = armature_obj.name
            props.step1_completed = True
            props.status_message = f"Step 1 Complete: Applied transforms for '{armature_obj.name}' and {len(mesh_objs)} mesh(es)."
            
            self.report({'INFO'}, f"Transforms cleanly applied for '{armature_obj.name}' and character mesh(es).")
            return {'FINISHED'}
            
        except Exception as e:
            err_text = f"Failed to prepare character: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            return {'CANCELLED'}


class MSK_OT_process_rig_vertex_groups(bpy.types.Operator):
    """Purge helper bones, restructure hierarchy to UE5 standard, and synchronize vertex groups simultaneously."""
    bl_idname = "master_sk.process_rig_vertex_groups"
    bl_label = "2. Process Rig & Sync Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props
        
        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, err_msg or "Please select both the DAZ Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Step 2."
            return {'CANCELLED'}

        try:
            ref_path = props.custom_reference_path if props.use_custom_reference else None
            ref_data = load_reference_data(ref_path)

            # 1. Rename Armature Object to 'SKM <mesh_name>' and Datablock to 'root'
            rename_armature_and_datablock(armature_obj, mesh_objs)

            # 2. Completely wipe all Bone Collections (Blender 4.4.3 un-grouped structure)
            purge_all_bone_collections(armature_obj)

            # 3. Bone Purge & Hierarchy Restructuring (Edit Mode: pelvic top-level bone)
            purge_bones_and_restructure_hierarchy(armature_obj, ref_data)

            # 4. Synchronized Vertex Group Renaming & Cleanup
            sync_bone_and_vertex_group_names(armature_obj, mesh_objs, ref_data)

            props.step2_completed = True
            props.status_message = f"Step 2 Complete: Restructured '{armature_obj.name}' (Data: 'root') & synced weights."
            
            self.report({'INFO'}, f"Rig hierarchy restructured to 'pelvis' top-level and vertex groups synchronized for '{armature_obj.name}'.")
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error processing rig & vertex groups: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            return {'CANCELLED'}


class MSK_OT_inject_ik_bones(bpy.types.Operator):
    """Inject UE5 / ALS standard IK bones with 0 roll offset relative to world space."""
    bl_idname = "master_sk.inject_ik_bones"
    bl_label = "3. Inject UE5 / ALS IK Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props

        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj:
            self.report({'ERROR'}, "Please select the target Master SK Armature.")
            props.status_message = "Error: Armature selection invalid for Step 3."
            return {'CANCELLED'}

        try:
            inject_ue5_als_ik_bones(armature_obj)

            props.step3_completed = True
            props.status_message = f"Step 3 Complete: Injected UE5/ALS IK bones for '{armature_obj.name}'."
            
            self.report({'INFO'}, f"UE5 / ALS IK bones successfully injected into '{armature_obj.name}'.")
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error injecting IK bones: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            return {'CANCELLED'}


class MSK_OT_reload_reference(bpy.types.Operator):
    """Reload reference mapping configuration file."""
    bl_idname = "master_sk.reload_reference"
    bl_label = "Reload Reference File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.master_sk_props
        ref_path = props.custom_reference_path if props.use_custom_reference else None
        ref_data = load_reference_data(ref_path)
        
        source_name = ref_data.get("source", "Unknown")
        num_mappings = len(ref_data.get("DAZ_TO_MASTER_MAP", {}))
        
        self.report({'INFO'}, f"Loaded reference file from '{source_name}' ({num_mappings} bone mappings).")
        props.status_message = f"Reference File Loaded: {source_name}"
        return {'FINISHED'}


classes = (
    MSK_OT_prepare_character,
    MSK_OT_process_rig_vertex_groups,
    MSK_OT_inject_ik_bones,
    MSK_OT_reload_reference,
)

def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister_operators():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
