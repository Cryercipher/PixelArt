"""
拼豆图纸识别器 - 使用示例

演示如何使用 PerlerBeadDetector 处理拼豆图纸
"""

from perler_bead_detector import PerlerBeadDetector
import os


def main():
    """主函数"""
    
    # 1. 创建检测器
    print("=" * 60)
    print("拼豆图纸识别工具")
    print("=" * 60)
    
    detector = PerlerBeadDetector(
        min_grid_size=10,   # 最小网格大小
        max_grid_size=100   # 最大网格大小
    )
    
    # 2. 设置输入输出路径
    input_image = 'input.jpg'  # 替换为你的拼豆图纸图片路径
    output_svg = 'output.svg'
    output_palette = 'color_palette.txt'
    output_visualization = 'result.png'
    
    # 检查输入文件是否存在
    if not os.path.exists(input_image):
        print(f"\n❌ 错误：找不到输入图片 '{input_image}'")
        print("\n请将你的拼豆图纸图片命名为 'input.jpg' 并放在当前目录")
        print("或者修改 example.py 中的 input_image 变量")
        
        # 创建一个示例说明文件
        create_sample_guide()
        return
    
    try:
        # 3. 处理图片
        print(f"\n📸 正在处理图片: {input_image}")
        print("-" * 60)
        
        result = detector.process_image(
            input_image, 
            debug=False  # 设置为 True 可以看到调试信息
        )
        
        print(f"\n✅ 检测完成！")
        print(f"   网格大小: {result['rows']} 行 x {result['cols']} 列")
        print(f"   总计: {result['rows'] * result['cols']} 个方格")
        
        # 4. 保存SVG矢量图
        print(f"\n📐 生成SVG矢量图...")
        detector.save_svg(result, output_svg, cell_size=20)
        
        # 5. 保存颜色调色板
        print(f"\n🎨 分析颜色调色板...")
        color_counts = detector.save_color_palette(result, output_palette)
        
        # 6. 可视化对比结果
        print(f"\n📊 生成可视化对比图...")
        detector.visualize_result(input_image, result, output_visualization)
        
        # 7. 显示摘要
        print("\n" + "=" * 60)
        print("✨ 处理完成！生成的文件：")
        print("=" * 60)
        print(f"📄 {output_svg:30s} - SVG矢量图（可在浏览器中打开）")
        print(f"📄 {output_palette:30s} - 颜色调色板")
        print(f"📄 {output_visualization:30s} - 可视化对比图")
        print("=" * 60)
        
        # 8. 显示颜色统计
        print(f"\n🎨 颜色统计：")
        print(f"   共检测到 {len(color_counts)} 种不同的颜色")
        print(f"\n   最常用的5种颜色：")
        for idx, (color, count) in enumerate(color_counts.most_common(5), 1):
            r, g, b = color
            percentage = count / (result['rows'] * result['cols']) * 100
            print(f"   {idx}. RGB({r:3d}, {g:3d}, {b:3d}) - {count:3d} 个方格 ({percentage:.1f}%)")
        
        print("\n💡 提示：")
        print(f"   - 在浏览器中打开 {output_svg} 查看矢量图")
        print(f"   - 查看 {output_palette} 了解所有使用的颜色")
        print(f"   - 查看 {output_visualization} 对比原图和识别结果")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        print("\n可能的原因：")
        print("   1. 图片质量太低，无法识别网格")
        print("   2. 图片中没有明显的网格线")
        print("   3. 图片格式不支持")
        print("\n建议：")
        print("   - 使用清晰的拼豆图纸图片")
        print("   - 确保图片中有明显的网格线")
        print("   - 尝试调整图片亮度和对比度")


def create_sample_guide():
    """创建示例指南"""
    guide_path = 'HOW_TO_USE.txt'
    
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write("""
╔═══════════════════════════════════════════════════════════╗
║           拼豆图纸识别工具 - 使用指南                    ║
╚═══════════════════════════════════════════════════════════╝

📖 快速开始
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  本项目使用 uv 进行 Python 包管理

1. 安装依赖
   uv pip install -r requirements.txt

2. 准备你的拼豆图纸图片
   - 将图片命名为 'input.jpg'
   - 放在项目根目录
   - 或者修改 example.py 中的文件名

3. 运行示例
   python example.py

4. 查看结果
   - output.svg - 矢量图（可缩放）
   - color_palette.txt - 颜色列表
   - result.png - 对比图


📋 支持的图片格式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ JPG/JPEG
✅ PNG
✅ BMP
✅ TIFF


💡 图片要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

理想的拼豆图纸图片应该：

✓ 有清晰的网格线（黑色或深色）
✓ 光照均匀，避免阴影
✓ 分辨率足够（建议 > 800x600）
✓ 每个方格的颜色相对纯净
✓ 图片清晰，不模糊


🔧 高级使用
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

自定义代码示例：

from perler_bead_detector import PerlerBeadDetector

# 创建检测器
detector = PerlerBeadDetector(
    min_grid_size=10,   # 调整最小网格大小
    max_grid_size=100   # 调整最大网格大小
)

# 处理图片（开启调试模式）
result = detector.process_image('my_image.jpg', debug=True)

# 自定义SVG大小
detector.save_svg(result, 'output.svg', cell_size=30)

# 获取颜色统计
colors = detector.save_color_palette(result)


🐛 常见问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: 无法检测到网格？
A: 尝试：
   - 增强图片对比度
   - 确保网格线清晰可见
   - 调整 min_grid_size 和 max_grid_size 参数

Q: 颜色识别不准确？
A: 这个工具使用 K-means 聚类来处理颜色差异
   如果还是不准确，可以：
   - 使用更清晰的图片
   - 确保光照均匀
   - 后期在 SVG 中手动调整

Q: 处理速度慢？
A: 大图片需要更多时间
   建议将图片缩小到合适尺寸（如 2000x2000 以内）


📞 技术支持
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

遇到问题？查看：
- README.md - 项目说明
- perler_bead_detector.py - 源代码注释

""")
    
    print(f"\n📖 已创建使用指南: {guide_path}")
    print("   请阅读该文件了解如何使用本工具")


if __name__ == '__main__':
    main()
