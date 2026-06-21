# 实验 5 综合扩展任务 1 上位机输入与缩放策略 远程开发证据

## 运行信息

- 日期：2026-06-17
- 分支：`exp/05-ext-scaling`（提交号以 `git log` 为准：feat `a76324c`、test `e28346c`、docs 本次）
- 工具：Python 3.11.15（`D:/Miniconda3/python.exe`）、numpy 2.4.6、OpenCV 4.13.0、pyserial 3.5
- 设计方案：**方案 A —— 上位机统一缩放到固定 `128×72`**，不改 FPGA/PS/PL/BD/XDC，不改 `sobel_05` 工程
- 改动文件：仅 `host_camera_uart/camera_uart_sender.py`、`camera_uart_gui.py`，新增 `host_camera_uart/tests/`
- 状态：**上位机离线验证通过，待现场上板演示**。本目录全部为离线（无板/无串口/无摄像头）结果。

## 设计要点

任意尺寸输入经一个公共函数 `prepare_frame(frame_bgr, width=128, height=72, fit_mode, content_size, fill)`
统一映射为固定 `128×72 RGB888`，CLI 与 GUI 共用（消除原先两份内联 `cv2.resize` 重复）：

- `stretch`：直接 `cv2.resize` 到 `128×72`，可能改变宽高比（默认，缩小时与旧工具逐字节一致）。
- `letterbox`：等比缩放 `s=min(W/w, H/h)`，居中放置，空白区补 `fill` 色，主体不变形。
- `center-crop`：等比放大 `s=max(W/w, H/h)`，居中裁剪到 `128×72`，铺满无黑边。
- 缩小用 `INTER_AREA`、放大用 `INTER_LINEAR`，最后统一 `BGR->RGB`。
- 目标处理尺寸 `--proc-size`：`128x72`（满幅）或 `64x36`（先把内容处理到 `64×36`，再最近邻放回固定
  `128×72` 帧，HDMI 上可见更粗分辨率）。无论选哪种，**发送给 FPGA 的帧恒为 `128×72`**。

发送协议保持不变（与 `sobel_03/04/05` 兼容）：帧头 `55 aa 80 00 48 00 18`，整帧 `27943` 字节，
控制帧 `A5 5A cmd value`。因此 PS 接收、BRAM 地址、PL 扫描、HDMI 放大、Sobel 尺寸均无需改动。

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `ext_fit_modes_landscape.png` | `640×480`(4:3) 源经 stretch / letterbox / center-crop 的 `128×72`(×10) 对比：圆形在 stretch 下被压成椭圆，letterbox 保持正圆并补黑边，center-crop 保持正圆且铺满裁掉上下 |
| `ext_fit_modes_portrait.png` | `1080×1920`(竖图) 源三策略对比：letterbox 左右大面积补黑（主体 `40×72`），center-crop 取中间竖条铺满 |
| `ext_proc_size.png` | 同一 `640×480` 源在 `proc 128x72`(满幅) 与 `proc 64x36`(更粗) 下的 `128×72`(×10) 对比，后者明显块状 |
| `ext_scaling_matrix.txt` | 3 fit 模式 × 3 原始尺寸 × 2 处理尺寸 = 18 组：输出形状/包长/帧头核对；letterbox 主体框宽高比与填充像素；center-crop 无黑边核对 |
| `ext_offline_tests.txt` | 两套离线测试 standalone 运行结果（`7/7` + `4/4` = `11/11` 全过）与三不变量摘要 |
| `ext_cli_help.txt` | CLI `--help`，含新增 `--fit-mode` / `--proc-size` / `--fill-color` |

对比图为本机离线渲染的“PC 端处理结果”，不是 HDMI 实拍；真实上板照片待现场回传。

## 课设要求逐条对应

### 完成内容

| # | 要求 | 状态 | 说明 |
| --- | --- | --- | --- |
| 1 | 多输入来源（单图/多图/图片目录/摄像头/MP4） | 完成 | CLI 既有 `--image/--images/--image-dir/--video/camera`（未重写，回归测试通过）；GUI 新增 `Folder`（图片目录）按钮，复用 `collect_image_paths` |
| 2 | 可选目标处理尺寸（`128×72` + ≥1 新尺寸） | 完成 | CLI `--proc-size {128x72,64x36}`，GUI `Proc size` 下拉；`64×36` 为新处理尺寸（见对比图与 matrix） |
| 3 | 设计“不同尺寸如何进 FPGA” | 完成 | 方案 A：上位机统一缩放到固定 `128×72`，三种 fit 策略可选 |
| 4 | 若改硬件尺寸需同步改 BRAM/宽高/HDMI/仿真 | **N/A** | 采用方案 A，未修改 PL 处理尺寸，无硬件同步项。第二种“处理尺寸”在上位机以 `64×36` content_size 实现 |
| 5 | 保持 `sobel_05` 控制命令可用（原图/灰度/边缘/叠加/阈值） | 完成 | `send_control_command` / `send_requested_controls` 语义未改，`A5 5A cmd value` 字节经测试核对一致；CLI/GUI 控制入口保留 |

### 仿真或验证要求

| # | 要求 | 状态 | 说明 |
| --- | --- | --- | --- |
| 1 | ≥2 种不同原始尺寸图片输入测试 | 完成（离线） | 测试覆盖 `640×480`、`1920×1080`、`1080×1920` 三种原始尺寸 |
| 2 | 上位机缩放/裁剪/填充策略说明 | 完成 | 见上“设计要点”与对比图：stretch 拉伸 / letterbox 填充 / center-crop 裁剪 |
| 3 | 若改 PL 尺寸须给 BRAM 地址或显示控制仿真截图 | **N/A** | 采用方案 A 未改 PL；`sobel_05` 原显示控制链路仿真见 `06_pc_control` |
| 4 | 上板演示 ≥2 种输入来源或尺寸 | **待现场** | 离线已就绪；现场演示清单见文末 |

## 关键结果

- 离线测试 `11/11` 全过（`ext_offline_tests.txt`）：
  - 形状：三 fit 模式 × 三原始尺寸 × 两处理尺寸输出均为 `(72, 128, 3)` `uint8`。
  - letterbox 主体宽高比保持：`640×480->96×72`(1.333)、`1920×1080->128×72`(1.778)、`1080×1920->40×72`(0.556≈0.562)，填充区等于指定 `fill` 色。
  - center-crop 无黑边：纯色源输出 `min==max`，无填充引入。
  - stretch 与旧内联 `cv2.resize(...,INTER_AREA)+cvtColor` 逐字节一致（向后兼容）。
  - `content_size=64×36`：输出 `2×2` 像素块均匀（更粗）且仍为合法 `128×72` 帧。
- 三不变量（`ext_scaling_matrix.txt` 全部 `OK`）：包长 `27943` 字节、帧头 `55 aa 80 00 48 00 18`、控制帧 `A5 5A cmd value`（如 `A5 5A 01 03`）。
- 协议字节与 `sobel_05` 契约未变动，证明 FPGA 接收侧无需任何修改。

诚实边界：以上仅覆盖上位机缩放策略、协议格式与控制字节的离线验证；“离线验证通过”不等于“上板通过”。
真实 JTAG / 串口 / HDMI 现象待现场。

## 现场上板演示建议（配合 `exp/05-pc-control` 已构建的 bitstream + PS ELF）

1. 单张 `640×480` 图片，依次发送三种 fit：
   - `python camera_uart_sender.py --port COMx --image pic_640x480.jpg --once --fit-mode stretch`
   - `... --fit-mode letterbox`（看左右补黑、主体不变形）
   - `... --fit-mode center-crop`（看铺满无黑边）
2. 一张 `1920×1080` 与一张 `1080×1920` 图片，验证 ≥2 种原始尺寸：`--fit-mode letterbox`。
3. 目标处理尺寸对比：`--proc-size 128x72` 与 `--proc-size 64x36`（看 HDMI 画面变粗）。
4. 多输入来源：`--image-dir .\frames`（图片目录）、`--video demo.mp4`（MP4）或摄像头，验证 ≥2 种来源。
5. 在同一输入下切换 `sobel_05` 控制，确认控制命令仍可用：
   - `--control-only --mode original` / `gray` / `edge --threshold 80` / `overlay --overlay on`。
6. GUI 等价操作：Input source 选 `Image sequence` + `Folder`、`Single image`、`Video file`；Frame settings 选
   `Fit mode` 与 `Proc size`；`Display control for sobel_05` 切换模式/阈值/叠加。

## 待现场回传的证据

- 实际测试分支与完整提交号；板卡型号、Vivado/Vitis 版本、COM 口、显示器型号、测试日期。
- 至少 2 种原始尺寸图片在 stretch / letterbox / center-crop 下的 HDMI 实拍照片（看变形/黑边/裁剪差异）。
- `proc 128x72` 与 `proc 64x36` 的 HDMI 对比照片（看分辨率粗细差异）。
- 至少 2 种输入来源（如图片目录 + MP4 或摄像头）的 HDMI 照片或短视频。
- 同一输入下 `sobel_05` 原图/灰度/边缘/叠加切换照片与串口 `control:` 回显，证明控制命令未受影响。
- 上位机命令行或 GUI 日志（含 `input WxH -> 128x72 (mode)` 的尺寸打印）。
