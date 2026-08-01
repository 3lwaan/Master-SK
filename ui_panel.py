import bpy

class MSK_PT_main_panel(bpy.types.Panel):
    """Sidebar Panel for Master SK DAZ to UE5/ALS Rig Conversion Tools"""
    bl_label = "Master SK Tools"
    bl_idname = "MSK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master SK"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.master_sk_props

        # Header Box
        header_box = layout.box()
        header_row = header_box.row(align=True)
        header_row.label(text="Master SK - DAZ Genesis 9", icon='ARMATURE_DATA')

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
        s1_row.label(text="Step 1: Preparation", icon=s1_icon)

        # Guide Text
        guide_col = step1_box.column(align=True)
        guide_col.scale_y = 0.8
        guide_col.label(text="Select DAZ Armature & Character Mesh", icon='HELP')
        
        # Step 1 Operator Button
        btn1 = step1_box.operator("master_sk.prepare_character", text="1. Prepare Active Character", icon='PLAY')

        layout.separator()

        # STEP 2 BOX
        step2_box = layout.box()
        s2_row = step2_box.row(align=True)
        s2_icon = 'CHECKMARK' if props.step2_completed else 'RADIOBUT_OFF'
        s2_row.label(text="Step 2: Rig & Weight Sync", icon=s2_icon)

        s2_guide = step2_box.column(align=True)
        s2_guide.scale_y = 0.8
        s2_guide.label(text="Purge helpers, align hierarchy, sync weights", icon='HELP')

        btn2 = step2_box.operator("master_sk.process_rig_vertex_groups", text="2. Process Rig & Sync Vertex Groups", icon='MOD_ARMATURE')

        layout.separator()

        # STEP 3 BOX
        step3_box = layout.box()
        s3_row = step3_box.row(align=True)
        s3_icon = 'CHECKMARK' if props.step3_completed else 'RADIOBUT_OFF'
        s3_row.label(text="Step 3: Inject UE5 / ALS IK Bones", icon=s3_icon)

        s3_guide = step3_box.column(align=True)
        s3_guide.scale_y = 0.8
        s3_guide.label(text="Inject ik_foot & ik_hand bones (UE5 / ALS)", icon='HELP')

        btn3 = step3_box.operator("master_sk.inject_ik_bones", text="3. Inject UE5 / ALS IK Bones", icon='BONE_DATA')

        layout.separator()

        # REFERENCE FILE SETTINGS BOX
        ref_box = layout.box()
        ref_header = ref_box.row()
        ref_header.label(text="Reference File Configuration", icon='FILE_TEXT')

        ref_box.prop(props, "use_custom_reference", text="Custom Reference Path")
        if props.use_custom_reference:
            ref_box.prop(props, "custom_reference_path", text="Path")

        ref_box.operator("master_sk.reload_reference", text="Reload Reference File", icon='FILE_REFRESH')


def register_panel():
    bpy.utils.register_class(MSK_PT_main_panel)

def unregister_panel():
    bpy.utils.unregister_class(MSK_PT_main_panel)
