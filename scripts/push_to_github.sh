#!/bin/bash

# PixelArt GitHub 推送脚本
# 用于自动化 GitHub 仓库配置和代码推送

set -e

echo "======================================"
echo "  PixelArt - GitHub 推送工具"
echo "======================================"
echo ""

# 检查是否是 git 仓库
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是 git 仓库"
    exit 1
fi

# 获取 GitHub 用户名和仓库名
echo "📝 请输入你的 GitHub 信息："
echo ""
read -p "GitHub 用户名 (如: johnsmith): " GITHUB_USER
read -p "仓库名 (默认: PixelArt): " REPO_NAME
REPO_NAME=${REPO_NAME:-PixelArt}

# 选择连接方式
echo ""
echo "🔐 选择连接方式："
echo "1) HTTPS (推荐初学者)"
echo "2) SSH (需要配置 SSH 密钥)"
read -p "请选择 [1/2]: " CONNECT_TYPE
CONNECT_TYPE=${CONNECT_TYPE:-1}

# 构造远程仓库 URL
if [ "$CONNECT_TYPE" = "2" ]; then
    REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
    echo "⚠️  使用 SSH，确保已配置 SSH 密钥"
else
    REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    echo "✓ 使用 HTTPS"
fi

echo ""
echo "🔗 远程仓库: $REMOTE_URL"
echo ""

# 检查是否已有 origin 远程
if git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  检测到已有 origin 远程"
    read -p "是否要覆盖? (y/n): " OVERWRITE
    if [ "$OVERWRITE" = "y" ] || [ "$OVERWRITE" = "Y" ]; then
        git remote remove origin
        echo "✓ 已删除旧的 origin"
    else
        echo "❌ 取消操作"
        exit 1
    fi
fi

# 添加远程仓库
echo ""
echo "📦 配置远程仓库..."
git remote add origin "$REMOTE_URL"
echo "✓ 远程仓库已添加"

# 验证配置
echo ""
echo "🔍 验证配置..."
git remote -v

# 推送代码
echo ""
echo "📤 正在推送代码到 GitHub..."
git push -u origin main
echo "✓ 代码推送成功！"

# 推送标签
echo ""
echo "🏷️  正在推送标签..."
if git tag | grep -q .; then
    git push origin --tags
    echo "✓ 标签推送成功"
else
    echo "ℹ️  没有找到标签"
fi

# 显示完成信息
echo ""
echo "======================================"
echo "  ✨ 推送完成！"
echo "======================================"
echo ""
echo "📍 仓库地址: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "👉 接下来的步骤:"
echo "   1. 访问上述链接检查代码"
echo "   2. 在 GitHub 仓库设置中添加项目描述和主题"
echo "   3. （可选）配置 PyPI 发布令牌（docs/GITHUB_DEPLOYMENT.md）"
echo "   4. （可选）启用 GitHub Pages 文档"
echo ""
echo "📚 查看部署指南: docs/GITHUB_DEPLOYMENT.md"
echo ""
