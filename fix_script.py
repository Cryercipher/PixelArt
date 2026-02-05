#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 读取文件
with open('web/static/script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修改 1: 将 handleCanvasClick 改为 async
for i, line in enumerate(lines):
    if 'function handleCanvasClick(event) {' in line:
        lines[i] = line.replace('function handleCanvasClick(event) {', 'async function handleCanvasClick(event) {')
        print(f"✓ 修改 1: 第{i+1}行 - 将 handleCanvasClick 改为 async")
        break

# 修改 2: 删除 DOMContentLoaded 末尾的按钮绑定代码
in_delete_section = False
delete_start = None
for i, line in enumerate(lines):
    if '// 初始化库存管理按钮' in line:
        delete_start = i
        in_delete_section = True
    elif in_delete_section and '});' in line and i > 0 and 'selectAllBtn' not in lines[i-1]:
        # 找到了要删除的区域的结束
        del lines[delete_start:i]
        print(f"✓ 修改 2: 删除第{delete_start+1}-{i}行的按钮绑定代码")
        break

# 修改 3: 在 loadInventoryPage 末尾添加按钮绑定
for i in range(len(lines)-1, -1, -1):
    line = lines[i]
    if 'renderInventoryGrid();' in line and i+1 < len(lines) and 'updateSelectedCount();' in lines[i+1]:
        # 找到 loadInventoryPage 的这两行
        indent = '    '
        insert_pos = i + 2
        new_code = f'''{indent}
{indent}// 绑定按钮事件
{indent}const selectAllBtn = document.getElementById('selectAllBtn');
{indent}const deselectAllBtn = document.getElementById('deselectAllBtn');
{indent}
{indent}if (selectAllBtn) {{
{indent}    selectAllBtn.removeEventListener('click', selectAllColors);
{indent}    selectAllBtn.addEventListener('click', selectAllColors);
{indent}}}
{indent}if (deselectAllBtn) {{
{indent}    deselectAllBtn.removeEventListener('click', deselectAllColors);
{indent}    deselectAllBtn.addEventListener('click', deselectAllColors);
{indent}}}
'''
        lines.insert(insert_pos, new_code)
        print(f"✓ 修改 3: 在第{insert_pos+1}行插入按钮绑定代码")
        break

# 写回文件
with open('web/static/script.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ 所有修改已完成！")
