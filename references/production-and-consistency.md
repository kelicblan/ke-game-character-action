# From a character source to production-grade animation

The deliverable is not simply “an AI image with eight adjacent poses.” Animation production needs identity consistency, clean geometry, coherent arcs, timing, event alignment, and an engine-usable format.

## Production mode selection

| Production mode | Best for | Limits |
| --- | --- | --- |
| Single-image transforms | Tiny idle/tilt/flash/first prototype | Cannot independently bend knees, torso and head; can look like a cardboard cutout |
| Frame-by-frame | Large silhouette changes, extreme perspective, strong impacts, organic deformation | Requires consistent frame alignment, cleanup and potentially many unique assets |
| 2D cutout/skeletal | Reusable gait/idle, local upper-body reactions, cloth and attachment follow-through | Needs proper underpainting and pivots; extreme foreshortening may still need replacement art |
| Hybrid | Common skeletal actions plus unique impact poses/attachments | Requires careful crossfade or attachment swap |
| 3D rig | Perspective turns, physical interaction, detailed joint chains | Rig, skinning, physics, render complexity |

Choose based on required deformation and what is actually available. If tools cannot produce usable editable sources, state that clearly rather than pretending a static sprite sheet is a rig.

## Steps

1. **Identity lock**: inspect source image(s) at normal resolution. Capture silhouette, head/face, costume, props, asymmetries and forbidden changes in the character profile.
2. **Action key poses**: draw ready, anticipation, active, follow-through, hold, recovery, and transition, adjusted for each action. Determine floor/contact/shadow at each stage.
3. **Technical asset plan**: for cutout/rig identify rigid body segments, pivot locations, underpainted overlap, render stacking, prop attachment; for frame animation define stable canvas/pivot and consistent character scale.
4. **Candidate generation**: produce few candidates first; same visual identity, angle, camera and lighting, no extra characters or unwanted typography, and transparent background when supported.
5. **Frame-by-frame screening**: compare each frame against source and neighbors. Reject wrong facial hair, changed head shape, disappearing limbs, costume pattern drift, mutated hands, new jewelry, different perspective, altered width/height relation, inconsistent feet.
6. **Timing and motion**: order approved poses with uneven frame durations. Draw in-betweens only as necessary; smooth movement paths, not just equal-frame sequencing. Preserve velocity continuity or purposeful sudden impact.
7. **Secondary movement**: append cloth, hair, pendant, tail, smoke to the **correct** primary motion, with lag and settling. Avoid attachments leading the movement arbitrarily.
8. **Export and import**: retain source, actual sprites/rig, timing card, events, anchors, collision/transform data and proof of target-engine playback.

## Output requirements for frame animation

- Transparent RGBA ideally (or a well-documented separate background-removal step). A checkerboard drawn into image pixels is not transparency.
- Fixed logical canvas and ground/pivot coordinate. Trim bounds can vary, but record offsets or reconstruct original registration.
- Exact `columns`, `rows`, `frame_width`, `frame_height`, sequence order, per-frame timing, loop policy and action ID.
- Frames may differ in bounding box because poses differ; they must not mysteriously resize anatomy.
- Shadow position must reflect grounded, jumping and hovering states; shadows usually follow contact plane, not the airborne sprite root.
- If viewed at actual in-game size, attack/impact poses remain distinguishable and accessories do not hide the hit point.

## Common AI generation failure modes and fixes

| Symptom | Cause / response |
| --- | --- |
| “Animated” frame sequence barely changes | Model copied the same pose. Redesign key silhouettes; do not interpolate identical images. |
| Character changes identity from frame to frame | The generation lacked reliable identity control. Reuse verified reference, constrain camera/style, generate limited poses, manually redraw/reject mismatches. |
| Sprite sheet is actually a contact sheet | Background, cell borders, text or unequal cell content are painted. Separate real frame assets and align/trim. |
| All motions are elastic backbends | No character/strike analysis. Apply hit-context matrix and support mechanics first. |
| Hitstop is visually indistinguishable from pose hold | Separate the engine-selected pause clock and action pose duration. |
| Hit character always returns to same screen position | Root translation was baked into artwork then reset. Move gameplay root and keep visual animation local. |
| Airborne hop hit produces a second artificial jump | Air movement not composed with current velocity; redesign fall/land trajectory. |
| Feet slide when walking | Root travel and stance anchor mismatch; correct contacts or change gait. |
| Sides are mechanically mirrored but costume is asymmetrical | Provide directional art or rig changes with correct handedness. |

## Source retention and licensing

Do not put private/current/historical images in this SKILL repository. In the user's project keep source reference, layer file, candidate frames, approved frames, animation source, spritesheet/rig, previews and QA report with versioned IDs. Confirm the user has rights to every source. Document model/asset provenance and any restrictions before distribution.

## Acceptance

An image passes **visual QA** only after every frame matches identity and is clean. A sequence passes **motion QA** only after playback has correct timing, movement, contacts, and transitions. An **engine QA** claim requires real import and running inspection.
