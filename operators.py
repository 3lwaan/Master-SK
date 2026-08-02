import bpy
from .reference_loader import load_reference_data
from .rig_utils import (
    validate_selection,
    apply_transforms,
    rename_armature_and_datablock,
    purge_all_bone_collections,
    clear_pelvis_constraints,
    rename_uv_layers,
    merge_hip_weights_to_pelvis,
    purge_bones_and_restructure_hierarchy,
    sync_bone_and_vertex_group_names,
    inject_ue5_als_ik_bones,
    separate_head_mesh_by_material,
    prune_face_rig_bones,
    prune_body_rig_bones,
    purge_orphaned_vgroups_for_split,
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
    """Purge helper bones, restructure hierarchy to UE5 standard, clean pelvis constraints, rename UV layers, and sync vertex groups."""
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

            # 3. Clear pelvis pose constraints for ALS locomotion compatibility
            clear_pelvis_constraints(armature_obj)

            # 4. Rename primary UV map layers to 'UVMap'
            rename_uv_layers(mesh_objs)

            # 5. Merge vertex weights from 'hip' into 'pelvis' before purging hip bone to prevent skinning bugs
            merge_hip_weights_to_pelvis(mesh_objs)

            # 6. Bone Purge (including 20 child toe bones) & Hierarchy Restructuring
            purge_bones_and_restructure_hierarchy(armature_obj, ref_data)

            # 7. Synchronized Vertex Group Renaming & Cleanup
            sync_bone_and_vertex_group_names(armature_obj, mesh_objs, ref_data)

            props.step2_completed = True
            props.status_message = f"Step 2 Complete: Restructured '{armature_obj.name}', cleaned pelvis constraints & UVMap."
            
            self.report({'INFO'}, f"Rig hierarchy restructured, pelvis constraints cleared, UV map renamed, and weights synced.")
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


class MSK_OT_separate_head_modularize(bpy.types.Operator):
    """Separate head geometry via 'Head' material slot, split armatures into SKM_Body_Rig and SKM_Face_Rig, and purge orphaned weights."""
    bl_idname = "master_sk.separate_head_modularize"
    bl_label = "4. Separate Head & Modularize Rigs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props

        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, "Please select the Master SK Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Step 4."
            return {'CANCELLED'}

        target_mesh = mesh_objs[0]

        try:
            # Step 4.1: Separate Head Mesh via Material Slot
            head_mesh, body_mesh, sep_err = separate_head_mesh_by_material(target_mesh)
            if sep_err:
                self.report({'ERROR'}, sep_err)
                props.status_message = f"Error: {sep_err}"
                return {'CANCELLED'}

            # Step 4.2: Duplicate Armature to create SKM_Body_Rig and SKM_Face_Rig
            body_rig = armature_obj
            body_rig.name = "SKM_Body_Rig"

            # Duplicate body_rig in Object mode
            bpy.ops.object.select_all(action='DESELECT')
            body_rig.select_set(True)
            bpy.context.view_layer.objects.active = body_rig
            bpy.ops.object.duplicate()
            face_rig = bpy.context.view_layer.objects.active
            face_rig.name = "SKM_Face_Rig"

            # Step 4.3: Prune SKM_Face_Rig & setup SKM_Head_Mesh
            prune_face_rig_bones(face_rig)
            
            # Re-target Armature Modifier on SKM_Head_Mesh
            for mod in list(head_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    mod.object = face_rig
                    
            purge_orphaned_vgroups_for_split(head_mesh, face_rig)

            # Step 4.4: Prune SKM_Body_Rig & setup SKM_Body_Mesh
            prune_body_rig_bones(body_rig)
            
            # Re-target Armature Modifier on SKM_Body_Mesh
            for mod in list(body_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    mod.object = body_rig

            purge_orphaned_vgroups_for_split(body_mesh, body_rig)

            # Parent mesh objects under respective rigs cleanly
            head_mesh.parent = face_rig
            body_mesh.parent = body_rig

            props.step4_completed = True
            props.status_message = "Step 4 Complete: Modularized into 'SKM_Body_Rig' & 'SKM_Face_Rig'."
            
            self.report({'INFO'}, "Successfully separated head mesh and modularized Body & Face rigs.")
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error modularizing head & rigs: {str(e)}"
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


class MSK_OT_reset_progress(bpy.types.Operator):
    """Reset step completion checkmarks and status message."""
    bl_idname = "master_sk.reset_progress"
    bl_label = "Reset Step Progress"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.master_sk_props
        props.step1_completed = False
        props.step2_completed = False
        props.step3_completed = False
        props.step4_completed = False
        props.status_message = "Ready. Select your DAZ Armature and Character Mesh to begin."
        self.report({'INFO'}, "Master SK workflow progress reset.")
        return {'FINISHED'}


classes = (
    MSK_OT_prepare_character,
    MSK_OT_process_rig_vertex_groups,
    MSK_OT_inject_ik_bones,
    MSK_OT_separate_head_modularize,
    MSK_OT_reload_reference,
    MSK_OT_reset_progress,
)

def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister_operators():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
