<!-- About 简介（推送后填写到仓库 About 栏）：
小红书种草专家：卖点到爆款笔记一键生成 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-xiaohongshu
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, xiaohongshu, marketing, copywriting -->

# lhg-xiaohongshu：小红书种草专家

> **一句话介绍**：给 AI 写作助手装上"小红书种草流水线"——卖点提炼、8 大标题公式、痛点共鸣正文、1242×1660 封面规范、16 条广告法合规审计，小白也能产出可发布的种草笔记。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-xiaohongshu
> /plugin install lhg-xiaohongshu@lhg-plugs
> ```

## 它是什么

`lhg-xiaohongshu` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **3 个命令**（小白入口）：`xhs` 卖点→发布草稿一键生成，`xhs-title` 标题专项批量生成+打分，`xhs-audit` 发文前自检
- **3 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：种草文案、封面图规范、合规自查
- **2 个专家 agent**：种草写手、合规审查
- **2 个硬门 hooks**：发布命令前合规拦截、写笔记后自动提醒（均可一键豁免）
- **16 条确定性审计规则**：极限词 / 标题 / 标签 / 封面尺寸 / 正文 / 营销信号，纯 Python、零第三方依赖，10 秒出结果

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-xiaohongshu:xhs` | 卖点→3 版标题+正文+标签→封面图→合规检测→发布草稿 | `/lhg-xiaohongshu:xhs "99块的去黑头鼻贴"` |
| `/lhg-xiaohongshu:xhs-title` | 8 大标题公式批量生成，按四维打分选最佳 | `/lhg-xiaohongshu:xhs-title "防晒霜"` |
| `/lhg-xiaohongshu:xhs-audit` | 发文前自检（脚本 + 人工复核清单，分级报告） | `/lhg-xiaohongshu:xhs-audit notes/2026-10-11.md` |

## 封面图说明

封面走"确定性绘制"路线：不依赖 AI 生图（中文大字笔画易错），用 HTML Canvas 按 1242×1660 规范精确绘制，所见即所得。`lhg-xhs-cover` skill 第 7 节给出了可直接使用的绘制代码骨架。

## 自查说明

自查 = 确定性脚本（机器）+ 人工复核清单（人）：

1. 先跑 `scripts/audit/xhs_audit.py`（16 条规则），零 LLM 成本；
2. 发现分三级：**blocker**（广告法极限词、封面比例非 3:4，必须清零，发布前 hook 会拦截）、**warning**（标题过长、标签异常、功效断言、联系方式，修或写已知风险理由）、**nit**（顺手修）；
3. 再按 `lhg-xhs-compliance` skill 的人工复核过一遍脚本抓不到的（营销号限流风险、广告标识、功效表述口吻、封面人工看）。

blocker 清零才建议发布；为清零改规则算作弊，不许。

## 目录结构

```
lhg-xiaohongshu/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：xhs / xhs-title / xhs-audit
├── skills/                  # 3 个平台中立 skill（lhg-xhs-copy/cover/compliance）
├── agents/                  # 2 个专家 agent（xhs-writer / xhs-reviewer）
├── hooks/                   # 2 个硬门（发布前合规拦截 / 写笔记后提醒）+ 豁免说明
├── scripts/audit/           # 16 条确定性合规审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好/坏封面，对照 PNG 封面）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你有产品要种草，但标题总没点击、正文像说明书时 → `/lhg-xiaohongshu:xhs` 一句话开工
- 你只想批量打磨标题时 → `/lhg-xiaohongshu:xhs-title` 8 个公式一次给够
- 笔记写完了、发之前怕违规限流时 → `/lhg-xiaohongshu:xhs-audit` 跑一遍分级自检
- 你是商家/博主，想给写手立一套"发文前必须过"的纪律时 → 它的 hooks 硬门开箱即用

**什么时候不用：**

- 你要的是公众号长文/短视频脚本 → 去用 `lhg-wechat-article`（姊妹插件），本插件为 300~800 字种草笔记优化
- 你希望 AI 直接登录你的小红书账号代发布 → 本插件永远不碰账号登录，发布必须由你亲手完成（这是设计，不是缺功能）
- 你的内容是英文或其他语种 → 极限词库、标题公式、标签策略全部按中文小红书生态编写

## 风险提示（诚实说明）

1. **平台对营销号限流**：小红书的营销号判定是综合行为画像（发文频率、硬广比例、引流行为），不是单篇合规就能解决的。本插件只能保证"这一篇不违规"，**不能保证**账号不限流。新号建议生活内容与种草 7:3 搭配，连续硬广必被限流。
2. **极限词库需持续维护**：脚本内置词库是 2026-10 快照，广告法执法口径和平台审核尺度会变，新型擦边词会不断出现。发现漏报/误报请按 skill 里的反馈渠道提 issue，词库随插件版本更新。**不要**自己改脚本阈值来"清零"，那是作弊。
3. **AI 味与真实感**：脚本能抓八股词、联系方式等硬信号，抓不到"读着像广告"的语气问题。最终质检是 lhg-xhs-copy 第 7 节"去广告味清单"——没有真实细节的种草就是硬广，神仙也救不了。
4. **封面绘制**：Canvas 绘制是确定性方案，但审美上限取决于你的配色和文案。AI 生图可做灵感参考，但中文大字必须用绘制方案，**不许**直接用 AI 生图的文字部分发布（笔画错误率极高）。

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、16 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-xiaohongshu/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
