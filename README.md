# 🎨 拼豆图纸识别工具（PixelArt Detector）

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/yourusername/PixelArt?include_prereleases)](https://github.com/yourusername/PixelArt/releases)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/yourusername/PixelArt)](https://github.com/yourusername/PixelArt/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/PixelArt)](https://github.com/yourusername/PixelArt/stargazers)

一个自动识别拼豆图纸的工具，可以将拼豆图纸图片转换为矢量图（SVG）和颜色统计。

## ✨ 功能特点

- 🔍 **智能网格检测**：自动识别不同 margin 和网格间距的拼豆图纸
- 🎨 **精准颜色识别**：使用 K-means 聚类处理颜色差异和色号干扰
- 📐 **矢量输出**：生成清晰的 SVG 矢量图，可无限缩放
- 📊 **颜色统计**：自动统计所有颜色及其用量
- 🛠️ **鲁棒性强**：处理不同清晰度、光照条件和格式的图片

## 🚀 快速开始

### 安装

```bash
# 使用 uv 安装依赖
uv pip install -r requirements.txt
```

### 基本使用

```python
from src import PerlerBeadDetector

# 创建检测器
detector = PerlerBeadDetector()

# 处理图片
result = detector.process_image('input_image.jpg')

# 生成 SVG 矢量图
detector.save_svg(result, 'output.svg', cell_size=20, grid_width=1.5)

# 保存颜色统计
detector.save_color_palette(result, 'colors.txt')

# 生成可视化对比
detector.visualize_result('input_image.jpg', result, 'comparison.png')
```

### 完整示例

参见 [examples/quickstart.py](examples/quickstart.py)

```bash
python examples/quickstart.py
```

## 🔧 核心算法

### 1. 网格检测

**难点**：图片的边距（margin）不同，网格大小可能不一致

**解决方案**：
- 自适应阈值二值化适应不同光照
- 形态学操作增强网格线
- 霍夫变换精确检测线条位置
- 自动过滤相近线条去除检测重复

**参数**：
```python
threshold=50          # 霍夫变换灵敏度
minLineLength=30      # 最小线条长度
maxLineGap=5          # 最大线条间隙
```

### 2. 颜色识别

**难点**：图片清晰度差异、色号文字干扰、光照不均

**解决方案**：

#### 单方格颜色提取
1. **边距裁剪**：每个方格裁剪 10% 边缘，去除网格线干扰
2. **中值滤波**：去除噪声
3. **K-means 聚类**：分离背景色和色号文字（5 个簇）
4. **智能颜色过滤**：
   - 排除极端黑色（色号常用）
   - 判断白色：亮度 > 200 且色差 < 20
   - 选择最大的非极端颜色簇

#### 全局颜色合并
1. **分离白色背景**：识别所有浅色无色差的颜色
2. **白色合并**：将所有白色背景变种合并成一种标准白
3. **K-means 聚类**：将超过 50 种颜色聚类到目标数量

**效果**：
- 自动合并相似颜色（如浅黄色变种）
- 保留真实的浅色拼豆（如浅粉、浅蓝）
- 消除色号文字干扰

### 3. 矢量化

将检测结果转换为 SVG 格式：
- 每个方格对应一个矩形
- 黑色网格线标注边界
- RGB 颜色准确渲染

## 📊 输出格式

### SVG 矢量图
```
output.svg - 高质量矢量图，可在浏览器打开或用设计工具编辑
```

### 颜色统计文件
```
colors.txt:
共检测到 XX 种不同的颜色

1. RGB(221, 144, 77) = #dd904d - 出现 139 次
2. RGB(219, 145, 79) = #db914f - 出现 113 次
...
```

### 可视化对比图
```
comparison.png - 左图为原始图片，右图为识别结果（带网格线）
```

## 🎯 使用参数

### PerlerBeadDetector

```python
detector = PerlerBeadDetector(
    min_grid_size=10,   # 最小网格大小（像素）
    max_grid_size=100   # 最大网格大小（像素）
)
```

### process_image

```python
result = detector.process_image(
    image_path='input.jpg',
    debug=False  # 显示调试信息
)
```

### save_svg

```python
detector.save_svg(
    result,
    output_path='output.svg',
    cell_size=20,       # 每个方格大小（像素）
    grid_width=1.5      # 网格线宽度（像素）
)
```

## 💡 最佳实践

### 图片要求

理想的拼豆图纸应该：
- ✅ 有清晰的网格线（黑色或深色）
- ✅ 光照均匀，避免阴影
- ✅ 分辨率足够（建议 > 800x600）
- ✅ 每个方格的颜色相对纯净
- ✅ 图片清晰，不模糊

### 参数调整

如果识别效果不理想：

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 网格错位 | 线条检测不完整 | 已自动优化，无需调整 |
| 颜色不准 | 光照不均 | 使用 Photoshop 等工具调整亮度 |
| 白色背景混色 | 浅色被误识别 | 检查 `color_range` 判断逻辑 |
| 色号干扰 | 文字颜色未被过滤 | 增加极端黑色过滤的色差范围 |

## 📦 依赖

- Python 3.8+
- OpenCV (`opencv-python`)
- NumPy (`numpy`)
- scikit-learn (`scikit-learn`)
- Pillow (`Pillow`)
- svgwrite (`svgwrite`)

## 🏗️ 项目结构

```
PixelArt/
├── src/
│   ├── __init__.py
│   └── perler_bead_detector.py    # 核心检测器
├── examples/
│   └── quickstart.py               # 快速开始示例
├── docs/
│   ├── ALGORITHM.md                # 算法详解
│   └── TROUBLESHOOT.md             # 问题排查
├── README.md                        # 项目说明
├── requirements.txt                 # 依赖列表
├── .gitignore                       # Git 忽略文件
└── LICENSE                          # 许可证
```

## 🐛 常见问题

### Q: 如何处理多种拼豆大小？
A: 工具自动适应，无需调整。`min_grid_size` 和 `max_grid_size` 参数控制检测范围。

### Q: SVG 文件怎么用？
A: 
- 在浏览器中直接打开
- 在 Illustrator、Inkscape 等设计工具中编辑
- 用于 3D 打印准备工作

### Q: 如何提高颜色识别准确度？
A: 
1. 确保光照均匀
2. 避免颜色反光（降低拍照角度）
3. 使用高清相机或扫描仪

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如遇问题，请查看：
1. [TROUBLESHOOT.md](docs/TROUBLESHOOT.md) - 问题排查指南
2. [ALGORITHM.md](docs/ALGORITHM.md) - 算法详解
3. 提交 GitHub Issue
