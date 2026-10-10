# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 | 作者 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| claude-code-social-skills | AINightCoder | 未披露（2026-10-11 经 GitHub API 核实：该仓库未声明公开许可，2 stars） | https://github.com/ainightcoder/claude-code-social-skills | 「多平台内容 → 评分 → 发布」链路编排思想，以及其 xhs skill 中"文字卡片确定性生成"的思路；本插件 `/xhs` 命令的端到端流程受其启发，**未复制其任何代码与文案** |
| curriculum（xhs-posters / bootcamp-video skill） | bianbianzhu | 未披露（2026-10-11 经 GitHub API 核实：该仓库未声明公开许可，0 stars） | https://github.com/bianbianzhu/curriculum | 「Canvas 确定性绘制海报/封面」的思路：用精确绘制代替 AI 生图，保证文字与尺寸可控；本插件 `lhg-xhs-cover` 的 Canvas 绘制方法受其启发，**绘制代码为原创** |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则词表、命令流程、封面绘制代码均为独立撰写。
2. **许可合规**：上述两个仓库在核实日（2026-10-11）均未声明公开许可（GitHub API 返回 license 为空）。本插件未复制其任何受版权保护的表达，仅借鉴不受保护的通用方法论思路；如其后续声明许可，本文件将同步更新。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
