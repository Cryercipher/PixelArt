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
    """
    自适应计算形态学核长度。
    先用边缘检测估算网格间距，然后选择合适的核长度。
    """
    h, w = image.shape[:2]

    # 先估算网格间距
    estimated_spacing = _estimate_grid_spacing(image)

    if estimated_spacing > 0:
        # kernel 长度设为网格间距的 1.2 倍，确保能检测到网格线
        adaptive_len = int(estimated_spacing * 1.2)
        # 限制在合理范围内
        adaptive_len = max(15, min(adaptive_len, 60))
        return adaptive_len

    # 回退到原来的计算方式
    return max(config.kernel_len_min, int(min(h, w) * config.kernel_len_ratio))


def _estimate_grid_spacing(image: np.ndarray) -> float:
    """
    使用 Sobel 边缘检测估算网格间距。
    """
    try:
        from scipy.signal import find_peaks
    except ImportError:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 用 Sobel 检测垂直和水平边缘
    sobel_h = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))
    sobel_v = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))

    # 投影
    h_profile = sobel_h.sum(axis=1)
    v_profile = sobel_v.sum(axis=0)

    # 归一化
    h_profile = h_profile / (h_profile.max() + 1e-6)
    v_profile = v_profile / (v_profile.max() + 1e-6)

    # 找峰值
    h_peaks, _ = find_peaks(h_profile, distance=10, prominence=0.05)
    v_peaks, _ = find_peaks(v_profile, distance=10, prominence=0.05)

    # 计算中位间距
    spacings = []
    if len(h_peaks) > 2:
        h_spacing = np.median(np.diff(h_peaks))
        spacings.append(h_spacing)
    if len(v_peaks) > 2:
        v_spacing = np.median(np.diff(v_peaks))
        spacings.append(v_spacing)

    if spacings:
        return float(np.mean(spacings))
    return 0.0


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
    """
    使用 Hough 变换检测线条。

    angle_threshold: 与水平/垂直方向的允许角度偏差（度）
    """
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

    # 使用固定的角度阈值来判断水平和垂直线
    h_threshold = 15  # 与水平方向（0度或180度）的允许偏差
    v_threshold = 15  # 与垂直方向（90度）的允许偏差

    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

        # 水平线: 角度接近 0 或 180
        if angle < h_threshold or angle > 180 - h_threshold:
            detected_lines.append((x1, (y1 + y2) // 2))
        # 垂直线: 角度接近 90
        elif 90 - v_threshold < angle < 90 + v_threshold:
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
    """
    归一化网格位置，填补漏检的线条。
    """
    if len(positions) < 3:
        return positions

    positions = sorted(positions)
    diffs = np.diff(positions)
    spacing = np.median(diffs)

    if spacing <= 0:
        return positions

    # 如果间距已经很均匀，直接返回
    if (np.std(diffs) / spacing) < 0.2 and np.min(diffs) > spacing * 0.6:
        return positions

    # 检测并填补漏掉的线条
    filled_positions = [positions[0]]
    for i in range(1, len(positions)):
        gap = positions[i] - positions[i - 1]
        # 如果间距超过 1.4 倍中位数，可能漏掉了线条
        if gap > spacing * 1.4:
            # 计算应该有多少条线
            num_missing = int(round(gap / spacing)) - 1
            if num_missing > 0:
                # 均匀插入缺失的线条
                step = gap / (num_missing + 1)
                for j in range(1, num_missing + 1):
                    filled_positions.append(int(positions[i - 1] + j * step))
        filled_positions.append(positions[i])

    # 填补后再次合并过近的线条
    filled_positions = sorted(filled_positions)
    min_dist = max(5, int(spacing * 0.4))
    merged = _filter_close_lines(filled_positions, min_distance=min_dist)

    return merged


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
