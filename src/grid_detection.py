"""
网格检测逻辑
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .config import GridDetectionConfig


def detect_grid(image: np.ndarray, debug: bool, config: GridDetectionConfig) -> Optional[Dict]:
    """
    检测图片中的网格结构。
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_block_size,
        config.adaptive_c,
    )

    binary = cv2.bitwise_not(binary)

    kernel_len = _get_grid_kernel_len(image, config)
    kernel_horizontal, kernel_vertical = _build_grid_kernels(kernel_len)

    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_horizontal)
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_vertical)

    grid_lines = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0)

    if debug:
        cv2.imshow('Binary', binary)
        cv2.imshow('Horizontal Lines', horizontal_lines)
        cv2.imshow('Vertical Lines', vertical_lines)
        cv2.imshow('Grid Lines', grid_lines)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    h_lines = _detect_lines(
        horizontal_lines,
        angle_threshold=config.angle_threshold_h,
        threshold=config.hough_threshold,
        min_line_length=config.min_line_length,
        max_line_gap=config.max_line_gap,
    )
    v_lines = _detect_lines(
        vertical_lines,
        angle_threshold=config.angle_threshold_v,
        threshold=config.hough_threshold,
        min_line_length=config.min_line_length,
        max_line_gap=config.max_line_gap,
    )

    if len(h_lines) < 2 or len(v_lines) < 2:
        print(
            f"检测到的线条不足: 水平线 {len(h_lines)}, 垂直线 {len(v_lines)}，尝试投影法回退"
        )
        h_positions, v_positions = _detect_grid_by_projection(image, config)
    else:
        h_positions = _positions_from_lines(h_lines, axis='h')
        v_positions = _positions_from_lines(v_lines, axis='v')

    if len(h_positions) < 2 or len(v_positions) < 2:
        print(f"投影法仍不足: 水平线 {len(h_positions)}, 垂直线 {len(v_positions)}")
        return None

    h_positions, v_positions = _postprocess_grid_positions(h_positions, v_positions, config)

    if _is_irregular_grid(h_positions, config) or _is_irregular_grid(v_positions, config):
        strong_kernel_len = int(kernel_len * 1.5)
        strong_kernel_horizontal, strong_kernel_vertical = _build_grid_kernels(strong_kernel_len)

        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, strong_kernel_horizontal)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, strong_kernel_vertical)

        h_lines = _detect_lines(
            horizontal_lines,
            angle_threshold=config.angle_threshold_h,
            threshold=config.hough_threshold_strong,
            min_line_length=config.min_line_length,
            max_line_gap=config.max_line_gap,
        )
        v_lines = _detect_lines(
            vertical_lines,
            angle_threshold=config.angle_threshold_v,
            threshold=config.hough_threshold_strong,
            min_line_length=config.min_line_length,
            max_line_gap=config.max_line_gap,
        )

        if len(h_lines) >= 2 and len(v_lines) >= 2:
            h_positions = _positions_from_lines(h_lines, axis='h')
            v_positions = _positions_from_lines(v_lines, axis='v')
            h_positions, v_positions = _postprocess_grid_positions(
                h_positions, v_positions, config
            )

    print(f"检测到 {len(h_positions)} 条水平线, {len(v_positions)} 条垂直线")

    avg_h_spacing = _median_spacing(h_positions)
    avg_v_spacing = _median_spacing(v_positions)

    print(f"平均网格间距: 水平 {avg_h_spacing:.1f}, 垂直 {avg_v_spacing:.1f}")

    return {
        'h_positions': h_positions,
        'v_positions': v_positions,
        'h_lines': h_positions,
        'v_lines': v_positions,
        'h_spacing': avg_h_spacing,
        'v_spacing': avg_v_spacing,
    }


def _get_grid_kernel_len(image: np.ndarray, config: GridDetectionConfig) -> int:
    h, w = image.shape[:2]
    return max(config.kernel_len_min, int(min(h, w) * config.kernel_len_ratio))


def _build_grid_kernels(kernel_len: int) -> Tuple[np.ndarray, np.ndarray]:
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    return kernel_horizontal, kernel_vertical


def _positions_from_lines(lines: List[Tuple[int, int]], axis: str) -> List[int]:
    if axis == 'h':
        return sorted(set([int(y) for _, y in lines]))
    return sorted(set([int(x) for x, _ in lines]))


def _postprocess_grid_positions(
    h_positions: List[int], v_positions: List[int], config: GridDetectionConfig
) -> Tuple[List[int], List[int]]:
    rough_h_spacing = _median_spacing(h_positions)
    rough_v_spacing = _median_spacing(v_positions)

    min_dist_h = (
        max(config.merge_min_distance, int(rough_h_spacing * config.merge_spacing_ratio))
        if rough_h_spacing > 0
        else config.merge_min_distance
    )
    min_dist_v = (
        max(config.merge_min_distance, int(rough_v_spacing * config.merge_spacing_ratio))
        if rough_v_spacing > 0
        else config.merge_min_distance
    )

    h_positions = _filter_close_lines(h_positions, min_distance=min_dist_h)
    v_positions = _filter_close_lines(v_positions, min_distance=min_dist_v)

    h_positions = _normalize_grid_positions(h_positions)
    v_positions = _normalize_grid_positions(v_positions)

    return h_positions, v_positions


def _median_spacing(positions: List[int]) -> float:
    if len(positions) > 1:
        return float(np.median(np.diff(sorted(positions))))
    return 0.0


def _detect_lines(
    image: np.ndarray,
    angle_threshold: float = 10,
    threshold: int = 50,
    min_line_length: int = 30,
    max_line_gap: int = 5,
) -> List[Tuple[int, int]]:
    lines = cv2.HoughLinesP(
        image,
        rho=1,
        theta=np.pi / 180,
        threshold=threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )

    if lines is None:
        return []

    detected_lines: List[Tuple[int, int]] = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

        if angle < angle_threshold or angle > 180 - angle_threshold:
            detected_lines.append((x1, (y1 + y2) // 2))
        elif 90 - angle_threshold < angle < 90 + angle_threshold:
            detected_lines.append(((x1 + x2) // 2, y1))

    return detected_lines


def _filter_close_lines(positions: List[int], min_distance: int = 5) -> List[int]:
    if not positions:
        return []

    positions = sorted(positions)
    merged: List[int] = []
    cluster = [positions[0]]

    for pos in positions[1:]:
        if pos - cluster[-1] <= min_distance:
            cluster.append(pos)
        else:
            merged.append(int(round(np.mean(cluster))))
            cluster = [pos]

    merged.append(int(round(np.mean(cluster))))

    return merged


def _normalize_grid_positions(positions: List[int]) -> List[int]:
    if len(positions) < 3:
        return positions

    positions = sorted(positions)
    diffs = np.diff(positions)
    spacing = np.median(diffs)

    if spacing <= 0:
        return positions

    if (np.std(diffs) / spacing) < 0.25 and np.min(diffs) > spacing * 0.6:
        return positions

    index_map: Dict[int, List[int]] = {}
    base = positions[0]
    for pos in positions:
        idx = int(round((pos - base) / spacing))
        index_map.setdefault(idx, []).append(pos)

    normalized = [int(round(np.mean(index_map[i]))) for i in sorted(index_map.keys())]
    return normalized


def _is_irregular_grid(positions: List[int], config: GridDetectionConfig) -> bool:
    if len(positions) < 3:
        return False
    diffs = np.diff(sorted(positions))
    spacing = np.median(diffs)
    if spacing <= 0:
        return False
    return (np.std(diffs) / spacing) > config.irregular_spacing_std_ratio or np.min(
        diffs
    ) < spacing * config.irregular_min_ratio


def _detect_grid_by_projection(
    image: np.ndarray, config: GridDetectionConfig
) -> Tuple[List[int], List[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)

    h_profile = edges.sum(axis=1)
    v_profile = edges.sum(axis=0)

    h_positions = _positions_from_profile(h_profile, config)
    v_positions = _positions_from_profile(v_profile, config)

    return h_positions, v_positions


def _positions_from_profile(profile: np.ndarray, config: GridDetectionConfig) -> List[int]:
    if profile.size == 0:
        return []

    threshold = np.median(profile) + np.std(profile) * config.projection_std_ratio
    indices = np.where(profile >= threshold)[0]
    if len(indices) == 0:
        return []

    positions: List[int] = []
    start = indices[0]
    prev = indices[0]
    for idx in indices[1:]:
        if idx == prev + 1:
            prev = idx
            continue
        center = (start + prev) // 2
        positions.append(int(center))
        start = idx
        prev = idx
    center = (start + prev) // 2
    positions.append(int(center))

    return positions
