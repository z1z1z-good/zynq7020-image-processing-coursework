#!/usr/bin/env python3
"""Render selected experiment-0 VCD signals as a compact SVG."""

from __future__ import annotations

import argparse
import html
from pathlib import Path


SIGNALS = (
    ("frame_start", "frame_start"),
    ("rgb_valid", "rgb_valid"),
    ("gray_valid", "gray_valid"),
    ("edge_valid", "edge_valid"),
    ("video_frame_done", "edge_frame_done (mirrored)"),
)


def read_transitions(path: Path) -> tuple[dict[str, list[tuple[int, int]]], int]:
    ids: dict[str, str] = {}
    selected_ids: dict[str, str] = {}
    transitions = {name: [] for name, _ in SIGNALS}
    current_time = 0
    final_time = 0
    in_header = True

    with path.open("r", encoding="ascii", errors="replace") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if not line:
                continue

            if in_header:
                if line.startswith("$var "):
                    fields = line.split()
                    if len(fields) >= 5:
                        identifier = fields[3]
                        reference = fields[4]
                        ids[identifier] = reference
                elif line == "$enddefinitions $end":
                    in_header = False
                    wanted = {name for name, _ in SIGNALS}
                    selected_ids = {
                        identifier: reference
                        for identifier, reference in ids.items()
                        if reference in wanted
                    }
                continue

            if line.startswith("#"):
                current_time = int(line[1:])
                final_time = current_time
                continue

            if line[0] in "01xz" and line[1:] in selected_ids:
                name = selected_ids[line[1:]]
                value = 1 if line[0] == "1" else 0
                if not transitions[name] or transitions[name][-1][1] != value:
                    transitions[name].append((current_time, value))

    missing = [name for name, _ in SIGNALS if not transitions[name]]
    if missing:
        raise SystemExit(f"{path}: missing transitions for {', '.join(missing)}")

    return transitions, final_time


def rising_edges(points: list[tuple[int, int]]) -> list[int]:
    return [time for time, value in points if value == 1]


def value_at(points: list[tuple[int, int]], target: int) -> int:
    value = 0
    for time, next_value in points:
        if time > target:
            break
        value = next_value
    return value


def clipped_points(
    points: list[tuple[int, int]], start: int, end: int
) -> list[tuple[int, int]]:
    result = [(start, value_at(points, start))]
    result.extend((time, value) for time, value in points if start < time <= end)
    if result[-1][0] != end:
        result.append((end, result[-1][1]))
    return result


def svg_path(
    points: list[tuple[int, int]],
    start: int,
    end: int,
    x0: float,
    width: float,
    y_low: float,
    y_high: float,
) -> str:
    clipped = clipped_points(points, start, end)

    def x_pos(time: int) -> float:
        return x0 + ((time - start) / max(end - start, 1)) * width

    def y_pos(value: int) -> float:
        return y_high if value else y_low

    commands = [f"M {x_pos(clipped[0][0]):.2f} {y_pos(clipped[0][1]):.2f}"]
    previous_value = clipped[0][1]
    for time, value in clipped[1:]:
        x = x_pos(time)
        commands.append(f"H {x:.2f}")
        if value != previous_value:
            commands.append(f"V {y_pos(value):.2f}")
            previous_value = value
    return " ".join(commands)


def render_svg(
    transitions: dict[str, list[tuple[int, int]]],
    final_time: int,
    output: Path,
) -> None:
    frame_start_time = rising_edges(transitions["frame_start"])[-1]
    frame_done_time = rising_edges(transitions["video_frame_done"])[-1]

    windows = (
        (
            "Valid frame start",
            max(0, frame_start_time - 50_000_000),
            min(final_time, frame_start_time + 150_000_000),
            frame_start_time,
        ),
        (
            "Sobel frame completion",
            max(0, frame_done_time - 100_000_000),
            min(final_time, frame_done_time + 10_000_000),
            frame_done_time,
        ),
    )

    width = 1600
    height = 760
    left = 285
    right = 45
    plot_width = width - left - right
    panel_height = 300
    row_height = 48
    colors = ("#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Consolas, 'Microsoft YaHei', sans-serif; fill: #e5e7eb; }",
        ".title { font-size: 27px; font-weight: 700; }",
        ".subtitle { font-size: 17px; fill: #94a3b8; }",
        ".label { font-size: 17px; }",
        ".tick { font-size: 14px; fill: #94a3b8; }",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#0f172a"/>',
        '<text x="40" y="45" class="title">Experiment 0: default RTL simulation waveform</text>',
        (
            '<text x="40" y="75" class="subtitle">'
            "Source: ModelSim-generated VCD; edge_frame_done is observed through "
            "video_frame_done, its registered mirror."
            "</text>"
        ),
    ]

    for panel_index, (title, start, end, marker) in enumerate(windows):
        top = 110 + panel_index * 330
        plot_top = top + 48
        parts.append(
            f'<rect x="25" y="{top}" width="{width - 50}" height="{panel_height}" '
            'rx="10" fill="#111827" stroke="#334155"/>'
        )
        parts.append(f'<text x="45" y="{top + 32}" class="title">{html.escape(title)}</text>')

        for tick in range(6):
            ratio = tick / 5
            x = left + ratio * plot_width
            time = start + int(ratio * (end - start))
            parts.append(
                f'<line x1="{x:.2f}" y1="{plot_top - 8}" x2="{x:.2f}" '
                f'y2="{plot_top + row_height * len(SIGNALS)}" stroke="#243244"/>'
            )
            parts.append(
                f'<text x="{x:.2f}" y="{plot_top + row_height * len(SIGNALS) + 25}" '
                f'class="tick" text-anchor="middle">{time / 1_000_000:.3f} us</text>'
            )

        marker_x = left + ((marker - start) / max(end - start, 1)) * plot_width
        parts.append(
            f'<line x1="{marker_x:.2f}" y1="{plot_top - 12}" x2="{marker_x:.2f}" '
            f'y2="{plot_top + row_height * len(SIGNALS)}" stroke="#f87171" '
            'stroke-width="2" stroke-dasharray="7 5"/>'
        )

        for row, ((name, label), color) in enumerate(zip(SIGNALS, colors)):
            center = plot_top + row * row_height + 18
            y_high = center - 12
            y_low = center + 12
            parts.append(
                f'<text x="{left - 18}" y="{center + 6}" class="label" '
                f'text-anchor="end">{html.escape(label)}</text>'
            )
            parts.append(
                f'<line x1="{left}" y1="{y_low}" x2="{left + plot_width}" y2="{y_low}" '
                'stroke="#1f2937"/>'
            )
            path = svg_path(
                transitions[name], start, end, left, plot_width, y_low, y_high
            )
            parts.append(
                f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" '
                'stroke-linejoin="round"/>'
            )

    parts.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Valid frame_start: {frame_start_time / 1_000_000:.3f} us")
    print(f"Mirrored edge_frame_done: {frame_done_time / 1_000_000:.3f} us")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd", type=Path, default=Path("build/sobel_system_tb.vcd"))
    parser.add_argument(
        "--output", type=Path, default=Path("build/exp00_key_waveform.svg")
    )
    args = parser.parse_args()

    transitions, final_time = read_transitions(args.vcd)
    render_svg(transitions, final_time, args.output)


if __name__ == "__main__":
    main()
