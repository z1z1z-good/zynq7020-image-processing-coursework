#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import serial


FRAME_SYNC = bytes((0x55, 0xAA))
LINE_SYNC = bytes((0x33, 0xCC))
CONTROL_SYNC = bytes((0xA5, 0x5A))
RGB888_FORMAT = 0x18
CONTROL_MODE = 0x01
CONTROL_THRESHOLD = 0x02
CONTROL_OVERLAY = 0x03

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}

FIT_MODES = ("stretch", "letterbox", "center-crop")
PROC_SIZES = ("128x72", "64x36")


class FrameSource:
    def __init__(
        self,
        source: str,
        camera: int = 0,
        image: str | None = None,
        images: list[str] | None = None,
        image_dir: str | None = None,
        video: str | None = None,
        loop: bool = False,
    ) -> None:
        self.source = source
        self.camera = camera
        self.image = image
        self.images = images or []
        self.image_dir = image_dir
        self.video = video
        self.loop = loop
        self.cap = None
        self.static_bgr = None
        self.image_paths: list[Path] = []
        self.image_index = 0

    def open(self) -> None:
        if self.source == "camera":
            self.cap = cv2.VideoCapture(self.camera)
            if not self.cap.isOpened():
                raise RuntimeError(f"failed to open camera {self.camera}")
            return

        if self.source == "image":
            if self.image is None:
                raise RuntimeError("image path is required")
            self.static_bgr = cv2.imread(self.image, cv2.IMREAD_COLOR)
            if self.static_bgr is None:
                raise RuntimeError(f"failed to open image {self.image}")
            return

        if self.source == "images":
            self.image_paths = collect_image_paths(self.images, self.image_dir)
            if not self.image_paths:
                raise RuntimeError("no input image files found")
            return

        if self.source == "video":
            if self.video is None:
                raise RuntimeError("video path is required")
            self.cap = cv2.VideoCapture(self.video)
            if not self.cap.isOpened():
                raise RuntimeError(f"failed to open video {self.video}")
            return

        raise RuntimeError(f"unsupported source: {self.source}")

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.source == "image":
            return True, self.static_bgr.copy()

        if self.source == "images":
            if self.image_index >= len(self.image_paths):
                if not self.loop:
                    return False, None
                self.image_index = 0

            path = self.image_paths[self.image_index]
            self.image_index += 1
            frame_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if frame_bgr is None:
                raise RuntimeError(f"failed to open image {path}")
            return True, frame_bgr

        if self.source == "video":
            ok, frame_bgr = self.cap.read()
            if ok:
                return True, frame_bgr
            if not self.loop:
                return False, None
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame_bgr = self.cap.read()
            return ok, frame_bgr if ok else None

        ok, frame_bgr = self.cap.read()
        return ok, frame_bgr if ok else None

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def describe(self) -> str:
        if self.source == "camera":
            return f"camera {self.camera}"
        if self.source == "image":
            return f"image {self.image}"
        if self.source == "images":
            return f"{len(self.image_paths)} image files"
        if self.source == "video":
            return f"video {self.video}"
        return self.source


def collect_image_paths(images: list[str] | None = None, image_dir: str | None = None) -> list[Path]:
    paths: list[Path] = []

    for image in images or []:
        path = Path(image)
        if not path.is_file():
            raise RuntimeError(f"image file does not exist: {path}")
        paths.append(path)

    if image_dir:
        directory = Path(image_dir)
        if not directory.is_dir():
            raise RuntimeError(f"image directory does not exist: {directory}")
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                paths.append(path)

    return paths


def resolve_source(args: argparse.Namespace) -> str:
    selected = [
        args.image is not None,
        bool(args.images),
        args.image_dir is not None,
        args.video is not None,
    ]
    if sum(selected) > 1:
        raise ValueError("choose only one of --image, --images, --image-dir, or --video")
    if args.image is not None:
        return "image"
    if args.images or args.image_dir is not None:
        return "images"
    if args.video is not None:
        return "video"
    return "camera"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resize camera/image/video frames to RGB888 and send them to ZYNQ PS UART."
    )
    parser.add_argument("--port", required=True, help="Serial port, for example COM5 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115_200, help="UART baud rate")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--fps", type=float, default=0.2, help="Send frame rate")
    parser.add_argument("--width", type=int, default=128, help="Output image width")
    parser.add_argument("--height", type=int, default=72, help="Output image height")
    parser.add_argument(
        "--fit-mode",
        choices=FIT_MODES,
        default="stretch",
        help="How any-size input is fitted into the fixed output frame "
        "(stretch=resize, letterbox=pad, center-crop=crop)",
    )
    parser.add_argument(
        "--proc-size",
        choices=PROC_SIZES,
        default="128x72",
        help="Host processing resolution; 64x36 renders a coarser image but still "
        "transmits the fixed output size",
    )
    parser.add_argument(
        "--fill-color",
        help="Letterbox padding colour as 'R,G,B' (0..255 each); default black",
    )
    parser.add_argument("--image", help="Send one image file instead of reading the camera")
    parser.add_argument("--images", nargs="+", help="Send several image files in the given order")
    parser.add_argument("--image-dir", help="Send all supported images in one directory, sorted by file name")
    parser.add_argument("--video", help="Send frames from a video file such as MP4")
    parser.add_argument("--loop", action="store_true", help="Loop image sequence or video after reaching the end")
    parser.add_argument("--once", action="store_true", help="Send one frame and exit")
    parser.add_argument("--preview", action="store_true", help="Show a local preview window")
    parser.add_argument("--flip", action="store_true", help="Horizontally flip the camera/image/video frame")
    parser.add_argument("--line-delay", type=float, default=0.0, help="Delay after each line, in seconds")
    parser.add_argument(
        "--mode",
        choices=("original", "gray", "edge", "overlay"),
        help="sobel_05 display mode control command",
    )
    parser.add_argument("--threshold", type=int, help="sobel_05 threshold control command, 0..255")
    parser.add_argument(
        "--overlay",
        choices=("off", "on"),
        help="sobel_05 color edge overlay control command",
    )
    parser.add_argument("--control-only", action="store_true", help="Send only sobel_05 control commands and exit")
    return parser.parse_args()


def _interpolation(dst_w: int, dst_h: int, src_w: int, src_h: int) -> int:
    # Shrinking favours INTER_AREA, enlarging favours INTER_LINEAR.
    if dst_w * dst_h <= src_w * src_h:
        return cv2.INTER_AREA
    return cv2.INTER_LINEAR


def _fit_bgr(
    frame_bgr: np.ndarray,
    width: int,
    height: int,
    fit_mode: str,
    fill: tuple[int, int, int],
) -> np.ndarray:
    src_h, src_w = frame_bgr.shape[:2]

    if fit_mode == "stretch":
        interp = _interpolation(width, height, src_w, src_h)
        return cv2.resize(frame_bgr, (width, height), interpolation=interp)

    if fit_mode == "letterbox":
        scale = min(width / src_w, height / src_h)
        new_w = max(1, min(width, round(src_w * scale)))
        new_h = max(1, min(height, round(src_h * scale)))
        resized = cv2.resize(
            frame_bgr, (new_w, new_h), interpolation=_interpolation(new_w, new_h, src_w, src_h)
        )
        canvas = np.empty((height, width, 3), dtype=np.uint8)
        canvas[:, :] = fill
        x0 = (width - new_w) // 2
        y0 = (height - new_h) // 2
        canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
        return canvas

    if fit_mode == "center-crop":
        scale = max(width / src_w, height / src_h)
        new_w = max(width, round(src_w * scale))
        new_h = max(height, round(src_h * scale))
        resized = cv2.resize(
            frame_bgr, (new_w, new_h), interpolation=_interpolation(new_w, new_h, src_w, src_h)
        )
        x0 = (new_w - width) // 2
        y0 = (new_h - height) // 2
        return resized[y0:y0 + height, x0:x0 + width]

    raise ValueError(f"unsupported fit_mode: {fit_mode!r}")


def prepare_frame(
    frame_bgr: np.ndarray,
    width: int = 128,
    height: int = 72,
    fit_mode: str = "stretch",
    content_size: tuple[int, int] | None = None,
    fill: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """Map a BGR frame of any size onto a fixed width x height RGB888 array.

    fit_mode controls how the source aspect ratio is reconciled with the fixed
    output frame (Plan A: all scaling happens on the host, the FPGA always
    receives width x height):

        stretch     resize straight to width x height; aspect may change
                    (default; byte-for-byte identical to the previous tool when
                    downscaling, which is the normal 128x72 case)
        letterbox   uniform scale by min(W/w, H/h), centre, pad the margin with
                    fill; the subject keeps its aspect ratio
        center-crop uniform scale by max(W/w, H/h), centre-crop to width x height;
                    fills the frame with no padding bars

    Downscaling uses INTER_AREA, upscaling uses INTER_LINEAR.

    content_size optionally renders the picture at a coarser processing size
    (e.g. (64, 36)) first and then nearest-neighbour upsamples it back into the
    fixed width x height transmit frame. The HDMI image then looks coarser while
    the wire format stays width x height. None keeps the full output resolution.

    fill is a BGR triple (matching the BGR input convention) used for letterbox
    padding; after BGR->RGB the padded margin reads back as fill reversed.

    Returns an (height, width, 3) uint8 RGB array ready for build_frame_packet
    and send_frame_by_line.
    """
    if content_size is not None and tuple(content_size) != (width, height):
        proc_w, proc_h = content_size
        if proc_w <= 0 or proc_h <= 0:
            raise ValueError("content_size dimensions must be positive")
        content_bgr = _fit_bgr(frame_bgr, proc_w, proc_h, fit_mode, fill)
        # Upsample the coarse content back to the fixed transmit frame; nearest
        # neighbour keeps the enlarged pixels crisp so the lower processing
        # resolution stays visible on HDMI.
        fitted_bgr = cv2.resize(content_bgr, (width, height), interpolation=cv2.INTER_NEAREST)
    else:
        fitted_bgr = _fit_bgr(frame_bgr, width, height, fit_mode, fill)

    return cv2.cvtColor(fitted_bgr, cv2.COLOR_BGR2RGB)


def parse_proc_size(value: str, width: int, height: int) -> tuple[int, int] | None:
    """Map a --proc-size choice such as '64x36' to a content_size for
    prepare_frame. The transmit size (width x height) means full resolution and
    returns None."""
    proc_w, proc_h = (int(part) for part in value.lower().split("x"))
    if proc_w <= 0 or proc_h <= 0:
        raise ValueError("--proc-size dimensions must be positive")
    if (proc_w, proc_h) == (width, height):
        return None
    return (proc_w, proc_h)


def parse_fill_color(value: str) -> tuple[int, int, int]:
    """Parse a 'R,G,B' string (0..255 each) into a BGR fill tuple for
    prepare_frame's letterbox padding."""
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError("--fill-color must be 'R,G,B', for example '0,0,0'")
    r, g, b = (int(part) for part in parts)
    for channel in (r, g, b):
        if not 0 <= channel <= 255:
            raise ValueError("--fill-color channels must be in range 0..255")
    return (b, g, r)


def build_frame_packet(rgb_image: np.ndarray) -> bytes:
    height, width, channels = rgb_image.shape
    if channels != 3:
        raise ValueError("RGB image must have 3 channels")
    if rgb_image.dtype != np.uint8:
        raise ValueError("RGB image must be uint8")

    packet = bytearray()
    packet.extend(FRAME_SYNC)
    packet.extend((width & 0xFF, (width >> 8) & 0xFF))
    packet.extend((height & 0xFF, (height >> 8) & 0xFF))
    packet.append(RGB888_FORMAT)

    contiguous = np.ascontiguousarray(rgb_image)
    for row in range(height):
        packet.extend(LINE_SYNC)
        packet.extend((row & 0xFF, (row >> 8) & 0xFF))
        packet.extend(contiguous[row].tobytes())

    return bytes(packet)


def send_frame_by_line(ser: serial.Serial, rgb_image: np.ndarray, line_delay: float) -> None:
    height, width, _ = rgb_image.shape
    ser.write(FRAME_SYNC)
    ser.write(bytes((width & 0xFF, (width >> 8) & 0xFF)))
    ser.write(bytes((height & 0xFF, (height >> 8) & 0xFF)))
    ser.write(bytes((RGB888_FORMAT,)))

    contiguous = np.ascontiguousarray(rgb_image)
    for row in range(height):
        ser.write(LINE_SYNC)
        ser.write(bytes((row & 0xFF, (row >> 8) & 0xFF)))
        ser.write(contiguous[row].tobytes())
        if line_delay > 0.0:
            time.sleep(line_delay)


def send_control_command(ser: serial.Serial, command: int, value: int) -> None:
    if not 0 <= value <= 255:
        raise ValueError("control command value must be in range 0..255")
    ser.write(CONTROL_SYNC)
    ser.write(bytes((command & 0xFF, value & 0xFF)))


def send_requested_controls(
    ser: serial.Serial,
    mode: str | None = None,
    threshold: int | None = None,
    overlay: str | None = None,
) -> None:
    mode_values = {
        "original": 0,
        "gray": 1,
        "edge": 2,
        "overlay": 3,
    }
    if mode is not None:
        send_control_command(ser, CONTROL_MODE, mode_values[mode])
    if threshold is not None:
        if not 0 <= threshold <= 255:
            raise ValueError("--threshold must be in range 0..255")
        send_control_command(ser, CONTROL_THRESHOLD, threshold)
    if overlay is not None:
        send_control_command(ser, CONTROL_OVERLAY, 1 if overlay == "on" else 0)


def main() -> int:
    args = parse_args()
    source_name = resolve_source(args)

    if args.width != 128 or args.height != 72:
        print("warning: PS receiver currently accepts only 128x72 RGB888", file=sys.stderr)
    if args.fps <= 0:
        raise ValueError("--fps must be greater than 0")
    if args.line_delay < 0:
        raise ValueError("--line-delay cannot be negative")
    if args.control_only and not any(
        value is not None for value in (args.mode, args.threshold, args.overlay)
    ):
        raise ValueError("--control-only needs at least one of --mode, --threshold, or --overlay")

    content_size = parse_proc_size(args.proc_size, args.width, args.height)
    fill = parse_fill_color(args.fill_color) if args.fill_color else (0, 0, 0)

    source = FrameSource(
        source=source_name,
        camera=args.camera,
        image=args.image,
        images=args.images,
        image_dir=args.image_dir,
        video=args.video,
        loop=args.loop,
    )

    if not args.control_only:
        source.open()

    frame_interval = 1.0 / args.fps
    frame_count = 0

    try:
        with serial.Serial(args.port, args.baud, timeout=0, write_timeout=2) as ser:
            time.sleep(0.2)
            send_requested_controls(ser, args.mode, args.threshold, args.overlay)
            if any(value is not None for value in (args.mode, args.threshold, args.overlay)):
                print("sent sobel_05 control command(s)")
            if args.control_only:
                return 0

            print(
                f"sending {args.width}x{args.height} RGB888 ({args.fit_mode}, "
                f"proc {args.proc_size}) from {source.describe()} "
                f"to {args.port} at {args.baud} baud"
            )

            last_src_size: tuple[int, int] | None = None
            while True:
                start = time.monotonic()
                ok, frame_bgr = source.read()
                if not ok or frame_bgr is None:
                    break

                if args.flip:
                    frame_bgr = cv2.flip(frame_bgr, 1)

                src_h, src_w = frame_bgr.shape[:2]
                if (src_w, src_h) != last_src_size:
                    if content_size is None:
                        proc_desc = f"{args.width}x{args.height}"
                    else:
                        proc_desc = (
                            f"{content_size[0]}x{content_size[1]} content -> "
                            f"{args.width}x{args.height}"
                        )
                    print(f"input {src_w}x{src_h} -> {proc_desc} ({args.fit_mode})")
                    last_src_size = (src_w, src_h)

                frame_rgb = prepare_frame(
                    frame_bgr, args.width, args.height, args.fit_mode, content_size, fill
                )
                send_frame_by_line(ser, frame_rgb, args.line_delay)
                frame_count += 1

                if args.preview:
                    preview_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                    preview = cv2.resize(
                        preview_bgr,
                        (args.width * 5, args.height * 5),
                        interpolation=cv2.INTER_NEAREST,
                    )
                    cv2.imshow("camera uart sender", preview)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break

                if frame_count % 10 == 0:
                    print(f"sent {frame_count} frames")

                if args.once:
                    break

                elapsed = time.monotonic() - start
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        source.close()
        if args.preview:
            cv2.destroyAllWindows()

    print(f"sent {frame_count} frame(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
