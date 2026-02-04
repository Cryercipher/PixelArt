# 🎨 PixelArt

自动识别拼豆图纸的网格和颜色，输出为矢量图。

![Demo](result.png)

## 功能

- 🔍 智能网格检测 (Hough 变换)
- 🎨 精准颜色识别 (K-means)
- 📐 矢量图输出 (SVG)
- 📊 颜色统计和调色板

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```python
from src import PerlerBeadDetector

detector = PerlerBeadDetector()
result = detector.process_image('input.jpg')

detector.save_svg(result, 'output.svg')
detector.save_color_palette(result, 'palette.txt')
detector.visualize_result('input.jpg', result, 'comparison.png')
```

## 快速开始

```bash
python examples/quickstart.py
```

## 文档

- [算法](docs/ALGORITHM.md)
- [问题排查](docs/TROUBLESHOOT.md)
- [项目结构](docs/PROJECT_STRUCTURE.md)

## 许可证

MIT
