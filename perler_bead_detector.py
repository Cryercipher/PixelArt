"""
拼豆图纸识别器
自动识别拼豆图纸中的网格和颜色，并生成矢量图
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Tuple, Dict, Optional
import svgwrite
from collections import Counter


class PerlerBeadDetector:
    """拼豆图纸检测器"""
    
    def __init__(self, min_grid_size: int = 10, max_grid_size: int = 100):
        """
        初始化检测器
        
        Args:
            min_grid_size: 最小网格大小（像素）
            max_grid_size: 最大网格大小（像素）
        """
        self.min_grid_size = min_grid_size
        self.max_grid_size = max_grid_size
        self.grid_data = None
        self.colors = None
        
    def process_image(self, image_path: str, debug: bool = False) -> Dict:
        """
        处理拼豆图纸图片
        
        Args:
            image_path: 图片路径
            debug: 是否显示调试信息
            
        Returns:
            包含网格数据和颜色信息的字典
        """
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        print(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
        
        # 1. 检测网格
        grid_info = self._detect_grid(image, debug)
        
        if grid_info is None:
            raise ValueError("无法检测到网格结构")
        
        # 2. 提取每个方格的颜色
        colors = self._extract_colors(image, grid_info)
        
        # 4. 对所有颜色进行全局聚类，合并相似颜色
        colors = self._merge_similar_colors(colors)
        
        # 5. 存储结果
        self.grid_data = grid_info
        self.colors = colors
        
        result = {
            'grid_info': grid_info,
            'colors': colors,
            'rows': len(colors),
            'cols': len(colors[0]) if colors else 0
        }
        
        print(f"检测到 {result['rows']}x{result['cols']} 的网格")
        
        return result
    
    def _detect_grid(self, image: np.ndarray, debug: bool = False) -> Optional[Dict]:
        """
        检测图片中的网格结构
        
        这是解决难点1的核心算法：自动识别不同margin的网格
        
        Args:
            image: 输入图片
            debug: 是否显示调试图片
            
        Returns:
            包含网格信息的字典，包括行列坐标
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值二值化
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 反转（黑线变白线）
        binary = cv2.bitwise_not(binary)
        
        # 形态学操作：增强网格线
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        # 检测水平线
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_horizontal)
        # 检测垂直线
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_vertical)
        
        # 合并线条
        grid_lines = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0)
        
        if debug:
            cv2.imshow('Binary', binary)
            cv2.imshow('Horizontal Lines', horizontal_lines)
            cv2.imshow('Vertical Lines', vertical_lines)
            cv2.imshow('Grid Lines', grid_lines)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # 使用霍夫变换检测线条
        h_lines = self._detect_lines(horizontal_lines, angle_threshold=10)
        v_lines = self._detect_lines(vertical_lines, angle_threshold=80)
        
        if len(h_lines) < 2 or len(v_lines) < 2:
            print(f"检测到的线条不足: 水平线 {len(h_lines)}, 垂直线 {len(v_lines)}")
            return None
        
        # 排序并过滤线条
        h_positions = sorted(set([int(y) for _, y in h_lines]))
        v_positions = sorted(set([int(x) for x, _ in v_lines]))
        
        # 过滤掉太近的线条（去除重复检测）
        h_positions = self._filter_close_lines(h_positions)
        v_positions = self._filter_close_lines(v_positions)
        
        print(f"检测到 {len(h_positions)} 条水平线, {len(v_positions)} 条垂直线")
        
        # 计算网格间距
        if len(h_positions) > 1:
            h_spacings = np.diff(h_positions)
            avg_h_spacing = np.median(h_spacings)
        else:
            avg_h_spacing = 0
            
        if len(v_positions) > 1:
            v_spacings = np.diff(v_positions)
            avg_v_spacing = np.median(v_spacings)
        else:
            avg_v_spacing = 0
        
        print(f"平均网格间距: 水平 {avg_h_spacing:.1f}, 垂直 {avg_v_spacing:.1f}")
        
        return {
            'h_lines': h_positions,
            'v_lines': v_positions,
            'h_spacing': avg_h_spacing,
            'v_spacing': avg_v_spacing
        }
    
    def _detect_lines(self, image: np.ndarray, angle_threshold: float = 10) -> List[Tuple[int, int]]:
        """
        使用霍夫变换检测线条
        
        Args:
            image: 二值化图像
            angle_threshold: 角度阈值（度），用于过滤非水平/垂直线
            
        Returns:
            线条位置列表 [(x或y坐标, 另一坐标)]
        """
        lines = cv2.HoughLinesP(
            image, 
            rho=1, 
            theta=np.pi/180, 
            threshold=50,          # 降低从100到50，检测更弱的线条
            minLineLength=30,      # 降低从50到30，适应更小的格子
            maxLineGap=5           # 降低从10到5，更严格地连接线条
        )
        
        if lines is None:
            return []
        
        detected_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 计算角度
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 水平线 (角度接近0或180)
            if angle < angle_threshold or angle > 180 - angle_threshold:
                detected_lines.append((x1, (y1 + y2) // 2))
            # 垂直线 (角度接近90)
            elif 90 - angle_threshold < angle < 90 + angle_threshold:
                detected_lines.append(((x1 + x2) // 2, y1))
        
        return detected_lines
    
    def _filter_close_lines(self, positions: List[int], min_distance: int = 5) -> List[int]:
        """
        过滤掉距离太近的线条
        
        Args:
            positions: 位置列表
            min_distance: 最小距离
            
        Returns:
            过滤后的位置列表
        """
        if not positions:
            return []
        
        filtered = [positions[0]]
        for pos in positions[1:]:
            if pos - filtered[-1] >= min_distance:
                filtered.append(pos)
        
        return filtered
    
    def _extract_colors(self, image: np.ndarray, grid_info: Dict) -> List[List[Tuple[int, int, int]]]:
        """
        提取每个方格的颜色
        
        这是解决难点2的核心算法：处理颜色差异
        
        Args:
            image: 原始图片
            grid_info: 网格信息
            
        Returns:
            颜色矩阵 (rows x cols)，每个元素是RGB颜色元组
        """
        h_lines = grid_info['h_lines']
        v_lines = grid_info['v_lines']
        
        rows = len(h_lines) - 1
        cols = len(v_lines) - 1
        
        colors = []
        
        for i in range(rows):
            row_colors = []
            for j in range(cols):
                # 获取方格区域
                y1, y2 = h_lines[i], h_lines[i + 1]
                x1, x2 = v_lines[j], v_lines[j + 1]
                
                # 计算方格大小
                cell_height = y2 - y1
                cell_width = x2 - x1
                
                # 使用动态边距裁剪，只取中心区域（避免边界颜色污染）
                margin_percent = 0.1  # 从每条边裁剪掉25%
                margin_y = int(cell_height * margin_percent)
                margin_x = int(cell_width * margin_percent)
                
                # 确保至少有一些像素
                margin_y = max(2, min(margin_y, cell_height // 3))
                margin_x = max(2, min(margin_x, cell_width // 3))
                
                cell = image[y1+margin_y:y2-margin_y, x1+margin_x:x2-margin_x]
                
                if cell.size == 0:
                    row_colors.append((255, 255, 255))
                    continue
                
                # 提取主要颜色
                color = self._get_dominant_color(cell)
                row_colors.append(color)
            
            colors.append(row_colors)
        
        return colors
    
    def _get_dominant_color(self, cell: np.ndarray, n_colors: int = 1) -> Tuple[int, int, int]:
        """
        获取方格的主导颜色
        
        使用多种方法确保颜色准确并抗色号文字干扰：
        1. 中值滤波去噪
        2. K-means聚类分离背景色和色号文字
        3. 选择最大簇的中心颜色（忽略色号文字）
        4. 过滤极端颜色（黑白色号）
        
        Args:
            cell: 方格图像
            n_colors: 聚类数量
            
        Returns:
            RGB颜色元组
        """
        # 1. 中值滤波去噪
        cell_filtered = cv2.medianBlur(cell, 5)
        
        # 2. 转换为RGB并重塑
        cell_rgb = cv2.cvtColor(cell_filtered, cv2.COLOR_BGR2RGB)
        pixels = cell_rgb.reshape(-1, 3)
        
        # 3. 如果像素太少，直接返回均值
        if len(pixels) < 10:
            return tuple(map(int, pixels.mean(axis=0)))
        
        # 4. 使用K-means聚类（处理颜色差异和色号干扰）
        try:
            # 使用更多聚类数以更好地分离色号文字
            n_clusters = min(5, len(pixels))  # 增加到5类，更好地区分背景和文字
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # 5. 找到最大的簇，但排除极端颜色（可能是色号文字）
            labels = kmeans.labels_
            label_counts = Counter(labels)
            
            # 按簇大小排序
            sorted_clusters = label_counts.most_common()
            
            # 尝试选择最大的非极端颜色簇
            for cluster_label, count in sorted_clusters:
                cluster_color = kmeans.cluster_centers_[cluster_label]
                r, g, b = cluster_color
                
                # 过滤极端黑色（色号常用黑色）
                if r < 50 and g < 50 and b < 50:
                    continue
                
                # 判断是否是白色/灰色：亮度高 + 色差小（无色性）
                avg_brightness = (r + g + b) / 3
                color_range = max(r, g, b) - min(r, g, b)
                
                # 白色条件：色差<20 且亮度>200
                # 这样可以区分白色 vs 浅黄色
                if avg_brightness > 200 and color_range < 20:
                    # 如果是浅色簇且占比合理，认为是白色背景
                    if count / len(pixels) > 0.3:
                        return tuple(map(int, cluster_color))
                    continue
                
                # 找到合适的背景色
                return tuple(map(int, cluster_color))
            
            # 如果所有簇都被过滤了，返回最大簇
            dominant_label = sorted_clusters[0][0]
            dominant_color = kmeans.cluster_centers_[dominant_label]
            return tuple(map(int, dominant_color))
        
        except Exception as e:
            print(f"K-means聚类失败: {e}，使用中位数颜色")
            # 备用方案：使用中位数
            return tuple(map(int, np.median(pixels, axis=0)))
    
    def _merge_similar_colors(self, colors: List[List[Tuple[int, int, int]]], 
                             max_colors: int = 50, 
                             color_threshold: int = 15) -> List[List[Tuple[int, int, int]]]:
        """
        合并相似的颜色，减少总颜色数量
        
        Args:
            colors: 原始颜色矩阵
            max_colors: 最大颜色数量（用于自动聚类）
            color_threshold: 颜色相似度阈值（欧氏距离）
            
        Returns:
            合并后的颜色矩阵
        """
        # 收集所有唯一颜色
        all_colors = []
        for row in colors:
            all_colors.extend(row)
        
        unique_colors = list(set(all_colors))
        
        # 分离白色背景和其他颜色
        white_colors = []
        other_colors = []
        
        for color in unique_colors:
            r, g, b = color
            # 判断是否是白色：亮度高 + 色差小
            avg_brightness = (r + g + b) / 3
            color_range = max(r, g, b) - min(r, g, b)
            
            # 白色/灰色条件：色差<20 且亮度>200
            if avg_brightness > 200 and color_range < 20:
                white_colors.append(color)
            else:
                other_colors.append(color)
        
        print(f"检测到 {len(unique_colors)} 种颜色 (其中 {len(white_colors)} 种白色背景变种，{len(other_colors)} 种其他颜色)")
        
        # 如果白色变种太多，先合并它们
        if len(white_colors) > 5:
            print(f"合并 {len(white_colors)} 种白色背景变种...")
            # 所有白色映射到第一个白色（或取平均值）
            if white_colors:
                avg_white = tuple(map(int, np.mean(white_colors, axis=0)))
                white_color_map = {c: avg_white for c in white_colors}
            else:
                white_color_map = {}
        else:
            white_color_map = {}
        
        if len(unique_colors) <= max_colors:
            print(f"颜色数量 ({len(unique_colors)}) 在合理范围内，跳过聚类")
            # 应用白色合并
            if white_color_map:
                merged_colors = []
                for row in colors:
                    merged_row = [white_color_map.get(c, c) for c in row]
                    merged_colors.append(merged_row)
                return merged_colors
            return colors
        
        print(f"进行全局聚类...")
        
        # 将颜色转换为数组
        color_array = np.array(unique_colors)
        
        # 使用K-means对所有颜色进行聚类
        try:
            # 自动确定聚类数量
            n_clusters = min(max_colors, len(unique_colors))
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(color_array)
            
            # 创建颜色映射字典
            color_map = {}
            for i, original_color in enumerate(unique_colors):
                cluster_id = kmeans.labels_[i]
                new_color = tuple(map(int, kmeans.cluster_centers_[cluster_id]))
                
                # 如果这是白色，优先使用白色合并的结果
                if original_color in white_color_map:
                    color_map[original_color] = white_color_map[original_color]
                else:
                    color_map[original_color] = new_color
            
            # 应用颜色映射
            merged_colors = []
            for row in colors:
                merged_row = [color_map.get(color, color) for color in row]
                merged_colors.append(merged_row)
            
            # 统计合并后的颜色数量
            merged_unique = set()
            for row in merged_colors:
                merged_unique.update(row)
            
            print(f"合并后剩余 {len(merged_unique)} 种颜色")
            
            return merged_colors
        
        except Exception as e:
            print(f"颜色合并失败: {e}，保持原始颜色")
            return colors
    
    def save_svg(self, result: Dict, output_path: str, cell_size: int = 20, grid_width: float = 1.0):
        """
        将结果保存为SVG矢量图
        
        Args:
            result: process_image返回的结果
            output_path: 输出文件路径
            cell_size: 每个方格的大小（像素）
            grid_width: 网格线宽度（像素）
        """
        colors = result['colors']
        rows = result['rows']
        cols = result['cols']
        
        # 创建SVG
        width = cols * cell_size
        height = rows * cell_size
        
        dwg = svgwrite.Drawing(output_path, size=(width, height))
        
        # 绘制每个方格
        for i in range(rows):
            for j in range(cols):
                r, g, b = colors[i][j]
                color = f'rgb({r},{g},{b})'
                
                dwg.add(dwg.rect(
                    insert=(j * cell_size, i * cell_size),
                    size=(cell_size, cell_size),
                    fill=color,
                    stroke='black',
                    stroke_width=grid_width
                ))
        
        dwg.save()
        print(f"SVG已保存到: {output_path}")
    
    def save_color_palette(self, result: Dict, output_path: str = 'color_palette.txt'):
        """
        保存颜色调色板（统计所有不同的颜色）
        
        Args:
            result: process_image返回的结果
            output_path: 输出文件路径
        """
        colors = result['colors']
        
        # 收集所有颜色
        all_colors = []
        for row in colors:
            all_colors.extend(row)
        
        # 统计颜色频率
        color_counts = Counter(all_colors)
        
        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"共检测到 {len(color_counts)} 种不同的颜色\n\n")
            
            for idx, (color, count) in enumerate(color_counts.most_common(), 1):
                r, g, b = color
                hex_color = f'#{r:02x}{g:02x}{b:02x}'
                f.write(f"{idx}. RGB({r:3d}, {g:3d}, {b:3d}) = {hex_color} - 出现 {count} 次\n")
        
        print(f"颜色调色板已保存到: {output_path}")
        print(f"共 {len(color_counts)} 种颜色")
        
        return color_counts
    
    def visualize_result(self, image_path: str, result: Dict, output_path: str = 'result.png'):
        """
        可视化检测结果
        
        Args:
            image_path: 原始图片路径
            result: 检测结果
            output_path: 输出路径
        """
        import matplotlib.pyplot as plt
        
        # 读取原图
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 创建结果图
        colors = result['colors']
        rows = result['rows']
        cols = result['cols']
        
        # 创建高分辨率的结果图，每个方格放大以便绘制网格线
        cell_size = 20  # 每个方格的像素大小
        result_image = np.zeros((rows * cell_size, cols * cell_size, 3), dtype=np.uint8)
        
        # 填充颜色并绘制网格线
        for i in range(rows):
            for j in range(cols):
                r, g, b = colors[i][j]
                # 填充方格
                y1, y2 = i * cell_size, (i + 1) * cell_size
                x1, x2 = j * cell_size, (j + 1) * cell_size
                result_image[y1:y2, x1:x2] = [r, g, b]
        
        # 绘制网格线
        grid_color = [0, 0, 0]  # 黑色网格线
        line_width = 1
        
        # 绘制水平线
        for i in range(rows + 1):
            y = i * cell_size
            if y < result_image.shape[0]:
                result_image[max(0, y-line_width//2):min(result_image.shape[0], y+line_width//2+1), :] = grid_color
        
        # 绘制垂直线
        for j in range(cols + 1):
            x = j * cell_size
            if x < result_image.shape[1]:
                result_image[:, max(0, x-line_width//2):min(result_image.shape[1], x+line_width//2+1)] = grid_color
        
        # 显示对比
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        axes[0].imshow(image_rgb)
        axes[0].set_title('原始图片')
        axes[0].axis('off')
        
        axes[1].imshow(result_image)
        axes[1].set_title(f'识别结果 ({rows}x{cols})')
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"可视化结果已保存到: {output_path}")
        plt.close()


if __name__ == '__main__':
    # 简单测试
    print("拼豆图纸识别器")
    print("使用方法参见 example.py")
