# Changelog

All notable changes to the MasterSK addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.0] - 2026-08-27

### Added
- **Native Daz ROM Cloning (Step 9):** Integrated the native Daz Studio ROM extraction dictionary (`daz_rom_full.json`). The addon now flawlessly clones the original mathematical frame clusters and matrix rotations, allowing 1-to-1 JCM/ROM extraction for Unreal Engine.
- **Automated Neck Flex Cleanup:** Added smart substring deletion in Step 7 to automatically hunt down and delete useless `NeckFlex` shape keys from the body mesh regardless of import prefix.
- **Shape Key Intensity Multiplier:** Integrated a 2.0x permanent mathematical vertex coordinate multiplier into Step 7 to guarantee all body shape keys hit extreme deformation while maintaining a clean UI slider maximum.
- **Symmetrical Slider Range:** Forced all body shape key slider minimums to `-1.0` during Step 7 cleanup to allow for inverse extreme deformations inside Unreal Engine.

## [3.1.0] - 2026-08-25

### Added
- **Mathematical Shape Key Cleaner (Step 7):** Added a highly optimized `numpy` scanner that executes instantly after the meshes are split. It scans every vertex of every shape key and permanently deletes keys that have absolutely zero geometric effect on the remaining mesh. This ensures the Head mesh only retains facial morphs, and the Body mesh only retains body JCMs, resulting in perfectly optimized Live Link assets.
- **Full Facial Rig Restoration:** Reverted the aggressive facial bone pruning logic to properly retain the entire Daz3D facial bone hierarchy. The script still intelligently identifies and annihilates heavy `(drv)` helper bones in Step 2, but preserves all standard poseable facial bones, enabling perfect traditional facial animation alongside ARKit shape keys.

## [3.0.0] - 2026-08-25

### Added
- **Zero-Length Bone Safeguard:** Added a mathematical scanner during rig generation that detects 0-length Daz helper bones and forces a microscopic tail extension. This prevents Blender's engine from silently purging facial bones upon exiting Edit Mode.
- **Automated Twist Bone Routing:** The pipeline now automatically transfers the heavy calf weight vertex groups directly to the `calf_twist_01` bones in Step 8, preserving knee articulation geometry during the rest pose matching phase.
- **Head Rig Expansion:** The Head Rig (`root_head`) now correctly retains the `upperarm` and `upperarm_twist` bones (in addition to the spine, clavicles, and neck) to prevent clipping between modular meshes in Unreal Engine.

### Fixed
- **The "3 Armatures" Bug:** Fixed an issue where the original Daz armature would survive the pipeline and clutter the scene. Step 8 now explicitly unlinks and forcefully deletes all intermediate armatures using UI-level API commands.
- **Missing Facial Bones:** Fixed a fatal logic flaw in Step 7 where the global pointer was incorrectly overwritten to the body armature, causing Step 8 to fail to transfer the 64+ facial bones to the Head Rig.
- **Head Mesh Weight Paint Corruption:** Resolved severe red/blue weight paint distortion on the facial meshes (jaw, teeth, eyes) by ensuring all facial bones seamlessly and perfectly transfer to the Head Rig.
- **IK Bone Leakage:** Fixed an issue where `ik_foot_root` and `ik_hand_gun` bones were erroneously left inside the Head rig.

## [2.0.0] - 2026-08-24

### Added
- **Full 8-Step Automated Pipeline:** Replaced the legacy workflow with a deterministic sequential process.
- **Kinematic Pose Matching Solver:** Mathematically calculates vector rotation differences to perfectly match Genesis 9 to the ALS Epic Mannequin A-Pose.
- **Dual-Rig Output Setup:** Generates clean, isolated `root` and `root_head` armatures, fully optimized for modular character construction in Unreal Engine 5.
- **Automated UV and Material Optimization:** Splitting meshes now automatically merges internal materials (Mouth Cavity to Head) and extracts precise UV coordinates for Fingernails/Toenails to merge them seamlessly into the Arms texture slot.
- **IK Bone Reconstruction:** Generates perfect IK bones for feet and hands based on the Unreal Engine skeleton, scaled dynamically to prevent viewport clipping.
- **Joint Roll Locking System:** Safely snaps ALS joints to the Genesis 9 geometry while rigorously preserving the internal UE5 bone lengths, directional vectors, and exact `roll` values.
- **Spine Alignment Notification Popup:** Explicit warning triggered after Finalization to remind riggers to manually align the `spine_01`, `spine_02`, and `spine_03` Z-axis coordinates to respect arbitrary anatomical mesh weights.
- **UI State Machine & Dynamic Locking:** The UI now strictly prevents out-of-order execution by disabling uncompleted steps and dynamically unlocking the next step as you progress.
- **Visual Progress Bar:** Added an intuitive, real-time visual progress tracker to the top of the panel to indicate the current phase of the pipeline.
- **Progress Reset Functionality:** Added a one-click reset button to clear the pipeline state, allowing users to restart the process easily on a new character.

### Changed
- Refactored `bone_math.py` to completely eliminate heuristic Z-offset guessing for spines, deferring to manual alignment to ensure perfect weight envelope preservation.
- Moved UI logic into a modernized `panel.py` with dynamic button disabling based on prerequisite step completion.
- Re-architected weight consolidation to use explicit maps for metacarpals, toes, and driver bones.

### Fixed
- Fixed an issue where the Genesis 9 Root Bone (named after the character) would cause duplicated hierarchy warnings during Unreal Engine import; the bone is now correctly deleted and merged into the Pelvis.
- Fixed a bug in IK scaling where child-matching caused IK bones to completely collapse into zero-length objects.
- Corrected Shape Key application during pose matching which previously caused severe visual exploding of the mesh if left enabled.

## [1.0.0] - Initial Release

### Added
- Basic vertex group renaming from Genesis 8/9 standard to Unreal Engine ALS standard.
- Simple weight merging functionality.
