"""
Contains tools for manipulation of 2D contours
"""
import numpy as np
from scipy.interpolate import interp1d
import logging

log = logging.getLogger(__name__)


def path_angles_2D(pnts, normalize: bool = None, degrees: bool = True):
    """
    Returns `len(pnts) - 2` angles between consecutive segments.

    Args:
        pnt (array): shape = (len(pnts), 2)
        normalize (bool): set `True` to normalize the `pnts` before calculating
            the angles
        degrees (bool): set `True` to return angles in degrees
    """
    if normalize:
        pnts_T = pnts.T
        min_xy = np.array([np.min(p) for p in pnts_T])
        max_xy = np.array([np.max(p) for p in pnts_T])
        pnts = (pnts - min_xy) / (max_xy - min_xy)

    a_pnts = pnts[:-2]
    b_pnts = pnts[1:-1]
    c_pnts = pnts[2:]

    ba_pnts = a_pnts - b_pnts
    bc_pnts = c_pnts - b_pnts

    angles = (
        (np.arctan2(*bc) - np.arctan2(*ba)) % (2 * np.pi)
        for ba, bc in zip(ba_pnts, bc_pnts)
    )

    if degrees:
        angles = (np.degrees(angle) for angle in angles)

    return angles


def interp_2D_contour(c_pnts, interp_method: str = "slinear"):
    """
    Returns and `interp1d` along a 2D contour path according to `interp_method`
    """
    assert interp_method in {"slinear", "quadratic", "cubic"}

    # Linear length along the line:
    distance = np.cumsum(np.sqrt(np.sum(np.diff(c_pnts, axis=0) ** 2, axis=1)))
    # Normalize
    distance = np.insert(distance, 0, 0) / distance[-1]

    interpolator = interp1d(distance, c_pnts, kind=interp_method, axis=0)

    return interpolator


def simplify_2D_path(path, angle_thr: float = 7.0, cumulative: bool = True):
    """
    Removes redundant points along a 2D path according to a threshold angle
    between consecutive segments.
    Consecutive points are assumed to be connected segments.

    Args:
        path (array): shape = (len(path), 2)
        angle_thr (float):  tolerance angle in degrees
            - applied after normalizing points along each dimensions
            - points that deviate from a straight line more than
                `angle_thr` will be included in the output path
        cumulative (bool): if true the `angle_thr` is conidered cumulative
            along the path. Gives beter results.

    """
    angles = np.fromiter(path_angles_2D(path, normalize=True), dtype=np.float64)
    dif_from_180 = angles - 180

    if cumulative:
        inlc = np.full(len(dif_from_180), False)

        cum_diff = 0
        for i, diff in enumerate(dif_from_180):
            cum_diff += diff
            if np.abs(cum_diff) > angle_thr:
                inlc[i] = True
                cum_diff = 0

        where_incl = np.where(inlc)
    else:
        where_incl = np.where(np.abs(dif_from_180) > angle_thr)

    # Include initial and final pnts
    path_out = np.concatenate(([path[0]], path[where_incl[0] + 1], [path[-1]]))

    return path_out