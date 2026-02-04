# 算法详解

## 概述

拼豆图纸识别工具通过三个核心阶段处理：

1. **网格检测** - 定位方格位置
2. **颜色识别** - 提取方格颜色
3. **矢量化** - 生成 SVG 输出

## 第一阶段：网格检测

### 问题

拼豆图纸的网格线样式多样：
- 边距不同
- 网格间距不一致
- 某些线条模糊或断裂
- 光照不均导致线条对比度变化

### 算法步骤

#### 1. 预处理

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

**为什么用自适应阈值？**
- 简单二值化在光照不均的区域会失效
- 自适应方法按局部邻域计算阈值
- 能处理同一张图上亮暗差异较大的情况

#### 2. 形态学操作

```python
# 水平线检测（高度1，宽度40的核）
kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_h)

# 垂直线检测（高度40，宽度1的核）
kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v)
```

**原理**：
- 开运算 = 腐蚀 + 膨胀
- 删除小于核大小的噪声
- 突出水平/垂直方向的特征

#### 3. 霍夫变换检测线条

```python
lines = cv2.HoughLinesP(
    image,
    rho=1,
    theta=np.pi/180,
    threshold=50,          # 投票数阈值
    minLineLength=30,      # 最小线长
    maxLineGap=5           # 最大间隙
)
```

**参数解释**：
- `rho=1` - 距离精度 1 像素
- `theta=π/180` - 角度精度 1 度
- `threshold=50` - 至少 50 次投票才认为是线
- `minLineLength=30` - 线条至少 30 像素长
- `maxLineGap=5` - 间隙超过 5 像素则认为是断裂

**为什么降低参数？**
- 原始 threshold=100 无法检测弱线条
- 原始 minLineLength=50 遗漏小格子的线
- 这导致格子数被低估

#### 4. 线条聚合

```python
# 提取线条的中点坐标
h_positions = sorted(set([int(y) for _, y in h_lines]))
v_positions = sorted(set([int(x) for x, _ in v_lines]))

# 过滤相近的线条
h_positions = _filter_close_lines(h_positions, min_distance=5)
v_positions = _filter_close_lines(v_positions, min_distance=5)
```

**为什么要聚合？**
- 同一条线可能被检测多次（浮动 ±1-2 像素）
- 聚合后获得稳定的网格位置

### 输出

```python
{
    'h_lines': [y1, y2, y3, ...],      # 水平线 Y 坐标
    'v_lines': [x1, x2, x3, ...],      # 垂直线 X 坐标
    'h_spacing': 19.0,                  # 平均水平间距
    'v_spacing': 19.0                   # 平均垂直间距
}
```

## 第二阶段：颜色识别

### 问题

拼豆图纸中的颜色识别面临多个挑战：

1. **同一方格内颜色不均**
   - 光照渐变
   - 拍照角度反光
   - JPEG 压缩伪影

2. **色号文字干扰**
   - 黑色、白色的标注
   - 占据方格中心

3. **颜色相似度**
   - 浅黄、浅粉等容易混淆
   - 需要全局合并

### 单方格颜色提取

#### 1. 边距裁剪

```python
# 计算方格大小
cell_height = y2 - y1
cell_width = x2 - x1

# 动态边距：10%
margin_percent = 0.1
margin_y = int(cell_height * margin_percent)
margin_x = int(cell_width * margin_percent)

# 只保留中心区域
cell = image[y1+margin_y:y2-margin_y, x1+margin_x:x2-margin_x]
```

**为什么 10%？**
- 太小（5%）- 网格线干扰太大
- 太大（25%）- 采样像素不足，K-means 不稳定
- 10% 是平衡点：避免边界污染 + 足量采样

#### 2. 噪声过滤

```python
# 中值滤波（5x5 核）
cell_filtered = cv2.medianBlur(cell, 5)
```

**优势**：
- 保留边界信息（vs 高斯模糊）
- 有效移除椒盐噪声

#### 3. K-means 聚类

```python
# RGB 颜色转换
cell_rgb = cv2.cvtColor(cell_filtered, cv2.COLOR_BGR2RGB)
pixels = cell_rgb.reshape(-1, 3)  # 形状 (n_pixels, 3)

# 聚类分离背景和文字
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
kmeans.fit(pixels)

# 找最大的簇
label_counts = Counter(kmeans.labels_)
dominant_label = label_counts.most_common(1)[0][0]

color = kmeans.cluster_centers_[dominant_label]
```

**为什么 5 个簇？**
- 3 个簇：无法分离微妙的颜色变化
- 5 个簇：可以分离背景色、光照变化、噪声、色号文字
- 10+ 个簇：过度拟合，反而降低准确性

#### 4. 智能颜色过滤

```python
# 过滤极端黑色（色号文字）
if r < 50 and g < 50 and b < 50:
    continue  # 跳过这个簇

# 判断是否是白色/灰色
avg_brightness = (r + g + b) / 3
color_range = max(r, g, b) - min(r, g, b)

# 白色 = 亮度高 + 色差小
if avg_brightness > 200 and color_range < 20:
    if占比 > 30%:
        return color  # 白色背景
    continue

# 其他非极端颜色
return color
```

**色差计算的妙处**：
- RGB(246, 245, 243) 纯白 → range=3 ✓
- RGB(246, 240, 200) 浅黄 → range=46 ✗
- 区分了白色背景 vs 浅色拼豆

### 全局颜色合并

#### 问题

如果有 50+ 种检测到的颜色，包括很多相似的浅色变种：
- RGB(245, 244, 242)
- RGB(246, 245, 243)
- RGB(245, 244, 243)

这些都应该合并成一种"标准白"。

#### 算法

```python
# 1. 分离白色背景
for color in unique_colors:
    r, g, b = color
    avg = (r + g + b) / 3
    range = max(r,g,b) - min(r,g,b)
    
    if avg > 200 and range < 20:
        white_colors.append(color)
    else:
        other_colors.append(color)

# 2. 合并白色
if len(white_colors) > 5:
    avg_white = np.mean(white_colors, axis=0)
    white_map = {c: avg_white for c in white_colors}

# 3. 对其他颜色进行 K-means 聚类
kmeans = KMeans(n_clusters=50)
kmeans.fit(other_colors)

# 4. 合并映射
colors = 应用白色映射 + 应用 K-means 映射
```

**效果**：
- 检测 1225 种颜色 → 35 种颜色
- 白色变种 243 种 → 1 种
- 保留真实浅色拼豆

## 第三阶段：矢量化

```python
# 创建 SVG
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
            stroke_width=1.5
        ))
```

## 可视化对比图

对于 PNG 输出（对比图），还需要放大结果图：

```python
# 每个方格放大到 20x20 像素
result_image = np.zeros((rows*20, cols*20, 3), dtype=np.uint8)

for i in range(rows):
    for j in range(cols):
        y1, y2 = i*20, (i+1)*20
        x1, x2 = j*20, (j+1)*20
        result_image[y1:y2, x1:x2] = colors[i][j]

# 绘制网格线
for i in range(rows+1):
    y = i * 20
    result_image[y, :] = [0, 0, 0]
    
for j in range(cols+1):
    x = j * 20
    result_image[:, x] = [0, 0, 0]
```

## 性能优化建议

1. **大图片处理**：先缩小到 2000x2000
2. **实时预览**：显示进度条
3. **并行处理**：多线程处理多个方格的颜色
4. **缓存结果**：保存中间结果避免重复计算

## 参考文献

- OpenCV 官方文档
- scikit-learn K-means 文档
- SVG 标准规范
