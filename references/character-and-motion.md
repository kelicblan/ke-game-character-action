# Character analysis and motion personality

Run this analysis **before generating frames or rigging animation**. A visual design is not proof of its movement. Make a plausible motion hypothesis, preview it, and refine it from game readability.

## 1. Input evidence

Record: source file/link and revision, visual angle, size, crop/occlusions, body and limb count, approximate anatomy, foot/ground contact, held props, hair/cloth/secondary attachments, and whether the scene is 2D side, three-quarter, top-down, or full 3D. Only label things you can actually see as confirmed.

If the input image shows a static standing pose:
- Hidden legs/arms **cannot** be inferred with certainty; mark them for redraw.
- Single-image cutout rotation exposes seams; plan underpaint and overlap.
- Character orientation and perspective must remain coherent across frames.
- Identical frame height is not a substitute for stable proportions; changing orientation can change the visible bounding box while maintaining correct anatomy.

## 2. Character motion profile

Use these dimensions to write a compact motion signature (not a universal numerical score).

| Dimension | Questions | Animation consequence |
| --- | --- | --- |
| Geometry | Humanoid, quadruped, multi-legged, floating, articulated monster? | Joints, stance, limb order and constraints |
| Apparent mass | Light/heavy, high/low center of mass? | Acceleration, amplitude, recovery, stopping |
| Joint mobility | Stiff, flexible, partially locked, segmented? | Rotation limits and pose construction |
| Support | Two feet, multiple legs, airborne, magical hover? | Step, landing, stabilization and reaction |
| Locomotion | Step, shuffle, hop, crawl, slide, flap, hover? | Contacts and path/phase |
| Equipment | Headgear, long sleeves, chain, pendant, tail, cape? | Follow-through and secondary delay |
| Character | Alert, solemn, erratic, predatory, robotic? | Tempo, holds and gesture vocabulary |
| Camera/scale | Actual on-screen character height and facing? | Minimum silhouette separation |

## 3. Locomotion is not interchangeable

**Grounded walk**: stance leg accepts weight; the other leg swings, then foot contacts; pelvis advances without perpetual foot sliding. Heavy/stiff characters often use short steps and small arm swing, not large rebounds.

**Two-foot hop**: compression → takeoff → flight → landing → stabilization. Feet visibly leave ground in flight; shadow stays grounded. Avoid fake hops where the entire image simply moves upward and back without takeoff/landing cues.

**Airborne flight/hover**: maintain continuous elevation and baseline motion; minor oscillation can be visual-only, and landing should not happen unless gameplay actually changes state. Flight is not a walk cycle with feet hidden.

**Crawl/multi-leg gait**: distribute support across limbs. Distinct body segmentation and foot contacts matter more than human stepping patterns.

**Stationary idle**: movement is lower-energy than locomotion. A stiff or undead silhouette can remain almost motionless while cloth, hair, smoke, particles or small appendages move independently. Unless intentionally alive, avoid human-like chest breathing.

## 4. Source-image lock

Write identity invariants before production:
- Face/eye and mouth shape; presence/absence of facial hair; headwear and attachment count.
- Proportions, silhouette and joint count; body part topology.
- Color/shading/line weight, costume shape, ornaments, asymmetrical markings.
- Weapon/prop size, side, attachment, and relationship to hands.
- Front/side/back and perspective consistency.

Then list allowed changes: articulation, perspective variation, expression under impact, cloth dynamics, local deformation, pose change. Never hallucinate new ornaments, facial features or missing limbs to fill a pose.

## 5. Character examples (illustrative archetypes, not defaults)

- Small rigid hopper: quiet idle; high information in both-foot flight and landing; airborne knockback must alter trajectory.
- Heavy humanoid shuffler: anchored shoulders/hips; short, deliberate steps; head hit may require a recovery step, belly hit may compress torso, overhead hit compresses vertical support.
- Floating specter: drifting hover; impact shifts flying velocity; recovery involves re-stabilization in air, not a forced footstep.
- Multi-legged creature: load redistributed to several support limbs; damage may cause asymmetric stumble, not a human backbend.

## 6. Handoff

Fill `templates/character-profile.json` (replace example placeholders). State motion assumptions, limitations, and which contact/rig details need confirmation. If the user supplies a game engine, pass concrete coordinate and pivot conventions to production.
