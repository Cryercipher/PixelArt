# PixelArt

自动识别拼豆图纸的网格和颜色，输出为矢量图 SVG。

![Demo](result.png)

## 功能

- **智能网格检测** - 自适应 Hough 变换 + Sobel 边缘检测，自动估算网格间距
- **精准颜色识别** - 直方图聚类 + K-means，过滤噪声和色号文字
- **标准色号映射** - 匹配拼豆标准色卡（支持库存管理）
- **SVG 矢量图输出** - 支持导入/导出编辑

## 安装

```bash
# 使用 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

## 使用

### Web 应用

```bash
python web/app.py
# 打开 http://localhost:5001
```

**功能特性：**
- 上传图片自动识别
- HEX 模式 / 色卡模式切换
- 编辑模式：点击修改颜色
- 裁剪模式：选择区域裁剪
- SVG 导入/导出
- 库存管理：选择你拥有的拼豆颜色

### Python API

```python
from src import PerlerBeadDetector

detector = PerlerBeadDetector()
result = detector.process_image('input.jpg')

# 保存结果
detector.save_svg(result, 'output.svg')
detector.save_color_palette(result, 'palette.txt')

# 获取网格信息
print(f"网格: {result['rows']} x {result['cols']}")
```

## 项目结构

```
PixelArt/
├── src/                        # 核心算法
│   ├── perler_bead_detector.py # 主处理流程
│   ├── grid_detection.py       # 网格检测（自适应 kernel + 间隙填补）
│   ├── color_processing.py     # 颜色提取（直方图 + K-means）
│   ├── color_mapper.py         # 色号映射
│   └── config.py               # 配置参数
├── web/                        # Flask Web 应用
│   ├── app.py                  # 后端 API
│   ├── static/                 # CSS + JavaScript
│   └── templates/              # HTML 模板
├── docs/                       # 文档
│   ├── ALGORITHM.md            # 算法详解
│   └── TROUBLESHOOT.md         # 问题排查
├── examples/                   # 示例代码
│   └── quickstart.py
├── adjusted_colors.xlsx        # 拼豆色卡数据
└── CLAUDE.md                   # AI 辅助指南
```

## 算法说明

### 网格检测
1. Sobel 边缘检测估算网格间距
2. 自适应形态学核长度（间距 × 1.2）
3. Hough 变换检测直线
4. 自动填补漏检的网格线

### 颜色识别
1. 直方图量化快速提取主色
2. 过滤黑色边框和白色背景
3. K-means 回退处理复杂情况
4. Delta-E 色差匹配标准色号

## 文档

- [算法详解](docs/ALGORITHM.md) - 网格检测和颜色识别的实现原理
- [问题排查](docs/TROUBLESHOOT.md) - 常见问题解决方案

## License

MIT
