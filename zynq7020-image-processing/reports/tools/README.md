# 最终报告生成脚本

一键从证据图片重新生成同目录上一级的 `../最终报告.docx` 和 `../最终报告.pdf`。
脚本里的路径都相对本文件解析，所以在任何机器上 clone 仓库后都能直接跑。

## 依赖

- **生成 docx**：Python 3.x + `python-docx`、`Pillow`
- **生成 pdf**：Windows + 安装了 Microsoft Word + `pywin32`
  （PDF 步骤用 Word COM 导出，会自动更新目录页码、生成书签）

本机参考：`D:/Miniconda3/python.exe` 或 `Python311`（注意 PDF 步骤的 `pywin32` 只在 Python311 装了）。

## 用法

```bash
python build_report.py    # 读证据图片 -> 生成 ../最终报告.docx（图片自动降采样）
python to_pdf.py          # 用 Word 把 docx 导出为 ../最终报告.pdf
```

## 说明

- **内容只改 `build_report.py`，不要手改 docx**（重跑会覆盖）。封面信息、各章正文、§10 成员分工表都在脚本里。
- `assets/`：广东工业大学校徽 / 集成电路学院院徽（从老师报告模板裁出）+ 实验 5 阈值切换三张图（`thr_sparse/mid/dense.png`）。
- 其余图片直接取自 `../../coursework/evidence/`（现场照片）与其下 `照片证明/大拓展最终验收视频截图/`（大拓展验收图）。
- 章节结构对齐老师最终报告要求与等级评定（任务 1 = C 档、任务 3 = B 档）。
