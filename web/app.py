#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼豆像素画 Web 应用
星露谷物语风格的像素艺术识别工具
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import json
import svgwrite
import xml.etree.ElementTree as ET

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 延迟加载检测器
detector = None

def get_detector():
    global detector
    if detector is None:
        from src import PerlerBeadDetector
        detector = PerlerBeadDetector()
    return detector


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def rgb_to_hex(r, g, b):
    """RGB转16进制颜色"""
    return f'#{r:02x}{g:02x}{b:02x}'


def hex_to_rgb(hex_color: str):
    """16进制颜色转RGB"""
    value = hex_color.lstrip('#')
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def build_color_stats_from_hex_grid(color_grid):
    stats = {}
    for row in color_grid:
        for hex_color in row:
            if hex_color in stats:
                stats[hex_color]['count'] += 1
            else:
                r, g, b = hex_to_rgb(hex_color)
                stats[hex_color] = {
                    'rgb': f'RGB({r},{g},{b})',
                    'count': 1
                }
    return stats


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """处理图片上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 处理图片
            det = get_detector()
            result = det.process_image(filepath, debug=False)
            
            if result is None:
                return jsonify({'error': '无法识别图片中的网格'}), 400
            
            # 裁剪白色边界
            colors = det._crop_white_borders(result['colors'])
            rows = len(colors)
            cols = len(colors[0]) if rows > 0 else 0
            
            # 转换颜色数据为前端格式
            color_grid = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    # colors 中已经是 RGB 格式（来自 _get_dominant_color 中的 cv2.COLOR_BGR2RGB 转换）
                    r, g, b = colors[i][j]
                    hex_color = rgb_to_hex(r, g, b)
                    row.append(hex_color)
                color_grid.append(row)

            color_stats = build_color_stats_from_hex_grid(color_grid)
            
            # 按使用次数排序颜色统计
            sorted_colors = sorted(
                color_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            return jsonify({
                'success': True,
                'rows': rows,
                'cols': cols,
                'colors': color_grid,
                'colorStats': dict(sorted_colors),
                'totalColors': len(color_stats)
            })
        
        except Exception as e:
            return jsonify({'error': f'处理失败: {str(e)}'}), 500
        
        finally:
            # 清理上传的文件
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': '不支持的文件格式'}), 400


@app.route('/export_svg', methods=['POST'])
def export_svg():
    """导出当前颜色网格为SVG"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': '无效请求'}), 400

        colors = data.get('colors')
        rows = data.get('rows')
        cols = data.get('cols')

        if not colors or not rows or not cols:
            return jsonify({'error': '缺少颜色网格数据'}), 400

        cell_size = int(data.get('cellSize', 20))
        width = cols * cell_size
        height = rows * cell_size

        dwg = svgwrite.Drawing(size=(width, height))

        # metadata 中保存原始网格
        meta_payload = {
            'rows': rows,
            'cols': cols,
            'colors': colors,
            'cellSize': cell_size,
        }
        dwg.add(dwg.metadata(json.dumps(meta_payload, ensure_ascii=False)))

        for i in range(rows):
            for j in range(cols):
                color = colors[i][j]
                dwg.add(
                    dwg.rect(
                        insert=(j * cell_size, i * cell_size),
                        size=(cell_size, cell_size),
                        fill=color,
                        stroke='black',
                        stroke_width=1.0,
                    )
                )

        svg_text = dwg.tostring()
        return app.response_class(svg_text, mimetype='image/svg+xml')
    except Exception as e:
        print(f'SVG导出错误: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@app.route('/import_svg', methods=['POST'])
def import_svg():
    """导入带有metadata的SVG"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    content = file.read()
    try:
        root = ET.fromstring(content)
    except Exception:
        return jsonify({'error': 'SVG 解析失败'}), 400

    metadata_node = root.find('.//{*}metadata')
    if metadata_node is None or not (metadata_node.text and metadata_node.text.strip()):
        return jsonify({'error': 'SVG 缺少可导入的 metadata'}), 400

    try:
        meta = json.loads(metadata_node.text.strip())
        colors = meta.get('colors')
        rows = meta.get('rows')
        cols = meta.get('cols')
    except Exception:
        return jsonify({'error': 'metadata 格式不正确'}), 400

    if not colors or not rows or not cols:
        return jsonify({'error': 'metadata 数据不完整'}), 400

    color_stats = build_color_stats_from_hex_grid(colors)

    sorted_colors = sorted(
        color_stats.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )

    return jsonify({
        'success': True,
        'rows': rows,
        'cols': cols,
        'colors': colors,
        'colorStats': dict(sorted_colors),
        'totalColors': len(color_stats)
    })


@app.route('/static/<path:path>')
def send_static(path):
    """静态文件服务"""
    return send_from_directory('static', path)


if __name__ == '__main__':
    print("🎮 拼豆像素画识别器启动中...")
    print("🌟 打开浏览器访问: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
