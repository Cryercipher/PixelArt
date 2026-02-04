from src import PerlerBeadDetector
import numpy as np

detector = PerlerBeadDetector()
result = detector.process_image('test.jpg', debug=False)
colors = result['colors']
rows = len(colors)
cols = len(colors[0])

print(f"颜色矩阵尺寸: {rows}x{cols}")

def is_white(color):
    r, g, b = color
    avg = (r + g + b) / 3
    color_range = max(r, g, b) - min(r, g, b)
    return avg > 200 and color_range < 20

def count_unique_colors(row):
    return len(set(row))

print("\n=== 每行分析 ===")
for i in range(rows):
    unique_colors = count_unique_colors(colors[i])
    white_count = sum(1 for j in range(cols) if is_white(colors[i][j]))
    white_ratio = white_count / cols
    
    # 判断是否是内容行（原逻辑）
    is_content = unique_colors > 15 and white_ratio < 0.50
    
    marker = " <-- 内容行" if is_content else ""
    if i >= 20:  # 只显示第20行往后
        print(f"第{i:2d}行: {unique_colors:2d}种颜色, 白色{white_ratio:5.1%}{marker}")
