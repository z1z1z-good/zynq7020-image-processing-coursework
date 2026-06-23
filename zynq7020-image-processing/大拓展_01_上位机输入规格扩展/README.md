# 大拓展 01：上位机输入规格扩展

本目录是第二周综合大拓展的独立交付目录，避免与 `sobel_05_pc_control_display` 基础实验混合。

## 目标

对应评分表中的 C 档方向：硬件不变，上位机统一缩放至 3 种以上尺寸后发送。本方案保留实验 5 的
PS/PL/BRAM/HDMI 链路不变，在 PC 端完成输入适配，再统一发出硬件兼容的 `128x72 RGB888` 图像帧。

已支持的处理尺寸：

```text
128x72    C 档参考尺寸，默认硬件发送尺寸
160x90    C 档参考尺寸，16:9 中间处理尺寸
144x108   C 档参考尺寸，4:3 中间处理尺寸
64x36     低处理尺寸对比，用于展示块状粗分辨率效果
```

无论选择哪个 `--proc-size`，最终发给 FPGA 的帧仍固定为 `128x72 RGB888`，因此实验 5 的控制命令、BRAM
地址、PL Sobel 和 HDMI 显示逻辑都不用修改。

## 目录

| 目录 | 内容 |
| --- | --- |
| `host_tool/` | 独立上位机工具，包含 CLI、GUI、依赖和离线测试 |
| `evidence/` | 大拓展验证证据，包括 help、测试日志、36 组矩阵和对比图 |

## 运行示例

```bash
cd zynq7020-image-processing/大拓展_01_上位机输入规格扩展/host_tool
python camera_uart_sender.py --port COM7 --image pic.jpg --once --fit-mode stretch --proc-size 128x72
python camera_uart_sender.py --port COM7 --image pic.jpg --once --fit-mode letterbox --proc-size 160x90
python camera_uart_sender.py --port COM7 --image pic.jpg --once --fit-mode center-crop --proc-size 144x108
python camera_uart_sender.py --port COM7 --image pic.jpg --once --fit-mode stretch --proc-size 64x36
```

离线验证：

```bash
python tests/test_prepare_frame.py
python tests/test_protocol_invariants.py
```

当前验证结果：

```text
tests/test_prepare_frame.py: 8/8 passed
tests/test_protocol_invariants.py: 4/4 passed
summary: 12/12 offline assertions passed
3 fit modes x 3 original sizes x 4 proc sizes = 36 groups
```

## 评分说明

- C 档：已覆盖 `128x72`、`160x90`、`144x108` 三种参考尺寸，且上位机统一适配后发送。
- B 档：要求修改硬件支持 5 种以上固定尺寸，本目录不声称达到。
- A 档：要求 1080P 图像传输与 HDMI 显示，并迁移到 DDR，本目录不声称达到。
