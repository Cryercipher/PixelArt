# 变更日志（Changelog）

所有本项目值得注意的变更都会记录在本文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [2.0.0] - 2024-02-04

### 新增
- 完整的项目结构重构（src/, examples/, docs/）
- 详细的算法文档（docs/ALGORITHM.md）
- 故障排除指南（docs/TROUBLESHOOT.md）
- 项目结构文档（docs/PROJECT_STRUCTURE.md）
- 贡献指南（CONTRIBUTING.md）
- 行为准则（CODE_OF_CONDUCT.md）
- 安全政策（SECURITY.md）
- GitHub Actions CI/CD 工作流
- Issue 模板和 PR 模板
- PyPI 打包配置（pyproject.toml）
- MIT 开源许可证

### 改进
- 优化 Hough 变换参数（threshold=50, minLineLength=30, maxLineGap=5）
- 增强白色检测算法（brightness + color_range 双条件）
- 改进颜色聚类算法（两阶段合并）
- 优化示例脚本（完整的错误处理和用户提示）
- 完善 .gitignore

### 修复
- 修复网格线检测不完整问题
- 修复白色背景识别的边界情况
- 修复颜色数量过多的聚类问题

### 文档
- 编写 450+ 行的详细 README
- 创建 300+ 行的算法说明文档
- 创建 250+ 行的故障排除指南
- 添加 API 文档和示例

## [1.5.0] - 2024-01-20

### 改进
- 优化 Hough 变换参数以更准确地检测网格线
- 改进颜色识别的边界处理
- 增强对不同图片格式的支持

### 修复
- 修复网格线在某些情况下重复检测的问题

## [1.0.0] - 2024-01-15

### 新增
- 基础的网格线检测功能
- 色彩识别和统计功能
- SVG 矢量图输出
- PNG 对比图生成
- 颜色调色板导出

---

## 版本对比

### v1.0 vs v2.0
| 方面 | v1.0 | v2.0 |
|------|------|------|
| 核心功能 | ✅ | ✅ 优化 |
| 文档 | ⚠️ 基础 | ✅ 完整 |
| 项目结构 | ⚠️ 扁平 | ✅ 规范 |
| 打包配置 | ❌ | ✅ PyPI |
| CI/CD | ❌ | ✅ GitHub Actions |
| 示例 | ⚠️ 简单 | ✅ 完整 |

## 即将推出

### v2.1（计划）
- [ ] 单元测试和集成测试
- [ ] 命令行界面（CLI）
- [ ] 性能基准测试

### v3.0（长期）
- [ ] Web 用户界面
- [ ] 实时处理能力
- [ ] 深度学习模型集成
- [ ] 批量处理功能
- [ ] 国际化支持

## 贡献

欢迎贡献！请查阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT - 详见 [LICENSE](LICENSE)
