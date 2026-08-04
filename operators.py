import bpy
from .reference_loader import load_reference_data
from .rig_utils import (
    add_audit_log_entry,
    validate_selection,
    apply_transforms,
    setup_male_variant_rig_and_mesh,
    setup_female_variant_rig_and_mesh,
    rename_armature_and_datablock,
    purge_all_bone_collections,
    clear_pelvis_constraints,
    rename_uv_layers,
    merge_hip_weights_to_pelvis,
    merge_child_toe_weights_to_toes,
    merge_metacarpal_weights_to_hands,
    purge_bones_and_restructure_hierarchy,
    update_all_drivers_and_constraints,
    sync_bone_and_vertex_group_names,
    inject_ue5_als_ik_bones,
    consolidate_pre_split_materials,
    separate_head_mesh_by_material,
    prune_face_rig_bones,
    prune_body_rig_bones,
    purge_orphaned_vgroups_for_split,
    purge_all_animation_drivers,
    purge_body_shape_keys,
    optimize_head_shape_keys,
    join_head_and_facial_meshes,
    consolidate_post_join_head_materials,
    audit_final_material_slots,
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
            add_audit_log_entry(context, "Step 1", "Failed selection validation.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            apply_transforms(armature_obj, mesh_objs)
            
            # Auto-populate target dropdown selectors
            props.target_body_armature = armature_obj
            props.target_body_mesh = mesh_objs[0]

            props.active_armature_name = armature_obj.name
            props.step1_completed = True
            msg = f"Step 1 Complete: Applied transforms for '{armature_obj.name}' and {len(mesh_objs)} mesh(es)."
            props.status_message = msg
            
            add_audit_log_entry(context, "Step 1", f"Transforms applied for '{armature_obj.name}' and {len(mesh_objs)} mesh(es). Targets set.", "SUCCESS", "CHECKMARK")
            self.report({'INFO'}, msg)
            return {'FINISHED'}
            
        except Exception as e:
            err_text = f"Failed to prepare character: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Step 1", err_text, "ERROR", "ERROR")
            return {'CANCELLED'}


class MSK_OT_process_rig_vertex_groups(bpy.types.Operator):
    """Purge helper/toe/metacarpal bones, restructure hierarchy to UE5 standard, clean pelvis constraints, rename UV layers, and sync vertex groups."""
    bl_idname = "master_sk.process_rig_vertex_groups"
    bl_label = "2. Process Rig & Sync Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props
        
        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, err_msg or "Please select both the DAZ Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Step 2."
            add_audit_log_entry(context, "Step 2", "Selection invalid for Step 2.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            ref_path = props.custom_reference_path if props.use_custom_reference else None
            ref_data = load_reference_data(ref_path)

            # 1. Rename Armature Object to 'root' directly and Datablock to 'root'
            rename_armature_and_datablock(armature_obj, mesh_objs)

            # 2. Completely wipe all Bone Collections (Blender 4.4.3 un-grouped structure)
            purge_all_bone_collections(armature_obj)

            # 3. Clear pelvis pose constraints for ALS locomotion compatibility
            clear_pelvis_constraints(armature_obj)

            # 4. Rename primary UV map layers to 'UVMap'
            rename_uv_layers(mesh_objs)

            # 5. Merge vertex weights from 'hip' into 'pelvis' before purging hip bone to prevent skinning bugs
            merge_hip_weights_to_pelvis(mesh_objs)

            # 6. Merge 20 child toe weights into 'toes_l' and 'toes_r'
            merge_child_toe_weights_to_toes(mesh_objs)

            # 7. Merge 8 metacarpal weights into 'hand_l' and 'hand_r'
            meta_verts, meta_vgs = merge_metacarpal_weights_to_hands(mesh_objs)

            # 8. Bone Purge (including 20 child toe bones & 8 metacarpal bones) & Hierarchy Restructuring
            deleted_count = purge_bones_and_restructure_hierarchy(armature_obj, ref_data)

            # 9. Synchronized Vertex Group Renaming & Cleanup
            sync_bone_and_vertex_group_names(armature_obj, mesh_objs, ref_data)

            # 10. Update subtarget bone names across all drivers & constraints (e.g. l_eye -> eye_l)
            update_all_drivers_and_constraints(ref_data)

            props.step2_completed = True
            msg = f"Step 2 Complete: Restructured '{armature_obj.name}', purged {deleted_count} bones & transferred metacarpal/toe weights."
            props.status_message = msg
            
            add_audit_log_entry(context, "Step 2", f"Purged {deleted_count} bones; transferred {meta_verts} metacarpal vertex weights to hand_l/r.", "SUCCESS", "CHECKMARK")
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error processing rig & vertex groups: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Step 2", err_text, "ERROR", "ERROR")
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
            add_audit_log_entry(context, "Step 3", "Armature selection invalid for Step 3.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            inject_ue5_als_ik_bones(armature_obj)

            props.step3_completed = True
            msg = f"Step 3 Complete: Injected UE5/ALS IK bones for '{armature_obj.name}'."
            props.status_message = msg
            
            add_audit_log_entry(context, "Step 3", f"Injected ik_foot_root, ik_hand_root, ik_foot_l/r, ik_hand_l/r into '{armature_obj.name}'.", "SUCCESS", "CHECKMARK")
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error injecting IK bones: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Step 3", err_text, "ERROR", "ERROR")
            return {'CANCELLED'}


class MSK_OT_separate_head_modularize(bpy.types.Operator):
    """Consolidate pre-split materials, separate head geometry, split armatures into SKM_Body_Rig and SKM_Face_Rig, and purge orphaned weights."""
    bl_idname = "master_sk.separate_head_modularize"
    bl_label = "4. Modular Head & Body Rig Separator"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props

        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, "Please select the Master SK Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Step 4."
            add_audit_log_entry(context, "Step 4", "Selection invalid for Step 4.", "ERROR", "ERROR")
            return {'CANCELLED'}

        target_mesh = mesh_objs[0]

        try:
            ref_path = props.custom_reference_path if props.use_custom_reference else None
            ref_data = load_reference_data(ref_path)

            # Step 4.0: Consolidate Pre-Split Material Slots (Mouth Cavity -> Head, Nails -> Arms)
            pre_split_mat_logs = consolidate_pre_split_materials(target_mesh)
            if pre_split_mat_logs:
                add_audit_log_entry(context, "Step 4", pre_split_mat_logs, "INFO", "INFO")

            # Step 4.1: Separate Head Mesh via Material Slot
            head_mesh, body_mesh, sep_err = separate_head_mesh_by_material(target_mesh)
            if sep_err:
                self.report({'ERROR'}, sep_err)
                props.status_message = f"Error: {sep_err}"
                add_audit_log_entry(context, "Step 4", sep_err, "ERROR", "ERROR")
                return {'CANCELLED'}

            # Step 4.2: Duplicate Armature to create SKM_Body_Rig and SKM_Face_Rig
            body_rig = armature_obj
            body_rig.name = "SKM_Body_Rig"
            if body_rig.data:
                body_rig.data.name = "SKM_Body_Rig"

            bpy.ops.object.select_all(action='DESELECT')
            body_rig.select_set(True)
            bpy.context.view_layer.objects.active = body_rig
            bpy.ops.object.duplicate()
            face_rig = bpy.context.view_layer.objects.active
            face_rig.name = "SKM_Face_Rig"
            if face_rig.data:
                face_rig.data = body_rig.data.copy()
                face_rig.data.name = "SKM_Face_Rig"

            # Step 4.3: Prune SKM_Face_Rig & setup SKM_Head_Mesh
            prune_face_rig_bones(face_rig)
            sync_bone_and_vertex_group_names(face_rig, [head_mesh], ref_data)
            
            for mod in list(head_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    mod.object = face_rig
                    
            purge_orphaned_vgroups_for_split(head_mesh, face_rig)

            # Step 4.4: Prune SKM_Body_Rig & setup SKM_Body_Mesh
            prune_body_rig_bones(body_rig)
            sync_bone_and_vertex_group_names(body_rig, [body_mesh], ref_data)
            
            for mod in list(body_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    mod.object = body_rig

            purge_orphaned_vgroups_for_split(body_mesh, body_rig)

            head_mesh.parent = face_rig
            body_mesh.parent = body_rig

            # Step 4.5: Purge Drivers & Optimize Shape Keys for UE5 Export
            d_cleared = purge_all_animation_drivers()
            body_sk_cleared = purge_body_shape_keys(body_mesh)
            head_sk_optimized = optimize_head_shape_keys(head_mesh)

            # Auto-fill target pointers for Step 5
            props.target_head_armature = face_rig
            props.target_head_mesh = head_mesh

            props.step4_completed = True
            msg = "Step 4 Complete: Modularized head & body rigs, purged drivers, and optimized shape keys for UE5."
            props.status_message = msg
            
            add_audit_log_entry(context, "Step 4", f"Separated SKM_Head_Mesh & SKM_Body_Mesh. Purged {d_cleared} drivers, {body_sk_cleared} body shape keys & optimized head morphs.", "SUCCESS", "CHECKMARK")
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error modularizing head & rigs: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Step 4", err_text, "ERROR", "ERROR")
            return {'CANCELLED'}


class MSK_OT_join_facial_meshes(bpy.types.Operator):
    """Standardise UV maps across head/facial meshes, join into SKM_Head_Mesh, and consolidate Teeth -> Mouth and EyeMoisture -> Eyes."""
    bl_idname = "master_sk.join_facial_meshes"
    bl_label = "5. Join Facial Meshes & Finalize Head"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props

        # Resolve Head Mesh & Face Rig
        head_mesh = props.target_head_mesh or bpy.data.objects.get("SKM_Head_Mesh")
        body_mesh = props.target_body_mesh or bpy.data.objects.get("SKM_Body_Mesh")
        face_rig = props.target_head_armature or bpy.data.objects.get("SKM_Face_Rig")

        if not head_mesh or head_mesh.type != 'MESH':
            self.report({'ERROR'}, "Target SKM_Head_Mesh not found or invalid.")
            props.status_message = "Error: Target SKM_Head_Mesh invalid."
            add_audit_log_entry(context, "Step 5", "Target SKM_Head_Mesh invalid.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            ref_path = props.custom_reference_path if props.use_custom_reference else None
            ref_data = load_reference_data(ref_path)

            # Collect external facial meshes from properties or search fallback
            facial_objs = []
            for prop_obj in [props.target_eyes_mesh, props.target_eyelashes_mesh, props.target_mouth_mesh]:
                if prop_obj and prop_obj.name in bpy.data.objects and prop_obj != head_mesh:
                    facial_objs.append(prop_obj)

            if not facial_objs:
                # Search scene for unjoined facial meshes
                for obj in bpy.data.objects:
                    if obj.type == 'MESH' and obj != head_mesh and obj != body_mesh:
                        oname = obj.name.lower()
                        if any(k in oname for k in ["eye", "eyelash", "mouth", "teeth"]):
                            facial_objs.append(obj)

            # Step 5.1 & 5.2: Apply Transforms, Sync Weights to Face Rig, UV Standardisation & Joining
            success, join_msg = join_head_and_facial_meshes(head_mesh, facial_objs, face_rig, ref_data)
            add_audit_log_entry(context, "Step 5", join_msg, "INFO", "INFO")

            # Step 5.3: Post-Join Material Consolidation (Teeth -> Mouth, EyeMoisture -> Eyes)
            post_mat_logs = consolidate_post_join_head_materials(head_mesh)
            if post_mat_logs:
                add_audit_log_entry(context, "Step 5", post_mat_logs, "INFO", "INFO")

            # Step 5.4: Final Material Slot Audit
            slot_audit_text = audit_final_material_slots(head_mesh, body_mesh)
            add_audit_log_entry(context, "Step 5", slot_audit_text, "SUCCESS", "CHECKMARK")

            props.step5_completed = True
            msg = "Step 5 Complete: Joined facial meshes & consolidated head materials."
            props.status_message = msg
            
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error joining facial meshes & consolidating materials: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Step 5", err_text, "ERROR", "ERROR")
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
        
        msg = f"Loaded reference file from '{source_name}' ({num_mappings} bone mappings)."
        self.report({'INFO'}, msg)
        props.status_message = f"Reference File Loaded: {source_name}"
        add_audit_log_entry(context, "Ref", msg, "INFO", "FILE_REFRESH")
        return {'FINISHED'}


class MSK_OT_reset_progress(bpy.types.Operator):
    """Reset step completion checkmarks, audit log, and status message."""
    bl_idname = "master_sk.reset_progress"
    bl_label = "Reset Step Progress"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.master_sk_props
        props.step1_completed = False
        props.step2_completed = False
        props.step3_completed = False
        props.step4_completed = False
        props.step5_completed = False
        props.status_message = "Ready. Select your DAZ Armature and Character Mesh to begin."

        if hasattr(context.scene, "master_sk_audit_log"):
            context.scene.master_sk_audit_log.clear()

        self.report({'INFO'}, "Master SK workflow progress & audit log reset.")
        return {'FINISHED'}


class MSK_OT_setup_male(bpy.types.Operator):
    """Deletes pectoral bones and purges pectoral vertex groups for male character variants."""
    bl_idname = "master_sk.setup_male"
    bl_label = "Set Up Male Variant"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props
        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, "Please select both the Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Male Variant Setup."
            add_audit_log_entry(context, "Gender Setup", "Selection invalid for Male Setup.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            success, msg = setup_male_variant_rig_and_mesh(armature_obj, mesh_objs)
            if not success:
                self.report({'ERROR'}, msg)
                props.status_message = f"Error: {msg}"
                add_audit_log_entry(context, "Gender Setup", msg, "ERROR", "ERROR")
                return {'CANCELLED'}

            props.status_message = msg
            add_audit_log_entry(context, "Gender Setup", "Male variant configured: Pectoral bones & vertex groups removed.", "SUCCESS", "USER")
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error configuring male variant: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Gender Setup", err_text, "ERROR", "ERROR")
            return {'CANCELLED'}


class MSK_OT_setup_female(bpy.types.Operator):
    """Retains pectoral bones and injects glute_l/r bones with generated vertex weights for female character variants."""
    bl_idname = "master_sk.setup_female"
    bl_label = "Set Up Female Variant"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.master_sk_props
        armature_obj, mesh_objs, err_msg = validate_selection(context)
        if not armature_obj or not mesh_objs:
            self.report({'ERROR'}, "Please select both the Armature and Character Mesh.")
            props.status_message = "Error: Selection invalid for Female Variant Setup."
            add_audit_log_entry(context, "Gender Setup", "Selection invalid for Female Setup.", "ERROR", "ERROR")
            return {'CANCELLED'}

        try:
            success, msg = setup_female_variant_rig_and_mesh(armature_obj, mesh_objs)
            if not success:
                self.report({'ERROR'}, msg)
                props.status_message = f"Error: {msg}"
                add_audit_log_entry(context, "Gender Setup", msg, "ERROR", "ERROR")
                return {'CANCELLED'}

            props.status_message = msg
            add_audit_log_entry(context, "Gender Setup", "Female variant configured: Glute bones injected and weights generated.", "SUCCESS", "USER")
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        except Exception as e:
            err_text = f"Error configuring female variant: {str(e)}"
            self.report({'ERROR'}, err_text)
            props.status_message = f"Error: {err_text}"
            add_audit_log_entry(context, "Gender Setup", err_text, "ERROR", "ERROR")
            return {'CANCELLED'}


classes = (
    MSK_OT_prepare_character,
    MSK_OT_setup_male,
    MSK_OT_setup_female,
    MSK_OT_process_rig_vertex_groups,
    MSK_OT_inject_ik_bones,
    MSK_OT_separate_head_modularize,
    MSK_OT_join_facial_meshes,
    MSK_OT_reload_reference,
    MSK_OT_reset_progress,
)

def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister_operators():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

