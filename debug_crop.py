import cv2
import numpy as np

image = cv2.imread('test.jpg')
h, w = image.shape[:2]
print(f'原图尺寸: {w}x{h}')

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
white_mask = gray > 160
white_ratio_rows = white_mask.sum(axis=1) / w
white_ratio_cols = white_mask.sum(axis=0) / h

content_rows = white_ratio_rows < 0.75
content_cols = white_ratio_cols < 0.75

row_indices = np.where(content_rows)[0]
col_indices = np.where(content_cols)[0]

top = row_indices[0]
bottom = row_indices[-1]
left = col_indices[0]
right = col_indices[-1]

print(f'\n初始边界: top={top}, bottom={bottom}, left={left}, right={right}')
print(f'初始裁剪后尺寸: {right-left+1}x{bottom-top+1}')

# 从下往上扫描
bottom_cutoff_threshold = 0.90
print(f'\n从第{h-1}行开始向上扫描，阈值={bottom_cutoff_threshold}')

found = False
for i in range(h - 1, bottom, -1):
    if i > h - 10:
        print(f'第{i}行: 白色比例={white_ratio_rows[i]:.2%}')
    
    if white_ratio_rows[i] > bottom_cutoff_threshold:
        print(f'\n找到高白色行: 第{i}行（白色比例={white_ratio_rows[i]:.2%}）')
        cutoff_row = i
        
        # 继续往上找连续白色区域的起点
        for j in range(i - 1, bottom, -1):
            if white_ratio_rows[j] > bottom_cutoff_threshold:
                cutoff_row = j
            else:
                break
        
        print(f'连续白色区域起点: 第{cutoff_row}行')
        
        if cutoff_row < bottom:
            print(f'应该从第{cutoff_row}行截断，裁掉{h - cutoff_row}行')
            bottom = cutoff_row - 1
            found = True
        break

if not found:
    print(f'\n未找到需要截断的区域（所有行的白色比例都<{bottom_cutoff_threshold}）')

print(f'\n最终边界: top={top}, bottom={bottom}')
print(f'最终裁剪后尺寸高度: {bottom-top+1}')
