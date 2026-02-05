// ============ 全局变量 ============
let currentData = null;
let selectedColor = null;
let canvas = null;
let ctx = null;
const CELL_SIZE = 12;
let editMode = false;
let cropMode = false;
let isCropping = false;
let cropStart = null;
let cropEnd = null;
let originalImageUrl = null;

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
    canvas = document.getElementById('pixelCanvas');
    ctx = canvas.getContext('2d');
    
    // 禁用抗锯齿，保持像素风格
    ctx.imageSmoothingEnabled = false;
    
    // 文件选择事件
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);

    // 编辑模式按钮
    bindEditModeButton();
    updateEditModeUI();

    // 裁剪模式按钮
    bindCropModeButton();
    updateCropModeUI();

    // SVG 导入导出按钮
    bindSvgButtons();
    
    // 原图预览折叠按钮
    bindPreviewToggle();
    
    // 画布点击事件
    canvas.addEventListener('click', handleCanvasClick);
    // 裁剪拖拽事件
    canvas.addEventListener('mousedown', handleCropMouseDown);
    canvas.addEventListener('mousemove', handleCropMouseMove);
    canvas.addEventListener('mouseup', handleCropMouseUp);
    canvas.addEventListener('mouseleave', handleCropMouseLeave);
});

// ============ 文件选择处理 ============
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 保存原图 URL
    originalImageUrl = URL.createObjectURL(file);
    
    // 显示加载动画
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('resultSection').style.display = 'none';
    
    // 上传文件
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentData = data;
            displayResult(data);
        } else {
            alert('❌ 处理失败: ' + (data.error || '未知错误'));
            resetUpload();
        }
    } catch (error) {
        console.error('上传错误:', error);
        alert('❌ 上传失败: ' + error.message);
        resetUpload();
    }
}

// ============ 显示识别结果 ============
function displayResult(data) {
    // 隐藏加载，显示结果
    document.getElementById('loading').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';
    
    // 更新信息栏
    document.getElementById('gridSize').textContent = `${data.rows} × ${data.cols}`;
    document.getElementById('colorCount').textContent = `${data.totalColors}`;
    
    // 重置选择
    clearSelection();
    editMode = false;
    updateEditModeUI();
    cropMode = false;
    updateCropModeUI();
    
    // 重新绑定编辑/裁剪/SVG按钮（防止动态渲染导致事件丢失）
    bindEditModeButton();
    bindCropModeButton();
    bindSvgButtons();

    // 绘制画布
    drawCanvas(data);
    
    // 显示色号统计
    displayColorStats(data);
    
    // 平滑滚动到画布区域
    setTimeout(() => {
        document.querySelector('.canvas-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// ============ 绘制画布 ============
function drawCanvas(data) {
    const { rows, cols, colors } = data;
    
    // 设置画布大小
    canvas.width = cols * CELL_SIZE;
    canvas.height = rows * CELL_SIZE;
    
    // 绘制每个格子
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const color = colors[i][j];
            drawCell(i, j, color, false);
        }
    }
    
    // 绘制网格线
    drawGrid(rows, cols);
}

// ============ 绘制单个格子 ============
function drawCell(row, col, color, isDimmed = false) {
    const x = col * CELL_SIZE;
    const y = row * CELL_SIZE;
    
    // 填充颜色 - 确保是有效的hex格式
    ctx.fillStyle = color;
    ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE);
    
    // 如果是暗化状态
    if (isDimmed) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE);
    }
    
    // 高亮边框
    if (selectedColor && color === selectedColor) {
        ctx.strokeStyle = 'rgba(255, 107, 53, 0.9)';
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 0.5, y + 0.5, CELL_SIZE - 1, CELL_SIZE - 1);
    }
}

// ============ 绘制网格线 ============
function drawGrid(rows, cols) {
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 0.5;
    
    // 垂直线
    for (let i = 0; i <= cols; i++) {
        ctx.beginPath();
        ctx.moveTo(i * CELL_SIZE, 0);
        ctx.lineTo(i * CELL_SIZE, rows * CELL_SIZE);
        ctx.stroke();
    }
    
    // 水平线
    for (let i = 0; i <= rows; i++) {
        ctx.beginPath();
        ctx.moveTo(0, i * CELL_SIZE);
        ctx.lineTo(cols * CELL_SIZE, i * CELL_SIZE);
        ctx.stroke();
    }
}

// ============ 画布点击处理 ============
function handleCanvasClick(event) {
    if (!currentData) return;
    if (cropMode) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    const col = Math.floor(x / CELL_SIZE);
    const row = Math.floor(y / CELL_SIZE);
    
    if (row >= 0 && row < currentData.rows && col >= 0 && col < currentData.cols) {
        const clickedColor = currentData.colors[row][col];
        if (editMode && selectedColor) {
            applyColorToCell(row, col, selectedColor);
        } else {
            selectColor(clickedColor);
        }
    }
}

// ============ 编辑模式切换 ============
function toggleEditMode() {
    editMode = !editMode;
    if (editMode) {
        cropMode = false;
        updateCropModeUI();
    }
    updateEditModeUI();
}

window.toggleEditMode = toggleEditMode;

function bindEditModeButton() {
    const editBtn = document.getElementById('editModeBtn');
    if (!editBtn) return;
    editBtn.onclick = (event) => {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        toggleEditMode();
    };
}

// ============ 裁剪模式切换 ============
function toggleCropMode() {
    cropMode = !cropMode;
    if (cropMode) {
        editMode = false;
        updateEditModeUI();
    }
    resetCropSelection();
    updateCropModeUI();
}

window.toggleCropMode = toggleCropMode;

function bindCropModeButton() {
    const cropBtn = document.getElementById('cropModeBtn');
    if (!cropBtn) return;
    cropBtn.onclick = (event) => {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        toggleCropMode();
    };
}

// ============ SVG 导入导出 ==========
function bindSvgButtons() {
    const saveBtn = document.getElementById('saveSvgBtn');
    const importBtn = document.getElementById('importSvgBtn');
    const svgInput = document.getElementById('svgInput');

    if (saveBtn) {
        saveBtn.onclick = (event) => {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }
            handleSaveSvg();
        };
    }

    if (importBtn && svgInput) {
        importBtn.onclick = (event) => {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }
            svgInput.click();
        };
    }

    if (svgInput) {
        svgInput.onchange = handleImportSvgChange;
    }
}

async function handleSaveSvg() {
    if (!currentData) return;

    try {
        const response = await fetch('/export_svg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rows: currentData.rows,
                cols: currentData.cols,
                colors: currentData.colors,
                cellSize: CELL_SIZE
            })
        });

        if (!response.ok) {
            throw new Error('导出失败');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `pixelart_${currentData.rows}x${currentData.cols}.svg`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('❌ 导出失败: ' + error.message);
    }
}

async function handleImportSvgChange(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/import_svg', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentData = data;
            displayResult(data);
        } else {
            alert('❌ 导入失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        alert('❌ 导入失败: ' + error.message);
    } finally {
        event.target.value = '';
    }
}

function updateCropModeUI() {
    const cropBtn = document.getElementById('cropModeBtn');
    const hint = document.getElementById('cropHint');
    if (cropBtn) {
        cropBtn.textContent = cropMode ? 'Crop Mode: ON' : 'Crop Mode: OFF';
        cropBtn.classList.toggle('active', cropMode);
    }
    if (hint) {
        hint.style.display = cropMode ? 'block' : 'none';
    }
}

function resetCropSelection() {
    isCropping = false;
    cropStart = null;
    cropEnd = null;
    if (currentData) {
        redrawWithHighlight();
    }
}

// ============ 原图预览折叠 ============
function bindPreviewToggle() {
    const toggleBtn = document.getElementById('togglePreview');
    if (toggleBtn) {
        toggleBtn.onclick = () => {
            const content = document.getElementById('previewContent');
            if (content) {
                content.classList.toggle('collapsed');
                toggleBtn.textContent = content.classList.contains('collapsed') ? '+' : '−';
            }
        };
    }
}

function handleCropMouseDown(event) {
    if (!cropMode || !currentData) return;
    const { row, col } = getCellFromEvent(event);
    if (row === null || col === null) return;
    isCropping = true;
    cropStart = { row, col };
    cropEnd = { row, col };
    redrawWithCropOverlay();
}

function handleCropMouseMove(event) {
    if (!cropMode || !isCropping || !currentData) return;
    const { row, col } = getCellFromEvent(event);
    if (row === null || col === null) return;
    cropEnd = { row, col };
    redrawWithCropOverlay();
}

function handleCropMouseUp() {
    if (!cropMode || !isCropping || !currentData) return;
    isCropping = false;
    applyCropSelection();
}

function handleCropMouseLeave() {
    if (!cropMode || !isCropping) return;
    isCropping = false;
    redrawWithCropOverlay();
}

function getCellFromEvent(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const col = Math.floor(x / CELL_SIZE);
    const row = Math.floor(y / CELL_SIZE);
    if (!currentData || row < 0 || col < 0 || row >= currentData.rows || col >= currentData.cols) {
        return { row: null, col: null };
    }
    return { row, col };
}

function redrawWithCropOverlay() {
    redrawWithHighlight();
    if (!cropStart || !cropEnd) return;
    const minRow = Math.min(cropStart.row, cropEnd.row);
    const maxRow = Math.max(cropStart.row, cropEnd.row);
    const minCol = Math.min(cropStart.col, cropEnd.col);
    const maxCol = Math.max(cropStart.col, cropEnd.col);

    const x = minCol * CELL_SIZE;
    const y = minRow * CELL_SIZE;
    const w = (maxCol - minCol + 1) * CELL_SIZE;
    const h = (maxRow - minRow + 1) * CELL_SIZE;

    ctx.save();
    ctx.fillStyle = 'rgba(255, 215, 0, 0.2)';
    ctx.strokeStyle = 'rgba(255, 165, 0, 0.9)';
    ctx.lineWidth = 2;
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    ctx.restore();
}

function applyCropSelection() {
    if (!cropStart || !cropEnd) return;
    const minRow = Math.min(cropStart.row, cropEnd.row);
    const maxRow = Math.max(cropStart.row, cropEnd.row);
    const minCol = Math.min(cropStart.col, cropEnd.col);
    const maxCol = Math.max(cropStart.col, cropEnd.col);

    const newColors = [];
    for (let r = minRow; r <= maxRow; r++) {
        const newRow = currentData.colors[r].slice(minCol, maxCol + 1);
        newColors.push(newRow);
    }

    currentData.colors = newColors;
    currentData.rows = newColors.length;
    currentData.cols = newColors[0]?.length || 0;

    rebuildColorStatsFromGrid();
    resetCropSelection();
    drawCanvas(currentData);
    displayColorStats(currentData);
    document.getElementById('gridSize').textContent = `${currentData.rows} × ${currentData.cols}`;
    document.getElementById('colorCount').textContent = `${currentData.totalColors}`;
}

function rebuildColorStatsFromGrid() {
    const stats = {};
    for (let r = 0; r < currentData.rows; r++) {
        for (let c = 0; c < currentData.cols; c++) {
            const color = currentData.colors[r][c];
            if (stats[color]) {
                stats[color].count += 1;
            } else {
                stats[color] = {
                    rgb: hexToRgbString(color),
                    count: 1
                };
            }
        }
    }
    currentData.colorStats = stats;
    currentData.totalColors = Object.keys(stats).length;
}

function updateEditModeUI() {
    const editBtn = document.getElementById('editModeBtn');
    if (!editBtn) return;
    editBtn.textContent = editMode ? 'Edit Mode: ON' : 'Edit Mode: OFF';
    editBtn.classList.toggle('active', editMode);
}

// ============ 应用颜色到单元格 ============
function applyColorToCell(row, col, newColor) {
    const oldColor = currentData.colors[row][col];
    if (oldColor === newColor) return;

    currentData.colors[row][col] = newColor;
    updateColorStatsData(oldColor, newColor);
    redrawWithHighlight();
}

function updateColorStatsData(oldColor, newColor) {
    const stats = currentData.colorStats || {};

    if (stats[oldColor]) {
        stats[oldColor].count -= 1;
        if (stats[oldColor].count <= 0) {
            delete stats[oldColor];
        }
    }

    if (stats[newColor]) {
        stats[newColor].count += 1;
    } else {
        stats[newColor] = {
            rgb: hexToRgbString(newColor),
            count: 1
        };
    }

    currentData.colorStats = stats;
    currentData.totalColors = Object.keys(stats).length;
    document.getElementById('colorCount').textContent = `${currentData.totalColors}`;

    displayColorStats(currentData);
    updateColorStatsSelection(selectedColor);
}

function hexToRgbString(hex) {
    const cleaned = hex.replace('#', '');
    const r = parseInt(cleaned.substring(0, 2), 16);
    const g = parseInt(cleaned.substring(2, 4), 16);
    const b = parseInt(cleaned.substring(4, 6), 16);
    return `RGB(${r},${g},${b})`;
}

// ============ 颜色选择 ============
function selectColor(color) {
    if (selectedColor === color) {
        // 取消选择
        clearSelection();
        return;
    }
    
    selectedColor = color;
    
    // 重新绘制画布（高亮选中颜色）
    redrawWithHighlight();
    
    // 更新工具栏显示
    updateToolbarSelection(color);
    
    // 更新色号统计的选中状态
    updateColorStatsSelection(color);
}

// ============ 重新绘制画布（带高亮）============
function redrawWithHighlight() {
    const { rows, cols, colors } = currentData;
    
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const color = colors[i][j];
            const isDimmed = selectedColor && color !== selectedColor;
            drawCell(i, j, color, isDimmed);
        }
    }
    
    drawGrid(rows, cols);
}

// ============ 更新工具栏选中状态 ============
function updateToolbarSelection(color) {
    const badge = document.getElementById('selectedColorBadge');
    const colorDot = document.getElementById('colorDot');
    const colorText = document.getElementById('selectedColorText');
    
    if (color) {
        colorDot.style.backgroundColor = color;
        colorText.textContent = color.toUpperCase();
        badge.style.display = 'inline-flex';
    } else {
        badge.style.display = 'none';
    }
}

// ============ 清除选择 ============
function clearSelection() {
    selectedColor = null;
    
    if (currentData) {
        drawCanvas(currentData);
    }
    
    updateToolbarSelection(null);
    updateColorStatsSelection(null);
}

// ============ 显示色号统计 ============
function displayColorStats(data) {
    const container = document.getElementById('colorStatsList');
    container.innerHTML = '';
    
    // 按数量排序
    const sortedColors = Object.entries(data.colorStats).sort((a, b) => {
        return b[1].count - a[1].count;
    });
    
    sortedColors.forEach(([hexColor, info]) => {
        const item = document.createElement('div');
        item.className = 'color-item';
        item.dataset.color = hexColor;
        
        const swatch = document.createElement('div');
        swatch.className = 'color-swatch';
        swatch.style.backgroundColor = hexColor;
        
        const info_div = document.createElement('div');
        info_div.className = 'color-info';
        
        const hex = document.createElement('div');
        hex.className = 'color-hex';
        hex.textContent = hexColor.toUpperCase();
        
        const count = document.createElement('div');
        count.className = 'color-count';
        count.textContent = `${info.count} pixels`;
        
        info_div.appendChild(hex);
        info_div.appendChild(count);
        
        item.appendChild(swatch);
        item.appendChild(info_div);
        
        // 点击选择
        item.addEventListener('click', () => {
            selectColor(hexColor);
        });
        
        // 悬停效果
        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateX(4px)';
        });
        
        item.addEventListener('mouseleave', () => {
            item.style.transform = 'translateX(0)';
        });
        
        container.appendChild(item);
    });
}

// ============ 更新色号统计选中状态 ============
function updateColorStatsSelection(color) {
    const items = document.querySelectorAll('.color-item');
    items.forEach(item => {
        if (item.dataset.color === color) {
            item.classList.add('active');
            item.classList.remove('dimmed');
        } else if (color) {
            item.classList.remove('active');
            item.classList.add('dimmed');
        } else {
            item.classList.remove('active');
            item.classList.remove('dimmed');
        }
    });
}

// ============ 重置上传 ============
function resetUpload() {
    currentData = null;
    selectedColor = null;
    editMode = false;
    updateEditModeUI();
    cropMode = false;
    updateCropModeUI();
    
    if (originalImageUrl) {
        URL.revokeObjectURL(originalImageUrl);
        originalImageUrl = null;
    }
    
    document.getElementById('uploadSection').style.display = 'flex';
    document.getElementById('loading').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('fileInput').value = '';
    const svgInput = document.getElementById('svgInput');
    if (svgInput) svgInput.value = '';
    
    const originalPreview = document.getElementById('originalPreview');
    if (originalPreview) originalPreview.style.display = 'none';
}
