# 算法详解

## 概述

拼豆图纸识别工具通过三个核心阶段处理：

1. **网格检测** - 定位方格位置（~0.14s）
2. **颜色识别** - 提取方格颜色（~0.27s）
3. **矢量化** - 生成 SVG 输出（~0.01s）

## 第一阶段：网格检测

### 问题

拼豆图纸的网格线样式多样：
- 边距不同
- 网格间距不一致
- 某些线条模糊或断裂
- 光照不均导致线条对比度变化

### 算法步骤

#### 1. 网格间距估算（新增）

```python
# 使用 Sobel 边缘检测估算网格间距
sobel_h = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))
sobel_v = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))

# 投影到一维
h_profile = sobel_h.sum(axis=1)
v_profile = sobel_v.sum(axis=0)

# 峰值检测获取网格线位置
from scipy.signal import find_peaks
h_peaks, _ = find_peaks(h_profile, distance=10, prominence=0.05)
v_peaks, _ = find_peaks(v_profile, distance=10, prominence=0.05)

# 计算中位间距
spacing = np.median(np.diff(peaks))
```

**为什么要先估算间距？**
- 形态学核长度需要与网格间距匹配
- 核太长会过滤掉细网格线
- 核太短会引入噪声

#### 2. 预处理

```python
# 灰度化
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 自适应阈值二值化
binary = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 11, 2
)

# 反转（黑线 → 白线）
binary = cv2.bitwise_not(binary)
```

#### 3. 自适应形态学操作

```python
# 自适应核长度 = 网格间距 × 1.2
kernel_len = int(estimated_spacing * 1.2)
kernel_len = max(15, min(kernel_len, 60))  # 限制在合理范围

# 水平线检测
kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_h)

# 垂直线检测
kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v)
```

**原理**：
- 开运算 = 腐蚀 + 膨胀
- 删除小于核大小的噪声
- 突出水平/垂直方向的特征

#### 4. 霍夫变换检测线条

```python
lines = cv2.HoughLinesP(
    image,
    rho=1,
    theta=np.pi/180,
    threshold=40,          # 投票数阈值
    minLineLength=30,      # 最小线长
    maxLineGap=5           # 最大间隙
)
```

#### 5. 间隙填补（新增）

```python
def _normalize_grid_positions(positions):
    spacing = np.median(np.diff(positions))

    filled = [positions[0]]
    for i in range(1, len(positions)):
        gap = positions[i] - positions[i-1]

        # 如果间距超过 1.4 倍中位数，填补漏检的线
        if gap > spacing * 1.4:
            num_missing = int(round(gap / spacing)) - 1
            step = gap / (num_missing + 1)
            for j in range(1, num_missing + 1):
                filled.append(int(positions[i-1] + j * step))

        filled.append(positions[i])

    return sorted(filled)
```

**为什么要填补？**
- 某些网格线可能因为颜色浅或被文字遮挡而漏检
- 填补后网格更均匀，颜色提取更准确

### 输出

```python
{
    'h_lines': [y1, y2, y3, ...],      # 水平线 Y 坐标
    'v_lines': [x1, x2, x3, ...],      # 垂直线 X 坐标
    'h_spacing': 20.0,                  # 平均水平间距
    'v_spacing': 20.0                   # 平均垂直间距
}
```

## 第二阶段：颜色识别

### 问题

拼豆图纸中的颜色识别面临多个挑战：

1. **同一方格内颜色不均** - 光照渐变、反光、JPEG 压缩伪影
2. **色号文字干扰** - 黑色、白色的标注占据方格中心
3. **颜色相似度** - 浅黄、浅粉等容易混淆

### 单方格颜色提取

#### 1. 自适应采样（新增）

```python
# 大单元格使用更大的采样步长
sample_step = 1
if cell_height > 60 and cell_width > 60:
    sample_step = 3  # 减少 9 倍像素
elif cell_height > 30 and cell_width > 30:
    sample_step = 2  # 减少 4 倍像素

cell = image[y1+margin:y2-margin:sample_step, x1+margin:x2-margin:sample_step]
```

**为什么要采样？**
- 1000×1000 图片有 54×54 = 2916 个单元格
- 每个单元格处理时间直接影响总时间
- 采样后颜色精度几乎不变

#### 2. 快速路径：颜色一致性检测（新增）

```python
# 如果像素颜色非常一致，直接返回中位数
pixel_std = np.std(pixels, axis=0)
if np.all(pixel_std < 15):
    return tuple(map(int, np.median(pixels, axis=0)))
```

#### 3. 直方图量化（新增，主要方法）

```python
# 量化颜色到较少的 bin（8 levels per channel = 512 种颜色）
quantized = (pixels // 32) * 32 + 16

# 统计每种量化颜色的出现次数
unique, counts = np.unique(quantized, axis=0, return_counts=True)

# 找最常见的非黑非白颜色
for color in sorted_by_count:
    if is_black(color) and not enough_dark_pixels:
        continue
    if is_white(color) and not enough_white_pixels:
        continue

    # 返回该颜色对应的原始像素平均值
    mask = np.all(quantized == color, axis=1)
    return tuple(map(int, pixels[mask].mean(axis=0)))
```

**优势**：
- 比 K-means 快 10 倍以上
- 对于大多数单元格足够准确
- 自动过滤噪声（少数像素的颜色被忽略）

#### 4. K-means 回退（复杂情况）

```python
# 仅当直方图方法不可用时使用
kmeans = KMeans(n_clusters=3, random_state=42, n_init=3, max_iter=100)
kmeans.fit(pixels)

# 找最大的非黑非白簇
for cluster in sorted_by_size:
    if not is_black(cluster) and not is_white(cluster):
        return cluster
```

### 全局颜色合并

```python
# 1. 分离白色背景
white_colors = [c for c in colors if brightness(c) > 215 and range(c) < 12]

# 2. 合并白色变种
avg_white = np.mean(white_colors, axis=0)

# 3. 对其他颜色进行相似度合并（Delta-E）
similar_map = merge_similar_colors(other_colors, threshold=100)

# 4. 应用映射
merged = apply_mapping(colors, white_map, similar_map)
```

## 第三阶段：矢量化

```python
# 创建 SVG
dwg = svgwrite.Drawing(output_path, size=(width, height))

for i in range(rows):
    for j in range(cols):
        r, g, b = colors[i][j]
        dwg.add(dwg.rect(
            insert=(j * cell_size, i * cell_size),
            size=(cell_size, cell_size),
            fill=f'rgb({r},{g},{b})',
            stroke='black',
            stroke_width=1.5
        ))
```

## 性能优化总结

| 优化 | 效果 |
|------|------|
| Sobel 间距估算 | 自适应核长度，减少漏检 |
| 间隙填补 | 网格更均匀 |
| 自适应采样 | 减少 4-9 倍像素处理 |
| 直方图替代 K-means | 速度提升 10 倍 |
| 快速一致性检测 | 跳过简单单元格 |

**总处理时间**：54×54 网格 ~0.4 秒（之前 ~2 秒）

## 参考文献

- OpenCV 官方文档
- scikit-learn K-means 文档
- SVG 标准规范
