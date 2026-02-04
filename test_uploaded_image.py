"""
测试上传的拼豆图纸
"""

from perler_bead_detector import PerlerBeadDetector
import os
import sys


def test_uploaded_image(image_path='蘑菇豆.png'):
    """测试上传的图片"""
    
    if not os.path.exists(image_path):
        print(f"❌ 找不到图片: {image_path}")
        print(f"\n请将图片保存为 '{image_path}' 并放在当前目录")
        return False
    
    print("=" * 60)
    print("测试拼豆图纸识别")
    print("=" * 60)
    print(f"图片: {image_path}\n")
    
    try:
        # 创建检测器
        detector = PerlerBeadDetector(
            min_grid_size=5,   # 降低最小网格大小以适应更密集的网格
            max_grid_size=100
        )
        
        # 处理图片（开启调试模式）
        print("🔍 开始检测...")
        result = detector.process_image(image_path, debug=False)
        
        print(f"\n✅ 检测成功！")
        print(f"   网格大小: {result['rows']} 行 x {result['cols']} 列")
        print(f"   总方格数: {result['rows'] * result['cols']}")
        
        # 保存结果
        print(f"\n📐 生成 SVG 矢量图...")
        detector.save_svg(result, 'uploaded_result.svg', cell_size=15, grid_width=1.5)
        
        print(f"\n🎨 分析颜色...")
        color_counts = detector.save_color_palette(result, 'uploaded_colors.txt')
        print(f"   检测到 {len(color_counts)} 种不同的颜色")
        
        # 显示最常用的颜色
        print(f"\n   最常用的 5 种颜色:")
        for idx, (color, count) in enumerate(color_counts.most_common(5), 1):
            r, g, b = color
            percentage = count / (result['rows'] * result['cols']) * 100
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            print(f"   {idx}. RGB({r:3d}, {g:3d}, {b:3d}) {hex_color} - {count:3d} 格 ({percentage:.1f}%)")
        
        print(f"\n📊 生成可视化对比图...")
        detector.visualize_result(image_path, result, 'uploaded_comparison.png')
        
        print("\n" + "=" * 60)
        print("✨ 处理完成！生成文件:")
        print("=" * 60)
        print(f"📄 uploaded_result.svg - SVG矢量图")
        print(f"📄 uploaded_colors.txt - 颜色调色板")
        print(f"📄 uploaded_comparison.png - 对比图")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 检测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 可能的原因:")
        print("   - 网格线不够清晰")
        print("   - 图片分辨率太低")
        print("   - 需要调整检测参数")
        
        return False


if __name__ == '__main__':
    # 如果命令行提供了图片路径，使用该路径
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = '蘑菇豆.png'
    
    test_uploaded_image(image_path)
