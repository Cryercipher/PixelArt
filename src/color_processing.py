"""
颜色提取与合并逻辑
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

import cv2
import numpy as np
from sklearn.cluster import KMeans

from .config import ColorProcessingConfig


def _build_watermark_mask(
    image: np.ndarray, config: ColorProcessingConfig
) -> np.ndarray | None:
    if not config.watermark_filter_enabled:
        return None

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    brightness = (r + g + b) / 3.0
    color_range = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    mask = (
        (brightness >= config.watermark_brightness_min)
        & (brightness <= config.watermark_brightness_max)
        & (color_range <= config.watermark_color_range)
    )

    return mask


def _build_watermark_edge_mask(
    image: np.ndarray, config: ColorProcessingConfig
) -> np.ndarray | None:
    if not config.watermark_edge_filter_enabled:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    v = float(np.median(gray))
    lower = int(max(0, (1.0 - config.watermark_edge_sigma) * v))
    upper = int(min(255, (1.0 + config.watermark_edge_sigma) * v))
    edges = cv2.Canny(gray, lower, upper)

    if config.watermark_edge_dilate > 0:
        kernel = np.ones((config.watermark_edge_dilate, config.watermark_edge_dilate), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

    return edges > 0


def _merge_similar_palette(
    colors: List[Tuple[int, int, int]],
    counts: Counter,
    threshold: float,
) -> Dict[Tuple[int, int, int], Tuple[int, int, int]]:
    if threshold <= 0 or len(colors) < 2:
        return {}

    color_array = np.array(colors, dtype=np.uint8).reshape(-1, 1, 3)
    labs = cv2.cvtColor(color_array, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)

    order = sorted(range(len(colors)), key=lambda i: counts.get(colors[i], 1), reverse=True)
    clusters: List[Dict[str, np.ndarray | float]] = []

    for idx in order:
        color = colors[idx]
        lab = labs[idx]
        weight = float(counts.get(color, 1))

        best_idx = None
        best_dist = float('inf')
        for c_idx, cluster in enumerate(clusters):
            dist = float(np.linalg.norm(lab - cluster['lab']))
            if dist <= threshold and dist < best_dist:
                best_dist = dist
                best_idx = c_idx

        if best_idx is None:
            clusters.append(
                {
                    'lab': lab.copy(),
                    'rgb': np.array(color, dtype=np.float32),
                    'count': weight,
                }
            )
        else:
            cluster = clusters[best_idx]
            total = float(cluster['count']) + weight
            cluster['lab'] = (cluster['lab'] * cluster['count'] + lab * weight) / total
            cluster['rgb'] = (cluster['rgb'] * cluster['count'] + np.array(color, dtype=np.float32) * weight) / total
            cluster['count'] = total

    final_labs = np.array([c['lab'] for c in clusters], dtype=np.float32)
    final_rgbs = [tuple(map(int, np.round(c['rgb']))) for c in clusters]

    mapping: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    for i, color in enumerate(colors):
        lab = labs[i]
        dists = np.linalg.norm(final_labs - lab, axis=1)
        min_idx = int(np.argmin(dists))
        if float(dists[min_idx]) <= threshold:
            mapping[color] = final_rgbs[min_idx]
        else:
            mapping[color] = color

    return mapping


def extract_colors(
    image: np.ndarray, grid_info: Dict, config: ColorProcessingConfig
) -> List[List[Tuple[int, int, int]]]:
    h_lines = grid_info['h_lines']
    v_lines = grid_info['v_lines']
    
    rows = len(h_lines) - 1
    cols = len(v_lines) - 1

    colors: List[List[Tuple[int, int, int]]] = []
    watermark_mask = _build_watermark_mask(image, config)
    edge_mask = _build_watermark_edge_mask(image, config)
    use_watermark_filter = (
        config.watermark_filter_enabled
        and watermark_mask is not None
        and float(np.mean(watermark_mask)) >= config.watermark_ratio_threshold
    )
    use_edge_filter = config.watermark_edge_filter_enabled and edge_mask is not None

    for i in range(rows):
        row_colors: List[Tuple[int, int, int]] = []
        for j in range(cols):
            y1, y2 = h_lines[i], h_lines[i + 1]
            x1, x2 = v_lines[j], v_lines[j + 1]

            cell_height = y2 - y1
            cell_width = x2 - x1

            margin_y = int(cell_height * config.margin_percent)
            margin_x = int(cell_width * config.margin_percent)

            margin_y = max(config.margin_min, min(margin_y, cell_height // config.margin_max_divisor))
            margin_x = max(config.margin_min, min(margin_x, cell_width // config.margin_max_divisor))

            # 性能优化：对于较大的单元格，使用采样减少像素数量
            sample_step = 1
            if cell_height > 60 and cell_width > 60:
                sample_step = 3
            elif cell_height > 30 and cell_width > 30:
                sample_step = 2
            cell = image[y1 + margin_y : y2 - margin_y : sample_step, x1 + margin_x : x2 - margin_x : sample_step]
            cell_watermark = None
            cell_edge = None
            if use_watermark_filter and watermark_mask is not None:
                cell_watermark = watermark_mask[
                    y1 + margin_y : y2 - margin_y : sample_step,
                    x1 + margin_x : x2 - margin_x : sample_step,
                ]
            if use_edge_filter and edge_mask is not None:
                cell_edge = edge_mask[
                    y1 + margin_y : y2 - margin_y : sample_step,
                    x1 + margin_x : x2 - margin_x : sample_step,
                ]

            if cell.size == 0:
                row_colors.append((255, 255, 255))
                continue

            color = get_dominant_color(cell, config, cell_watermark, cell_edge)
            row_colors.append(color)

        colors.append(row_colors)

    return colors


def get_dominant_color(
    cell: np.ndarray,
    config: ColorProcessingConfig,
    watermark_mask: np.ndarray | None = None,
    edge_mask: np.ndarray | None = None,
) -> Tuple[int, int, int]:
    # 只对足够大的cell应用medianBlur，避免尺寸问题
    if cell.shape[0] >= 5 and cell.shape[1] >= 5:
        cell_filtered = cv2.medianBlur(cell, 5)
    else:
        cell_filtered = cell
    cell_rgb = cv2.cvtColor(cell_filtered, cv2.COLOR_BGR2RGB)
    pixels = cell_rgb.reshape(-1, 3)

    if watermark_mask is not None:
        # 确保mask和pixels维度匹配
        if watermark_mask.shape[0] * watermark_mask.shape[1] != len(pixels):
            pass  # 跳过维度不匹配的情况
        else:
            mask_flat = watermark_mask.reshape(-1)
            gray_ratio = float(np.mean(mask_flat))
            if gray_ratio < config.watermark_cell_keep_gray_ratio:
                filtered_pixels = pixels[~mask_flat]
                if len(filtered_pixels) >= config.watermark_min_pixels:
                    pixels = filtered_pixels

    if edge_mask is not None:
        # 确保mask和pixels维度匹配
        if edge_mask.shape[0] * edge_mask.shape[1] != len(pixels):
            pass  # 跳过维度不匹配的情况
        else:
            edge_flat = edge_mask.reshape(-1)
            edge_ratio = float(np.mean(edge_flat))
            if edge_ratio >= config.watermark_edge_ratio_threshold:
                filtered_pixels = pixels[~edge_flat]
                if len(filtered_pixels) >= config.watermark_edge_min_pixels:
                    pixels = filtered_pixels

    if config.robust_trim_enabled and len(pixels) >= config.robust_trim_min_pixels:
        lab = cv2.cvtColor(pixels.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB)
        lab = lab.reshape(-1, 3).astype(np.float32)
        median = np.median(lab, axis=0)
        distances = np.linalg.norm(lab - median, axis=1)
        threshold = np.percentile(distances, config.robust_trim_percentile)
        trimmed = pixels[distances <= threshold]
        if len(trimmed) >= config.robust_trim_min_pixels:
            pixels = trimmed

    near_black_mask = (
        (pixels[:, 0] < config.black_filter_threshold)
        & (pixels[:, 1] < config.black_filter_threshold)
        & (pixels[:, 2] < config.black_filter_threshold)
    )
    dark_pixel_ratio = float(np.mean(near_black_mask))

    if len(pixels) < 10:
        return tuple(map(int, pixels.mean(axis=0)))

    # 快速路径：如果像素颜色非常一致，直接返回中位数
    pixel_std = np.std(pixels, axis=0)
    if np.all(pixel_std < 15):  # 颜色非常一致
        return tuple(map(int, np.median(pixels, axis=0)))

    # 快速路径：使用直方图方法代替K-means
    if len(pixels) > 50:
        # 量化颜色到较少的bin
        quantized = (pixels // 32) * 32 + 16  # 8个level per channel
        unique, counts = np.unique(quantized, axis=0, return_counts=True)

        # 找到最常见的颜色（排除黑色）
        sorted_indices = np.argsort(-counts)
        for idx in sorted_indices:
            color = unique[idx]
            r, g, b = color

            # 跳过黑色（除非黑色占比很高）
            if r < config.black_filter_threshold and g < config.black_filter_threshold and b < config.black_filter_threshold:
                if dark_pixel_ratio >= config.dark_pixel_ratio and (counts[idx] / len(pixels)) >= config.black_cluster_ratio:
                    # 使用原始像素的平均值而不是量化值
                    mask = np.all(quantized == color, axis=1)
                    return tuple(map(int, pixels[mask].mean(axis=0)))
                continue

            # 跳过白色（除非白色占比很高）
            avg_brightness = (int(r) + int(g) + int(b)) / 3
            color_range = max(int(r), int(g), int(b)) - min(int(r), int(g), int(b))
            if avg_brightness > config.white_brightness and color_range < config.white_color_range:
                if counts[idx] / len(pixels) > config.white_cluster_ratio:
                    mask = np.all(quantized == color, axis=1)
                    return tuple(map(int, pixels[mask].mean(axis=0)))
                continue

            # 返回这个颜色对应的原始像素平均值
            mask = np.all(quantized == color, axis=1)
            return tuple(map(int, pixels[mask].mean(axis=0)))

        # 如果所有颜色都被跳过，返回最常见的
        color = unique[sorted_indices[0]]
        mask = np.all(quantized == color, axis=1)
        return tuple(map(int, pixels[mask].mean(axis=0)))

    # 回退到K-means（仅用于小样本）
    try:
        n_clusters = min(config.kmeans_clusters, len(pixels))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=config.kmeans_n_init, max_iter=100)
        kmeans.fit(pixels)

        labels = kmeans.labels_
        label_counts = Counter(labels)
        sorted_clusters = label_counts.most_common()

        for cluster_label, count in sorted_clusters:
            cluster_color = kmeans.cluster_centers_[cluster_label]
            r, g, b = cluster_color

            if r < config.black_filter_threshold and g < config.black_filter_threshold and b < config.black_filter_threshold:
                if dark_pixel_ratio >= config.dark_pixel_ratio and (count / len(pixels)) >= config.black_cluster_ratio:
                    return tuple(map(int, cluster_color))
                continue

            avg_brightness = (r + g + b) / 3
            color_range = max(r, g, b) - min(r, g, b)

            if avg_brightness > config.white_brightness and color_range < config.white_color_range:
                if count / len(pixels) > config.white_cluster_ratio:
                    return tuple(map(int, cluster_color))
                continue

            return tuple(map(int, cluster_color))

        dominant_label = sorted_clusters[0][0]
        dominant_color = kmeans.cluster_centers_[dominant_label]
        return tuple(map(int, dominant_color))

    except Exception as exc:
        return tuple(map(int, np.median(pixels, axis=0)))


def merge_similar_colors(
    colors: List[List[Tuple[int, int, int]]],
    config: ColorProcessingConfig,
) -> List[List[Tuple[int, int, int]]]:
    all_colors: List[Tuple[int, int, int]] = []
    for row in colors:
        all_colors.extend(row)

    color_counts = Counter(all_colors)

    unique_colors = list(set(all_colors))

    white_colors = []
    other_colors = []
    near_black_colors = []

    for color in unique_colors:
        r, g, b = color
        avg_brightness = (r + g + b) / 3
        color_range = max(r, g, b) - min(r, g, b)

        if avg_brightness > config.white_brightness and color_range < config.white_color_range:
            white_colors.append(color)
        elif (
            config.protect_near_black
            and r < config.black_filter_threshold
            and g < config.black_filter_threshold
            and b < config.black_filter_threshold
        ):
            near_black_colors.append(color)
        else:
            other_colors.append(color)

    print(
        f"检测到 {len(unique_colors)} 种颜色 (其中 {len(white_colors)} 种白色背景变种，{len(other_colors)} 种其他颜色)"
    )

    if len(white_colors) > 1:
        print(f"合并 {len(white_colors)} 种白色背景变种...")
        avg_white = tuple(map(int, np.mean(white_colors, axis=0)))
        white_color_map = {c: avg_white for c in white_colors}
    else:
        white_color_map = {}

    black_color_map: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    if config.near_black_merge_enabled and len(near_black_colors) > config.near_black_merge_limit:
        avg_black = tuple(map(int, np.mean(near_black_colors, axis=0)))
        black_color_map = {c: avg_black for c in near_black_colors}

    similar_color_map = _merge_similar_palette(
        other_colors,
        color_counts,
        config.color_threshold,
    )

    if similar_color_map:
        unique_merged = len(set(similar_color_map.values()))
        print(f"相近颜色合并: {len(other_colors)} -> {unique_merged}")

    merge_trigger = max(
        int(config.max_colors * config.merge_trigger_ratio),
        config.max_colors + config.merge_trigger_min_overflow,
    )

    def _map_color(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        mapped = white_color_map.get(color)
        if mapped is not None:
            return mapped
        mapped = black_color_map.get(color)
        if mapped is not None:
            return mapped
        return similar_color_map.get(color, color)

    premerge_unique = set()
    for color in unique_colors:
        premerge_unique.add(_map_color(color))

    if len(premerge_unique) <= merge_trigger:
        print(
            f"颜色数量 ({len(premerge_unique)}) 未明显超过阈值 ({merge_trigger})，跳过聚类"
        )
        if white_color_map or black_color_map or similar_color_map:
            merged_colors = []
            for row in colors:
                merged_row = [_map_color(c) for c in row]
                merged_colors.append(merged_row)
            return merged_colors
        return colors

    print("进行全局聚类...")

    cluster_candidates = []
    for color in unique_colors:
        if color in white_color_map:
            continue
        if color in black_color_map:
            continue
        if color in similar_color_map:
            continue
        if not config.protect_near_black and color in near_black_colors:
            cluster_candidates.append(color)
            continue
        if color in near_black_colors:
            continue
        cluster_candidates.append(color)

    color_array = np.array(cluster_candidates)

    try:
        available_clusters = config.max_colors
        if config.protect_near_black:
            available_clusters = max(1, config.max_colors - len(near_black_colors))
        n_clusters = min(available_clusters, len(cluster_candidates))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=config.kmeans_n_init)
        kmeans.fit(color_array)

        color_map: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
        label_lookup = {}
        for i, original_color in enumerate(cluster_candidates):
            cluster_id = kmeans.labels_[i]
            label_lookup[original_color] = cluster_id

        for original_color in unique_colors:
            if original_color in white_color_map:
                color_map[original_color] = white_color_map[original_color]
                continue
            if original_color in black_color_map:
                color_map[original_color] = black_color_map[original_color]
                continue
            if original_color in similar_color_map:
                color_map[original_color] = similar_color_map[original_color]
                continue
            if config.protect_near_black and original_color in near_black_colors:
                color_map[original_color] = original_color
                continue

            cluster_id = label_lookup.get(original_color)
            if cluster_id is None:
                color_map[original_color] = original_color
                continue

            new_color = tuple(map(int, kmeans.cluster_centers_[cluster_id]))
            color_map[original_color] = new_color

        merged_colors = []
        for row in colors:
            merged_row = [color_map.get(color, color) for color in row]
            merged_colors.append(merged_row)

        merged_unique = set()
        for row in merged_colors:
            merged_unique.update(row)

        print(f"合并后剩余 {len(merged_unique)} 种颜色")

        return merged_colors

    except Exception as exc:
        print(f"颜色合并失败: {exc}，保持原始颜色")
        return colors


def crop_white_borders(
    colors: List[List[Tuple[int, int, int]]], max_margin: int = 5
) -> List[List[Tuple[int, int, int]]]:
    return colors
