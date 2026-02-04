# 拼豆图纸识别工具

一个自动识别拼豆图纸的工具，可以将拼豆图纸图片转换为矢量图（SVG）。

## 功能特点

- 🔍 **智能网格检测**：自动识别不同margin的拼豆图纸
- 🎨 **颜色识别**：使用K-means聚类识别每个方格的主要颜色
- 📐 **矢量输出**：生成高质量的SVG矢量图
- 🛠️ **鲁棒性强**：处理不同清晰度和光照条件的图片

## 依赖管理

> ⚠️ **注意**：本项目使用 [uv](https://github.com/astral-sh/uv) 进行 Python 包管理，而非 pip。

## 安装依赖

```bash
# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 或者使用 uv sync（如果配置了 pyproject.toml）
uv sync
```

## 使用方法

```python
from perler_bead_detector import PerlerBeadDetector

# 创建检测器
detector = PerlerBeadDetector()

# 处理图片
result = detector.process_image('input_image.jpg')

# 保存为SVG
detector.save_svg(result, 'output.svg')
```

## 核心算法

### 1. 网格检测
- 使用霍夫变换检测水平和垂直线
- 自动处理不同的边距和网格间距
- 形态学操作增强网格线

### 2. 颜色识别
- 中值滤波去除噪声
- K-means聚类处理颜色差异
- 提取每个方格的主导颜色

### 3. 矢量化
- 将检测结果转换为SVG格式
- 保持颜色准确性
- 可缩放不失真

## 技术难点解决

### 难点1：识别像素点
通过霍夫变换检测网格线，自动适应不同的margin和网格间距。

### 难点2：颜色识别
使用中值滤波和K-means聚类，从每个方格中提取最具代表性的颜色。

## 示例

参见 `example.py` 了解详细使用方法。
