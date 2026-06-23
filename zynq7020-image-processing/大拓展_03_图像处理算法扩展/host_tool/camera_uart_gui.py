#!/usr/bin/env python3
"""大拓展 03（图像处理算法扩展，任务3 B档）验收 GUI —— 并入大拓展 01 输入缩放。

验收要点（对应用户要求“手操调整图形化界面，看到可见的实验结果改善”）：
  - 选择显示模式（含 **sharpen 锐化**）并实时下发给 FPGA；
  - 拖动 **锐化强度滑块(0..255)** 时实时下发 `A5 5A 04 k`（控制字 0x900C），HDMI 即时变锐，无需重发帧；
  - 同窗口并排「原图(缩放后) | 软件锐化(k)」实时刷新，既看“可见改善”，又是 B 档要求的**软件参考**；
  - **大拓展 01 共存**：fit 模式 + 处理分辨率（纯主机缩放，硬件仍收 128x72），可与锐化叠加演示。

软件预览用 sharpen_algo.py，与 PL/PS 定点逐位一致（协同仿真已证 RTL==软件 golden）。
未连接串口也能离线演示（软件预览 + 缩放），便于上板前彩排。

提示：锐化在**真实照片/柔和图**上看起来最像“变清晰”；合成硬边图会出现明显的边缘 overshoot（振铃），
那是 Laplacian 锐化的正常表现。默认占位图已做柔化处理，并建议「载入图片」用真实照片演示。
"""
from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

DEPENDENCY_ERROR: ImportError | None = None
try:
    import cv2
    import numpy as np
    import serial
    from serial.tools import list_ports

    import sharpen_algo
    from camera_uart_sender import (
        CONTROL_MODE,
        CONTROL_OVERLAY,
        CONTROL_SHARPEN,
        CONTROL_THRESHOLD,
        FIT_MODES,
        MODE_NAMES,
        MODE_VALUES,
        PROC_SIZES,
        build_frame_packet,
        load_source_bgr,
        parse_proc_size,
        prepare_frame,
    )
except ImportError as exc:
    DEPENDENCY_ERROR = exc

IMG_W = 128
IMG_H = 72
PREVIEW_SCALE = 4          # 128x72 -> 512x288 每个预览面板
DEFAULT_SHARPEN = 64       # 默认强度（偏温和，更像“锐化”而非振铃）


class SharpenGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("大拓展03 锐化扩展（含大拓展01 缩放）- Zynq UART 验收工具")
        self.geometry("1140x820")
        self.minsize(1000, 740)

        self.ser: "serial.Serial | None" = None
        self.serial_lock = threading.Lock()
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.source_bgr: "np.ndarray | None" = None     # 载入的整幅原图 BGR（缩放前）
        self.rgb_image: "np.ndarray | None" = None       # 缩放后 128x72 RGB（发送 + 锐化预览输入）
        self.orig_photo: "tk.PhotoImage | None" = None
        self.sharp_photo: "tk.PhotoImage | None" = None

        self._pending_sharpen: "int | None" = None
        self._sharpen_after_id: "str | None" = None
        self._sending_frame = False

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value="115200")
        self.conn_var = tk.StringVar(value="未连接")
        self.image_path_var = tk.StringVar(value="（未载入图片；正在用柔化占位图，建议载入真实照片）")
        self.fit_mode_var = tk.StringVar(value="stretch")
        self.proc_size_var = tk.StringVar(value="128x72")
        self.mode_var = tk.StringVar(value="sharpen")
        self.threshold_var = tk.IntVar(value=80)
        self.overlay_var = tk.BooleanVar(value=False)
        self.sharpen_var = tk.IntVar(value=DEFAULT_SHARPEN)
        self.status_var = tk.StringVar(value="就绪")

        self._build_ui()
        self.refresh_ports()
        self._make_placeholder_image()
        # 所有控件与占位图就绪后再定位滑块，避免构造期回调引用尚未创建的控件
        self.threshold_scale.set(self.threshold_var.get())
        self.sharpen_scale.set(self.sharpen_var.get())
        self._reprepare()
        self.after(100, self._drain_log_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----------------------------- UI -----------------------------
    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        conn = ttk.LabelFrame(root, text="串口连接", padding=8)
        conn.pack(fill=tk.X)
        ttk.Label(conn, text="端口").grid(row=0, column=0, padx=(0, 6))
        self.port_combo = ttk.Combobox(conn, textvariable=self.port_var, width=16)
        self.port_combo.grid(row=0, column=1)
        ttk.Button(conn, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=6)
        ttk.Label(conn, text="波特率").grid(row=0, column=3, padx=(16, 6))
        ttk.Combobox(conn, textvariable=self.baud_var, width=10,
                     values=("115200", "230400", "460800", "921600")).grid(row=0, column=4)
        self.connect_btn = ttk.Button(conn, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=5, padx=12)
        ttk.Label(conn, textvariable=self.conn_var, foreground="#555").grid(row=0, column=6, padx=6)

        # 图像 + 大拓展01 输入缩放
        img = ttk.LabelFrame(root, text="图像 + 输入缩放（大拓展01：纯主机缩放，硬件仍收 128x72）", padding=8)
        img.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(img, text="载入图片", command=self.load_image).grid(row=0, column=0)
        ttk.Label(img, textvariable=self.image_path_var, foreground="#555", width=46).grid(
            row=0, column=1, columnspan=4, sticky="w", padx=10)
        self.send_btn = ttk.Button(img, text="发送图像到 FPGA", command=self.send_image)
        self.send_btn.grid(row=0, column=5, padx=10)

        ttk.Label(img, text="Fit 模式").grid(row=1, column=0, sticky="w", pady=(8, 0))
        fit_combo = ttk.Combobox(img, textvariable=self.fit_mode_var, width=12, values=FIT_MODES, state="readonly")
        fit_combo.grid(row=1, column=1, sticky="w", pady=(8, 0))
        fit_combo.bind("<<ComboboxSelected>>", lambda e: self._reprepare())
        ttk.Label(img, text="处理分辨率").grid(row=1, column=2, sticky="w", padx=(16, 6), pady=(8, 0))
        proc_combo = ttk.Combobox(img, textvariable=self.proc_size_var, width=10, values=PROC_SIZES, state="readonly")
        proc_combo.grid(row=1, column=3, sticky="w", pady=(8, 0))
        proc_combo.bind("<<ComboboxSelected>>", lambda e: self._reprepare())

        # 算法控制
        ctrl = ttk.LabelFrame(root, text="算法控制（实时下发到 PL）", padding=8)
        ctrl.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(ctrl, text="显示模式").grid(row=0, column=0, padx=(0, 6))
        self.mode_combo = ttk.Combobox(ctrl, textvariable=self.mode_var, width=10,
                                       values=MODE_NAMES, state="readonly")
        self.mode_combo.grid(row=0, column=1)
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
        ttk.Label(ctrl, text="边缘阈值").grid(row=0, column=2, padx=(16, 6))
        self.threshold_scale = ttk.Scale(ctrl, from_=0, to=255, orient=tk.HORIZONTAL, length=150,
                                         command=self.on_threshold_change)
        self.threshold_scale.grid(row=0, column=3)
        self.threshold_lbl = ttk.Label(ctrl, text="80", width=4)
        self.threshold_lbl.grid(row=0, column=4, padx=(4, 0))
        ttk.Checkbutton(ctrl, text="红色边缘叠加", variable=self.overlay_var,
                        command=self.on_overlay_change).grid(row=0, column=5, padx=(16, 0))

        # 锐化强度（验收主控件）
        sharp = ttk.LabelFrame(root, text="锐化强度（拖动即时生效：软件预览 + HDMI 同步变锐）", padding=8)
        sharp.pack(fill=tk.X, pady=(10, 0))
        sharp.columnconfigure(1, weight=1)
        ttk.Label(sharp, text="k =").grid(row=0, column=0, padx=(0, 8))
        self.sharpen_scale = ttk.Scale(sharp, from_=0, to=255, orient=tk.HORIZONTAL,
                                       command=self.on_sharpen_change)
        self.sharpen_scale.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.sharpen_lbl = ttk.Label(sharp, text=str(DEFAULT_SHARPEN), width=5, font=("", 11, "bold"))
        self.sharpen_lbl.grid(row=0, column=2)
        presets = ttk.Frame(sharp)
        presets.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(presets, text="快捷预设：").pack(side=tk.LEFT)
        for k in (0, 32, 64, 128, 255):
            ttk.Button(presets, text=f"k={k}", width=6,
                       command=lambda v=k: self.set_sharpen(v)).pack(side=tk.LEFT, padx=3)
        ttk.Label(presets, text="  （0=原图；真实照片上 32~96 最像“变清晰”，过大会出现边缘振铃）",
                  foreground="#888").pack(side=tk.LEFT, padx=(8, 0))

        # 预览
        prev = ttk.LabelFrame(root, text="软件预览（= HDMI 硬件输出逐像素参考；硬件结果见 HDMI 显示器）",
                              padding=8)
        prev.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        left = ttk.Frame(prev)
        left.pack(side=tk.LEFT, expand=True)
        ttk.Label(left, text="原图（缩放后 = 发送/HDMI 输入）").pack()
        self.orig_label = ttk.Label(left)
        self.orig_label.pack()
        right = ttk.Frame(prev)
        right.pack(side=tk.LEFT, expand=True, padx=(16, 0))
        self.sharp_title = ttk.Label(right, text=f"软件锐化 k={DEFAULT_SHARPEN}")
        self.sharp_title.pack()
        self.sharp_label = ttk.Label(right)
        self.sharp_label.pack()

        bottom = ttk.Frame(root)
        bottom.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(bottom, text="状态:").pack(side=tk.LEFT)
        ttk.Label(bottom, textvariable=self.status_var, foreground="#06c").pack(side=tk.LEFT, padx=(4, 0))
        log_frame = ttk.LabelFrame(root, text="日志", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        self.log_text = tk.Text(log_frame, height=5, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scroll.set)

        self._sync_control_state()

    # ----------------------------- serial -----------------------------
    def refresh_ports(self) -> None:
        ports = [p.device for p in list_ports.comports()]
        self.port_combo.configure(values=ports)
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
        self._log(f"发现 {len(ports)} 个串口")

    def toggle_connection(self) -> None:
        if self.ser is not None:
            self._close_serial()
            return
        port = self.port_var.get().strip()
        if not port:
            messagebox.showerror("无效设置", "请先选择串口。")
            return
        try:
            baud = int(self.baud_var.get())
            ser = serial.Serial(port, baud, timeout=0, write_timeout=2)
        except Exception as exc:
            messagebox.showerror("连接失败", str(exc))
            self._log(f"连接失败: {exc}")
            return
        time.sleep(0.2)
        self.ser = ser
        self.conn_var.set(f"已连接 {port} @ {baud}")
        self.connect_btn.configure(text="断开")
        self._log(f"已连接 {port} @ {baud}")
        self.push_all_controls()

    def _close_serial(self) -> None:
        with self.serial_lock:
            if self.ser is not None:
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
        self.conn_var.set("未连接")
        self.connect_btn.configure(text="连接")
        self._log("已断开串口")

    def _write(self, data: bytes) -> bool:
        with self.serial_lock:
            if self.ser is None:
                return False
            try:
                self.ser.write(data)
                return True
            except Exception as exc:
                self._log(f"串口写入失败: {exc}")
                return False

    def _send_ctrl(self, command: int, value: int) -> None:
        if self._write(bytes((0xA5, 0x5A, command & 0xFF, value & 0xFF))):
            name = {CONTROL_MODE: "mode", CONTROL_THRESHOLD: "threshold",
                    CONTROL_OVERLAY: "overlay", CONTROL_SHARPEN: "sharpen"}.get(command, hex(command))
            self._log(f"下发控制 {name}={value}")

    def push_all_controls(self) -> None:
        self._send_ctrl(CONTROL_MODE, MODE_VALUES[self.mode_var.get()])
        self._send_ctrl(CONTROL_THRESHOLD, int(self.threshold_var.get()))
        self._send_ctrl(CONTROL_OVERLAY, 1 if self.overlay_var.get() else 0)
        self._send_ctrl(CONTROL_SHARPEN, int(self.sharpen_var.get()))

    # ----------------------------- control callbacks -----------------------------
    def on_mode_change(self, _event=None) -> None:
        self._send_ctrl(CONTROL_MODE, MODE_VALUES[self.mode_var.get()])
        self._sync_control_state()

    def on_threshold_change(self, value: str) -> None:
        k = int(float(value))
        self.threshold_var.set(k)
        self.threshold_lbl.configure(text=str(k))
        self._send_ctrl(CONTROL_THRESHOLD, k)

    def on_overlay_change(self) -> None:
        self._send_ctrl(CONTROL_OVERLAY, 1 if self.overlay_var.get() else 0)

    def on_sharpen_change(self, value: str) -> None:
        k = int(float(value))
        self.sharpen_var.set(k)
        self.sharpen_lbl.configure(text=str(k))
        self.sharp_title.configure(text=f"软件锐化 k={k}")
        self._update_preview()
        self._schedule_sharpen_send(k)

    def set_sharpen(self, k: int) -> None:
        self.sharpen_scale.set(k)
        self.on_sharpen_change(k)

    def _schedule_sharpen_send(self, k: int) -> None:
        self._pending_sharpen = k
        if self._sharpen_after_id is None:
            self._sharpen_after_id = self.after(15, self._flush_sharpen_send)

    def _flush_sharpen_send(self) -> None:
        self._sharpen_after_id = None
        if self._pending_sharpen is not None:
            self._send_ctrl(CONTROL_SHARPEN, self._pending_sharpen)
            self._pending_sharpen = None

    def _sync_control_state(self) -> None:
        edge_like = self.mode_var.get() in ("edge", "overlay")
        self.threshold_scale.configure(state=tk.NORMAL if edge_like else tk.DISABLED)

    # ----------------------------- image / scaling / preview -----------------------------
    def load_image(self) -> None:
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=(("图片", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")))
        if not path:
            return
        try:
            self.source_bgr = load_source_bgr(path)
        except Exception as exc:
            messagebox.showerror("载入失败", str(exc))
            return
        self.image_path_var.set(path)
        self._log(f"载入图片 {path}（{self.source_bgr.shape[1]}x{self.source_bgr.shape[0]}）")
        self._reprepare()

    def _make_placeholder_image(self) -> None:
        """柔化占位图：渐变 + 抗锯齿形状 + 文字，再高斯模糊，使锐化能明显“恢复清晰”而非振铃。"""
        h, w = IMG_H, IMG_W
        yy, xx = np.mgrid[0:h, 0:w]
        img = np.zeros((h, w, 3), np.uint8)
        img[..., 0] = (60 + 150 * xx / (w - 1)).astype(np.uint8)            # B
        img[..., 1] = (70 + 120 * yy / (h - 1)).astype(np.uint8)            # G
        img[..., 2] = (110 + 110 * (xx + yy) / (w + h - 2)).astype(np.uint8)  # R
        cv2.circle(img, (34, 38), 15, (235, 235, 235), -1, lineType=cv2.LINE_AA)
        cv2.rectangle(img, (66, 16), (110, 52), (40, 70, 210), 2, lineType=cv2.LINE_AA)
        cv2.putText(img, "FPGA", (64, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.line(img, (4, 64), (124, 6), (0, 210, 210), 1, lineType=cv2.LINE_AA)
        img = cv2.GaussianBlur(img, (5, 5), 1.4)        # 略微失焦的输入
        self.source_bgr = np.ascontiguousarray(img)

    def _reprepare(self) -> None:
        """按当前 fit 模式 / 处理分辨率把原图缩放成 128x72（大拓展01），再刷新预览。"""
        if self.source_bgr is None:
            return
        try:
            content = parse_proc_size(self.proc_size_var.get(), IMG_W, IMG_H)
            self.rgb_image = prepare_frame(self.source_bgr, IMG_W, IMG_H, self.fit_mode_var.get(), content)
        except Exception as exc:
            self._log(f"缩放失败: {exc}")
            return
        self._update_preview()

    def _to_photo(self, rgb: "np.ndarray") -> "tk.PhotoImage":
        up = cv2.resize(rgb, (IMG_W * PREVIEW_SCALE, IMG_H * PREVIEW_SCALE), interpolation=cv2.INTER_NEAREST)
        up = np.ascontiguousarray(up)
        header = f"P6 {up.shape[1]} {up.shape[0]} 255\n".encode("ascii")
        return tk.PhotoImage(data=header + up.tobytes(), format="PPM")

    def _update_preview(self) -> None:
        if self.rgb_image is None:
            return
        k = int(self.sharpen_var.get())
        self.orig_photo = self._to_photo(self.rgb_image)
        self.sharp_photo = self._to_photo(sharpen_algo.sharpen(self.rgb_image, k))
        self.orig_label.configure(image=self.orig_photo)
        self.sharp_label.configure(image=self.sharp_photo)

    # ----------------------------- send frame -----------------------------
    def send_image(self) -> None:
        if self.ser is None:
            messagebox.showinfo("未连接", "请先连接串口再发送图像。\n（软件预览/缩放无需连接即可使用）")
            return
        if self.rgb_image is None:
            messagebox.showinfo("无图片", "请先载入图片。")
            return
        if self._sending_frame:
            return
        self._sending_frame = True
        self.send_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在发送图像…")
        packet = build_frame_packet(self.rgb_image)
        threading.Thread(target=self._send_frame_worker, args=(packet,), daemon=True).start()

    def _send_frame_worker(self, packet: bytes) -> None:
        ok = self._write(packet)
        if ok:
            self.push_all_controls()
        self.log_queue.put("__frame_done__:" + ("ok" if ok else "fail"))

    # ----------------------------- logging / lifecycle -----------------------------
    def _log(self, message: str) -> None:
        self.log_queue.put(f"[{time.strftime('%H:%M:%S')}] {message}")

    def _drain_log_queue(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg.startswith("__frame_done__:"):
                    ok = msg.split(":", 1)[1] == "ok"
                    self._sending_frame = False
                    self.send_btn.configure(state=tk.NORMAL)
                    self.status_var.set("图像已发送" if ok else "图像发送失败")
                    self._append_log(f"[{time.strftime('%H:%M:%S')}] "
                                     + ("图像发送完成" if ok else "图像发送失败"))
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def on_close(self) -> None:
        self._close_serial()
        self.after(80, self.destroy)


def main() -> int:
    if DEPENDENCY_ERROR is not None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "缺少 Python 依赖",
            "Python 依赖未就绪。\n\n"
            f"{DEPENDENCY_ERROR}\n\n"
            "请先安装：\n  pip install -r requirements.txt",
        )
        return 1
    app = SharpenGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
