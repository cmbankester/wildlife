"""Parametric Pi HQ camera mount. Units: mm. Run build.py to export and check.

X = travel/lens axis; Y = shelf width; Z = height above shelf. Models here
retain assembly coordinates. Print-oriented exports are generated separately.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq


@dataclass(frozen=True)
class Parameters:
    rail_length: float
    rail_width: float
    base_thickness: float
    dovetail_height: float
    dovetail_bottom_width: float
    flank_clearance: float
    roof_clearance: float
    carriage_length: float
    carriage_width: float
    deck_thickness: float
    arm_length: float
    arm_thickness: float
    stop_length: float
    camera_x: float
    camera_pad_height: float
    camera_bore: float
    camera_head_diameter: float
    camera_head_recess: float
    saddle_slot_start: float
    saddle_slot_end: float
    saddle_radius: float
    saddle_min_base: float
    saddle_height_travel: float
    liner_thickness: float
    m3_clearance: float
    m3_nut_af: float
    m3_nut_depth: float
    m4_clearance: float
    m4_nut_af: float
    m4_nut_depth: float

    @classmethod
    def from_file(cls, path: Path):
        raw = json.loads(path.read_text())
        if any(
            type(v) not in (float, int) or not math.isfinite(v) or v <= 0
            for v in raw.values()
        ):
            raise ValueError("Parameters must be finite positive numbers")
        p = cls(**raw)
        if not (p.travel > 0 and p.rail_width <= 70 and p.rail_length <= 210):
            raise ValueError("Rail/travel must fit the 70 × 210 shelf")
        if not (0.15 <= p.flank_clearance <= 0.6):
            raise ValueError("Flank clearance must be 0.15–0.60 mm per face")
        if not (p.saddle_slot_start < p.saddle_slot_end < p.arm_length - 15):
            raise ValueError("Saddle slots must stay inside arm")
        if p.saddle_radius > 21 or p.saddle_min_base < 6:
            raise ValueError("Cradle must retain its side tabs and foot clearance")
        if p.deck_thickness - p.camera_head_recess + p.camera_pad_height < 4:
            raise ValueError("Camera screw requires at least 4 mm of seating web")
        return p

    @property
    def rail_top(self):
        return self.base_thickness + self.dovetail_height

    @property
    def deck_top(self):
        return self.rail_top + self.roof_clearance + self.deck_thickness

    @property
    def travel(self):
        return self.rail_length - 2 * self.stop_length - self.carriage_length

    @property
    def intercept(self):
        return self.dovetail_bottom_width / 2 - self.base_thickness


def box(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
        .val()
    )


def prism_x(points_yz, x0, length):
    return (
        cq.Workplane("YZ", origin=(x0, 0, 0))
        .polyline(points_yz)
        .close()
        .extrude(length)
        .val()
    )


def cylinder(r, length, origin, direction=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, length, cq.Vector(*origin), cq.Vector(*direction))


def hex_prism(af, length, origin, axis="z"):
    r = af / math.sqrt(3)
    pts = [
        (
            r * math.cos(math.radians(30 + 60 * i)),
            r * math.sin(math.radians(30 + 60 * i)),
        )
        for i in range(6)
    ]
    plane = {"z": "XY", "x": "YZ", "y": "XZ"}[axis]
    # XZ has normal -Y. Rotate its 2D normal convention into +Y after extrusion.
    solid = cq.Workplane(plane).polyline(pts).close().extrude(length).val()
    if axis == "y":
        solid = solid.rotate((0, 0, 0), (1, 0, 0), 180)
    return solid.translate(origin)


def slot_z(x0, x1, y, diameter, z0, height):
    r = diameter / 2
    return box(x0, x1, y - r, y + r, z0, z0 + height).fuse(
        cylinder(r, height, (x0, y, z0)), cylinder(r, height, (x1, y, z0))
    )


def slot_x(y, z0, z1, diameter, x0, length):
    r = diameter / 2
    return box(x0, x0 + length, y - r, y + r, z0, z1).fuse(
        cylinder(r, length, (x0, y, z0), (1, 0, 0)),
        cylinder(r, length, (x0, y, z1), (1, 0, 0)),
    )


def male(p, length=None):
    b = p.dovetail_bottom_width / 2
    t = b + p.dovetail_height
    return prism_x(
        [
            (-b, p.base_thickness),
            (b, p.base_thickness),
            (t, p.rail_top),
            (-t, p.rail_top),
        ],
        0,
        length or p.rail_length,
    )


def female_tool(p, x0, length, clearance=None):
    c = p.flank_clearance if clearance is None else clearance
    # y = ±(z + intercept); horizontal shift c*sqrt(2) = normal clearance c.
    z0 = p.base_thickness - 2
    z1 = p.rail_top + p.roof_clearance
    a = p.intercept + c * math.sqrt(2)
    return prism_x(
        [(-z0 - a, z0), (z0 + a, z0), (z1 + a, z1), (-z1 - a, z1)], x0, length
    )


def rail(p):
    r = box(
        0, p.rail_length, -p.rail_width / 2, p.rail_width / 2, 0, p.base_thickness
    ).fuse(male(p))
    for x in (22, p.rail_length - 22):
        for y in (-27, 27):
            r = r.cut(cylinder(2.2, 8, (x, y, -1)))
            r = r.cut(
                cq.Solid.makeCone(
                    2.2,
                    4.2,
                    2,
                    cq.Vector(x, y, p.base_thickness - 2),
                    cq.Vector(0, 0, 1),
                )
            )
    for x in (p.stop_length / 2, p.rail_length - p.stop_length / 2):
        for y in (-26, 26):
            r = r.cut(cylinder(p.m3_clearance / 2, 6, (x, y, -1)))
            r = r.cut(hex_prism(p.m3_nut_af, p.m3_nut_depth + 0.1, (x, y, -0.1)))
    return r.clean()


def stop(p):
    s = box(0, p.stop_length, -30, 30, p.base_thickness, p.rail_top + 3)
    s = s.cut(female_tool(p, -1, p.stop_length + 2))
    for y in (-26, 26):
        s = s.cut(cylinder(p.m3_clearance / 2, 20, (p.stop_length / 2, y, 0)))
        s = s.cut(cylinder(3.1, 4, (p.stop_length / 2, y, p.rail_top)))
    return s.clean()


def carriage(p):
    d = p.deck_top
    r = box(
        0,
        p.carriage_length,
        -p.carriage_width / 2,
        p.carriage_width / 2,
        p.base_thickness + p.roof_clearance,
        d,
    )
    r = r.fuse(
        box(p.carriage_length - 10, p.arm_length, -29, 29, d - p.arm_thickness, d)
    )
    # Lock boss supplies the nut's outward retention wall.
    r = r.fuse(box(26, 46, 28, 33, p.base_thickness + p.roof_clearance, 17))
    r = r.cut(female_tool(p, -1, p.carriage_length + 2))
    # Open rear ribbon relief; a separate 2 mm pad supports the tripod block.
    r = r.cut(box(-1, 5, -12, 12, d - 3, d + 1))
    r = r.cut(cylinder(p.camera_bore / 2, 30, (p.camera_x, 0, 0)))
    r = r.cut(
        cylinder(
            p.camera_head_diameter / 2,
            p.rail_top + p.roof_clearance + p.camera_head_recess,
            (p.camera_x, 0, 0),
        )
    )
    # Rectangular shoe is inserted from the vacant dovetail before loading rail.
    r = r.cut(box(32.7, 39.3, 0, 24.7, 6.7, 11.3))
    r = r.cut(cylinder(p.m4_clearance / 2, 20, (36, 20, 9), (0, 1, 0)))
    r = r.cut(hex_prism(p.m4_nut_af, p.m4_nut_depth, (36, 27, 9), "y"))
    # Nut loading slot opens at top; outer 2.6-mm wall retains reaction force.
    r = r.cut(
        box(
            36 - p.m4_nut_af / 2,
            36 + p.m4_nut_af / 2,
            27,
            27 + p.m4_nut_depth,
            9,
            d + 1,
        )
    )
    for y in (-14, 14):
        r = r.cut(
            slot_z(
                p.saddle_slot_start,
                p.saddle_slot_end,
                y,
                p.m3_clearance,
                d - p.arm_thickness - 0.1,
                p.arm_thickness + 0.2,
            )
        )
        # Portion over the bearing has a recessed tool/head channel, above rail.
        r = r.cut(
            slot_z(
                p.saddle_slot_start,
                p.saddle_slot_end,
                y,
                7.6,
                p.rail_top + p.roof_clearance,
                d - p.arm_thickness - (p.rail_top + p.roof_clearance),
            )
        )
    return r.clean()


def shoe(p):
    # 0.45 mm horizontal tip gap = 0.318 mm normal, before screw pressure.
    return prism_x(
        [
            (7 + p.intercept + 0.45, 7),
            (24.4, 7),
            (24.4, 11),
            (11 + p.intercept + 0.45, 11),
        ],
        33,
        6,
    )


def knob(p):
    # Build around Z; assembly transformation turns knob axis along Y.
    k = cylinder(8.5, 8, (0, 0, 0))
    for i in range(8):
        a = 2 * math.pi * i / 8
        k = k.cut(cylinder(1.6, 10, (8.5 * math.cos(a), 8.5 * math.sin(a), -1)))
    k = k.cut(cylinder(p.m4_clearance / 2, 12, (0, 0, -1)))
    k = k.cut(hex_prism(7.15, 3.1, (0, 0, 4.9)))
    return k.clean()


def saddle_foot(p):
    # Local: bolt centers X0/Y±14, deck interface Z0.
    f = box(-12, 12, -29, 29, 0, 5)
    for y in (-25, 25):
        f = f.fuse(box(0, 6, y - 4, y + 4, 4, 32))
        f = f.cut(
            slot_x(
                y,
                p.saddle_min_base + 7,
                p.saddle_min_base + 7 + p.saddle_height_travel,
                p.m3_clearance,
                -1,
                8,
            )
        )
    for y in (-14, 14):
        f = f.cut(cylinder(p.m3_clearance / 2, 7, (0, y, -1)))
        f = f.cut(
            hex_prism(p.m3_nut_af, p.m3_nut_depth + 0.1, (0, y, 5 - p.m3_nut_depth))
        )
    return f.clean()


def cradle(p):
    # Circle centered 24 mm above cradle bottom; valley height 24-radius.
    c = box(6.3, 14.3, -29, 29, 0, 24)
    c = c.cut(cylinder(p.saddle_radius, 10, (5.3, 0, 24), (1, 0, 0)))
    for y in (-25, 25):
        c = c.cut(cylinder(p.m3_clearance / 2, 10, (5.3, y, 7), (1, 0, 0)))
        c = c.cut(
            hex_prism(
                p.m3_nut_af, p.m3_nut_depth + 0.1, (14.3 - p.m3_nut_depth, y, 7), "x"
            )
        )
    return c.clean()


def liner(p):
    # 120-degree open arc; no overhang above equator and no barrel clamp.
    tube = cylinder(p.saddle_radius, 8, (6.3, 0, 24), (1, 0, 0)).cut(
        cylinder(p.saddle_radius - p.liner_thickness, 10, (5.3, 0, 24), (1, 0, 0))
    )
    sector = prism_x(
        [
            (0, 24),
            (-50, 24 - 50 / math.sqrt(3)),
            (0, -50),
            (50, 24 - 50 / math.sqrt(3)),
        ],
        5.3,
        10,
    )
    return tube.intersect(sector).clean()


def all_parts(p):
    car = carriage(p)
    track = rail(p)
    # Coupons retain actual profiles. Female coupon keeps complete lock region.
    return {
        "rail": track,
        "carriage": car,
        "camera_pad": box(
            p.camera_x - 8,
            p.camera_x + 8,
            -10,
            10,
            p.deck_top,
            p.deck_top + p.camera_pad_height,
        )
        .cut(cylinder(p.camera_bore / 2, 30, (p.camera_x, 0, 0)))
        .clean(),
        "end_stop": stop(p),
        "pressure_shoe": shoe(p),
        "lock_knob": knob(p),
        "saddle_foot": saddle_foot(p),
        "saddle_cradle": cradle(p),
        "soft_liner": liner(p),
        "fit_rail": track.intersect(box(0, 28, -40, 40, 0, 40)).clean(),
        "fit_carriage": car.intersect(box(26, 46, -40, 40, 0, 40)).clean(),
        "camera_screw_coupon": car.intersect(box(3, 22, -11, 11, 12.3, 30)).clean(),
    }


def assembly_parts(p, parts, travel=68, saddle_x=52, rise=7):
    x = p.stop_length + travel
    cradle_z = p.deck_top + p.saddle_min_base + rise
    return {
        "rail": parts["rail"],
        "rear_stop": parts["end_stop"],
        "front_stop": parts["end_stop"].translate(
            (p.rail_length - p.stop_length, 0, 0)
        ),
        "carriage": parts["carriage"].translate((x, 0, 0)),
        "camera_pad": parts["camera_pad"].translate((x, 0, 0)),
        "pressure_shoe": parts["pressure_shoe"].translate((x, 0, 0)),
        "lock_knob": parts["lock_knob"]
        .rotate((0, 0, 0), (1, 0, 0), -90)
        .translate((x + 36, 35.5, 9)),
        "saddle_foot": parts["saddle_foot"].translate((x + saddle_x, 0, p.deck_top)),
        "saddle_cradle": parts["saddle_cradle"].translate((x + saddle_x, 0, cradle_z)),
        "soft_liner": parts["soft_liner"].translate((x + saddle_x, 0, cradle_z)),
    }


def print_oriented(name, shape):
    # Rail stands on its flange; its 45-degree flanks are self-supporting.
    # Carriage upside down gives a flat deck and self-supporting female flanks.
    if name in ("carriage", "fit_carriage", "camera_screw_coupon", "end_stop"):
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
    elif name in ("saddle_cradle", "soft_liner", "pressure_shoe"):
        shape = shape.rotate((0, 0, 0), (0, 1, 0), -90)
    b = shape.BoundingBox()
    return shape.translate((-b.xmin, -b.ymin, -b.zmin))
