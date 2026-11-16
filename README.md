# ke-game-character-action

**独立、可复用的游戏角色动画 Agent Skill**。将角色参考图、分层素材、骨骼或已有资源转化为可评审的动作设计、可制作的动画规格，以及经过验证的游戏动画资源。

面向 2D 逐帧、2D 骨骼／混合动画和 3D 角色。支持待机、行走、跳跃、飞行、攻击、受击、击退、倒地、起身、死亡和动作衔接；不预设角色种类、世界观、画风或游戏引擎。

> 本仓库只包含 SKILL 指令、技术说明、JSON 模板和小型辅助脚本；**不包含角色原图、历史生成图片、精灵图、GIF、视频或模型资产**。

## 一张图自动生成多套动作

**默认执行：**用户提供角色设计图并要求生成动作时，AI 先识别角色，再**直接调用当前 Agent 环境已有的图片生成能力**，自动生成关键姿势、中间帧和可预览的动画素材；不必逐个动作重复询问。这是调用方 Agent 负责执行的工作，不需要在本仓库绑定某家图片 API。

**能力边界：**调用 Skill 的语言模型不一定就是图片生成模型。若其环境提供独立图像生成工具，则使用该工具；若模型本身支持图片输出，则使用原生输出；两者都没有，才明确告知当前环境不能生成图片。只安装一个 Markdown Skill 不会让纯文本模型凭空具备图像输出能力。

| 调用方环境 | 默认执行 |
| --- | --- |
| 当前 AI 自带图片生成能力 | 直接使用可用的原生生成能力 |
| 当前 AI 可调用图片生成工具 | 使用当前环境中实际提供的图片生成工具，保留参考图 |
| 当前 AI 只有文本能力 | 说明缺少图片生成能力，输出可移交的生成任务，不虚构产物 |

**生成链路：**原图 → 角色动作分析 → 分动作时间表与关键姿势 → **实际调用图片工具** → 逐帧检查和错误帧定向重绘 → 补齐过渡帧 → 真实透明序列帧或精灵表 → JSON 动画时间表 → 在线/本地动态预览 →（可用时）引擎运行验收。

注意：生成图像不等于生成可直接使用的动作资源。帧间角色一致性、真透明通道、脚底/根节点、均匀格子与逐帧持续时间均需要检查；模型如果只能出概念分镜或 GIF，应如实标注阶段。

[完整的模型无关调用与质量控制规范](references/host-native-image-generation.md)

## 设计理念

- **先分析角色，后设计动作**：骨架、支撑、重心、质量感、僵硬程度、服饰与道具共同决定运动方式。
- **动作姿势与节奏分开描述**：出手的快慢、关键姿势停留、命中顿帧、受击硬直与行动恢复分别配置。
- **受击不是统一后仰**：根据命中部位、施力方向、力度、移动状态、地面支撑和既有速度选择动作与位移。
- **生成结果必须可验证**：逐帧身份一致、动作连续、起落地成立、攻击判定准确、交付与引擎状态明确。
- **不依赖其他 Skill**：单独安装即可工作。

## 安装

要求支持 [Agent Skills](https://agentskills.io/) 的 AI 工具，或允许 AI 读取本地 Markdown 文件。请将**整个仓库目录**放入工具能够发现 Skill 的目录中，保持目录名 `ke-game-character-action`，不要只复制 `SKILL.md` 而丢掉 `references/`、`templates/`、`scripts/`。

### Codex（Windows PowerShell）

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
git clone https://github.com/kelicblan/ke-game-character-action.git "$HOME\.codex\skills\ke-game-character-action"
```

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/kelicblan/ke-game-character-action.git ~/.codex/skills/ke-game-character-action
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/kelicblan/ke-game-character-action.git ~/.claude/skills/ke-game-character-action
```

Windows PowerShell 对应路径为 `$HOME\.claude\skills\ke-game-character-action`。

### 其他 Agent / 项目级使用

使用该工具公开支持的 Skills 路径，例如项目内 `.agents/skills/ke-game-character-action/`（以具体工具文档为准）。如果工具不支持自动发现，将下面这句添加到项目的 Agent 指令中：

```text
处理游戏角色动画、受击、动作节奏或精灵动画任务时，先读取 ke-game-character-action/SKILL.md，并按需要读取该目录下的 references。角色图和动画产物保存在当前游戏项目中，不写入 Skill 仓库。
```

安装后重启会话或按 AI 工具要求重新加载 Skill。更新已安装版本：

```bash
git -C ~/.codex/skills/ke-game-character-action pull --ff-only
```

### 如何告诉 AI 使用这个 Skill

直接给出角色素材与目标即可：

```text
请使用 ke-game-character-action。
根据附件角色设计图，自动分析角色特征，设计待机、移动、攻击和受击。
无需只给方案：请调用你当前环境可用的图片生成能力，自动生成各动作的关键姿势和多帧图，
按命中部位、方向、强度、地面/空中状态分别设计受击，确保动作差异真实可读。
逐帧核对角色身份并定向重绘错误帧，输出实际可用的序列帧/精灵图、时间表和动态预览。
若当前环境没有任何图片生成能力，明确说明缺少什么，禁止假装已生成。
若没有真实在引擎中运行，不要宣称素材已通过引擎验收。
```

如果技能未自动触发，明确要求 AI 打开 `SKILL.md`；不同工具对自动发现和名称调用的支持有所差异。

## 使用流程

```text
角色原图 / 分层图 / 骨骼 / 文字设定
                 ↓
体型、运动、支撑与身份特征分析
                 ↓
动作卡 + 关键姿势 + 毫秒级时间表
                 ↓
分层补绘 / 关键帧 / 骨骼或逐帧动画
                 ↓
命中部位、施力方向与位移编排
                 ↓
可播放预览 + 逐帧一致性检查
                 ↓
引擎导入、动作事件与性能验收
```

技能按 G0（输入）至 G5（实际引擎运行）分级验收。概念分镜、GIF 与可导入精灵图不是同一个交付级别。

## 命令行辅助工具

可选工具仅依赖 Python 3.9+ 标准库；技能本身不要求 Python。

```bash
# 只检查动作卡元数据；模板可直接用于格式检查
python scripts/validate_motion.py templates/action-card.json

# 完整动作资产完成后检查文件、布局与时间配置
python scripts/validate_motion.py path/to/action-card.json --check-assets

# 将存在的 PNG 精灵图表及动作卡生成自包含的 HTML 预览
python scripts/preview.py path/to/action-card.json -o path/to/preview.html

# 运行内置测试
python -m unittest discover -s tests -v
```

动作卡中 `visual.path` 相对当前动作卡文件目录；预览工具不会创建、修改或替代角色图片，且不假装进行了 Cocos／Unity 引擎验收。

## 仓库结构

```text
ke-game-character-action/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── references/
│   ├── host-native-image-generation.md
│   ├── character-and-motion.md
│   ├── timing-and-states.md
│   ├── hit-reaction-system.md
│   ├── production-and-consistency.md
│   └── integration-and-qa.md
├── templates/
│   ├── character-profile.json
│   ├── action-card.json
│   └── hit-reaction.json
├── scripts/
│   ├── validate_motion.py
│   └── preview.py
└── tests/
    └── test_validate_motion.py
```

## 输出与版权

将具体游戏角色原图、PNG、GIF、序列帧、骨骼、视频、引擎构建结果和项目私有数据写入目标游戏工程。仓库的 `.gitignore` 明确排除媒体和生成目录，防止误把历史素材上传。角色素材须由使用方拥有合法使用权。

源代码与文档采用 [MIT License](LICENSE)；游戏素材不随此许可授权。

## 技术参考

受击动作以可读性、命中区域、方向和强度为基本设计维度。参考资料：

- [Jonathan Colin：Gameplay animation, hit reactions and readability](https://www.animotionx.com/en/post/interview-jonathan-colin-readability-silhouette-and-gameplay-animation-secrets)
- [GDC：《The Division 2》Hit Reactions](https://media.gdcvault.com/gdc2019/presentations/Dunstan_Philip_FightingSequelitisCreating.pdf)
- [Cocos Creator 3.8：Animation Events](https://docs.cocos.com/creator/3.8/manual/en/animation/animation-event.html)
- [Spine：Applying Animations](https://esotericsoftware.com/spine-applying-animations)

这些资料用于启发设计。Skill 会驱动调用方使用**当前实际可用**的图像生成能力，不内置或捆绑任何图像模型；引擎运行验证仍需真实工程环境。
