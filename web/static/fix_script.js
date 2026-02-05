// 临时修复脚本 - 手动应用这三处修改：

// 1. 修改第 315 行（在 "// ============ 画布点击处理 ============" 之后）
// 从: function handleCanvasClick(event) {
// 到: async function handleCanvasClick(event) {

// 2. 删除第 100-109 行（在 DOMContentLoaded 监听器末尾，tab切换代码之后）
// 删除这段：
//     // 初始化库存管理按钮
//     const selectAllBtn = document.getElementById('selectAllBtn');
//     const deselectAllBtn = document.getElementById('deselectAllBtn');
//     
//     if (selectAllBtn) {
//         selectAllBtn.addEventListener('click', selectAllColors);
//     }
//     if (deselectAllBtn) {
//         deselectAllBtn.addEventListener('click', deselectAllColors);
//     }

// 3. 在第 1399 行（loadInventoryPage 函数末尾）添加：
//     renderInventoryGrid();
//     updateSelectedCount();
//     
//     // 绑定按钮事件
//     const selectAllBtn = document.getElementById('selectAllBtn');
//     const deselectAllBtn = document.getElementById('deselectAllBtn');
//     
//     if (selectAllBtn) {
//         selectAllBtn.removeEventListener('click', selectAllColors);
//         selectAllBtn.addEventListener('click', selectAllColors);
//     }
//     if (deselectAllBtn) {
//         deselectAllBtn.removeEventListener('click', deselectAllColors);
//         deselectAllBtn.addEventListener('click', deselectAllColors);
//     }
// }
