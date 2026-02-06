# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PixelArt is a tool that automatically detects grid patterns and colors from perler bead craft templates, outputting vector SVG images. It includes both a Python library and a Flask web application.

## Commands

```bash
# Install dependencies (use uv, not pip)
uv pip install -r requirements.txt

# Run the web application
python web/app.py  # Opens at http://localhost:5001

# Run tests
pytest tests/

# Linting and formatting
black src/ web/
flake8 src/ web/
mypy src/
```

## Architecture

### Core Processing Pipeline

```
Image → Grid Detection → Color Extraction → Color Merging → SVG Output
        (0.14s)         (0.27s)            (0.01s)
```

1. **Grid Detection** (`src/grid_detection.py`):
   - Sobel edge detection to estimate grid spacing
   - Adaptive morphological kernel length (spacing × 1.2)
   - Hough transform to detect grid lines
   - Gap filling for missed lines

2. **Color Processing** (`src/color_processing.py`):
   - Histogram-based dominant color extraction (fast path)
   - K-means clustering fallback for complex cases (k=3)
   - Black/white filtering for borders and backgrounds
   - Adaptive sampling for large cells (>60px: 3x, >30px: 2x step)

3. **Color Mapper** (`src/color_mapper.py`):
   - Delta-E color difference matching
   - Maps to standard perler bead color codes
   - Requires `adjusted_colors.xlsx`

4. **Main Orchestrator** (`src/perler_bead_detector.py`):
   - `PerlerBeadDetector` class coordinates the pipeline
   - Provides public API for processing and saving

### Web Application

- `web/app.py`: Flask server (port 5001)
  - `/upload`: Image upload and processing
  - `/export_svg`, `/import_svg`: SVG handling
  - `/api/all_colors`, `/api/find_color`: Color mapping API

- `web/static/script.js`: Frontend logic
  - Canvas rendering with pixel art style
  - HEX mode / Color Card mode switching
  - Edit mode, Crop mode
  - Inventory management (localStorage)

- `web/static/style.css`: Stardew Valley pixel aesthetic

### Key Configuration

`src/config.py`:
- `GridDetectionConfig`: Hough threshold=40, minLineLength=30, maxLineGap=5
- `ColorProcessingConfig`: margin=10%, kmeans_clusters=3, max_colors=20

## Usage Example

```python
from src import PerlerBeadDetector

detector = PerlerBeadDetector()
result = detector.process_image('input.jpg')

# result contains: rows, cols, colors (2D array)
detector.save_svg(result, 'output.svg')
detector.save_color_palette(result, 'palette.txt')
```

## Performance

Processing time for a 54×54 grid (~1000×1000 pixels):
- Grid detection: ~0.14s
- Color extraction: ~0.27s
- Color merging: ~0.01s
- **Total: ~0.4s**
