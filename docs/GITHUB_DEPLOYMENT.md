# GitHub 部署指南

本文档说明如何将 PixelArt 项目推送到 GitHub。

## 前置条件

1. **GitHub 账户**: 拥有有效的 GitHub 账户
2. **Git 配置**: 已安装并配置好 git
3. **SSH 密钥**（推荐）或 HTTPS 凭证

## 步骤

### 1. 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 `+` → `New repository`
3. 填写仓库信息：
   - **Repository name**: `PixelArt`
   - **Description**: `自动识别拼豆图纸的网格线和颜色，输出为矢量图 SVG`
   - **Public/Private**: 选择 `Public`（推荐公开）
   - **Initialize**: 勾选 `Add a README file`（可选，我们已有）

4. 点击 `Create repository`

### 2. 添加远程仓库

```bash
cd /Users/niubei/项目/PixelArt

# 使用 HTTPS（推荐初学者）
git remote add origin https://github.com/yourusername/PixelArt.git

# 或使用 SSH（需要配置 SSH 密钥）
git remote add origin git@github.com:yourusername/PixelArt.git
```

**注意**: 将 `yourusername` 替换为你的 GitHub 用户名

### 3. 验证远程配置

```bash
git remote -v
```

输出应该显示：
```
origin  https://github.com/yourusername/PixelArt.git (fetch)
origin  https://github.com/yourusername/PixelArt.git (push)
```

### 4. 推送代码

```bash
# 推送 main 分支
git push -u origin main

# 推送所有标签（如果有）
git push origin --tags
```

### 5. 验证推送成功

访问 `https://github.com/yourusername/PixelArt` 检查代码是否已上传。

## 配置 GitHub 仓库设置

### 通用设置

1. **Repository Settings** → **General**
   - 确保主分支是 `main`
   - 启用 `Discussions`（可选）
   - 启用 `Projects`（可选）

### 分支保护规则

1. **Settings** → **Branches**
2. 点击 `Add rule`
3. **Branch name pattern**: `main`
4. 勾选：
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Dismiss stale pull request approvals when new commits are pushed

### 启用 GitHub Pages（可选）

1. **Settings** → **Pages**
2. **Source**: 选择 `Deploy from a branch`
3. **Branch**: 选择 `main` 和 `/docs`
4. 点击 `Save`

### 配置 Actions（CI/CD）

1. **Actions** → **General**
2. 确保 `Read and write permissions` 已启用
3. 配置 **Required status checks**

## 添加项目标题和描述

1. **Settings** → **General**
2. 在顶部的 `About` 部分点击 ⚙️
3. 填写：
   - **Description**: 项目简介
   - **Website**: 官方网站（如有）
   - **Topics**: 添加标签（如 `image-processing`, `python`, `opencv`）

## 配置 Secret（可选，用于自动发布）

如果要启用自动发布到 PyPI：

1. **Settings** → **Secrets and variables** → **Actions**
2. 点击 `New repository secret`
3. **Name**: `PYPI_API_TOKEN`
4. **Secret**: 粘贴你的 PyPI API Token

获取 PyPI Token：
- 登录 [PyPI](https://pypi.org)
- 点击用户名 → `Account settings`
- 左侧菜单 → `API tokens`
- 点击 `Add API token`
- 复制 token

## 创建 Release（发布版本）

1. 在项目页面点击 **Releases**
2. 点击 **Create a new release**
3. **Tag version**: `v2.0.0`
4. **Release title**: `v2.0.0 - Project Restructure & Documentation`
5. **Description**: 
   ```
   ## Changes
   - Project structure reorganization
   - Comprehensive documentation
   - GitHub Actions CI/CD
   - Professional configurations
   
   See [CHANGELOG.md](CHANGELOG.md) for full details.
   ```
6. 如果部署到 PyPI，勾选 `Set as the latest release`
7. 点击 `Publish release`

## 常见问题

### 问题 1: Permission denied (publickey)
**解决**: 配置 SSH 密钥或使用 HTTPS

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
cat ~/.ssh/id_ed25519.pub
# 复制输出，在 GitHub 上传
```

### 问题 2: fatal: 'origin' does not appear to be a git repository
**解决**: 添加远程仓库

```bash
git remote add origin https://github.com/yourusername/PixelArt.git
```

### 问题 3: error: failed to push some refs
**解决**: 拉取远程更改

```bash
git pull origin main --rebase
git push origin main
```

## 后续步骤

1. ✅ 代码推送到 GitHub
2. ✅ 配置 GitHub Pages 文档
3. ✅ 启用 GitHub Actions
4. ✅ 创建 Release
5. ⏳ 发布到 PyPI
6. ⏳ 宣传和获取反馈

## 相关资源

- [GitHub 文档](https://docs.github.com)
- [Git 学习指南](https://git-scm.com/book/zh/v2)
- [开源指南](https://opensource.guide/zh-Hans/)

## 许可证

MIT - 详见 [LICENSE](LICENSE)
