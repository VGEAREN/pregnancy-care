# pregnancy-care

OpenClaw skill - 通过聊天管理孕期健康数据。

[English](README_EN.md)

## 功能

- **报告识别**：发送产检报告照片，AI 自动识别、提取关键指标并结构化归档
- **趋势追踪**：自动按指标类别（血常规、甲功、尿常规等）汇总趋势表
- **B超管理**：支持普通照片和 DICOM 原始影像，自动提取测量数据
- **异常分析**：结合孕周参考范围和知识库，区分正常生理变化与需关注异常
- **产检计划**：基于孕周自动维护产检时间线
- **PDF 报告**：一键生成包含趋势图表的综合产检报告
- **知识库**：可扩展的书籍知识库，AI 回答问题时引用具体章节

## 安装

```bash
# 从 GitHub 安装
openclaw skills install <github-url>

# 或手动复制
cp -r pregnancy-care ~/.openclaw/skills/

# 安装 Python 依赖（必需）
pip3 install reportlab

# 可选：DICOM 影像支持
pip3 install pydicom Pillow numpy

# 可选：添加书籍到知识库
pip3 install ebooklib beautifulsoup4
```

## 使用方法

首次使用时，skill 会引导你完成初始化（填写基本信息、创建数据目录）。之后：

| 操作 | 方式 |
|------|------|
| 录入产检报告 | 发送报告照片 |
| 录入 B超 | 发送 B超照片或 DICOM ZIP 文件 |
| 生成 PDF 报告 | 发送"生成PDF报告" |
| 查询孕期问题 | 直接提问，如"孕早期TSH偏高正常吗" |
| 添加知识库书籍 | 发送 epub 文件 |
| 查看产检计划 | 发送"产检计划" |

## 知识库

`references/books/` 目录默认为空（版权原因）。你可以添加自己的书籍：

```bash
python3 scripts/epub-to-md.py "你的书.epub" "references/books/书名/"
```

添加后让 bot 更新知识库索引即可。推荐书目：

| 书名 | 作者 | 特点 |
|------|------|------|
| 梅奥健康怀孕全书（第2版） | 玛拉·魏克 | 权威百科，豆瓣9.3 |
| 协和产科门诊200问 | 马良坤 | 国内建档/产检流程 |
| 怀孕呵护指南 | 六层楼先生 | 通俗实用，国内视角 |
| 范志红详解孕产妇饮食营养全书 | 范志红 | 营养饮食专项 |

## 项目结构

```
pregnancy-care/
├── SKILL.md                  ← 主指令文件
├── references/
│   ├── INDEX.md              ← 全局主题索引
│   ├── indicator-ranges.md   ← 孕期指标参考范围
│   └── books/                ← 知识库书籍（用户自行添加）
├── scripts/
│   ├── epub-to-md.py         ← epub 转 Markdown
│   ├── dicom-export.py       ← DICOM 转 JPG
│   └── generate-pdf.py       ← 生成 PDF 报告
└── assets/                   ← 运行时输出
```

## 数据存储

所有数据以 Markdown 文件存储在工作区的 `pregnancy/` 目录下：

```
pregnancy/
├── profile.md       ← 基本信息（姓名、年龄、预产期）
├── summary.md       ← 指标趋势表 + 产检计划
├── records/         ← 结构化报告
├── reports/         ← 原始报告图片
├── ocr_results/     ← 识别原文
└── ultrasound/      ← B超影像
```

## 免责声明

所有分析仅供参考，不构成医学建议。异常指标请及时咨询专业医生。

## 许可证

MIT
