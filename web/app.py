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

# 延迟加载检测器和颜色映射器
detector = None
color_mapper = None

def get_detector():
    global detector
    if detector is None:
        from src import PerlerBeadDetector
        detector = PerlerBeadDetector()
    return detector


def get_color_mapper():
    global color_mapper
    if color_mapper is None:
        from src.color_mapper import PerlerBeadColorMapper
        excel_path = project_root / 'adjusted_colors.xlsx'
        color_mapper = PerlerBeadColorMapper(str(excel_path))
    return color_mapper


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
            # 获取用户选中的色号列表
            selected_colors_str = request.form.get('selected_colors', '[]')
            try:
                selected_colors = json.loads(selected_colors_str)
            except:
                selected_colors = []
            
            print(f"用户选中的色号数量: {len(selected_colors)}")
            
            # 处理图片
            print(f"开始处理图片: {filename}")
            det = get_detector()
            result = det.process_image(filepath, debug=False)
            
            if result is None:
                return jsonify({'error': '无法识别图片中的网格'}), 400
            
            # 裁剪白色边界
            colors = det._crop_white_borders(result['colors'])
            rows = len(colors)
            cols = len(colors[0]) if rows > 0 else 0
            print(f"检测到网格: {rows}x{cols}")
            
            # 映射到拼豆标准色号（只在用户选中的色号中查找）
            print("开始映射颜色到标准色号...")
            mapper = get_color_mapper()
            mapping_result = mapper.map_colors(colors, allowed_colors=selected_colors)
            print(f"映射完成，使用了 {mapping_result['statistics']['unique_colors']} 种色号")
            
            # 转换颜色数据为前端格式
            color_grid = []
            mapped_color_grid = []  # 映射后的颜色
            color_codes_grid = []  # 完整的 cell 数据（包含 top_3）
            
            for i in range(rows):
                row = []
                mapped_row = []
                code_row = []
                for j in range(cols):
                    # 原始颜色
                    r, g, b = colors[i][j]
                    hex_color = rgb_to_hex(r, g, b)
                    row.append(hex_color)
                    
                    # 映射后的颜色和完整信息
                    cell_info = mapping_result['grid'][i][j]
                    mapped_r, mapped_g, mapped_b = cell_info['mapped']
                    mapped_hex = rgb_to_hex(mapped_r, mapped_g, mapped_b)
                    mapped_row.append(mapped_hex)
                    
                    # 保存完整的 cell 信息（包含 top_3）
                    code_row.append(cell_info)
                
                color_grid.append(row)
                mapped_color_grid.append(mapped_row)
                color_codes_grid.append(code_row)

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
                'colors': color_grid,  # 原始检测颜色
                'mappedColors': mapped_color_grid,  # 映射后的标准色号颜色
                'colorCodes': color_codes_grid,  # 完整的 cell 数据（包含 code, mapped, delta_e, top_3）
                'colorStats': dict(sorted_colors),
                'totalColors': len(color_stats),
                'palette': mapping_result['palette'],  # 拼豆调色板
                'statistics': mapping_result['statistics']  # 映射统计信息
            })
        
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
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

        # metadata 中保存原始网格（使用注释形式）
        meta_payload = {
            'rows': rows,
            'cols': cols,
            'colors': colors,
            'cellSize': cell_size,
        }
        meta_json = json.dumps(meta_payload, ensure_ascii=False)
        
        # 手动构建SVG字符串
        svg_lines = [
            f'<?xml version="1.0" encoding="utf-8" ?>',
            f'<svg baseProfile="full" height="{height}" version="1.1" width="{width}" xmlns="http://www.w3.org/2000/svg" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xlink="http://www.w3.org/1999/xlink">',
            f'<!-- PIXELART_METADATA:{meta_json} -->',
            f'<defs />'
        ]
        
        for i in range(rows):
            for j in range(cols):
                color = colors[i][j]
                x = j * cell_size
                y = i * cell_size
                svg_lines.append(
                    f'<rect fill="{color}" height="{cell_size}" stroke="black" stroke-width="1.0" width="{cell_size}" x="{x}" y="{y}" />'
                )
        
        svg_lines.append('</svg>')
        svg_text = '\n'.join(svg_lines)
        
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
    
    # 先尝试从注释中提取metadata
    try:
        content_str = content.decode('utf-8') if isinstance(content, bytes) else content
        import re
        match = re.search(r'<!-- PIXELART_METADATA:(.+?) -->', content_str, re.DOTALL)
        if match:
            meta_json = match.group(1)
            meta = json.loads(meta_json)
            colors = meta.get('colors')
            rows = meta.get('rows')
            cols = meta.get('cols')
            
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
    except Exception as e:
        print(f'注释解析失败: {str(e)}')
    
    # 兼容旧版本：尝试XML元素解析
    try:
        root = ET.fromstring(content)
    except Exception:
        return jsonify({'error': 'SVG 解析失败'}), 400

    # 查找 desc 元素中的 metadata
    desc_node = root.find('.//{*}desc[@id="pixelart-metadata"]')
    if desc_node is None:
        # 兼容旧版本的 metadata 元素
        desc_node = root.find('.//{*}metadata')
    
    if desc_node is None or not (desc_node.text and desc_node.text.strip()):
        return jsonify({'error': 'SVG 缺少可导入的 metadata'}), 400

    try:
        meta = json.loads(desc_node.text.strip())
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


@app.route('/api/all_colors', methods=['GET'])
def get_all_colors():
    """获取所有拼豆色号列表"""
    try:
        mapper = get_color_mapper()
        colors = []
        
        for code, rgb in mapper.color_map.items():
            r, g, b = rgb
            hex_color = rgb_to_hex(r, g, b)
            colors.append({
                'code': code,
                'hex': hex_color,
                'rgb': list(rgb)
            })
        
        # 按色号排序
        colors.sort(key=lambda x: x['code'])
        
        return jsonify({
            'success': True,
            'colors': colors,
            'total': len(colors)
        })
    except Exception as e:
        print(f"获取色号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/find_color', methods=['POST'])
def find_color():
    """查找单个颜色的最接近色号"""
    try:
        data = request.get_json()
        rgb = tuple(data.get('rgb', [0, 0, 0]))
        selected_colors = data.get('selected_colors', [])
        
        mapper = get_color_mapper()
        
        # 如果没有选中的色号，使用所有色号
        if not selected_colors:
            selected_colors = None
        
        # 获取 Top 3 结果
        top_3 = mapper.find_closest_color(rgb, top_n=3, allowed_colors=selected_colors)
        best_match = top_3[0]
        code, mapped_rgb, delta_e = best_match
        
        # 转换 top_3 为前端格式
        top_3_formatted = []
        for c, rgb_val, de in top_3:
            r, g, b = rgb_val
            top_3_formatted.append({
                'code': c,
                'rgb': rgb_val,
                'hex': rgb_to_hex(r, g, b),
                'delta_e': round(de, 2)
            })
        
        r, g, b = mapped_rgb
        return jsonify({
            'success': True,
            'code': code,
            'mapped_rgb': mapped_rgb,
            'mapped_hex': rgb_to_hex(r, g, b),
            'delta_e': round(delta_e, 2),
            'top_3': top_3_formatted
        })
    except Exception as e:
        print(f"查找颜色失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🎮 拼豆像素画识别器启动中...")
    print("🌟 打开浏览器访问: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
