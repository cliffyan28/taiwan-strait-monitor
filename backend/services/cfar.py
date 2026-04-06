"""OS-CFAR (Order Statistic Constant False Alarm Rate) ship detector for SAR imagery."""

import math

import numpy as np
from scipy.optimize import brentq


def _os_cfar_threshold_factor(N: int, k: int, pfa: float) -> float:
    """Compute the OS-CFAR threshold multiplier alpha for exponential clutter.

    For N i.i.d. Exp(lambda) background samples, cell under test also Exp(lambda),
    the exact false alarm probability when threshold T = alpha * X_(k) is:

        Pfa = prod_{j=0}^{k-1} (N-k+1+j) / (N-k+1+alpha+j)

    Derivation: Pfa = E[(1-Y)^alpha] where Y ~ Beta(k, N-k+1),
    which equals B(k, N-k+1+alpha) / B(k, N-k+1).

    Args:
        N: number of valid background samples.
        k: OS rank index (1-indexed; k=1 is the minimum).
        pfa: target probability of false alarm.

    Returns:
        Threshold multiplier alpha such that P(X_cut > alpha * X_(k)) = pfa.
    """
    m = N - k + 1  # number of samples "above" the k-th in expectation

    def pfa_func(alpha: float) -> float:
        log_pfa = sum(
            math.log(m + j) - math.log(m + alpha + j) for j in range(k)
        )
        return math.exp(log_pfa) - pfa

    # alpha is always positive; search in a reasonable range
    try:
        return brentq(pfa_func, 1e-6, 1000.0, xtol=1e-4, rtol=1e-4)
    except ValueError:
        # Fallback: return a conservative large multiplier
        return 1000.0


def os_cfar_2d(
    image: np.ndarray,
    water_mask: np.ndarray,
    guard_cells: int = 4,
    bg_cells: int = 16,
    pfa: float = 1e-4,
    os_rank: float = 0.75,
) -> np.ndarray:
    """Run OS-CFAR ship detection on a SAR intensity image.

    Args:
        image: 2D array of linear intensity values (sigma0, NOT dB).
        water_mask: boolean mask, True = water (valid for detection).
        guard_cells: number of guard cells around the cell under test.
        bg_cells: number of background cells outside the guard band.
        pfa: probability of false alarm (lower = fewer false alarms).
        os_rank: percentile rank for order statistic (0.0-1.0).

    Returns:
        Boolean 2D array, True = detected target.
    """
    rows, cols = image.shape
    total_win = guard_cells + bg_cells
    detections = np.zeros((rows, cols), dtype=bool)

    # Cache threshold factors by N to avoid repeated root-finding
    alpha_cache: dict[int, float] = {}

    # Pad image and mask to handle borders
    padded_img = np.pad(image, total_win, mode='reflect')
    padded_mask = np.pad(water_mask, total_win, mode='constant', constant_values=False)

    for r in range(rows):
        for c in range(cols):
            if not water_mask[r, c]:
                continue

            pr = r + total_win
            pc = c + total_win

            # Extract background window, excluding guard cells
            bg_window = padded_img[
                pr - total_win : pr + total_win + 1,
                pc - total_win : pc + total_win + 1,
            ].copy()
            bg_mask = padded_mask[
                pr - total_win : pr + total_win + 1,
                pc - total_win : pc + total_win + 1,
            ].copy()

            # Zero out guard region (center); g = offset to reach guard zone start
            g = bg_cells
            bg_window[g : g + 2 * guard_cells + 1, g : g + 2 * guard_cells + 1] = 0
            bg_mask[g : g + 2 * guard_cells + 1, g : g + 2 * guard_cells + 1] = False

            # Collect valid background samples
            bg_samples = bg_window[bg_mask]
            N = len(bg_samples)
            if N < 10:
                continue

            # Order statistic: sort and pick the rank-th element
            bg_sorted = np.sort(bg_samples)
            rank_idx = int(os_rank * N)
            rank_idx = min(rank_idx, N - 1)
            os_estimate = bg_sorted[rank_idx]

            # k is 1-indexed rank; rank_idx is 0-indexed so k = rank_idx + 1
            k = rank_idx + 1

            if N not in alpha_cache:
                alpha_cache[N] = _os_cfar_threshold_factor(N, k, pfa)
            threshold_factor = alpha_cache[N]

            threshold = os_estimate * threshold_factor

            if image[r, c] > threshold:
                detections[r, c] = True

    return detections


def count_vessels(
    detections: np.ndarray,
    min_pixels: int = 3,
) -> tuple:
    """Count detected vessels using connected component labeling.

    Args:
        detections: boolean detection mask from os_cfar_2d.
        min_pixels: minimum cluster size to count as a vessel.

    Returns:
        (vessel_count, list of (row, col) centroids)
    """
    from scipy.ndimage import center_of_mass, label

    labeled, num_features = label(detections)
    vessels = []

    for i in range(1, num_features + 1):
        component = labeled == i
        if component.sum() >= min_pixels:
            centroid = center_of_mass(component)
            vessels.append((float(centroid[0]), float(centroid[1])))

    return len(vessels), vessels
