"""
配置与默认参数
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridDetectionConfig:
    adaptive_block_size: int = 11
    adaptive_c: int = 2
    hough_threshold: int = 40
    hough_threshold_strong: int = 50
    min_line_length: int = 30
    max_line_gap: int = 5
    angle_threshold_h: int = 10
    angle_threshold_v: int = 80
    kernel_len_ratio: float = 0.05
    kernel_len_min: int = 40
    merge_spacing_ratio: float = 0.6
    merge_min_distance: int = 6
    irregular_spacing_std_ratio: float = 0.35
    irregular_min_ratio: float = 0.5
    projection_std_ratio: float = 1.5


@dataclass(frozen=True)
class ColorProcessingConfig:
    margin_percent: float = 0.1
    margin_min: int = 2
    margin_max_divisor: int = 3
    kmeans_clusters: int = 5
    kmeans_n_init: int = 10
    black_filter_threshold: int = 50
    black_cluster_ratio: float = 0.05
    dark_pixel_ratio: float = 0.08
    white_brightness: int = 215
    white_color_range: int = 12
    white_cluster_ratio: float = 0.3
    max_colors: int = 20
    color_threshold: int = 100
    white_merge_limit: int = 5
    protect_near_black: bool = True
    merge_trigger_ratio: float = 1.5
    merge_trigger_min_overflow: int = 6
    near_black_merge_enabled: bool = True
    near_black_merge_limit: int = 3
    watermark_filter_enabled: bool = True
    watermark_brightness_min: int = 120
    watermark_brightness_max: int = 210
    watermark_color_range: int = 12
    watermark_ratio_threshold: float = 0.08
    watermark_cell_keep_gray_ratio: float = 0.6
    watermark_min_pixels: int = 30
    watermark_edge_filter_enabled: bool = True
    watermark_edge_sigma: float = 0.33
    watermark_edge_dilate: int = 1
    watermark_edge_ratio_threshold: float = 0.01
    watermark_edge_min_pixels: int = 30
    robust_trim_enabled: bool = True
    robust_trim_percentile: float = 80.0
    robust_trim_min_pixels: int = 50
