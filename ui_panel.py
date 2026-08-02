import bpy

class MSK_PT_main_panel(bpy.types.Panel):
    """Sidebar Panel for Master SK DAZ to UE5/ALS Rig Conversion & Modularization Tools"""
    bl_label = "Master SK Tools"
    bl_idname = "MSK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master SK"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.master_sk_props

        completed_steps = sum([
            props.step1_completed,
            props.step2_completed,
            props.step3_completed,
            props.step4_completed
        ])
        
        # Header Box
        header_box = layout.box()
        h_row = header_box.row(align=True)
        h_row.label(text="Master SK Pipeline", icon='ARMATURE_DATA')
        h_row.label(text=f"[{completed_steps}/4 Done]")

        # Active Selection Info Box
        sel_box = layout.box()
        s_col = sel_box.column(align=True)
        
        armature_names = []
        mesh_names = []
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                armature_names.append(obj.name)
            elif obj.type == 'MESH':
                mesh_names.append(obj.name)

        if armature_names:
            s_col.label(text=f"Rig: {', '.join(armature_names[:2])}", icon='POSE_HLT')
        else:
            s_col.label(text="Rig: None Selected", icon='RADIOBUT_OFF')

        if mesh_names:
            s_col.label(text=f"Mesh: {', '.join(mesh_names[:2])}", icon='OUTLINER_OB_MESH')
        else:
            s_col.label(text="Mesh: None Selected", icon='RADIOBUT_OFF')

        # Status Message Box
        if props.status_message:
            msg_box = layout.box()
            msg_row = msg_box.row()
            if "Error" in props.status_message:
                msg_row.alert = True
                msg_row.label(text=props.status_message, icon='ERROR')
            elif "Complete" in props.status_message:
                msg_row.label(text=props.status_message, icon='CHECKMARK')
            else:
                msg_row.label(text=props.status_message, icon='INFO')

        layout.separator()

        # STEP 1 BOX
        step1_box = layout.box()
        s1_row = step1_box.row(align=True)
        s1_icon = 'CHECKMARK' if props.step1_completed else 'RADIOBUT_OFF'
        s1_row.label(text="Step 1: Prepare Character", icon=s1_icon)

        g1_col = step1_box.column(align=True)
        g1_col.scale_y = 0.8
        g1_col.label(text="Select Armature & Mesh; apply transforms", icon='HELP')
        
        b1_col = step1_box.column(align=True)
        b1_col.scale_y = 1.25
        b1_col.operator("master_sk.prepare_character", text="1. Prepare Active Character", icon='PLAY')

        layout.separator()

        # STEP 2 BOX
        step2_box = layout.box()
        s2_row = step2_box.row(align=True)
        s2_icon = 'CHECKMARK' if props.step2_completed else 'RADIOBUT_OFF'
        s2_row.label(text="Step 2: Rig & Weight Sync", icon=s2_icon)

        g2_col = step2_box.column(align=True)
        g2_col.scale_y = 0.8
        g2_col.label(text="Purge helpers/toes, clear constraints, UVMap", icon='HELP')

        b2_col = step2_box.column(align=True)
        b2_col.scale_y = 1.25
        b2_col.operator("master_sk.process_rig_vertex_groups", text="2. Process Rig & Sync Vertex Groups", icon='MOD_ARMATURE')

        layout.separator()

        # STEP 3 BOX
        step3_box = layout.box()
        s3_row = step3_box.row(align=True)
        s3_icon = 'CHECKMARK' if props.step3_completed else 'RADIOBUT_OFF'
        s3_row.label(text="Step 3: Inject IK Bones", icon=s3_icon)

        g3_col = step3_box.column(align=True)
        g3_col.scale_y = 0.8
        g3_col.label(text="Inject ik_foot & ik_hand bones (UE5 / ALS)", icon='HELP')

        b3_col = step3_box.column(align=True)
        b3_col.scale_y = 1.25
        b3_col.operator("master_sk.inject_ik_bones", text="3. Inject UE5 / ALS IK Bones", icon='BONE_DATA')

        layout.separator()

        # STEP 4 BOX
        step4_box = layout.box()
        s4_row = step4_box.row(align=True)
        s4_icon = 'CHECKMARK' if props.step4_completed else 'RADIOBUT_OFF'
        s4_row.label(text="Step 4: Modular Head & Face Split", icon=s4_icon)

        g4_col = step4_box.column(align=True)
        g4_col.scale_y = 0.8
        g4_col.label(text="Split head mesh & create Body/Face Rigs", icon='HELP')

        b4_col = step4_box.column(align=True)
        b4_col.scale_y = 1.25
        b4_col.operator("master_sk.separate_head_modularize", text="4. Separate Head & Modularize Rigs", icon='MOD_BOOLEAN')

        layout.separator()

        # CONFIGURATION & UTILITIES BOX
        util_box = layout.box()
        u_header = util_box.row()
        u_header.label(text="Reference & Utilities", icon='SETTINGS')

        util_box.prop(props, "use_custom_reference", text="Custom Reference Path")
        if props.use_custom_reference:
            util_box.prop(props, "custom_reference_path", text="Path")

        u_row = util_box.row(align=True)
        u_row.operator("master_sk.reload_reference", text="Reload Ref", icon='FILE_REFRESH')
        u_row.operator("master_sk.reset_progress", text="Reset Progress", icon='LOOP_BACK')


def register_panel():
    bpy.utils.register_class(MSK_PT_main_panel)

def unregister_panel():
    bpy.utils.unregister_class(MSK_PT_main_panel)
