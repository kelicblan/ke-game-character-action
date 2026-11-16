# Contextual hit-reaction system

## Principle: force, body part, state, support, and intensity

A believable-looking reaction is **not** one reusable backbend. Different hits transmit apparent force through different body chains. Stylize for the game's silhouette, but preserve causal direction and movement-state continuity. Real reactions vary widely; these tables are **animation design starting points**, not deterministic medical predictions.

For every hit collect:

```text
hitPart       = head_front | head_side | head_top | chest | abdomen | arm | leg | other
impulseDir    = target-local normalized vector POINTING in the direction force pushes target
hitIntensity  = cosmetic | light | medium | heavy | lethal
movePhase     = idle | left_stance | right_stance | takeoff | flight | landing | hover | ... 
currentMotion = root velocity (and airborne vertical velocity, if any)
support       = grounded | airborne | hover | multi_support | knocked_down
constraints   = wall, floor, obstacles, platform edge, attack armor, stagger resistance
```

**Direction convention:** `impulseDir` is force imparted **to the victim**. This is not the direction from which the blow originated; if a projectile comes from left to right, the impulse is usually rightward. Use local-space conversion for left/right/front/back. A top-down blow has a negative vertical component. Do not infer the direction of impulse solely from collision normal unless it matches the authored ability.

## Body regions and primary response

| Region/strike | Primary response | Secondary & support | Common mistake |
| --- | --- | --- | --- |
| Face/head frontal | Head turn/recoil first, neck and upper torso follow | If center of mass exceeds support, corrective backward step or slide | Whole figure bends from the waist with no head motion |
| Head lateral | Head deviates/rotates away, shoulders follow | Side step/foot pivot based on stability | Every hit pushes backward regardless of direction |
| Abdomen frontal | Local contraction, torso folds forward around waist | Knees soften, shoulders close, optional short ground correction | Head recoils backward as if face was struck |
| Chest frontal | Sternum/shoulder response with partial opening/back lean | Hip shift, corrective step at higher impact | Identical to abdomen bend |
| Top-of-head/downward | Head/neck shorten visually, shoulders and knees compress downward | Floor contact and weight support, delayed rise | Entire sprite scaled vertically without believable joints |
| Legs | Support limb buckles/shifts, pelvis drops/tilts | Other foot must stabilize or actor falls | Upper body alone moves |
| Arm/weapon block | Hit arm/weapon deflects, upper body absorbs | Guard recovery determined by actual block rule | Plays damage stagger for a valid guard |

### Example variations

A small/light humanoid with weak stance under head impact can visibly step backward. A heavy, braced target under the same strike may only turn the head. Do not hardwire “head hit always steps back.” An abdomen hit can be local flex only, or a full-body stumble when momentum/strength justifies it.

## Locomotion-state matrix

| Support / movement | Light reaction | Heavy reaction | Recovery requirement |
| --- | --- | --- | --- |
| Standing with stable feet | Local flinch, conditional weight correction | Step, slide, or knockdown | Restore support before motion resumes |
| Walking/shuffling | Current planted foot adjusts; avoid sliding both feet without cause | Stumble/step replacement, interrupted stride | Re-enter correct gait phase |
| Two-foot hopping in flight | Recoil pose + modify existing velocity; displacement follows impulse | Trajectory interruption, backward arc or fall | Land at actual new position, absorb contact, resume hop |
| During takeoff/landing | Preserve contact constraints and phase when interrupted | Change takeoff velocity or landing recovery, possibly collapse | Never teleport to grounded idle |
| Hover/flying | Drift/rotate in air, velocity correction | Larger directional displacement, temporary loss of balance | Restabilize at current altitude unless knockdown is intended |
| Crawling/multi-support | Affect engaged support limbs and body axis | Redistribute support or tumble | Respect creature topology and contact |

**Do not** automatically apply a second scripted jump to an airborne character: re-use the ongoing trajectory plus impulse. Do not automatically demand translation for every cosmetic flinch; movement is determined by gameplay strength and support.

## Intensity and gameplay authority

- **Cosmetic flinch**: additive local reaction, optional no gameplay displacement. Can coexist with movement/attack if game design allows.
- **Stagger**: full-body pose and action interruption, possibly short correction step.
- **Knockback**: meaningful logic-root displacement along authored impulse, obeying collision; not a sprite-only screen offset.
- **Launch/knockdown**: updates vertical/root motion state, landing or fall recovery, grounded checks and subsequent behavior.
- **Death**: transition to terminal state; no stale timer restoring idle.

Keep `damage` separate from `impulse strength`; high damage does not imply large knockback and vice versa.

## Reaction synthesis (logical pseudocode)

```text
hit = combat.confirmed_result()
if not hit.valid: return
ctx = normalize_hit(hit.part, hit.force, hit.strength, actor.state, actor.velocity)
rule = choose_reaction(ctx, actor.body_type, armor, nearby_collision)
if hit.lethal: transition_to_death(rule)
else:
    apply_impact_visual(rule.pose, target_body_part=ctx.part)
    if rule.interrupts: schedule_hitstun(rule.hitstun_ms)
    if rule.root_motion: movement.apply_impulse_or_displacement(rule.root_motion, ctx.impulseDir)
    apply_secondary_motion(rule.attachments, ctx.impulseDir)
    transition_into_valid_recovery(ctx.support, actor.current_motion)
```

Gameplay movement/root collision owns actual location. Visual bone/scale/tilt is an overlay and must return to neutral without snapping the actor's game position back.

## Motion-direction QA probes

Review at least these tests when building a general response library:

1. Front head hit grounded → head moves first; if stagger selected, compensating step/slide is in correct direction.
2. Left/right head hit → distinct lateral orientation and root correction; mirror only if character design permits.
3. Abdomen hit → contraction with correct knees/support, no fake face recoil.
4. Downward top hit → clear vertical compress and recovery, floor remains registered.
5. In-flight hopping hit → momentum redirected, character lands in a physically/graphically consistent place.
6. Hover hit → drift with no magical footstep.
7. Simultaneous/repeated hits → merged or prioritized reactions; no event loop or infinite stun.
8. Wall collision → displacement clamps or changes to wall-reaction state rather than clipping through geometry.
9. Armor/block/death → correct state priority.
10. Tiny gameplay scale → different hit parts still readable.

## Source material

- Jonathan Colin, hit library organized by body part, direction and intensity: https://www.animotionx.com/en/post/interview-jonathan-colin-readability-silhouette-and-gameplay-animation-secrets
- `The Division 2` GDC 2019, separate cosmetic flinch from gameplay stagger: https://media.gdcvault.com/gdc2019/presentations/Dunstan_Philip_FightingSequelitisCreating.pdf
- Unreal Engine point damage and shot direction fields: https://dev.epicgames.com/documentation/en-us/unreal-engine/events-in-unreal-engine
- Masahiro Sakurai, Damage Animations: https://www.youtube.com/watch?v=0xHE3ypX96U
