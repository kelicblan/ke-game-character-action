# Motion timing, action holds and combat-state rules

The source of truth is the action card timeline in **milliseconds**. Rendered animation frames are samples from that timeline; they do not define game event truth by themselves.

## 1. Four different kinds of time

| Type | Definition | Governs |
| --- | --- | --- |
| Pose hold | Preserve the dominant attack/impact silhouette while animation time advances | Follow-through, legibility |
| Hitstop | Freeze selected actor animation and associated chosen movement clocks briefly on confirmed impact | Contact emphasis |
| Recovery/action lockout | Window before move/evade/attack commands may execute | Game control and commitment |
| Hitstun | Duration the target cannot perform specified actions, distinct from attacker lockout | Gameplay reaction |

A whiff may still include a pose hold, but should not automatically add hitstop. An attack can leave pose recovery while movement or a specific cancel becomes available. An already airborne hit target may continue moving while its pose freezes, but **choose and document** which simulation clocks pause so this is consistent.

## 2. Attack time skeleton (example only)

| Time (ms) | Phase | Design |
| --- | --- | --- |
| 0–100 | anticipation | wind up and weight support |
| 100–160 | acceleration/contact | fast motion, active hit 130–160 |
| 160–220 | follow-through | finish directional force and secondary motion |
| 220–280 | pose hold | readable extended striking silhouette |
| 280–460 | recovery | reduce velocity and transition |
| 460–500 | settle | return to idle, move, or a legal next action |

This is an illustrative 500 ms jab, **not** a default for all weapons, enemies or attacks. Attack speed scaling must preserve readable contact and adapt windows; uniform frame-speed scaling may destroy meaning.

### Conditional results

- **Whiff**: no target hit event or hitstop; continue designed follow-through and recovery.
- **Hit**: game collision/target rules confirm; one chosen hitstop per attack event; target applies a contextual reaction.
- **Block**: guard outcome decides attacker rebound pose, stop and sound; no phantom damage.
- **Combo**: next legal attack starts from current pose; do not insert idle unless intentionally designed.
- **Interrupt/death**: cancel old events, root motion and hitboxes; never restore old animation from stale callbacks.

## 3. Idle and locomotion

- Idle loop: last state matches first in position, tangent/speed and secondary-motion phase. Avoid big body movement; inspect at final game display size.
- Walk: grounded foot must remain plausibly planted during stance. Root movement and foot speed must agree.
- Hop: define takeoff/landing and duration; root horizontal displacement can be handled by simulation, but animation must convey push and contact.
- Hover: no fake footsteps or abrupt ground shadow contact.
- Attack from locomotion: preserve/cancel current velocity intentionally, not accidentally; blend the locomotion phase if needed.

## 4. A frame sheet is not a constant-FPS contract

Example 500 ms action may use eight visual samples with frame durations `[90,40,30,50,50,110,100,30]`. These samples sum to 500 ms. Additional, manually painted impact frames may exist; a pose hold can simply repeat one visual image for longer. Do not fabricate interpolation when only still frames exist.

An engine event should fire when animation time crosses its window boundary. Do not rely on “frame 4” or equality with a timestamp; those fail when render FPS drops. Continuous or swept hit detection is needed for fast attacks. Deduplicate the same attack segment hitting the same target.

## 5. Coordinate/time conventions

- Track **real elapsed time**, **gameplay simulation time**, **actor animation time**, and **hitstop release time** separately as needed.
- State the unit for displacements (pixels, world units, or ratios relative to character width/height). Ratios are tuning values, not implied forces.
- Declare whether root motion is logic-owned, animation-owned, or hybrid. Never apply both authoritative root motions.
- Time arrays must be strictly increasing/positive; hit and cancel windows must be within `total_ms`.
- Loop windows must close correctly; nonloop actions require a clear exit destination or interrupt rule.
- Root motion should not be lost on cancel. Account for position and velocity when entering follow-up or hit reaction states.

## 6. Testing

Normal-speed playback is the acceptance view; slow-motion and stepped playback are diagnostic. Test 30/60 FPS, slow/fast action scale, whiff, block, simultaneous attacks, repeated hits, and gameplay pause/resume. Confirm actual durations, contact times, and state transitions; do not evaluate timing solely from a row of key images.
