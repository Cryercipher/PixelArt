"""
拼豆图纸识别器
自动识别拼豆图纸中的网格和颜色，并生成矢量图
"""

import cv2
import numpy as np
from dataclasses import replace
from typing import List, Tuple, Dict, Optional
import svgwrite

from .color_processing import crop_white_borders, extract_colors, merge_similar_colors
from .config import ColorProcessingConfig, GridDetectionConfig
from .grid_detection import detect_grid


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
        self.grid_config = GridDetectionConfig()
        self.color_config = ColorProcessingConfig()
        
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
        
        # 0. 智能裁剪：移除白色边界和色卡
        image = self._smart_crop(image)
        
        # 1. 检测网格
        grid_info = self._detect_grid(image, debug)
        
        if grid_info is None:
            raise ValueError("无法检测到网格结构")
        
        # 1.5 根据网格信息进行精确裁剪（移除非网格区域和多余margin）
        image = self._crop_by_grid(image, grid_info, max_margin=1)
        
        # 重新检测网格（可选，确保裁剪后的图片仍能检测到网格）
        grid_info = self._detect_grid(image, debug)
        
        if grid_info is None:
            raise ValueError("裁剪后无法检测到网格结构")
        
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
        return detect_grid(image, debug, self.grid_config)
    
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
        return extract_colors(image, grid_info, self.color_config)
    
    def _merge_similar_colors(self, colors: List[List[Tuple[int, int, int]]], 
                             max_colors: int = 20, 
                             color_threshold: int = 20) -> List[List[Tuple[int, int, int]]]:
        """
        合并相似的颜色，减少总颜色数量
        
        Args:
            colors: 原始颜色矩阵
            max_colors: 最大颜色数量（用于自动聚类）
            color_threshold: 颜色相似度阈值（欧氏距离）
            
        Returns:
            合并后的颜色矩阵
        """
        config = replace(self.color_config, max_colors=max_colors, color_threshold=color_threshold)
        return merge_similar_colors(colors, config)
    
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
    
    def _smart_crop(self, image: np.ndarray, max_margin: int = 3) -> np.ndarray:
        """
        智能裁剪图片 - 已禁用
        
        Args:
            image: 输入图片
            max_margin: 最多保留的边距行数/列数
            
        Returns:
            原图（不裁剪）
        """
        return image
    
    def _crop_by_grid(self, image: np.ndarray, grid_info: Dict, max_margin: int = 3) -> np.ndarray:
        """
        根据网格信息精确裁剪图片 - 已禁用
        
        Args:
            image: 输入图片
            grid_info: 网格信息（包含h_positions和v_positions）
            max_margin: 最多保留的边距行数/列数
            
        Returns:
            原图（不裁剪）
        """
        return image
    
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
    
    def _crop_white_borders(self, colors: List[List[Tuple[int, int, int]]], 
                           max_margin: int = 5) -> List[List[Tuple[int, int, int]]]:
        """
        裁剪颜色矩阵 - 已禁用
        
        Args:
            colors: 颜色矩阵
            max_margin: 最多保留的边距行/列数
            
        Returns:
            原始颜色矩阵（不裁剪）
        """
        return crop_white_borders(colors, max_margin=max_margin)
    
    def visualize_result(self, image_path: str, result: Dict, output_path: str = 'result.png'):
        """
        可视化检测结果
        
        Args:
            image_path: 原始图片路径
            result: 检测结果
            output_path: 输出路径
        """
        # 读取原图
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 创建结果图
        colors = result['colors']
        rows = result['rows']
        cols = result['cols']
        
        # 智能裁剪colors矩阵，移除全白色的边界行/列
        colors = self._crop_white_borders(colors)
        rows = len(colors)
        cols = len(colors[0]) if rows > 0 else 0
        
        # 创建高分辨率的结果图，每个方格放大以便绘制网格线
        cell_size = 20  # 每个方格的像素大小
        result_image = np.zeros((rows * cell_size, cols * cell_size, 3), dtype=np.uint8)
        
        # 填充颜色并绘制网格线
        for i in range(rows):
            for j in range(cols):
                b, g, r = colors[i][j]  # colors 中存储的是 BGR
                # 填充方格
                y1, y2 = i * cell_size, (i + 1) * cell_size
                x1, x2 = j * cell_size, (j + 1) * cell_size
                result_image[y1:y2, x1:x2] = [b, g, r]
        
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
        
        # 使用 PIL 合成对比图（支持中文）
        from PIL import Image as PILImage, ImageDraw, ImageFont
        
        h1, w1 = image_rgb.shape[:2]
        h2, w2 = result_image.shape[:2]
        
        padding = 40
        label_h = 30
        
        # 计算居中位置
        max_h = max(h1, h2)
        y1_offset = (max_h - h1) // 2  # 原图垂直居中偏移
        y2_offset = (max_h - h2) // 2  # 生成图垂直居中偏移
        
        # 创建合成图
        canvas_w = w1 + w2 + 3 * padding
        canvas_h = max_h + label_h + 2 * padding
        
        canvas = PILImage.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
        
        # 转换图片为 PIL
        img1_pil = PILImage.fromarray(image_rgb)
        img2_pil = PILImage.fromarray(result_image)
        
        # 保存纯净版本的生成图片
        clean_output = output_path.replace('.png', '_clean.png')
        img2_pil.save(clean_output, quality=95)
        print(f"纯净版结果已保存到: {clean_output}")
        
        # 粘贴图片（居中对齐）
        canvas.paste(img1_pil, (padding, padding + label_h + y1_offset))
        canvas.paste(img2_pil, (w1 + 2 * padding, padding + label_h + y2_offset))
        
        # 绘制文字
        draw = ImageDraw.Draw(canvas)
        
        # 尝试加载中文字体
        font = None
        for font_name in ['/System/Library/Fonts/SimHei.ttf', 
                          '/System/Library/Fonts/STHeiti Light.ttc',
                          '/Library/Fonts/Arial.ttf']:
            try:
                font = ImageFont.truetype(font_name, 14)
                break
            except:
                pass
        
        if font is None:
            font = ImageFont.load_default()
        
        # 绘制标签
        draw.text((padding, padding - 5), '原始图片', fill=(0, 0, 0), font=font)
        draw.text((w1 + 2 * padding, padding - 5), f'识别结果 ({rows}x{cols})', fill=(0, 0, 0), font=font)
        
        canvas.save(output_path, quality=95)
        print(f"可视化结果已保存到: {output_path}")


if __name__ == '__main__':
    # 简单测试
    print("拼豆图纸识别器")
    print("使用方法参见 example.py")
