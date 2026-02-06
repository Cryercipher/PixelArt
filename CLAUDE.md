# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PixelArt (perler-bead-detector) is a tool that automatically detects grid patterns and colors from perler bead craft templates, outputting vector SVG images. It includes both a Python library and a Flask web application.

## Commands

```bash
# Install dependencies (use uv, not pip)
uv pip install -r requirements.txt
uv pip install -e ".[dev]"  # with dev dependencies

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
```

1. **Grid Detection** (`src/grid_detection.py`): Uses adaptive thresholding, morphological operations, and Hough transform to detect grid lines
2. **Color Processing** (`src/color_processing.py`): Extracts colors from each cell using K-means clustering (k=5) to filter out noise and text labels
3. **Color Mapper** (`src/color_mapper.py`): Maps detected colors to standard perler bead color codes using Delta-E color difference (requires `adjusted_colors.xlsx`)
4. **Main Orchestrator** (`src/perler_bead_detector.py`): `PerlerBeadDetector` class coordinates the pipeline and provides the public API

### Web Application

- `web/app.py`: Flask server (port 5001) with endpoints for upload, SVG export/import, and color mapping
- `web/templates/index.html`: Pixel-art styled UI with HTML5 Canvas for grid display
- `web/static/`: CSS and JavaScript assets

### Key Configuration

Configuration parameters are in `src/config.py`:
- `GridDetectionConfig`: Hough transform parameters (threshold=40, minLineLength=30, maxLineGap=5)
- `ColorProcessingConfig`: Cell margin (10%), K-means clusters (5), max colors (20)

## Usage Example

```python
from src import PerlerBeadDetector

detector = PerlerBeadDetector()
result = detector.process_image('input.jpg')
detector.save_svg(result, 'output.svg')
```
