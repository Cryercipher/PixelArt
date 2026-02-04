"""
拼豆图纸识别工具 - 快速开始示例

演示如何使用 PerlerBeadDetector 处理拼豆图纸
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import PerlerBeadDetector


def main():
    """主函数"""
    
    print("=" * 60)
    print("拼豆图纸识别工具 - 快速开始")
    print("=" * 60)
    
    # 1. 创建检测器
    print("\n📝 创建检测器...")
    detector = PerlerBeadDetector(
        min_grid_size=10,
        max_grid_size=100
    )
    
    # 2. 设置路径
    input_image = 'input.jpg'
    output_svg = 'output.svg'
    output_palette = 'color_palette.txt'
    output_visualization = 'result.png'
    
    if not os.path.exists(input_image):
        print(f"\n❌ 错误：找不到输入图片 '{input_image}'")
        print("\n使用方法：")
        print("  1. 将你的拼豆图纸图片放在项目根目录")
        print("  2. 命名为 'input.jpg'")
        return
    
    try:
        # 3. 处理图片
        print(f"\n🔍 正在处理图片: {input_image}")
        print("-" * 60)
        
        result = detector.process_image(input_image, debug=False)
        
        print(f"\n✅ 检测完成！")
        print(f"   网格大小: {result['rows']} 行 × {result['cols']} 列")
        print(f"   总计: {result['rows'] * result['cols']} 个方格")
        
        # 4. 保存结果
        print(f"\n📐 生成 SVG 矢量图...")
        detector.save_svg(result, output_svg, cell_size=20, grid_width=1.5)
        
        print(f"\n🎨 分析颜色调色板...")
        color_counts = detector.save_color_palette(result, output_palette)
        
        print(f"\n📊 生成可视化对比图...")
        detector.visualize_result(input_image, result, output_visualization)
        
        # 5. 显示摘要
        print("\n" + "=" * 60)
        print("✨ 处理完成！")
        print("=" * 60)
        print(f"📄 {output_svg}")
        print(f"📄 {output_palette}")
        print(f"📄 {output_visualization}")
        print("=" * 60)
        
        # 6. 颜色统计
        print(f"\n🎨 颜色统计：")
        print(f"   共 {len(color_counts)} 种颜色\n")
        print(f"   最常用的 5 种：")
        for idx, (color, count) in enumerate(color_counts.most_common(5), 1):
            r, g, b = color
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            pct = count / (result['rows'] * result['cols']) * 100
            print(f"   {idx}. RGB({r:3d}, {g:3d}, {b:3d}) {hex_color} - {pct:5.1f}%")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
