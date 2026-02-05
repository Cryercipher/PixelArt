"""拼豆标准色号映射模块

使用 CIEDE2000 算法将任意颜色映射到最接近的拼豆标准色号。
CIEDE2000 是目前最先进的颜色相似度算法，考虑了人眼对颜色差异的感知特性。
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Union


class PerlerBeadColorMapper:
    """拼豆颜色映射器"""
    
    def __init__(self, excel_path: str):
        """初始化颜色映射器
        
        Args:
            excel_path: 拼豆色号Excel文件路径
        """
        self.color_map: Dict[str, Tuple[int, int, int]] = {}
        self.lab_colors: Dict[str, np.ndarray] = {}
        self._load_colors(excel_path)
    
    def _rgb_to_lab(self, rgb: Tuple[int, int, int]) -> np.ndarray:
        """RGB转LAB色彩空间
        
        Args:
            rgb: (r, g, b) 元组，值范围 0-255
        
        Returns:
            LAB值的numpy数组 [L, a, b]
        """
        # 归一化到 0-1
        r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
        
        # Gamma 校正
        def gamma_correct(c):
            return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
        
        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)
        
        # RGB to XYZ
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # XYZ to LAB (使用 D65 标准光源)
        x = x / 0.95047
        y = y / 1.00000
        z = z / 1.08883
        
        def f(t):
            return t ** (1/3) if t > 0.008856 else (7.787 * t + 16/116)
        
        fx = f(x)
        fy = f(y)
        fz = f(z)
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return np.array([L, a, b])
    
    def _delta_e_cie2000(self, lab1: np.ndarray, lab2: np.ndarray) -> float:
        """计算 CIEDE2000 色差
        
        这是目前最精确的颜色差异计算方法，考虑了：
        - 人眼对不同亮度、色度、色相的敏感度差异
        - 中性色区域的补偿
        - 蓝色区域的旋转补偿
        
        Args:
            lab1, lab2: LAB色彩空间的颜色值 [L, a, b]
        
        Returns:
            色差值（ΔE2000），值越小越相似
        """
        L1, a1, b1 = lab1
        L2, a2, b2 = lab2
        
        # 计算 C1, C2
        C1 = np.sqrt(a1**2 + b1**2)
        C2 = np.sqrt(a2**2 + b2**2)
        C_bar = (C1 + C2) / 2
        
        # 计算 G
        G = 0.5 * (1 - np.sqrt(C_bar**7 / (C_bar**7 + 25**7)))
        
        # 计算 a'
        a1_prime = a1 * (1 + G)
        a2_prime = a2 * (1 + G)
        
        # 计算 C'
        C1_prime = np.sqrt(a1_prime**2 + b1**2)
        C2_prime = np.sqrt(a2_prime**2 + b2**2)
        C_bar_prime = (C1_prime + C2_prime) / 2
        
        # 计算 h'
        def calc_h_prime(a_prime, b):
            if a_prime == 0 and b == 0:
                return 0
            h = np.arctan2(b, a_prime)
            return h + 2*np.pi if h < 0 else h
        
        h1_prime = calc_h_prime(a1_prime, b1)
        h2_prime = calc_h_prime(a2_prime, b2)
        
        # 计算 ΔL', ΔC', ΔH'
        delta_L_prime = L2 - L1
        delta_C_prime = C2_prime - C1_prime
        
        # 计算 Δh'
        if C1_prime * C2_prime == 0:
            delta_h_prime = 0
        elif abs(h2_prime - h1_prime) <= np.pi:
            delta_h_prime = h2_prime - h1_prime
        elif h2_prime - h1_prime > np.pi:
            delta_h_prime = h2_prime - h1_prime - 2*np.pi
        else:
            delta_h_prime = h2_prime - h1_prime + 2*np.pi
        
        delta_H_prime = 2 * np.sqrt(C1_prime * C2_prime) * np.sin(delta_h_prime / 2)
        
        # 计算 L̄', C̄', H̄'
        L_bar_prime = (L1 + L2) / 2
        
        # 计算 H̄'
        if C1_prime * C2_prime == 0:
            H_bar_prime = h1_prime + h2_prime
        elif abs(h1_prime - h2_prime) <= np.pi:
            H_bar_prime = (h1_prime + h2_prime) / 2
        elif h1_prime + h2_prime < 2*np.pi:
            H_bar_prime = (h1_prime + h2_prime + 2*np.pi) / 2
        else:
            H_bar_prime = (h1_prime + h2_prime - 2*np.pi) / 2
        
        # 计算 T
        T = 1 - 0.17*np.cos(H_bar_prime - np.pi/6) + 0.24*np.cos(2*H_bar_prime) + \
            0.32*np.cos(3*H_bar_prime + np.pi/30) - 0.20*np.cos(4*H_bar_prime - 63*np.pi/180)
        
        # 计算 S_L, S_C, S_H
        S_L = 1 + (0.015 * (L_bar_prime - 50)**2) / np.sqrt(20 + (L_bar_prime - 50)**2)
        S_C = 1 + 0.045 * C_bar_prime
        S_H = 1 + 0.015 * C_bar_prime * T
        
        # 计算 R_T
        delta_theta = 30 * np.exp(-((H_bar_prime - 275*np.pi/180) / (25*np.pi/180))**2)
        R_C = 2 * np.sqrt(C_bar_prime**7 / (C_bar_prime**7 + 25**7))
        R_T = -np.sin(2 * delta_theta * np.pi / 180) * R_C
        
        # 计算 ΔE00
        delta_E = np.sqrt(
            (delta_L_prime / S_L)**2 +
            (delta_C_prime / S_C)**2 +
            (delta_H_prime / S_H)**2 +
            R_T * (delta_C_prime / S_C) * (delta_H_prime / S_H)
        )
        
        return float(delta_E)
    
    def _load_colors(self, excel_path: str) -> None:
        """从Excel文件加载拼豆标准色号
        
        Args:
            excel_path: Excel文件路径
        """
        df = pd.read_excel(excel_path)
        
        # Excel格式：每两列一对（色号列，颜色列）
        columns = df.columns.tolist()
        
        for i in range(0, len(columns), 2):
            code_col = columns[i]
            color_col = columns[i + 1]
            
            # 遍历每一行
            for idx, row in df.iterrows():
                code = row[code_col]
                hex_color = row[color_col]
                
                # 跳过 NaN 值
                if pd.isna(code) or pd.isna(hex_color):
                    continue
                
                # 解析16进制颜色
                try:
                    hex_color = str(hex_color).strip()
                    if hex_color.startswith('#'):
                        hex_color = hex_color[1:]
                    
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    
                    code = str(code).strip()
                    self.color_map[code] = (r, g, b)
                    
                    # 转换到 LAB 色彩空间用于 CIEDE2000 计算
                    self.lab_colors[code] = self._rgb_to_lab((r, g, b))
                    
                except (ValueError, IndexError) as e:
                    print(f"⚠️ 解析颜色失败: {code} = {hex_color}, 错误: {e}")
                    continue
        
        print(f"✅ 加载了 {len(self.color_map)} 个拼豆标准色号")
    
    def find_closest_color(self, rgb: Tuple[int, int, int], top_n: int = 1, allowed_colors: List[str] = None) -> Union[Tuple[str, Tuple[int, int, int], float], List[Tuple[str, Tuple[int, int, int], float]]]:
        """查找最接近的拼豆标准色号
        
        使用 CIEDE2000 算法计算颜色差异，该算法考虑了：
        - 亮度差异
        - 色度差异
        - 色相差异
        - 人眼对不同颜色区域的敏感度差异
        
        Args:
            rgb: 输入颜色 (r, g, b)
            top_n: 返回前 N 个最接近的结果，默认 1
            allowed_colors: 允许的色号列表，如果为None则使用所有色号
        
        Returns:
            如果 top_n=1: (色号, RGB值, 色差值) 元组
            如果 top_n>1: [(色号, RGB值, 色差值), ...] 列表
        """
        # 转换输入颜色到 LAB 色彩空间
        input_lab = self._rgb_to_lab(rgb)
        
        # 如果指定了允许的色号，过滤色号列表
        if allowed_colors is not None and len(allowed_colors) > 0:
            colors_to_check = {code: rgb for code, rgb in self.color_map.items() if code in allowed_colors}
            lab_colors_to_check = {code: lab for code, lab in self.lab_colors.items() if code in allowed_colors}
        else:
            colors_to_check = self.color_map
            lab_colors_to_check = self.lab_colors
        
        # 计算与所有标准色号的 CIEDE2000 色差
        results = []
        for code, standard_rgb in colors_to_check.items():
            standard_lab = lab_colors_to_check[code]
            delta_e = self._delta_e_cie2000(input_lab, standard_lab)
            results.append((code, standard_rgb, delta_e))
        
        # 按色差排序
        results.sort(key=lambda x: x[2])
        
        # 返回前 N 个结果
        if top_n == 1:
            return results[0]
        else:
            return results[:top_n]
    
    def map_colors(self, colors: List[List[Tuple[int, int, int]]], allowed_colors: List[str] = None) -> Dict:
        """将颜色网格映射到拼豆标准色号
        
        Args:
            colors: 二维颜色列表 [[color, ...], ...]
            allowed_colors: 允许的色号列表，如果为None则使用所有色号
        
        Returns:
            包含映射结果的字典
        """
        result = {
            'grid': [],
            'palette': {},
            'statistics': {
                'total_cells': 0,
                'unique_colors': 0,
                'avg_delta_e': 0.0,
                'max_delta_e': 0.0
            }
        }
        
        delta_e_values = []
        color_usage = {}  # 统计每个色号的使用次数
        
        # 处理每个单元格
        for row in colors:
            mapped_row = []
            for rgb in row:
                # 获取 Top 3 结果（考虑用户选中的色号）
                top_3 = self.find_closest_color(rgb, top_n=3, allowed_colors=allowed_colors)
                code, mapped_rgb, delta_e = top_3[0]  # 使用最佳匹配
                
                mapped_row.append({
                    'original': rgb,
                    'code': code,
                    'mapped': mapped_rgb,
                    'delta_e': round(delta_e, 2),
                    'top_3': [{
                        'code': c,
                        'rgb': r,
                        'hex': '#{:02x}{:02x}{:02x}'.format(*r),
                        'delta_e': round(d, 2)
                    } for c, r, d in top_3]
                })
                
                delta_e_values.append(delta_e)
                result['statistics']['total_cells'] += 1
                
                # 统计色号使用
                if code not in color_usage:
                    color_usage[code] = {
                        'count': 0,
                        'rgb': mapped_rgb
                    }
                color_usage[code]['count'] += 1
            
            result['grid'].append(mapped_row)
        
        # 构建调色板（按使用次数排序）
        sorted_colors = sorted(color_usage.items(), key=lambda x: x[1]['count'], reverse=True)
        for code, info in sorted_colors:
            result['palette'][code] = {
                'rgb': info['rgb'],
                'hex': '#{:02x}{:02x}{:02x}'.format(*info['rgb']),
                'count': info['count']
            }
        
        # 计算统计信息
        result['statistics']['unique_colors'] = len(color_usage)
        if delta_e_values:
            result['statistics']['avg_delta_e'] = round(np.mean(delta_e_values), 2)
            result['statistics']['max_delta_e'] = round(max(delta_e_values), 2)
        
        return result
    
    def get_color_info(self, code: str) -> Dict:
        """获取色号详细信息
        
        Args:
            code: 色号
        
        Returns:
            色号信息字典
        """
        if code not in self.color_map:
            return None
        
        rgb = self.color_map[code]
        return {
            'code': code,
            'rgb': rgb,
            'hex': '#{:02x}{:02x}{:02x}'.format(*rgb)
        }
