# Camera mounting system — design and build plan

The approved concept is a screw-down PETG dovetail, captive lockable carriage,
recessed 1/4-20 camera fastener, removable hard stops, and a moving padded lens
saddle. The supplied photo establishes orientation, not measurement scale.

## Geometry

All dimensions are millimetres. X points toward the lens/window, Y across the
shelf, Z upward. Rail: 200 × 65, base 4 thick; male dovetail 24 wide at Z4 and
40 wide at Z12. Its flanks are 45 degrees. Female flank clearance is 0.30 normal
to each flank, and roof clearance is 0.30 vertical. Carriage bearing length 48;
two 8-long end stops leave 136 travel. Camera screw at local X12. Deck Z20.3,
camera seating pad Z22.3. Elevated arm ends at local X90 and passes over stops.

Two longitudinal saddle slots span X32–72, at Y±14. The U cradle contact plane
is 10.3 forward of the saddle foot fasteners: 30.3–70.3 ahead of the camera
screw. Side uprights leave the barrel unobstructed. A 40-diameter U profile with
1 mm soft liner accommodates a nominal 30 mm barrel; trial range 24–36 mm.
Cradle valley is adjustable 10–24 above the deck (before liner).

The full moving envelope can extend beyond the shelf. Mechanical travel does
not promise collision-free travel inside the photographed box. Lens dimensions,
glass position, ribbon slack, and access for the side knob require physical checks.

## Considered construction choices

- Selected: one-piece male rail and female carriage; robust capture with ordinary
  fasteners. Requires a sliding-fit coupon and support under the inverted rail
  overhang if printed upright.
- Two bolted rails: more screws and alignment work without helping this shelf.
- Flexure lock: fewer parts, but repeated bending/creep is less predictable than
  the selected separate pressure shoe driven by an M4 screw.

## Build plan

1. Generate editable CadQuery source and a parameter JSON file; derive all STL
   and STEP geometry from the same solid model. Use Python for native CadQuery.
2. Model rail, carriage/arm, two identical stops, pressure shoe, hand knob,
   saddle foot/uprights, U cradle, and optional soft liner.
3. Generate short male/female coupons with the actual sliding profile and
   actual lock hardware pockets; include camera screw test geometry.
4. Verify solid validity, connectedness, positive volume, watertight STL meshes,
   travel limits, stop capture, and collision-free combinations of translation
   and both saddle adjustments. Include representative fastener envelopes.
5. Produce a dimensioned overview, BOM, print orientations, assembly order,
   limits of verification, checks required before full printing, and ZIP bundle.
6. Apply automated source formatting and commit working deliverables.

## Acceptance limits

These are printable prototype CAD files, not a physical load qualification.
No inference of exact lens diameter, glass clearance, shelf thickness, thread
depth, or ribbon bend radius is made from the photograph. Numerical checks
must report modeled clearances separately from these unmeasured constraints.
