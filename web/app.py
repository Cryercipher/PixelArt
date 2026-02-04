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
            color_stats = {}
            
            for i in range(rows):
                row = []
                for j in range(cols):
                    # colors 中已经是 RGB 格式（来自 _get_dominant_color 中的 cv2.COLOR_BGR2RGB 转换）
                    r, g, b = colors[i][j]
                    hex_color = rgb_to_hex(r, g, b)
                    row.append(hex_color)
                    
                    # 统计颜色
                    if hex_color in color_stats:
                        color_stats[hex_color]['count'] += 1
                    else:
                        color_stats[hex_color] = {
                            'rgb': f'RGB({r},{g},{b})',
                            'count': 1
                        }
                
                color_grid.append(row)
            
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


@app.route('/static/<path:path>')
def send_static(path):
    """静态文件服务"""
    return send_from_directory('static', path)


if __name__ == '__main__':
    print("🎮 拼豆像素画识别器启动中...")
    print("🌟 打开浏览器访问: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
