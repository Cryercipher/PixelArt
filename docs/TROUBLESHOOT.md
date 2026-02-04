# 问题排查指南

## 常见问题及解决方案

### 1. 网格检测问题

#### 问题：检测不到网格线
**错误信息**：`无法检测到网格结构`

**原因**：
- 图片过暗或过亮
- 网格线不清晰
- 网格线颜色接近背景色

**解决方案**：
```python
# 方案 1：检查图片质量
import cv2
image = cv2.imread('image.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
print(f"亮度范围: {gray.min()}-{gray.max()}")
# 理想范围应该是 30-200 的混合

# 方案 2：使用图片编辑工具调整
# - 增加对比度
# - 调整亮度
# - 增强边缘清晰度
```

#### 问题：网格数量不对（如 4 格变 3 格）
**原因**：霍夫线条检测的阈值不合适

**检查方法**：
```python
detector = PerlerBeadDetector()
# 在 perler_bead_detector.py 的 _detect_grid 方法中
# 打印中间结果
result = detector.process_image('image.jpg')
print(f"水平线: {len(result['grid_info']['h_lines'])}")
print(f"垂直线: {len(result['grid_info']['v_lines'])}")
# 应该等于 rows+1 和 cols+1
```

**已优化的参数**：
```
threshold=50      # 霍夫变换灵敏度
minLineLength=30  # 最小线条长度
maxLineGap=5      # 最大线条间隙
```

---

### 2. 颜色识别问题

#### 问题：识别出的颜色不准
**现象**：识别颜色偏移，如应该是红色但识别成橙色

**原因**：
1. 光照不均
2. 拍照角度反光
3. 图片压缩伪影

**解决方案**：

```python
# 方案 1：检查光照
import cv2
import numpy as np

image = cv2.imread('image.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 计算光照均匀度
mean = gray.mean()
std = gray.std()
coefficient = std / mean  # 变异系数，越小越均匀

if coefficient > 0.3:
    print("⚠️ 光照不均！建议重新拍照")
else:
    print("✓ 光照可接受")

# 方案 2：调整参数
# 在 _extract_colors 中增加 margin_percent
margin_percent = 0.15  # 从 0.10 增加到 0.15
# 这样会裁剪更多边缘，但要确保采样像素足够
```

#### 问题：白色背景混入其他颜色
**现象**：白色区域出现灰色或浅黄色小方块

**原因**：白色识别条件过宽松

**检查和修复**：
```python
# 在 _get_dominant_color 方法中，检查白色判定
# 当前条件：
# avg_brightness > 200 and color_range < 20

# 如果问题仍存在，可以调整：
avg_brightness > 210  # 更严格
color_range < 15      # 更严格的色差
```

#### 问题：色号文字干扰识别
**现象**：标注色号的方格识别成黑色或混合色

**原因**：色号文字占比过大

**解决方案**：
```python
# 在 _get_dominant_color 中增强文字过滤
# 当前：
# if r < 50 and g < 50 and b < 50: continue

# 可改为：
if r < 100 and g < 100 and b < 100:  # 过滤更宽的黑灰
    continue
# 同时增加簇数量
n_clusters = 7  # 从 5 增加到 7
```

---

### 3. 输出文件问题

#### 问题：SVG 文件在浏览器打不开
**原因**：
- SVG 路径不存在
- 权限问题

**解决方案**：
```python
import os

output_path = 'output.svg'

# 检查目录是否存在
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# 检查权限
if not os.access(os.path.dirname(output_path), os.W_OK):
    print("❌ 没有写入权限")
```

#### 问题：SVG 文件太大
**原因**：方格太多或浏览器性能

**解决方案**：
```python
# 缩小方格大小
detector.save_svg(result, 'output.svg', cell_size=10)  # 从 20 改为 10

# 或者压缩 SVG
import gzip
with open('output.svg', 'rb') as f:
    with gzip.open('output.svg.gz', 'wb') as gz:
        gz.writelines(f)
```

---

### 4. 性能问题

#### 问题：处理速度很慢
**原因**：
- 图片分辨率太高
- 方格数量太多

**优化方案**：
```python
import cv2

image = cv2.imread('image.jpg')

# 缩小图片到合理大小（最长边 2000 像素）
height, width = image.shape[:2]
if max(height, width) > 2000:
    scale = 2000 / max(height, width)
    new_size = (int(width * scale), int(height * scale))
    image = cv2.resize(image, new_size)
    cv2.imwrite('resized.jpg', image)
    
# 然后处理缩小后的图片
detector.process_image('resized.jpg')
```

---

### 5. 环境问题

#### 问题：导入模块失败
```
ModuleNotFoundError: No module named 'cv2'
```

**解决方案**：
```bash
# 使用 uv 重新安装依赖
uv pip install -r requirements.txt

# 或者单独安装
uv pip install opencv-python scikit-learn
```

#### 问题：Python 版本不兼容
**要求**：Python 3.8+

**检查**：
```bash
python --version
# 应该输出 3.8 或更高版本
```

---

### 6. 调试技巧

#### 启用调试模式
```python
detector = PerlerBeadDetector()
result = detector.process_image('image.jpg', debug=True)
# 会显示网格检测的中间图片
```

#### 查看颜色统计
```python
detector.save_color_palette(result, 'colors.txt')

# 打开 colors.txt 查看所有颜色
with open('colors.txt') as f:
    print(f.read())
```

#### 添加自定义日志
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在代码中添加
logger.debug(f"检测到 {len(h_lines)} 条水平线")
```

---

## 提交 Bug 报告

如果遇到问题，请提交 GitHub Issue，包含：

1. Python 版本：`python --version`
2. 操作系统：`uname -a` 或 `systeminfo`
3. 依赖版本：`pip list`
4. 图片样本：附加小图片（不超过 2MB）
5. 完整错误信息：包括 traceback
6. 重现步骤：清晰的代码片段

---

## 性能基准

在标准配置下（MacBook Pro M1，Python 3.11）：

| 操作 | 图片大小 | 网格大小 | 耗时 |
|------|--------|--------|------|
| 网格检测 | 1000x1500 | 50x60 | ~0.5s |
| 颜色提取 | 1000x1500 | 50x60 | ~2s |
| 颜色合并 | - | - | ~0.1s |
| SVG 生成 | - | 50x60 | ~0.05s |
| **总计** | 1000x1500 | 50x60 | ~2.6s |

---

## 获取帮助

- 📖 [算法详解](ALGORITHM.md) - 了解工作原理
- 📝 [README](../README.md) - 基本使用方法
- 💬 [GitHub Discussion](https://github.com/xxx/issues) - 社区讨论
