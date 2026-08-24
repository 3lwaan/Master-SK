# MasterSK UI package initialization
import bpy
from .panel import MASTERSK_OT_auto_detect, MASTERSK_PT_main_panel

classes = (
    MASTERSK_OT_auto_detect,
    MASTERSK_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
