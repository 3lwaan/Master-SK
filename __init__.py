bl_info = {
    "name": "Master SK",
    "author": "Gate Studio",
    "version": (2, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Master SK",
    "description": "Automates DAZ Genesis 9 rig conversion to UE5 / ALS Master Skeleton Hierarchy with modular head separation & material optimization.",
    "warning": "",
    "doc_url": "",
    "category": "Rigging / Pipeline",
}

import bpy
from bpy.props import BoolProperty, StringProperty, PointerProperty, CollectionProperty
from bpy.types import PropertyGroup

if "bpy" in locals():
    import importlib
    if "reference_loader" in locals():
        importlib.reload(reference_loader)
    if "rig_utils" in locals():
        importlib.reload(rig_utils)
    if "operators" in locals():
        importlib.reload(operators)
    if "ui_panel" in locals():
        importlib.reload(ui_panel)
else:
    from . import reference_loader
    from . import rig_utils
    from . import operators
    from . import ui_panel

from .operators import register_operators, unregister_operators
from .ui_panel import register_panel, unregister_panel


def poll_armature(self, object):
    return object and object.type == 'ARMATURE'


def poll_mesh(self, object):
    return object and object.type == 'MESH'


class MasterSKAuditLogItem(PropertyGroup):
    timestamp: StringProperty(name="Timestamp", default="")
    step_name: StringProperty(name="Step Name", default="")
    message: StringProperty(name="Message", default="")
    status_type: StringProperty(name="Status Type", default="SUCCESS")
    icon_name: StringProperty(name="Icon Name", default="CHECKMARK")


class MasterSKProperties(PropertyGroup):
    # Step Completion States
    step1_completed: BoolProperty(name="Step 1 Completed", default=False)
    step2_completed: BoolProperty(name="Step 2 Completed", default=False)
    step3_completed: BoolProperty(name="Step 3 Completed", default=False)
    step4_completed: BoolProperty(name="Step 4 Completed", default=False)
    step5_completed: BoolProperty(name="Step 5 Completed", default=False)

    # Dynamic Object Target Selectors
    target_body_armature: PointerProperty(
        name="Target Body Rig",
        type=bpy.types.Object,
        poll=poll_armature,
        description="Active Body Armature object for conversion"
    )
    target_body_mesh: PointerProperty(
        name="Target Body Mesh",
        type=bpy.types.Object,
        poll=poll_mesh,
        description="Primary Body Character Mesh object"
    )
    target_head_armature: PointerProperty(
        name="Target Head Rig",
        type=bpy.types.Object,
        poll=poll_armature,
        description="Separated SKM_Face_Rig object"
    )
    target_head_mesh: PointerProperty(
        name="Target Head Mesh",
        type=bpy.types.Object,
        poll=poll_mesh,
        description="Separated SKM_Head_Mesh object"
    )

    # External Facial Mesh Selectors (Step 5)
    target_eyes_mesh: PointerProperty(
        name="Eyes Mesh",
        type=bpy.types.Object,
        poll=poll_mesh,
        description="External DAZ Eyes mesh object"
    )
    target_eyelashes_mesh: PointerProperty(
        name="Eyelashes Mesh",
        type=bpy.types.Object,
        poll=poll_mesh,
        description="External DAZ Eyelashes mesh object"
    )
    target_mouth_mesh: PointerProperty(
        name="Mouth Mesh",
        type=bpy.types.Object,
        poll=poll_mesh,
        description="External DAZ Mouth/Teeth mesh object"
    )

    # UI Settings & Status
    status_message: StringProperty(
        name="Status Message",
        default="Ready. Select your DAZ Armature and Character Mesh to begin."
    )
    active_armature_name: StringProperty(name="Active Armature", default="")
    show_audit_log: BoolProperty(name="Show Audit Log", default=True)

    use_custom_reference: BoolProperty(
        name="Use Custom Reference",
        default=False,
        description="Load mapping configuration from a custom Python or JSON file"
    )
    custom_reference_path: StringProperty(
        name="Custom Reference Path",
        subtype='FILE_PATH',
        default="",
        description="Absolute file path to custom .py or .json reference mapping file"
    )


classes = (
    MasterSKAuditLogItem,
    MasterSKProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.master_sk_props = PointerProperty(type=MasterSKProperties)
    bpy.types.Scene.master_sk_audit_log = CollectionProperty(type=MasterSKAuditLogItem)
    
    register_operators()
    register_panel()
    print("[Master SK v2.0] Addon registered successfully.")

def unregister():
    unregister_panel()
    unregister_operators()

    if hasattr(bpy.types.Scene, "master_sk_props"):
        del bpy.types.Scene.master_sk_props
    if hasattr(bpy.types.Scene, "master_sk_audit_log"):
        del bpy.types.Scene.master_sk_audit_log

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[Master SK v2.0] Addon unregistered.")

if __name__ == "__main__":
    register()
