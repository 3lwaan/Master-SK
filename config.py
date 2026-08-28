# MasterSK Configuration & Mapping Tables
# Pipeline v3: ALS hierarchy — "root" is the armature object, pelvis is
# the top-level bone (no root bone exists in ALS).
import os

ADDON_NAME = "MasterSK"
ASSET_BLEND_FILE = "als_base_skeleton.blend"

def get_asset_path(filename=ASSET_BLEND_FILE):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)

# ---------------------------------------------------------------------------
# Sentinel used in WEIGHT_CONSOLIDATION_MAP to reference the dynamic root bone.
# The root bone in Genesis 9 is named after the character (e.g. "Anice", "Sara").
# Operators must detect it at runtime as the only bone with no parent.
# In Step 2, this bone is DELETED and its weight merges into pelvis.
# ---------------------------------------------------------------------------
ROOT_BONE_SENTINEL = "__ROOT__"

# ---------------------------------------------------------------------------
# Step 1: Weight Consolidation Map
# Source vertex groups are merged INTO the target (key) vertex group.
# The target group is created if it does not exist.
# After merging, source groups are deleted from the mesh.
# ---------------------------------------------------------------------------
WEIGHT_CONSOLIDATION_MAP = {
    # Root & Hip -- hip weight merges into the character-named root bone.
    # In Step 2, the root bone itself is deleted and its weight merges
    # into pelvis (since ALS has no root bone).
    ROOT_BONE_SENTINEL: ["hip"],

    # Spines & Pectorals
    "spine3": [
        "spine4", "l_pectoral", "r_pectoral",
        "l_pectoral(drv)", "r_pectoral(drv)"
    ],

    # Neck
    "neck1": ["neck2"],

    # Hands, Metacarpals & Anchors
    "l_hand": [
        "l_hand_anchor", "l_indexmetacarpal", "l_midmetacarpal",
        "l_ringmetacarpal", "l_pinkymetacarpal"
    ],
    "r_hand": [
        "r_hand_anchor", "r_indexmetacarpal", "r_midmetacarpal",
        "r_ringmetacarpal", "r_pinkymetacarpal"
    ],

    # Left Foot (metatarsal merges into foot, not toes)
    "l_foot": ["l_metatarsal"],

    # Left Toes (merge all 10 individual toe bones into l_toes)
    "l_toes": [
        "l_bigtoe1", "l_bigtoe2",
        "l_indextoe1", "l_indextoe2", "l_midtoe1", "l_midtoe2",
        "l_ringtoe1", "l_ringtoe2", "l_pinkytoe1", "l_pinkytoe2"
    ],

    # Right Foot
    "r_foot": ["r_metatarsal"],

    # Right Toes
    "r_toes": [
        "r_bigtoe1", "r_bigtoe2",
        "r_indextoe1", "r_indextoe2", "r_midtoe1", "r_midtoe2",
        "r_ringtoe1", "r_ringtoe2", "r_pinkytoe1", "r_pinkytoe2"
    ],

    # Arm Twists & Drivers (twist2 + both drv merge into twist1)
    "l_upperarmtwist1": [
        "l_upperarmtwist2", "l_upperarmtwist1(drv)", "l_upperarmtwist2(drv)"
    ],
    "r_upperarmtwist1": [
        "r_upperarmtwist2", "r_upperarmtwist1(drv)", "r_upperarmtwist2(drv)"
    ],
    "l_forearmtwist1": [
        "l_forearmtwist2", "l_forearmtwist1(drv)", "l_forearmtwist2(drv)"
    ],
    "r_forearmtwist1": [
        "r_forearmtwist2", "r_forearmtwist1(drv)", "r_forearmtwist2(drv)"
    ],

    # Leg Twists & Drivers
    "l_thightwist1": [
        "l_thightwist2", "l_thightwist1(drv)", "l_thightwist2(drv)"
    ],
    "r_thightwist1": [
        "r_thightwist2", "r_thightwist1(drv)", "r_thightwist2(drv)"
    ],
}

# ---------------------------------------------------------------------------
# Step 2: Bones to Keep (Whitelist)
# After weight merging, every bone NOT in this set (and NOT a facial bone
# child of 'head') is deleted from the armature in Edit Mode.
# The character-named root bone is NOT in this set — it gets deleted.
# "hip" is NOT in this set — it was merged in Step 1.
# Pelvis becomes the top-level bone (matching ALS).
# ---------------------------------------------------------------------------
BONES_TO_KEEP = {
    # Pelvis is the top-level bone in ALS (no root bone)
    "pelvis",
    "spine1", "spine2", "spine3",
    "neck1", "head",

    # Left Arm
    "l_shoulder", "l_upperarm", "l_upperarmtwist1",
    "l_forearm", "l_forearmtwist1", "l_hand",

    # Left Fingers
    "l_thumb1", "l_thumb2", "l_thumb3",
    "l_index1", "l_index2", "l_index3",
    "l_mid1", "l_mid2", "l_mid3",
    "l_ring1", "l_ring2", "l_ring3",
    "l_pinky1", "l_pinky2", "l_pinky3",

    # Right Arm
    "r_shoulder", "r_upperarm", "r_upperarmtwist1",
    "r_forearm", "r_forearmtwist1", "r_hand",

    # Right Fingers
    "r_thumb1", "r_thumb2", "r_thumb3",
    "r_index1", "r_index2", "r_index3",
    "r_mid1", "r_mid2", "r_mid3",
    "r_ring1", "r_ring2", "r_ring3",
    "r_pinky1", "r_pinky2", "r_pinky3",

    # Left Leg
    "l_thigh", "l_thightwist1", "l_shin", "l_foot", "l_toes",

    # Right Leg
    "r_thigh", "r_thightwist1", "r_shin", "r_foot", "r_toes",
}

# ---------------------------------------------------------------------------
# Step 3: Bone Rename Mapping (G9 -> ALS)
# Applied to both armature bones AND mesh vertex groups simultaneously.
# Note: There is NO "root" bone in ALS. "root" is the armature object name.
# Pelvis is the top-level bone and keeps its name.
# ---------------------------------------------------------------------------
BONE_NAME_MAPPING = {
    # Core / Pelvis (top-level bone in ALS)
    "pelvis": "pelvis",
    "spine1": "spine_01",
    "spine2": "spine_02",
    "spine3": "spine_03",

    # Neck & Head
    "neck1": "neck_01",
    "head": "head",

    # Left Arm Chain
    "l_shoulder": "clavicle_l",
    "l_upperarm": "upperarm_l",
    "l_upperarmtwist1": "upperarm_twist_01_l",
    "l_forearm": "lowerarm_l",
    "l_forearmtwist1": "lowerarm_twist_01_l",
    "l_hand": "hand_l",

    # Left Hand Fingers
    "l_thumb1": "thumb_01_l",
    "l_thumb2": "thumb_02_l",
    "l_thumb3": "thumb_03_l",
    "l_index1": "index_01_l",
    "l_index2": "index_02_l",
    "l_index3": "index_03_l",
    "l_mid1": "middle_01_l",
    "l_mid2": "middle_02_l",
    "l_mid3": "middle_03_l",
    "l_ring1": "ring_01_l",
    "l_ring2": "ring_02_l",
    "l_ring3": "ring_03_l",
    "l_pinky1": "pinky_01_l",
    "l_pinky2": "pinky_02_l",
    "l_pinky3": "pinky_03_l",

    # Right Arm Chain
    "r_shoulder": "clavicle_r",
    "r_upperarm": "upperarm_r",
    "r_upperarmtwist1": "upperarm_twist_01_r",
    "r_forearm": "lowerarm_r",
    "r_forearmtwist1": "lowerarm_twist_01_r",
    "r_hand": "hand_r",

    # Right Hand Fingers
    "r_thumb1": "thumb_01_r",
    "r_thumb2": "thumb_02_r",
    "r_thumb3": "thumb_03_r",
    "r_index1": "index_01_r",
    "r_index2": "index_02_r",
    "r_index3": "index_03_r",
    "r_mid1": "middle_01_r",
    "r_mid2": "middle_02_r",
    "r_mid3": "middle_03_r",
    "r_ring1": "ring_01_r",
    "r_ring2": "ring_02_r",
    "r_ring3": "ring_03_r",
    "r_pinky1": "pinky_01_r",
    "r_pinky2": "pinky_02_r",
    "r_pinky3": "pinky_03_r",

    # Left Leg Chain
    "l_thigh": "thigh_l",
    "l_thightwist1": "thigh_twist_01_l",
    "l_shin": "calf_l",
    "l_foot": "foot_l",
    "l_toes": "ball_l",

    # Right Leg Chain
    "r_thigh": "thigh_r",
    "r_thightwist1": "thigh_twist_01_r",
    "r_shin": "calf_r",
    "r_foot": "foot_r",
    "r_toes": "ball_r",
}

# ---------------------------------------------------------------------------
# Keywords to classify material slots for mesh separation (Step 5)
# ---------------------------------------------------------------------------
HEAD_MATERIAL_KEYWORDS = [
    "head", "face", "eye", "cornea", "teeth", "mouth",
    "tongue", "eyelash", "brow", "tear", "moisture", "pupil", "sclera"
]

BODY_MATERIAL_KEYWORDS = [
    "body", "torso", "arm", "arms", "leg", "legs",
    "skin", "nails", "limbs", "finger", "fingers"
]

# ---------------------------------------------------------------------------
# ALS Epic Mannequin Base IK Bones (appended from asset, Step 6)
# ---------------------------------------------------------------------------
ALS_IK_BONES = [
    "ik_foot_root", "ik_foot_l", "ik_foot_r",
    "ik_hand_root", "ik_hand_gun", "ik_hand_l", "ik_hand_r"
]

# ---------------------------------------------------------------------------
# Torso bones kept in the Head/Face rig for UE modular alignment (Step 8)
# Note: No "root" bone — pelvis is the top-level bone in ALS.
# ---------------------------------------------------------------------------
BASE_TORSO_BONES = [
    "pelvis", "spine_01", "spine_02", "spine_03",
    "clavicle_l", "clavicle_r", "neck_01", "head",
    "upperarm_l", "upperarm_twist_01_l",
    "upperarm_r", "upperarm_twist_01_r"
]

# ---------------------------------------------------------------------------
# MasterSK FACS-to-ARKit Baking Map (Step 7)
# Maps the 52 standard Apple ARKit shape keys to their Daz FACS constituents.
# Missing components are ignored dynamically if not present on the mesh.
# ---------------------------------------------------------------------------
ARKIT_BAKING_MAP = {
    "EyeBlinkLeft": ["facs_bs_EyeBlinkLeft"],
    "EyeLookDownLeft": ["facs_bs_EyeLookDownLeft"],
    "EyeLookInLeft": ["facs_bs_EyeLookInLeft"],
    "EyeLookOutLeft": ["facs_bs_EyeLookOutLeft"],
    "EyeLookUpLeft": ["facs_bs_EyeLookUpLeft"],
    "EyeSquintLeft": ["facs_bs_EyeSquintLeft"],
    "EyeWideLeft": ["facs_bs_EyelidOpenUpperLeft", "facs_bs_EyelidOpenLowerLeft"],
    "EyeBlinkRight": ["facs_bs_EyeBlinkRight"],
    "EyeLookDownRight": ["facs_bs_EyeLookDownRight"],
    "EyeLookInRight": ["facs_bs_EyeLookInRight"],
    "EyeLookOutRight": ["facs_bs_EyeLookOutRight"],
    "EyeLookUpRight": ["facs_bs_EyeLookUpRight"],
    "EyeSquintRight": ["facs_bs_EyeSquintRight"],
    "EyeWideRight": ["facs_bs_EyelidOpenUpperRight", "facs_bs_EyelidOpenLowerRight"],
    "JawForward": ["facs_bs_JawChinCompression"], # Approximation or explicit if it exists
    "JawRight": ["facs_bs_JawRight"],
    "JawLeft": ["facs_bs_JawLeft"],
    "JawOpen": ["facs_bs_JawOpen"],
    "MouthClose": ["facs_bs_MouthCloseLowerLeft", "facs_bs_MouthCloseLowerRight", "facs_bs_MouthCloseUpperLeft", "facs_bs_MouthCloseUpperRight"],
    "MouthFunnel": ["facs_bs_MouthFunnelLowerLeft", "facs_bs_MouthFunnelLowerRight", "facs_bs_MouthFunnelUpperLeft", "facs_bs_MouthFunnelUpperRight"],
    "MouthPucker": ["facs_bs_MouthPurseLowerLeft", "facs_bs_MouthPurseLowerRight", "facs_bs_MouthPurseUpperLeft", "facs_bs_MouthPurseUpperRight"],
    "MouthLeft": ["facs_bs_MouthLeft"],
    "MouthRight": ["facs_bs_MouthRight"],
    "MouthSmileLeft": ["facs_bs_MouthSmileLeft"],
    "MouthSmileRight": ["facs_bs_MouthSmileRight"],
    "MouthFrownLeft": ["facs_bs_MouthFrownLeft"],
    "MouthFrownRight": ["facs_bs_MouthFrownRight"],
    "MouthDimpleLeft": ["facs_bs_MouthDimpleLeft"],
    "MouthDimpleRight": ["facs_bs_MouthDimpleRight"],
    "MouthStretchLeft": ["facs_bs_MouthStretchLeft"],
    "MouthStretchRight": ["facs_bs_MouthStretchRight"],
    "MouthRollLower": ["facs_bs_MouthRollLowerLeft", "facs_bs_MouthRollLowerRight"],
    "MouthRollUpper": ["facs_bs_MouthRollUpperLeft", "facs_bs_MouthRollUpperRight"],
    "MouthShrugLower": ["facs_bs_MouthShrugLowerLeft", "facs_bs_MouthShrugLowerRight"],
    "MouthShrugUpper": ["facs_bs_MouthShrugUpperLeft", "facs_bs_MouthShrugUpperRight"],
    "MouthPressLeft": ["facs_bs_MouthPressLowerLeft", "facs_bs_MouthPressUpperLeft"],
    "MouthPressRight": ["facs_bs_MouthPressLowerRight", "facs_bs_MouthPressUpperRight"],
    "MouthLowerDownLeft": ["facs_bs_MouthLowerDownLeft"],
    "MouthLowerDownRight": ["facs_bs_MouthLowerDownRight"],
    "MouthUpperUpLeft": ["facs_bs_MouthUpperUpLeft"],
    "MouthUpperUpRight": ["facs_bs_MouthUpperUpRight"],
    "BrowDownLeft": ["facs_BrowDownLeft"],
    "BrowDownRight": ["facs_BrowDownRight"],
    "BrowInnerUp": ["facs_bs_BrowInnerUpLeft", "facs_bs_BrowInnerUpRight"],
    "BrowOuterUpLeft": ["facs_BrowOuterUpLeft"],
    "BrowOuterUpRight": ["facs_BrowOuterUpRight"],
    "CheekPuff": ["facs_bs_CheekPuffLeft", "facs_bs_CheekPuffRight"],
    "CheekSquintLeft": ["facs_bs_CheekSquintLeft"],
    "CheekSquintRight": ["facs_bs_CheekSquintRight"],
    "NoseSneerLeft": ["facs_bs_NoseSneerLeft"],
    "NoseSneerRight": ["facs_bs_NoseSneerRight"],
    "TongueOut": ["facs_bs_TongueOut"]
}


# Mapping for Body Muscle JCMs to AAA Names and ROM Rotations
JCM_AAA_NAMING_MAP = \
{
    "FlexBicepsL": {
        "new_name": "BicepsFlexLeft",
        "daz_bone": "lowerarm_l",
        "rotations": {
            "Y": 135
        }
    },
    "FlexBicepsR": {
        "new_name": "BicepsFlexRight",
        "daz_bone": "lowerarm_r",
        "rotations": {
            "Y": 135
        }
    },
    "FlexCalfL": {
        "new_name": "CalfFlexLeft",
        "daz_bone": "calf_l",
        "rotations": {
            "X": 155
        }
    },
    "FlexCalfR": {
        "new_name": "CalfFlexRight",
        "daz_bone": "calf_r",
        "rotations": {
            "X": 155
        }
    },
    "FlexGluteClenchL": {
        "new_name": "GluteClenchFlexLeft",
        "daz_bone": "None",
        "rotations": {
            "X": 0
        }
    },
    "FlexGluteClenchR": {
        "new_name": "GluteClenchFlexRight",
        "daz_bone": "None",
        "rotations": {
            "X": 0
        }
    },
    "FlexHamstringL": {
        "new_name": "HamstringFlexLeft",
        "daz_bone": "calf_l",
        "rotations": {
            "X": 155
        }
    },
    "FlexHamstringR": {
        "new_name": "HamstringFlexRight",
        "daz_bone": "calf_r",
        "rotations": {
            "X": 155
        }
    },
    "FlexQuadL": {
        "new_name": "QuadFlexLeft",
        "daz_bone": "calf_l",
        "rotations": {
            "X": -90
        }
    },
    "FlexQuadR": {
        "new_name": "QuadFlexRight",
        "daz_bone": "calf_r",
        "rotations": {
            "X": -90
        }
    },
    "FlexShoulderUpperBackL": {
        "new_name": "ShoulderUpperBackFlexLeft",
        "daz_bone": "None",
        "rotations": {
            "X": 0
        }
    },
    "FlexShoulderUpperBackR": {
        "new_name": "ShoulderUpperBackFlexRight",
        "daz_bone": "None",
        "rotations": {
            "X": 0
        }
    },
    "FlexTricepsL": {
        "new_name": "TricepsFlexLeft",
        "daz_bone": "lowerarm_l",
        "rotations": {
            "Y": -90
        }
    },
    "FlexTricepsR": {
        "new_name": "TricepsFlexRight",
        "daz_bone": "lowerarm_r",
        "rotations": {
            "Y": -90
        }
    },
    "foot_x45n_l": {
        "new_name": "FootPitchLeft",
        "daz_bone": "foot_l",
        "rotations": {
            "X": -45
        }
    },
    "foot_x45n_r": {
        "new_name": "FootPitchRight",
        "daz_bone": "foot_r",
        "rotations": {
            "X": -45
        }
    },
    "foot_x65p_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "foot_l",
        "rotations": {
            "X": 65
        }
    },
    "foot_x65p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "foot_r",
        "rotations": {
            "X": 65
        }
    },
    "foot_z45n_l": {
        "new_name": "FootYawLeft",
        "daz_bone": "foot_l",
        "rotations": {
            "Z": -45
        }
    },
    "foot_z45p_r": {
        "new_name": "FootYawRight",
        "daz_bone": "foot_r",
        "rotations": {
            "Z": 45
        }
    },
    "forearm_y135n_l": {
        "new_name": "ElbowBendInFullLeft",
        "daz_bone": "lowerarm_l",
        "rotations": {
            "Y": -135
        }
    },
    "forearm_y135p_r": {
        "new_name": "ElbowBendOutFullRight",
        "daz_bone": "lowerarm_r",
        "rotations": {
            "Y": 135
        }
    },
    "forearm_y75n_l": {
        "new_name": "ElbowBendInHalfLeft",
        "daz_bone": "lowerarm_l",
        "rotations": {
            "Y": -75
        }
    },
    "forearm_y75p_r": {
        "new_name": "ElbowBendOutHalfRight",
        "daz_bone": "lowerarm_r",
        "rotations": {
            "Y": 75
        }
    },
    "hand_y28n_l": {
        "new_name": "HandBendLeft",
        "daz_bone": "hand_l",
        "rotations": {
            "Y": -28
        }
    },
    "hand_y28p_r": {
        "new_name": "HandBendRight",
        "daz_bone": "hand_r",
        "rotations": {
            "Y": 28
        }
    },
    "hand_z70n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "hand_l",
        "rotations": {
            "Z": -70
        }
    },
    "hand_z70p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "hand_r",
        "rotations": {
            "Z": 70
        }
    },
    "hand_z80n_r": {
        "new_name": "HandYawLeft",
        "daz_bone": "hand_r",
        "rotations": {
            "Z": -80
        }
    },
    "hand_z80p_l": {
        "new_name": "HandYawRight",
        "daz_bone": "hand_l",
        "rotations": {
            "Z": 80
        }
    },
    "neck1_x25n": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01",
        "rotations": {
            "X": -25
        }
    },
    "neck1_x40p": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01",
        "rotations": {
            "X": 40
        }
    },
    "neck1_z40n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01_l",
        "rotations": {
            "Z": -40
        }
    },
    "neck1_z40p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01_r",
        "rotations": {
            "Z": 40
        }
    },
    "pelvis_x25n": {
        "new_name": "DELETE_ME",
        "daz_bone": "pelvis",
        "rotations": {
            "X": -25
        }
    },
    "pelvis_x25p": {
        "new_name": "PelvisPitch",
        "daz_bone": "pelvis",
        "rotations": {
            "X": 25
        }
    },
    "shin_x155p_l": {
        "new_name": "ShinPitchUpFullLeft",
        "daz_bone": "calf_l",
        "rotations": {
            "X": 155
        }
    },
    "shin_x155p_r": {
        "new_name": "ShinPitchUpFullRight",
        "daz_bone": "calf_r",
        "rotations": {
            "X": 155
        }
    },
    "shin_x90p_l": {
        "new_name": "ShinPitchUpHalfLeft",
        "daz_bone": "calf_l",
        "rotations": {
            "X": 90
        }
    },
    "shin_x90p_r": {
        "new_name": "ShinPitchUpHalfRight",
        "daz_bone": "calf_r",
        "rotations": {
            "X": 90
        }
    },
    "shoulder_x30n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "clavicle_l",
        "rotations": {
            "X": -30
        }
    },
    "shoulder_x30n_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "clavicle_r",
        "rotations": {
            "X": -30
        }
    },
    "shoulder_x30p_l": {
        "new_name": "ShoulderPitchUpLeft",
        "daz_bone": "clavicle_l",
        "rotations": {
            "X": 30
        }
    },
    "shoulder_x30p_r": {
        "new_name": "ShoulderPitchUpRight",
        "daz_bone": "clavicle_r",
        "rotations": {
            "X": 30
        }
    },
    "shoulder_z55n_r": {
        "new_name": "ShoulderYawLeftRight",
        "daz_bone": "clavicle_r",
        "rotations": {
            "Z": -55
        }
    },
    "shoulder_z55p_l": {
        "new_name": "ShoulderYawRightLeft",
        "daz_bone": "clavicle_l",
        "rotations": {
            "Z": 55
        }
    },
    "spine1_x35p": {
        "new_name": "SpineLowerPitchUp",
        "daz_bone": "spine_01",
        "rotations": {
            "X": 35
        }
    },
    "spine1_z15n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "spine_01_l",
        "rotations": {
            "Z": -15
        }
    },
    "spine1_z15p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "spine_01_r",
        "rotations": {
            "Z": 15
        }
    },
    "spine2_x40p": {
        "new_name": "SpineMidPitchUp",
        "daz_bone": "spine_02",
        "rotations": {
            "X": 40
        }
    },
    "spine2_z24n_l": {
        "new_name": "SpineYawLeft",
        "daz_bone": "spine_02_l",
        "rotations": {
            "Z": -24
        }
    },
    "spine2_z24p_r": {
        "new_name": "SpineYawRight",
        "daz_bone": "spine_02_r",
        "rotations": {
            "Z": 24
        }
    },
    "spine3_x35p": {
        "new_name": "SpineUpperPitchUp",
        "daz_bone": "spine_03",
        "rotations": {
            "X": 35
        }
    },
    "spine3_z20n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "spine_03_l",
        "rotations": {
            "Z": -20
        }
    },
    "spine3_z20p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "spine_03_r",
        "rotations": {
            "Z": 20
        }
    },
    "thigh_x115n_l": {
        "new_name": "ThighPitchDownFullLeft",
        "daz_bone": "thigh_l",
        "rotations": {
            "X": -115
        }
    },
    "thigh_x115n_r": {
        "new_name": "ThighPitchDownFullRight",
        "daz_bone": "thigh_r",
        "rotations": {
            "X": -115
        }
    },
    "thigh_x115n_z90n_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "thigh_r",
        "rotations": {
            "X": -115,
            "Z": -90
        }
    },
    "thigh_x115n_z90p_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "thigh_l",
        "rotations": {
            "X": -115,
            "Z": 90
        }
    },
    "thigh_x35p_l": {
        "new_name": "ThighPitchUpLeft",
        "daz_bone": "thigh_l",
        "rotations": {
            "X": 35
        }
    },
    "thigh_x35p_r": {
        "new_name": "ThighPitchUpRight",
        "daz_bone": "thigh_r",
        "rotations": {
            "X": 35
        }
    },
    "thigh_x90n_l": {
        "new_name": "ThighPitchDownHalfLeft",
        "daz_bone": "thigh_l",
        "rotations": {
            "X": -90
        }
    },
    "thigh_x90n_r": {
        "new_name": "ThighPitchDownHalfRight",
        "daz_bone": "thigh_r",
        "rotations": {
            "X": -90
        }
    },
    "thigh_z90n_r": {
        "new_name": "ThighYawRight",
        "daz_bone": "thigh_r",
        "rotations": {
            "Z": -90
        }
    },
    "thigh_z90p_l": {
        "new_name": "ThighYawLeft",
        "daz_bone": "thigh_l",
        "rotations": {
            "Z": 90
        }
    },
    "upperarm_x95n_l": {
        "new_name": "UpperarmPitchDownLeft",
        "daz_bone": "upperarm_l",
        "rotations": {
            "X": -95
        }
    },
    "upperarm_x95n_r": {
        "new_name": "UpperarmPitchDownRight",
        "daz_bone": "upperarm_r",
        "rotations": {
            "X": -95
        }
    },
    "upperarm_y110n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_l",
        "rotations": {
            "Y": -110
        }
    },
    "upperarm_y110n_z40n_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_l",
        "rotations": {
            "Y": -110,
            "Z": -40
        }
    },
    "upperarm_y110n_z90p_l": {
        "new_name": "UpperarmBendInYawLeft",
        "daz_bone": "upperarm_l",
        "rotations": {
            "Y": -110,
            "Z": 90
        }
    },
    "upperarm_y110p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_r",
        "rotations": {
            "Y": 110
        }
    },
    "upperarm_y110p_z40p_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_r",
        "rotations": {
            "Y": 110,
            "Z": 40
        }
    },
    "upperarm_y110p_z90n_r": {
        "new_name": "UpperarmBendOutYawRight",
        "daz_bone": "upperarm_r",
        "rotations": {
            "Y": 110,
            "Z": -90
        }
    },
    "upperarm_z40n_l": {
        "new_name": "UpperarmYawLeft",
        "daz_bone": "upperarm_l",
        "rotations": {
            "Z": -40
        }
    },
    "upperarm_z40p_r": {
        "new_name": "UpperarmYawRight",
        "daz_bone": "upperarm_r",
        "rotations": {
            "Z": 40
        }
    },
    "upperarm_z90n_r": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_r",
        "rotations": {
            "Z": -90
        }
    },
    "upperarm_z90p_l": {
        "new_name": "DELETE_ME",
        "daz_bone": "upperarm_l",
        "rotations": {
            "Z": 90
        }
    },
    "facs_bs_NeckFlexLeft": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01",
        "rotations": {
            "Z": 40
        }
    },
    "facs_bs_NeckFlexRight": {
        "new_name": "DELETE_ME",
        "daz_bone": "neck_01",
        "rotations": {
            "Z": -40
        }
    }
}

