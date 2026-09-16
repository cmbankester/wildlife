# Print and assemble

**200 × 65 mm rail • 136 mm mechanical travel • 40 mm saddle position range
• 14 mm saddle height range.** The camera seats 25.3 mm above the shelf.

1. **Print the tests first:** `fit_rail.stl`, `fit_carriage.stl`,
   `camera_screw_coupon.stl`, plus the actual `camera_pad.stl`,
   `pressure_shoe.stl` and `lock_knob.stl`. Check the slide and lock, actual
   screw head fit and safe socket engagement before printing the long rail.
2. **Production prints:** one rail, carriage, camera pad, shoe, knob, saddle
   foot and cradle; **two identical end stops**. Add the optional liner in TPU,
   or use a thin neoprene/felt strip. STL orientations are ready for slicing.
3. **Settings:** PETG, 0.20 mm layers, 4–5 walls, 5 top/bottom layers, 35–45%
   infill. Use the filament maker's temperature profile. Inspect small bridges
   in the slicer; do not put full-length supports on the dovetail faces.
4. **Hardware:** 1 low-profile **1/4″-20 × 3/8″** camera screw; 1 **M4×16
   hex-head** screw and M4 nut; **4 M3×12**, **2 M3×10**, **2 M3×16** socket-head
   screws; **8 M3 nuts**, **4 M3 washers (7 OD × 0.5)**; 4 countersunk pine screws
   about Ø3.5, with length chosen for measured shelf thickness. Ordinary nuts,
   not taller locknuts. A 1 mm pad lines the cradle.
5. **Assembly order:** insert rail underside nuts → screw rail to pine → fit
   rear stop → install lock nut/shoe/knob in carriage → attach camera with its
   separate pad → attach saddle foot with screws from underneath → attach and
   pad cradle → slide carriage onto rail → fit front stop.
6. **Adjust gently:** set saddle under a stationary barrel band; raise it only
   enough to carry weight. Keep clear of rings and small lens screws. Loosen
   the knob to slide, then finger-tighten. Remove carriage for easiest access
   to the saddle's underside fore/aft adjustment screws.

**Must check on the actual hardware:** the camera screw projects approximately
**3.525 mm** above its pad; confirm socket depth rather than forcing it home.
Check tripod-block contact, PCB clearance and ribbon slack. The padded saddle
trough adjusts about **9–23 mm above the camera seating plane**.

At full travel the arm can overhang the shelf by **29 mm**; the knob needs side
and finger clearance. The box, lens and future glass may reduce the usable
136 mm travel. Set up and check the complete sweep before fitting the window.

CAD checks passed for all 12 STL meshes and 27 motion poses, plus lock contact,
stops and dovetail capture. This is an **unprinted prototype**, not a physical
fit or load certification. See [full instructions](README.md) for hardware
dimensions, measurement checks, editing and verification limits.
