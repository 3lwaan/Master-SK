bl_info = {
    "name": "Master SK",
    "author": "Gate Studio",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Master SK",
    "description": "Automates DAZ Genesis 9 rig conversion to UE5 / ALS Master Skeleton Hierarchy with synchronized vertex weight safety.",
    "warning": "",
    "doc_url": "",
    "category": "Rigging / Pipeline",
}

import bpy
from bpy.props import BoolProperty, StringProperty, PointerProperty
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

class MasterSKProperties(PropertyGroup):
    step1_completed: BoolProperty(
        name="Step 1 Completed",
        default=False
    )
    step2_completed: BoolProperty(
        name="Step 2 Completed",
        default=False
    )
    step3_completed: BoolProperty(
        name="Step 3 Completed",
        default=False
    )
    status_message: StringProperty(
        name="Status Message",
        default="Ready. Select your DAZ Armature and Character Mesh to begin."
    )
    active_armature_name: StringProperty(
        name="Active Armature",
        default=""
    )
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
    MasterSKProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.master_sk_props = PointerProperty(type=MasterSKProperties)
    
    register_operators()
    register_panel()
    print("[Master SK] Addon registered successfully.")

def unregister():
    unregister_panel()
    unregister_operators()

    if hasattr(bpy.types.Scene, "master_sk_props"):
        del bpy.types.Scene.master_sk_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[Master SK] Addon unregistered.")

if __name__ == "__main__":
    register()
