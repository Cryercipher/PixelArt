from src import PerlerBeadDetector
import numpy as np

detector = PerlerBeadDetector()
result = detector.process_image('test.jpg', debug=False)
colors = result['colors']
rows = len(colors)
cols = len(colors[0])

print(f"颜色矩阵尺寸: {rows}x{cols}")

# 检查最后10行的颜色模式
print("\n=== 最后10行分析 ===")
for i in range(max(0, rows-10), rows):
    unique_colors = len(set(colors[i]))
    row_colors = colors[i][:10]  # 只看前10个
    print(f"第{i}行: {unique_colors}种颜色, 样本: {row_colors}")

# 检查白色比例
def is_white(color):
    r, g, b = color
    avg = (r + g + b) / 3
    color_range = max(r, g, b) - min(r, g, b)
    return avg > 200 and color_range < 20

print("\n=== 最后10行白色比例 ===")
for i in range(max(0, rows-10), rows):
    white_count = sum(1 for j in range(cols) if is_white(colors[i][j]))
    white_ratio = white_count / cols
    print(f"第{i}行: 白色比例 {white_ratio:.1%}")
