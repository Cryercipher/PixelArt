# 项目结构

## 目录布局

```
PixelArt/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化，导出主类
│   └── perler_bead_detector.py  # 核心检测器类 (596 行)
│
├── examples/                     # 示例和教程
│   └── quickstart.py            # 快速开始示例
│
├── docs/                         # 文档
│   ├── ALGORITHM.md             # 算法详解
│   ├── TROUBLESHOOT.md          # 故障排除指南
│   └── PROJECT_STRUCTURE.md     # 本文件
│
├── tests/                        # 测试
│   └── test_*.py               # 单元测试
│
├── README.md                     # 项目概述和快速开始
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                       # MIT 许可证
├── pyproject.toml              # 项目元数据和构建配置
├── requirements.txt             # 依赖列表
├── .gitignore                   # Git 忽略规则
└── .venv/                       # 虚拟环境
```

## 核心文件说明

### `src/perler_bead_detector.py`

**类**: `PerlerBeadDetector`

**主要方法**:

| 方法 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `__init__()` | 初始化检测器参数 | min/max_grid_size | None |
| `process_image()` | 完整的处理流程 | image_path | 检测结果字典 |
| `_detect_grid()` | 网格线检测 | 图片数组 | h_lines, v_lines, 间距 |
| `_extract_colors()` | 颜色提取 | 图片数组, 网格信息 | 颜色矩阵 |
| `_get_dominant_color()` | 单个格子主颜色 | 格子图片 | RGB 颜色元组 |
| `_merge_similar_colors()` | 全局颜色聚类 | 颜色矩阵 | 合并后的颜色矩阵 |
| `save_svg()` | 导出矢量图 | 结果, 路径 | SVG 文件 |
| `save_color_palette()` | 导出调色板 | 结果, 路径 | 颜色计数 |
| `visualize_result()` | 生成对比图 | 原图, 结果, 路径 | PNG 文件 |

**关键常数**:
```python
MIN_CLUSTER_SIZE = 100          # K-means 最小样本数
MAX_COLORS = 50                 # 最终最大颜色数
MARGIN_RATIO = 0.1              # 边界裁剪比例
```

**处理流程**:
```
原始图片
  ├→ 灰度转换
  ├→ 自适应二值化
  ├→ 形态学操作（膨胀/腐蚀）
  ├→ Hough 直线检测 (threshold=50, minLineLength=30, maxLineGap=5)
  └→ 网格线提取和去重

每个格子
  ├→ 边界裁剪 (10%)
  ├→ 中值滤波（5×5）
  ├→ K-means 聚类 (k=5)
  └→ 智能颜色滤波

全局颜色合并
  ├→ 白色背景检测 (brightness>200 AND color_range<20)
  ├→ 白色变体合并
  └→ K-means 最终聚类 (max=50)

输出
  ├→ SVG 矢量图
  ├→ PNG 对比图
  └→ 颜色调色板
```

### `src/__init__.py`

导出公共 API：
```python
from .perler_bead_detector import PerlerBeadDetector

__version__ = "2.0.0"
__all__ = ["PerlerBeadDetector"]
```

### `examples/quickstart.py`

用户友好的示例：
- 完整的处理流程演示
- 错误处理和验证
- 详细的输出信息
- 颜色统计显示

## 依赖关系

```
perler-bead-detector
├── opencv-python (图像处理、Hough 变换)
├── numpy (数值计算)
├── scikit-learn (K-means 聚类)
├── Pillow (图像 I/O)
├── svgwrite (SVG 生成)
├── matplotlib (可视化)
└── scipy (数值方法)
```

## 版本历史

### v2.0.0
- ✅ 完整的项目结构重构
- ✅ 文档体系完善
- ✅ Hough 参数优化
- ✅ 颜色识别算法优化
- ✅ 白色检测准确性提升

### v1.0.0
- ✅ 基础网格检测
- ✅ 颜色识别
- ✅ SVG 输出

## 扩展指南

### 添加新功能

1. **修改核心类** → `src/perler_bead_detector.py`
2. **更新导出** → `src/__init__.py`
3. **添加例子** → `examples/new_feature.py`
4. **文档说明** → `docs/ALGORITHM.md`

### 自定义使用

```python
from src import PerlerBeadDetector

detector = PerlerBeadDetector(
    min_grid_size=5,
    max_grid_size=150,
    max_colors=100  # 自定义
)

result = detector.process_image('input.jpg', debug=True)
detector.save_svg(result, 'output.svg', cell_size=30)
```

### 参数调整

根据不同图片质量调整 Hough 参数：

```python
# 在 _detect_grid 方法中：
# threshold: 网格线强度阈值（50-100）
# minLineLength: 最小线长（20-50）
# maxLineGap: 最大间隙（5-10）
```

## 输出文件格式

### SVG 矢量图
- 可无限缩放
- 支持编辑
- 文件大小小

### PNG 对比图
- 原图 + 检测结果并排显示
- 包含网格线
- 便于验证准确度

### 调色板 TXT
- 每种颜色及数量
- RGB 值和 HEX 值
- 百分比统计

## 性能基准

| 图片大小 | 网格大小 | 处理时间 |
|----------|----------|----------|
| 1000×1500 | 50×60 | ~2.6s |
| 800×1000 | 40×50 | ~1.5s |
| 600×800 | 30×40 | ~0.8s |

## 测试覆盖

关键测试场景：
- ✅ 不同网格尺寸 (10×10 到 100×100)
- ✅ 不同图片比例 (正方形、横向、纵向)
- ✅ 边界颜色干扰处理
- ✅ 白色背景识别
- ✅ 颜色数量聚类

## 贡献指南

见 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 许可证

MIT License - 见 [LICENSE](../LICENSE)
