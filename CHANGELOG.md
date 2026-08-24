# Changelog

All notable changes to the MasterSK addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
