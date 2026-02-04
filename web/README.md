# 拼豆像素画 Web 应用

## 启动说明

### 1. 启动服务器

```bash
cd web
python app.py
```

### 2. 打开浏览器

访问: http://localhost:5000

## 功能特点

- 🎨 **星露谷物语像素风格** - 复古游戏美学界面
- 📤 **图片上传识别** - 自动识别拼豆图案网格
- 🎯 **点击高亮** - 点击颜色，高亮所有相同颜色
- 📊 **色号统计** - 实时显示颜色使用统计
- 🖼️ **智能裁剪** - 自动移除白色边界和色卡

## 技术栈

- **后端**: Flask + Python
- **前端**: HTML5 Canvas + Vanilla JavaScript
- **样式**: 像素风格 CSS + Press Start 2P 字体
- **核心**: OpenCV + scikit-learn

## 目录结构

```
web/
├── app.py              # Flask 应用主程序
├── templates/          # HTML 模板
│   └── index.html
├── static/            # 静态资源
│   ├── style.css      # 像素风格样式
│   └── script.js      # 前端交互逻辑
└── uploads/           # 临时上传目录
```
