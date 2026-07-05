#!/usr/bin/env python3
"""
extract_and_dekeystone.py

Find a (roughly) square/rectangular titanium art piece photographed on a
contrasting background (workbench, table, etc.), extract just the piece,
correct the perspective ("de-keystone" it) so it reads as a flat frontal
rectangle, and save the result as a JPG.

Input can be .heic/.heif, .png, .jpg/.jpeg, or most other formats Pillow reads.

HOW IT WORKS (so you can judge/tune it, not just trust it)
------------------------------------------------------------
1. Load the image, fix EXIF rotation, optionally downscale a *copy* for
   detection speed (the warp itself always uses the full-res original).
2. Canny edge detection, then a standard Hough transform (cv2.HoughLines)
   to find straight lines. Hough is used instead of contour-following
   because the piece's border is rarely one unbroken outline in the edge
   map (glare, low local contrast, JPEG noise) -- Hough accumulates votes
   for a line's direction+offset across broken fragments, so gaps in the
   physical edge don't break detection the way they break contour tracing.
3. Lines are split into "horizontal-ish" and "vertical-ish" by angle, then
   each group is split in two by position (top vs. bottom, left vs. right)
   with a simple 1-D k-means. The strongest line in each of the 4 groups
   is taken as that border.
4. The 4 border lines are intersected pairwise to get the 4 corners.
5. A perspective transform maps those 4 corners to a flat rectangle
   (the de-keystoning), sized from the longer of each pair of opposite
   edges so you don't lose resolution.

This is a real-world computer-vision heuristic, not a guarantee. It was
tuned and verified against an actual sample photo (piece tilted, some
perspective, wood-grain background) and produced pixel-accurate corners
there. Busier backgrounds, low contrast between the piece's edge and the
surface, or extreme angles can still fool it. Two safety nets are built in:

  --debug        writes the edge map and a corners overlay next to the
                 output so you can SEE what it detected before trusting it.
  --corners      lets you pass the 4 corners yourself (e.g. read off the
                 --debug overlay, or from any image viewer) to bypass
                 detection entirely.

USAGE
-----
    python3 extract_and_dekeystone.py photo.heic
    python3 extract_and_dekeystone.py photo.jpg -o piece.jpg --debug
    python3 extract_and_dekeystone.py photo.png --corners "120,80 1900,95 1880,1850 110,1830"

Requires: opencv-python, numpy, Pillow. For HEIC/HEIF input, also needs
either `pillow-heif` (pip install pillow-heif) or, on macOS, falls back to
the built-in `sips` command automatically.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

HEIC_EXTS = {".heic", ".heif"}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def _load_heic_via_pillow_heif(path: Path) -> Image.Image:
    import pillow_heif  # raises ImportError if not installed
    heif_file = pillow_heif.open_heif(str(path), convert_hdr_to_8bit=True)
    return heif_file.to_pillow()


def _load_heic_via_sips(path: Path) -> Image.Image:
    # macOS-only fallback: sips ships with every Mac, no extra install needed.
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "converted.png"
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(path), "--out", str(out_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"sips conversion failed: {result.stderr.strip()}")
        return Image.open(out_path).convert("RGB")


def load_image_as_bgr(path: Path) -> np.ndarray:
    """Load any image (including HEIC) as an OpenCV-style BGR uint8 array,
    with EXIF orientation already applied."""
    pil_img = None

    if path.suffix.lower() in HEIC_EXTS:
        try:
            pil_img = _load_heic_via_pillow_heif(path)
        except ImportError:
            try:
                pil_img = _load_heic_via_sips(path)
            except (FileNotFoundError, RuntimeError) as e:
                raise SystemExit(
                    f"Can't read HEIC/HEIF file: {path}\n"
                    f"Install support with:  pip install pillow-heif\n"
                    f"(macOS-only 'sips' fallback also failed: {e})"
                )
    else:
        pil_img = Image.open(path)

    pil_img = ImageOps.exif_transpose(pil_img)  # apply EXIF rotation if present
    pil_img = pil_img.convert("RGB")
    rgb = np.array(pil_img)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# --------------------------------------------------------------------------
# Corner detection
# --------------------------------------------------------------------------

def _kmeans_1d(vals: np.ndarray, iters: int = 25):
    """Tiny 1-D 2-means, no sklearn dependency."""
    vals = np.asarray(vals, dtype=float)
    c = np.array([vals.min(), vals.max()])
    for _ in range(iters):
        d0, d1 = np.abs(vals - c[0]), np.abs(vals - c[1])
        assign = d1 < d0
        if (~assign).any():
            c[0] = vals[~assign].mean()
        if assign.any():
            c[1] = vals[assign].mean()
    d0, d1 = np.abs(vals - c[0]), np.abs(vals - c[1])
    return d1 < d0, c


def _line_eq(rho_theta):
    rho, theta = rho_theta
    return np.cos(theta), np.sin(theta), rho


def _intersect(l1, l2):
    a1, b1, c1 = _line_eq(l1)
    a2, b2, c2 = _line_eq(l2)
    a = np.array([[a1, b1], [a2, b2]])
    b = np.array([c1, c2])
    return np.linalg.solve(a, b)


def detect_border_corners(
    bgr: np.ndarray,
    detect_max_dim: int = 2400,
    canny_sigma: float = 0.33,
    hough_thresh_frac: float = 0.10,
    angle_tol_deg: float = 25.0,
    debug_dir: Path | None = None,
):
    """Return 4 corners (tl, tr, br, bl) in ORIGINAL bgr's pixel coordinates,
    or None if detection failed."""
    h0, w0 = bgr.shape[:2]
    scale = min(1.0, detect_max_dim / max(h0, w0))
    small = cv2.resize(bgr, (int(round(w0 * scale)), int(round(h0 * scale))),
                        interpolation=cv2.INTER_AREA) if scale < 1.0 else bgr
    h, w = small.shape[:2]

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    v = np.median(blur)
    lower = int(max(0, (1.0 - canny_sigma) * v))
    upper = int(min(255, (1.0 + canny_sigma) * v))
    edges = cv2.Canny(blur, lower, upper)
    edges_d = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    hough_thresh = max(60, int(hough_thresh_frac * max(h, w)))
    lines = cv2.HoughLines(edges_d, 1, np.pi / 720, threshold=hough_thresh)

    if debug_dir is not None:
        cv2.imwrite(str(debug_dir / "debug_edges.png"), edges_d)

    if lines is None or len(lines) < 4:
        return None

    lines = lines[:, 0, :]  # (rho, theta) pairs, strongest first
    theta_deg = np.degrees(lines[:, 1])

    horiz = lines[np.abs(theta_deg - 90) < angle_tol_deg]
    vert = lines[(theta_deg < angle_tol_deg) | (theta_deg > 180 - angle_tol_deg)]
    if len(horiz) < 2 or len(vert) < 2:
        return None

    h_assign, h_c = _kmeans_1d(horiz[:, 0])
    top_grp = horiz[~h_assign] if h_c[0] < h_c[1] else horiz[h_assign]
    bot_grp = horiz[h_assign] if h_c[0] < h_c[1] else horiz[~h_assign]

    # Fold theta-near-180 lines onto theta-near-0 so rho is directly
    # comparable as an x-position for left/right clustering.
    vert_norm = vert.copy()
    fold = vert_norm[:, 1] > np.pi / 2
    vert_norm[fold, 0] *= -1
    vert_norm[fold, 1] -= np.pi

    v_assign, v_c = _kmeans_1d(vert_norm[:, 0])
    left_grp = vert_norm[~v_assign] if v_c[0] < v_c[1] else vert_norm[v_assign]
    right_grp = vert_norm[v_assign] if v_c[0] < v_c[1] else vert_norm[~v_assign]

    if min(len(top_grp), len(bot_grp), len(left_grp), len(right_grp)) == 0:
        return None

    top, bot, left, right = top_grp[0], bot_grp[0], left_grp[0], right_grp[0]

    try:
        tl = _intersect(top, left)
        tr = _intersect(top, right)
        bl = _intersect(bot, left)
        br = _intersect(bot, right)
    except np.linalg.LinAlgError:
        return None

    corners_small = np.array([tl, tr, br, bl], dtype=np.float32)

    if debug_dir is not None:
        vis = small.copy()
        for rt, color in [(top, (0, 255, 0)), (bot, (0, 255, 255)),
                           (left, (255, 0, 0)), (right, (255, 0, 255))]:
            rho, theta = rt
            a, b = np.cos(theta), np.sin(theta)
            x0, y0 = a * rho, b * rho
            L = 3000
            pt1 = (int(x0 - L * (-b)), int(y0 - L * a))
            pt2 = (int(x0 + L * (-b)), int(y0 + L * a))
            cv2.line(vis, pt1, pt2, color, 2)
        for pt in corners_small:
            cv2.circle(vis, (int(pt[0]), int(pt[1])), 10, (0, 0, 255), -1)
        cv2.imwrite(str(debug_dir / "debug_corners.png"), vis)

    return corners_small / scale  # map back to original resolution


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Return points ordered top-left, top-right, bottom-right, bottom-left,
    robust to whatever order they arrive in."""
    pts = np.asarray(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    diff = pts[:, 0] - pts[:, 1]
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmax(diff)]
    bl = pts[np.argmin(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


# --------------------------------------------------------------------------
# Warp
# --------------------------------------------------------------------------

def dekeystone(bgr: np.ndarray, corners: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = order_corners(corners)
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
                   dtype=np.float32)
    M = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl], dtype=np.float32), dst)
    return cv2.warpPerspective(bgr, M, (width, height))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_corners_arg(s: str) -> np.ndarray:
    """Accepts 'x1,y1 x2,y2 x3,y3 x4,y4' in any of the 4 orders (any winding),
    order_corners() sorts it out."""
    try:
        pts = [tuple(map(float, pair.split(","))) for pair in s.split()]
        assert len(pts) == 4
        return np.array(pts, dtype=np.float32)
    except Exception:
        raise argparse.ArgumentTypeError(
            "Expected 4 'x,y' pairs separated by spaces, e.g. "
            "\"120,80 1900,95 1880,1850 110,1830\""
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="source photo (.heic/.heif/.png/.jpg/...)")
    ap.add_argument("-o", "--output", type=Path, default=None,
                     help="output JPG path (default: <input>_extracted.jpg)")
    ap.add_argument("--quality", type=int, default=95, help="JPEG quality (default 95)")
    ap.add_argument("--debug", action="store_true",
                     help="save debug_edges.png and debug_corners.png next to the output")
    ap.add_argument("--corners", type=parse_corners_arg, default=None,
                     help="manually specify the 4 corners as 'x,y x,y x,y x,y' "
                          "(bypasses auto-detection)")
    ap.add_argument("--detect-max-dim", type=int, default=2400,
                     help="downscale copy used for detection, longer side in px "
                          "(default 2400; raise for more precision, lower for more speed)")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    output = args.output or args.input.with_name(args.input.stem + "_extracted.jpg")
    debug_dir = output.parent if args.debug else None

    bgr = load_image_as_bgr(args.input)
    print(f"Loaded {args.input.name}: {bgr.shape[1]}x{bgr.shape[0]}")

    if args.corners is not None:
        corners = args.corners
        print("Using manually specified corners (auto-detection skipped).")
    else:
        corners = detect_border_corners(bgr, detect_max_dim=args.detect_max_dim,
                                         debug_dir=debug_dir)
        if corners is None:
            msg = ("Couldn't confidently detect the piece's border.\n"
                   "Try:\n"
                   "  --debug            to see the edge map and inspect what's happening\n"
                   "  --corners 'x,y ...' to specify the 4 corners yourself")
            raise SystemExit(msg)

    ordered = order_corners(corners)
    print("Detected corners (tl, tr, br, bl):")
    for name, pt in zip(("top-left", "top-right", "bottom-right", "bottom-left"), ordered):
        print(f"    {name:>12}: ({pt[0]:.1f}, {pt[1]:.1f})")

    result = dekeystone(bgr, corners)
    print(f"Output size: {result.shape[1]}x{result.shape[0]}")

    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), result, [cv2.IMWRITE_JPEG_QUALITY, args.quality])
    print(f"Saved: {output}")

    if debug_dir is not None:
        print(f"Debug images: {debug_dir / 'debug_edges.png'}, "
              f"{debug_dir / 'debug_corners.png'}")


if __name__ == "__main__":
    main()
