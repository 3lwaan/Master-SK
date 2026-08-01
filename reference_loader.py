import os
import json
import importlib.util
from pathlib import Path

DEFAULT_DAZ_TO_MASTER_MAP = {
    "hip": "pelvis",
    "pelvis": "pelvis",
    "spine1": "spine_01",
    "spine2": "spine_02",
    "spine3": "spine_03",
    "neck": "neck_01",
    "head": "head",
    "l_shoulder": "clavicle_l",
    "l_arm": "upperarm_l",
    "l_forearm": "lowerarm_l",
    "l_hand": "hand_l",
    "r_shoulder": "clavicle_r",
    "r_arm": "upperarm_r",
    "r_forearm": "lowerarm_r",
    "r_hand": "hand_r",
    "l_thigh": "thigh_l",
    "l_shin": "calf_l",
    "l_foot": "foot_l",
    "l_toes": "ball_l",
    "r_thigh": "thigh_r",
    "r_shin": "calf_r",
    "r_foot": "foot_r",
    "r_toes": "ball_r",
}

DEFAULT_MASTER_SK_HIERARCHY = {
    "root": None,
    "pelvis": "root",
    "spine_01": "pelvis",
    "spine_02": "spine_01",
    "spine_03": "spine_02",
    "neck_01": "spine_03",
    "head": "neck_01",
    "clavicle_l": "spine_03",
    "upperarm_l": "clavicle_l",
    "lowerarm_l": "upperarm_l",
    "hand_l": "lowerarm_l",
    "clavicle_r": "spine_03",
    "upperarm_r": "clavicle_r",
    "lowerarm_r": "upperarm_r",
    "hand_r": "lowerarm_r",
    "thigh_l": "pelvis",
    "calf_l": "thigh_l",
    "foot_l": "calf_l",
    "ball_l": "foot_l",
    "thigh_r": "pelvis",
    "calf_r": "thigh_r",
    "foot_r": "calf_r",
    "ball_r": "foot_r",
    "ik_foot_root": "root",
    "ik_foot_l": "ik_foot_root",
    "ik_foot_r": "ik_foot_root",
    "ik_hand_root": "root",
    "ik_hand_l": "ik_hand_root",
    "ik_hand_r": "ik_hand_root",
}

DEFAULT_BONES_TO_DELETE = [
    "l_hand_anchor",
    "r_hand_anchor",
    "l_foot_anchor",
    "r_foot_anchor",
]

def load_reference_data(file_path=None):
    """
    Loads DAZ_TO_MASTER_MAP, MASTER_SK_HIERARCHY, and BONES_TO_DELETE from an external
    Python or JSON reference file.
    If no file_path is specified, searches the addon directory for daz_g9_reference.py or daz_g9_reference.json.
    """
    addon_dir = Path(__file__).parent.resolve()
    
    target_path = None
    if file_path and os.path.exists(file_path):
        target_path = Path(file_path)
    else:
        py_default = addon_dir / "daz_g9_reference.py"
        json_default = addon_dir / "daz_g9_reference.json"
        if py_default.exists():
            target_path = py_default
        elif json_default.exists():
            target_path = json_default

    if not target_path or not target_path.exists():
        return {
            "DAZ_TO_MASTER_MAP": DEFAULT_DAZ_TO_MASTER_MAP.copy(),
            "MASTER_SK_HIERARCHY": DEFAULT_MASTER_SK_HIERARCHY.copy(),
            "BONES_TO_DELETE": DEFAULT_BONES_TO_DELETE.copy(),
            "source": "INTERNAL_DEFAULTS"
        }

    ext = target_path.suffix.lower()

    if ext == ".json":
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "DAZ_TO_MASTER_MAP": data.get("DAZ_TO_MASTER_MAP", DEFAULT_DAZ_TO_MASTER_MAP.copy()),
                "MASTER_SK_HIERARCHY": data.get("MASTER_SK_HIERARCHY", DEFAULT_MASTER_SK_HIERARCHY.copy()),
                "BONES_TO_DELETE": data.get("BONES_TO_DELETE", DEFAULT_BONES_TO_DELETE.copy()),
                "source": str(target_path)
            }
        except Exception as e:
            print(f"[MasterSK] Error parsing JSON reference file '{target_path}': {e}")

    elif ext == ".py":
        try:
            spec = importlib.util.spec_from_file_location("master_sk_ref_module", target_path)
            if spec and spec.loader:
                ref_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ref_module)
                
                daz_map = getattr(ref_module, "DAZ_TO_MASTER_MAP", DEFAULT_DAZ_TO_MASTER_MAP.copy())
                hierarchy = getattr(ref_module, "MASTER_SK_HIERARCHY", DEFAULT_MASTER_SK_HIERARCHY.copy())
                to_delete = getattr(ref_module, "BONES_TO_DELETE", DEFAULT_BONES_TO_DELETE.copy())

                return {
                    "DAZ_TO_MASTER_MAP": daz_map,
                    "MASTER_SK_HIERARCHY": hierarchy,
                    "BONES_TO_DELETE": to_delete,
                    "source": str(target_path)
                }
        except Exception as e:
            print(f"[MasterSK] Error loading Python reference module '{target_path}': {e}")

    return {
        "DAZ_TO_MASTER_MAP": DEFAULT_DAZ_TO_MASTER_MAP.copy(),
        "MASTER_SK_HIERARCHY": DEFAULT_MASTER_SK_HIERARCHY.copy(),
        "BONES_TO_DELETE": DEFAULT_BONES_TO_DELETE.copy(),
        "source": "FALLBACK"
    }
