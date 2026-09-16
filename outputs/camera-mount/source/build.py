"""Generate solids, print-oriented meshes, numerical checks and assembly views."""

import itertools
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/Codex/camera-mount/matplotlib")
import matplotlib

matplotlib.use("Agg")
import cadquery as cq
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from model import (
    Parameters,
    all_parts,
    assembly_parts,
    box,
    cylinder,
    hex_prism,
    print_oriented,
)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parent.parent


def overlap(a, b):
    return a.intersect(b).Volume()


def hardware(p, travel, sx, rise):
    x = p.stop_length + travel
    d = p.deck_top
    seat = p.rail_top + p.roof_clearance + p.camera_head_recess
    h = {
        "camera_screw": cylinder(3.175, 9.525, (x + p.camera_x, 0, seat)).fuse(
            cylinder(5.6, 3.3, (x + p.camera_x, 0, seat - 3.3))
        )
    }
    # M4x16 hex screw; 7 mm AF head. Threads represented by nominal envelope.
    h["lock_screw"] = cylinder(2, 16, (x + 36, 24.4, 9), (0, 1, 0)).fuse(
        hex_prism(7, 2.8, (x + 36, 40.4, 9), "y")
    )
    # Nuts as rings: subtract thread minor approximation to avoid nominal shank overlaps.
    h["lock_nut"] = hex_prism(7, 3.2, (x + 36, 27, 9), "y").cut(
        cylinder(2.01, 4, (x + 36, 26.9, 9), (0, 1, 0))
    )
    for j, y in enumerate((-14, 14)):
        # M3x10 from below + 0.5 washer under head.
        h[f"foot_screw_{j}"] = cylinder(1.5, 10, (x + sx, y, d - 4.5)).fuse(
            cylinder(2.75, 3, (x + sx, y, d - 7.5))
        )
        h[f"foot_washer_{j}"] = cylinder(3.5, 0.5, (x + sx, y, d - 4.5)).cut(
            cylinder(1.7, 0.7, (x + sx, y, d - 4.6))
        )
        h[f"foot_nut_{j}"] = hex_prism(5.5, 2.4, (x + sx, y, d + 2.4)).cut(
            cylinder(1.51, 3, (x + sx, y, d + 2.3))
        )
    for j, y in enumerate((-25, 25)):
        z = d + p.saddle_min_base + rise + 7
        h[f"height_screw_{j}"] = cylinder(
            1.5, 16, (x + sx - 0.5, y, z), (1, 0, 0)
        ).fuse(cylinder(2.75, 3, (x + sx - 3.5, y, z), (1, 0, 0)))
        h[f"height_washer_{j}"] = cylinder(
            3.5, 0.5, (x + sx - 0.5, y, z), (1, 0, 0)
        ).cut(cylinder(1.7, 0.7, (x + sx - 0.6, y, z), (1, 0, 0)))
        h[f"height_nut_{j}"] = hex_prism(5.5, 2.4, (x + sx + 11.7, y, z), "x").cut(
            cylinder(1.51, 3, (x + sx + 11.6, y, z), (1, 0, 0))
        )
    for i, xx in enumerate((p.stop_length / 2, p.rail_length - p.stop_length / 2)):
        for j, y in enumerate((-26, 26)):
            h[f"stop_screw_{i}_{j}"] = cylinder(1.5, 12, (xx, y, p.rail_top - 12)).fuse(
                cylinder(2.75, 3, (xx, y, p.rail_top))
            )
            h[f"stop_nut_{i}_{j}"] = hex_prism(5.5, 2.4, (xx, y, 0.1)).cut(
                cylinder(1.51, 3, (xx, y, 0))
            )
    # The lock hardware follows the front-facing carriage/shoe reflection.
    for name in ("lock_screw", "lock_nut"):
        h[name] = h[name].mirror("XZ")
    return h


def main():
    p = Parameters.from_file(Path(__file__).with_name("parameters.json"))
    for directory in ("stl", "step", "docs"):
        (ROOT / directory).mkdir(exist_ok=True)
    parts = all_parts(p)
    report = {
        "units": "mm",
        "parts": {},
        "checks": {},
        "limitations": [
            "No physical printing, load test, creep test, or camera/box measurements performed.",
            "Camera and lens shown in diagrams are illustrative clearance envelopes, not measured replicas.",
            "Check thread depth, screw head, seating pad/PCB, ribbon routing, lens support band and enclosure sweep before full print.",
        ],
    }
    for name, shape in parts.items():
        assert shape.isValid(), f"Invalid solid: {name}"
        assert len(shape.Solids()) == 1, f"Disconnected solid: {name}"
        assert shape.Volume() > 0
        printable = print_oriented(name, shape)
        cq.exporters.export(
            printable,
            str(ROOT / "stl" / f"{name}.stl"),
            tolerance=0.03,
            angularTolerance=0.08,
        )
        cq.exporters.export(shape, str(ROOT / "step" / f"{name}.step"))
        mesh = trimesh.load_mesh(ROOT / "stl" / f"{name}.stl")
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, (
            name
        )
        report["parts"][name] = {
            "valid_solid": True,
            "connected_solids": 1,
            "watertight_stl": True,
            "volume_mm3": round(shape.Volume(), 2),
            "print_bounds_mm": np.round(mesh.extents, 3).tolist(),
            "triangles": len(mesh.faces),
        }
        print(f"Exported {name}: {len(mesh.faces)} triangles", flush=True)

    # Cartesian-product extremes/midpoints of three independent motion axes.
    max_volume = 0.0
    collisions = []
    checked = 0
    for t, sx, h in itertools.product(
        (0, p.travel / 2, p.travel),
        (
            p.saddle_slot_start,
            (p.saddle_slot_start + p.saddle_slot_end) / 2,
            p.saddle_slot_end,
        ),
        (0, p.saddle_height_travel / 2, p.saddle_height_travel),
    ):
        a = assembly_parts(p, parts, t, sx, h)
        for (an, ash), (bn, bsh) in itertools.combinations(a.items(), 2):
            v = overlap(ash, bsh)
            max_volume = max(max_volume, v)
            checked += 1
            if v > 0.001:
                collisions.append([t, sx, h, an, bn, round(v, 5)])
        for hn, hs in hardware(p, t, sx, h).items():
            for an, ash in a.items():
                v = overlap(hs, ash)
                checked += 1
                if v > 0.001:
                    collisions.append([t, sx, h, hn, an, round(v, 5)])
        print(f"Checked pose: travel={t:g}, saddle={sx:g}, rise={h:g}", flush=True)
    report["checks"]["motion_poses"] = 27
    report["checks"]["solid_pair_checks"] = checked
    report["checks"]["collisions"] = collisions
    report["checks"]["max_printed_part_overlap_mm3"] = round(max_volume, 8)
    report["checks"]["travel_mm"] = p.travel
    report["checks"]["flank_clearance_normal_mm"] = p.flank_clearance
    report["checks"]["roof_clearance_mm"] = p.roof_clearance
    report["checks"]["arm_to_stop_vertical_clearance_mm"] = (
        p.deck_top - p.arm_thickness - (p.rail_top + 3)
    )
    report["checks"]["camera_screw_tip_above_pad_mm"] = (
        p.rail_top
        + p.roof_clearance
        + p.camera_head_recess
        + 9.525
        - (p.deck_top + p.camera_pad_height)
    )
    report["checks"]["camera_head_to_rail_clearance_mm"] = (
        p.roof_clearance + p.camera_head_recess - 3.3
    )
    report["checks"]["foot_head_to_rail_clearance_mm"] = p.deck_top - 7.5 - p.rail_top
    report["checks"]["foot_head_to_stop_clearance_mm"] = (
        p.deck_top - 7.5 - (p.rail_top + 3)
    )
    # The lock must take up BOTH the shoe gap and opposite dovetail backlash.
    shift = p.flank_clearance * math.sqrt(2)
    advance = 0.45 + shift
    locked = assembly_parts(p, parts)
    assert locked["lock_knob"].BoundingBox().ymax < -35, (
        "Knob must face the accessible shelf front (-Y)"
    )
    assert locked["pressure_shoe"].BoundingBox().ymax < 0, (
        "Shoe must follow the front-facing lock"
    )
    report["checks"]["lock_side"] = "front (-Y), toward enclosure opening"
    for name in locked:
        if name not in ("rail", "rear_stop", "front_stop"):
            locked[name] = locked[name].translate((0, -shift, 0))
    for name in ("pressure_shoe", "lock_knob"):
        locked[name] = locked[name].translate((0, advance, 0))
    for (an, ash), (bn, bsh) in itertools.combinations(locked.items(), 2):
        v = overlap(ash, bsh)
        assert v < 0.001, f"Locked-position interference: {an}/{bn}: {v}"
    # Contact exists at the two clamping interfaces; another 0.05 mm cannot pass.
    assert (
        overlap(locked["pressure_shoe"].translate((0, 0.05, 0)), locked["rail"]) > 0.01
    )
    assert overlap(locked["carriage"].translate((0, -0.05, 0)), locked["rail"]) > 0.01
    report["checks"]["lock_stroke_to_contact_mm"] = round(advance, 4)
    report["checks"]["lock_knob_to_boss_at_contact_mm"] = round(35.5 - advance - 33, 4)
    report["checks"]["locked_pose_no_interference"] = True
    report["checks"]["shelf_margins_each_end_side_mm"] = [
        (210 - p.rail_length) / 2,
        (70 - p.rail_width) / 2,
    ]
    # Beyond-limit motion must produce solid interference, not just touch.
    for side, t in (("rear", -0.5), ("front", p.travel + 0.5)):
        a = assembly_parts(p, parts, t)
        v = overlap(a["carriage"], a[f"{side}_stop"])
        assert v > 1, f"Missing {side} hard stop"
        report["checks"][f"{side}_stop_overlap_at_0.5mm_overtravel_mm3"] = round(v, 3)
    # Upward movement must be blocked by the undercut, even without end caps.
    a = assembly_parts(p, parts)
    v = overlap(a["carriage"].translate((0, 0, 1)), a["rail"])
    assert v > 1, "Dovetail does not capture carriage"
    report["checks"]["capture_overlap_at_1mm_lift_mm3"] = round(v, 3)
    (ROOT / "docs" / "verification.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    assert not collisions, f"Interferences: {collisions[:10]}"

    assembled = assembly_parts(p, parts)
    assy = cq.Assembly(name="Pi_HQ_camera_mount")
    for name, shape in assembled.items():
        assy.add(shape, name=name)
    assy.export(str(ROOT / "step" / "assembly.step"))
    overview(p, parts)
    print("All checks passed. Files exported.", flush=True)


COLORS = {
    "rail": "#344e65",
    "rear_stop": "#eeb354",
    "front_stop": "#eeb354",
    "carriage": "#23a3a1",
    "camera_pad": "#287575",
    "pressure_shoe": "#b65828",
    "lock_knob": "#eeb354",
    "saddle_foot": "#74bdb4",
    "saddle_cradle": "#16a3a1",
    "soft_liner": "#343a40",
}


def add_solid(ax, shape, color, alpha=1):
    vs, fs = shape.tessellate(0.25, 0.15)
    vertices = np.array([v.toTuple() for v in vs])
    tris = vertices[np.array(fs)]
    # Subdivide long planar facets only for the illustration. Painter sorting
    # otherwise misorders a 200-mm triangle against a small elevated part.
    for _ in range(7):
        lengths = np.linalg.norm(tris - np.roll(tris, 1, axis=1), axis=2)
        split = lengths.max(axis=1) > 5
        if not split.any():
            break
        a, b, c = np.moveaxis(tris[split], 1, 0)
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        tris = np.concatenate(
            [
                tris[~split],
                np.stack([a, ab, ca], axis=1),
                np.stack([ab, b, bc], axis=1),
                np.stack([ca, bc, c], axis=1),
                np.stack([ab, bc, ca], axis=1),
            ]
        )
    if not hasattr(ax, "mount_faces"):
        ax.mount_faces = []
        ax.mount_colors = []
    ax.mount_faces.extend(tris)
    ax.mount_colors.extend([matplotlib.colors.to_rgba(color, alpha)] * len(tris))


def finish_solids(ax):
    # A single collection sorts all triangles together; separate collections
    # can wrongly draw a large shelf over parts that are physically above it.
    ax.add_collection3d(
        Poly3DCollection(
            ax.mount_faces,
            facecolors=ax.mount_colors,
            linewidths=0,
            antialiaseds=False,
            shade=True,
            lightsource=matplotlib.colors.LightSource(azdeg=300, altdeg=45),
        )
    )


def overview(p, parts):
    fig = plt.figure(figsize=(15, 10), facecolor="#f4f6f7")
    ax = fig.add_axes((0.03, 0.19, 0.72, 0.72), projection="3d", facecolor="#f4f6f7")
    a = assembly_parts(p, parts)
    add_solid(ax, box(-5, 205, -35, 35, -6, 0), "#d9ba8a")
    for name, shape in a.items():
        add_solid(ax, shape, COLORS[name])
    # Illustrative camera/lens shown faintly; not used as an exact-fit claim.
    x = p.stop_length + p.travel / 2 + p.camera_x
    axis = (
        p.deck_top
        + p.saddle_min_base
        + 7
        + 24
        - p.saddle_radius
        + p.liner_thickness
        + 15
    )
    add_solid(ax, box(x - 11, x - 9, -19, 19, axis - 19, axis + 19), "#477448", 0.4)
    add_solid(
        ax,
        box(x - 6, x + 6, -6, 6, p.deck_top + p.camera_pad_height, axis - 10),
        "#464f56",
        0.35,
    )
    add_solid(ax, cylinder(15, 65, (x, 0, axis), (1, 0, 0)), "#647382", 0.15)
    finish_solids(ax)
    ax.set(xlim=(-10, 240), ylim=(-45, 50), zlim=(-6, 80))
    ax.set_box_aspect((250, 95, 86))
    ax.view_init(elev=30, azim=-58)
    ax.set_axis_off()
    fig.text(
        0.045,
        0.945,
        "PI HQ CAMERA • SLIDING SHELF MOUNT",
        fontsize=23,
        weight="bold",
        color="#173047",
    )
    fig.text(
        0.045,
        0.907,
        "Parametric PETG prototype  |  dimensions in millimetres",
        fontsize=12,
        color="#536573",
    )
    fig.text(
        0.76,
        0.79,
        "200 × 65 rail\n136 mechanical travel\n48 bearing length\n90 overall carriage length",
        fontsize=13,
        linespacing=1.7,
        color="#173047",
    )
    fig.text(
        0.76,
        0.57,
        "Adjustable U saddle\n40 fore/aft adjustment\n14 height adjustment\n1 soft liner",
        fontsize=13,
        linespacing=1.7,
        color="#173047",
    )
    fig.text(
        0.76,
        0.35,
        "Hardware\n1/4-20 camera screw\nFront-facing M4 lock + shoe\nM3 saddle and stops",
        fontsize=13,
        linespacing=1.7,
        color="#173047",
    )
    fig.text(
        0.045,
        0.13,
        "PRINT FIT COUPONS FIRST",
        fontsize=13,
        weight="bold",
        color="#173047",
    )
    fig.text(
        0.045,
        0.092,
        "Full rail travel may be limited by the box, lens, glass and cable. The forward arm can overhang the shelf by 29 mm.",
        fontsize=11,
        color="#536573",
    )
    fig.text(
        0.045,
        0.06,
        "Translucent camera/lens are illustrative envelopes. Confirm socket depth, barrel support band and clearances on the actual hardware.",
        fontsize=11,
        color="#536573",
    )
    fig.savefig(ROOT / "docs" / "assembly-overview.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
