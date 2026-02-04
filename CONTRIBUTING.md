# 贡献指南

感谢对 PixelArt 的关注！本指南将帮助您做出有效的贡献。

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/PixelArt.git
cd PixelArt
```

### 2. 创建虚拟环境（使用 uv）

```bash
uv venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows
```

### 3. 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

## 代码风格

- **格式化**: 使用 `black` 格式化代码
  ```bash
  black src/ examples/ tests/
  ```

- **检查**: 使用 `flake8` 检查代码质量
  ```bash
  flake8 src/ examples/ tests/
  ```

- **类型检查**: 使用 `mypy` 验证类型标注
  ```bash
  mypy src/
  ```

## 提交流程

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行更改**
   - 修改代码
   - 更新文档
   - 添加测试（如需要）

3. **格式化和检查**
   ```bash
   black src/
   flake8 src/
   mypy src/
   ```

4. **提交**
   ```bash
   git add .
   git commit -m "feat: 添加功能说明"
   ```

5. **推送和提交 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 添加/修改测试
- `perf:` 性能优化
- `chore:` 其他（依赖更新等）

示例：
```
feat: 添加自动网格优化算法
docs: 更新算法文档
fix: 修复白色背景识别的边界情况
```

## 问题报告

发现 Bug 时，请：

1. 检查是否已有相同的 Issue
2. 提供清晰的问题描述
3. 包含输入图片、代码片段或错误日志
4. 说明预期行为

## 功能请求

建议新功能时：

1. 解释用途
2. 描述实现思路
3. 提供使用示例
4. 讨论潜在的影响

## 测试

如果您添加了新功能，请包含测试：

```python
# tests/test_new_feature.py
import pytest
from src import PerlerBeadDetector

def test_new_feature():
    detector = PerlerBeadDetector()
    # 测试代码
    assert result is not None
```

运行测试：
```bash
pytest
```

## 文档

- 更新 `README.md` 的特性列表
- 在 `docs/ALGORITHM.md` 添加算法细节
- 在 `docs/TROUBLESHOOT.md` 添加故障排除建议

## 许可证

提交代码即表示您同意将其贡献到此项目，并按 MIT 许可证发布。

## 行为准则

本项目遵循开放、包容的社区精神。我们尊重所有贡献者和用户。

## 有疑问？

- 查阅 [文档](README.md)
- 查看 [问题列表](https://github.com/yourusername/PixelArt/issues)
- 提交新 Issue

谢谢您的贡献！🎉
