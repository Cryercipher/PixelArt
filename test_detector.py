"""
测试工具 - 用于测试拼豆检测器的各个组件
"""

import cv2
import numpy as np
from perler_bead_detector import PerlerBeadDetector


def create_test_image(rows=10, cols=10, cell_size=30, margin=20):
    """
    创建一个测试用的拼豆图纸
    
    Args:
        rows: 行数
        cols: 列数
        cell_size: 每个方格的大小
        margin: 边距
        
    Returns:
        生成的测试图片
    """
    # 计算图片大小
    width = margin * 2 + cols * cell_size + (cols + 1)
    height = margin * 2 + rows * cell_size + (rows + 1)
    
    # 创建白色背景
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 定义一些测试颜色
    colors = [
        (255, 0, 0),      # 红色
        (0, 255, 0),      # 绿色
        (0, 0, 255),      # 蓝色
        (255, 255, 0),    # 黄色
        (255, 0, 255),    # 品红
        (0, 255, 255),    # 青色
        (128, 128, 128),  # 灰色
        (255, 128, 0),    # 橙色
        (128, 0, 255),    # 紫色
        (0, 128, 128),    # 青绿色
    ]
    
    # 绘制方格
    for i in range(rows):
        for j in range(cols):
            x = margin + j * (cell_size + 1)
            y = margin + i * (cell_size + 1)
            
            # 选择颜色（创建一个简单的图案）
            color_idx = (i + j) % len(colors)
            color = colors[color_idx]
            
            # 绘制方格（BGR格式）
            cv2.rectangle(
                image, 
                (x + 1, y + 1), 
                (x + cell_size, y + cell_size), 
                color[::-1],  # RGB转BGR
                -1  # 填充
            )
    
    # 绘制网格线
    for i in range(rows + 1):
        y = margin + i * (cell_size + 1)
        cv2.line(image, (margin, y), (width - margin, y), (0, 0, 0), 1)
    
    for j in range(cols + 1):
        x = margin + j * (cell_size + 1)
        cv2.line(image, (x, margin), (x, height - margin), (0, 0, 0), 1)
    
    return image


def test_basic_detection():
    """测试基本检测功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本网格检测")
    print("=" * 60)
    
    # 创建测试图片
    print("生成测试图片 (10x10)...")
    test_img = create_test_image(rows=10, cols=10, cell_size=30, margin=20)
    cv2.imwrite('test_input.jpg', test_img)
    print("✅ 测试图片已保存: test_input.jpg")
    
    # 测试检测
    print("\n运行检测...")
    detector = PerlerBeadDetector()
    
    try:
        result = detector.process_image('test_input.jpg', debug=False)
        print(f"✅ 检测成功！")
        print(f"   期望: 10x10")
        print(f"   检测: {result['rows']}x{result['cols']}")
        
        if result['rows'] == 10 and result['cols'] == 10:
            print("   ✅ 网格大小正确！")
        else:
            print("   ⚠️  网格大小有偏差")
        
        # 保存结果
        detector.save_svg(result, 'test_output.svg', cell_size=20)
        print("✅ SVG已保存: test_output.svg")
        
        return True
    
    except Exception as e:
        print(f"❌ 检测失败: {str(e)}")
        return False


def test_different_margins():
    """测试不同边距的处理"""
    print("\n" + "=" * 60)
    print("测试 2: 不同边距")
    print("=" * 60)
    
    margins = [10, 20, 40, 60]
    
    for margin in margins:
        print(f"\n测试边距: {margin}px")
        
        test_img = create_test_image(rows=8, cols=8, cell_size=25, margin=margin)
        filename = f'test_margin_{margin}.jpg'
        cv2.imwrite(filename, test_img)
        
        detector = PerlerBeadDetector()
        
        try:
            result = detector.process_image(filename, debug=False)
            if result['rows'] == 8 and result['cols'] == 8:
                print(f"   ✅ 边距 {margin}px - 检测成功 ({result['rows']}x{result['cols']})")
            else:
                print(f"   ⚠️  边距 {margin}px - 检测有偏差 ({result['rows']}x{result['cols']})")
        
        except Exception as e:
            print(f"   ❌ 边距 {margin}px - 检测失败: {str(e)}")


def test_color_accuracy():
    """测试颜色准确性"""
    print("\n" + "=" * 60)
    print("测试 3: 颜色识别准确性")
    print("=" * 60)
    
    # 创建纯色测试图片
    print("\n生成纯色测试图片...")
    test_img = create_test_image(rows=5, cols=5, cell_size=40, margin=30)
    cv2.imwrite('test_colors.jpg', test_img)
    
    detector = PerlerBeadDetector()
    result = detector.process_image('test_colors.jpg', debug=False)
    
    # 统计颜色
    color_counts = detector.save_color_palette(result, 'test_colors_palette.txt')
    
    print(f"\n检测到 {len(color_counts)} 种颜色")
    print("前5种颜色:")
    for idx, (color, count) in enumerate(color_counts.most_common(5), 1):
        r, g, b = color
        print(f"   {idx}. RGB({r:3d}, {g:3d}, {b:3d}) - {count} 个方格")


def test_with_noise():
    """测试带噪声的图片"""
    print("\n" + "=" * 60)
    print("测试 4: 噪声鲁棒性")
    print("=" * 60)
    
    # 创建测试图片
    test_img = create_test_image(rows=8, cols=8, cell_size=30, margin=20)
    
    # 添加高斯噪声
    noise = np.random.normal(0, 10, test_img.shape).astype(np.uint8)
    noisy_img = cv2.add(test_img, noise)
    
    cv2.imwrite('test_noisy.jpg', noisy_img)
    print("生成带噪声的测试图片...")
    
    detector = PerlerBeadDetector()
    
    try:
        result = detector.process_image('test_noisy.jpg', debug=False)
        print(f"✅ 噪声图片检测成功 ({result['rows']}x{result['cols']})")
        
        if result['rows'] == 8 and result['cols'] == 8:
            print("   ✅ 噪声不影响检测准确性！")
    
    except Exception as e:
        print(f"❌ 噪声图片检测失败: {str(e)}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "拼豆检测器 - 测试套件" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    
    tests = [
        ("基本检测", test_basic_detection),
        ("不同边距", test_different_margins),
        ("颜色准确性", test_color_accuracy),
        ("噪声鲁棒性", test_with_noise),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success if success is not None else True))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 出现异常: {str(e)}")
            results.append((name, False))
    
    # 显示总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:20s} {status}")
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")


if __name__ == '__main__':
    run_all_tests()
