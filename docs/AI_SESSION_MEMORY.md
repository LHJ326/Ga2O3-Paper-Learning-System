# Ga2O3 Paper Learning System
# AI Session Memory

## 1. Project Goal

本项目目标是建立一个长期科研论文 AI 学习系统。

核心流程：

```text
PDF 论文

↓

解析

↓

结构化 Document

↓

Knowledge Card

↓

RAG

↓

AI 科研助手
```

重点方向：Ga2O3 光电器件论文学习。

## 2. Current Architecture

```text
PDF

↓

MinerU 4.0.7

↓

Raw Output

↓

MinerUAdapter

↓

Document Schema

↓

后续 RAG 系统
```

## 3. Current Environment

- OS: Windows 11
- Python: 3.12.7
- GPU: RTX 4060 Laptop GPU
- CUDA: 12.6
- Main environment: `.venv`
- MinerU environment: `.venv-mineru`
- MinerU version: 4.0.7

## 4. Completed Milestones

Phase 0:

Project initialization

Phase 1:

Environment setup

Phase 1.5C:

MinerU environment

Phase 1.5D:

Paper Library

Phase 1.5D-1B-0:

MinerU Output Contract

Phase 1.5D-1B-1A:

P001 metadata

Phase 1.5D-1B-1B:

P001 MinerU raw parsing

Phase 1.5D-1B-2A:

MinerU output analysis

Phase 1.5D-1B-2B:

MinerUAdapter first conversion

Phase 1.5D-1B-3A:

Figure-caption mapping

Phase 1.5D-1B-3B:

Scientific Figure asset filtering

## 5. Current P001 Status

Paper:

`P001.pdf`

Location:

`data/papers/P001.pdf`

Raw:

`data/parsed/P001/mineru/raw/`

Conversion:

`MinerUAdapter.convert()`

Current output:

- Pages: 12
- Sections: 10
- TextBlocks: 214
- Figures: 6
- Tables: 0
- Equations: 0

## 6. Important Design Decisions

1. 不要直接绑定 MinerU 输出。

   必须通过：

   ```text
   Raw Output

   ↓

   Adapter

   ↓

   Document Schema
   ```

2. 论文原始文件保持不修改。

3. 大型安装、模型下载和 GPU 任务优先人工确认。

4. Codex 负责代码、架构和测试。

5. ChatGPT 负责路线规划和架构审核。

## 7. Current Limitations

- Figure caption 采用保守邻接匹配，仍需 Benchmark 验证
- 11 个非 Figure 图片资产仅保留在 Raw Output
- Equation 解析未完善
- Table 解析未完善
- Adapter 仍是第一版

## 8. Next Step

下一阶段：

Phase 1.5D-1B-3

目标：提升 MinerU Adapter。

- Figure evidence chain 增强
- Table 支持
- Equation 检测
- B01 Benchmark 准备

## 9. Rules For Future AI

未来继续时必须：

1. 先读取 `docs/PROJECT_STATE.md`。
2. 读取 `docs/AI_SESSION_MEMORY.md`。
3. 不要重新初始化项目。
4. 不要重新安装环境。
5. 不要重新解析 P001。
6. 先确认当前 Git 状态。
