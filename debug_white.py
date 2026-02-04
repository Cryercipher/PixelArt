import cv2
import numpy as np

image = cv2.imread('test.jpg')
h, w = image.shape[:2]
print(f'原图尺寸: {w}x{h}')

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

for threshold in [140, 160, 180, 200]:
    white_mask = gray > threshold
    white_ratio_rows = white_mask.sum(axis=1) / w
    high_white = (white_ratio_rows > 0.75).sum()
    mid_white = ((white_ratio_rows > 0.5) & (white_ratio_rows <= 0.75)).sum()
    low_white = (white_ratio_rows <= 0.5).sum()
    print(f'\n灰度阈值 {threshold}:')
    print(f'  >75%白色: {high_white}行')
    print(f'  50-75%白色: {mid_white}行')
    print(f'  <50%白色: {low_white}行')

print('\n=== 底部100行分析（灰度>160） ===')
white_mask = gray > 160
white_ratio_rows = white_mask.sum(axis=1) / w

for i in [h-100, h-80, h-60, h-40, h-20, h-10, h-5, h-1]:
    ratio = white_ratio_rows[i]
    print(f'第{i}行: 白色比例 {ratio:.1%}')

content_rows = white_ratio_rows < 0.75
row_indices = np.where(content_rows)[0]
if len(row_indices) > 0:
    last_content_row = row_indices[-1]
    print(f'\n最后一个内容行: 第{last_content_row}行')
    print(f'之后还有 {h - last_content_row - 1} 行')

# 从下往上扫描，找到第一个高白色比例行
print('\n=== 从下往上扫描 ===')
for i in range(h-1, -1, -1):
    if white_ratio_rows[i] > 0.90:
        print(f'第{i}行是高白色行(>{90}%)，应该从这里截断')
        print(f'可以裁掉 {h - i} 行')
        break
