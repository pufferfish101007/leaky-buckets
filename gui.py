from interpreter import Program
from tkinter import Tk, Canvas, simpledialog, messagebox
from tkinter.ttk import Frame, Label, Button
from enum import StrEnum
from collections.abc import Generator
from typing import Never, Self, Callable, Literal
from itertools import product
from math import ceil
from dataclasses import dataclass


class ProgramStatus(StrEnum):
    Running = "Running"
    Terminated = "Terminated"
    Error = "Error"


TILE_SIZE = 75


@dataclass
class CanvasOffset:
    offset: tuple[int, int] = (0, 0)

    def __getitem__(self, key: Literal[0] | Literal[1]) -> int:
        return self.offset[key]


class Tile:
    world_x: int = 0
    world_y: int = 0

    canvas: Canvas
    rect: int
    text: int

    program: Program

    is_static: bool = False

    info: str = ""

    mouse_on: bool = False
    show_info: Callable[[str], None]

    offset: CanvasOffset

    def __init__(
        self,
        canvas: Canvas,
        program: Program,
        show_info: Callable[[str], None],
        offset: CanvasOffset,
    ):
        self.canvas = canvas
        self.program = program
        self.rect = canvas.create_rectangle(0, 0, 0, 0)
        self.text = canvas.create_text(0, 0)
        self.show_info = show_info
        self.offset = offset
        canvas.tag_bind(self.rect, "<Enter>", lambda _: self.mouse_over())
        canvas.tag_bind(self.rect, "<Leave>", lambda _: self.mouse_out())

    def mouse_over(self):
        self.mouse_on = True
        self.show_info(self.info)

    def mouse_out(self) -> None:
        self.mouse_on = False

    def set_world_coords(self, x: int, y: int) -> Self:
        self.world_x = x
        self.world_y = y

        self.canvas.tag_raise(self.text)

        self.is_static = self.world_coords() in [
            self.program.depot_pos,
            self.program.tap_pos,
            self.program.pond_pos,
        ]
        self.update(force=True)

        return self

    def update_canvas_pos(self):
        x = self.world_x + self.offset[0]
        y = self.world_y + self.offset[1]

        self.canvas.coords(
            self.rect,
            x * TILE_SIZE,
            y * TILE_SIZE,
            x * TILE_SIZE + TILE_SIZE,
            y * TILE_SIZE + TILE_SIZE,
        )
        self.canvas.coords(
            self.text, x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2
        )

    def update(self, force: bool = False) -> None:
        if (not force) and self.is_static:
            return

        self.update_canvas_pos()

        if self.world_coords() == self.program.depot_pos:
            self.canvas.itemconfigure(
                self.rect, fill="#783302", outline="#565656", width=2
            )
            self.info = f"Bucket depot @ {self.world_coords()}"
            self.canvas.itemconfigure(self.text, text="depot")
        elif self.world_coords() == self.program.tap_pos:
            self.canvas.itemconfigure(
                self.rect, fill="#565656", outline="black", width=0
            )
            self.info = f"Tap @ {self.world_coords()}"
            self.canvas.itemconfigure(self.text, text="tap")
        elif self.world_coords() == self.program.pond_pos:
            self.canvas.itemconfigure(
                self.rect, fill="#00786E", outline="black", width=0
            )
            self.info = f"Pond @ {self.world_coords()}"
            self.canvas.itemconfigure(self.text, text="pond")
        elif self.world_coords() in self.program.buckets:
            bucket = self.program.buckets[self.world_coords()]
            if bucket.water > 0:
                self.canvas.itemconfigure(
                    self.rect, fill="#0162D0", outline="#783302", width=5
                )
                self.info = f"{bucket.capacity // 100} pint bucket with {bucket.holes} holes, {bucket.water / 100} pints full @ {self.world_coords()}"
                self.canvas.itemconfigure(self.text, text=f"{bucket.water / 100}")
            else:
                self.canvas.itemconfigure(
                    self.rect, fill="#783302", outline="#5c2702", width=5
                )
                self.info = f"Empty {bucket.capacity // 100} pint bucket with {bucket.holes} holes @ {self.world_coords()}"
                self.canvas.itemconfigure(self.text, text="empty")
        else:
            if (
                self.world_coords() not in self.program.water
                or self.program.water[self.world_coords()] == 0
            ):
                self.canvas.itemconfigure(
                    self.rect, fill="#00a500", outline="black", width=1
                )
                self.info = f"Dry ground @ {self.world_coords()}"
                self.canvas.itemconfigure(self.text, text="")
            else:
                self.canvas.itemconfigure(
                    self.rect, fill="#009fa5", outline="black", width=1
                )
                self.info = f"Ground wet with {self.program.water[self.world_coords()] / 100} pints @ {self.world_coords()}"
                self.canvas.itemconfigure(
                    self.text,
                    text=f"{self.program.water[self.world_coords()] / 100} pints",
                )

        if self.world_coords() == self.program.pos:
            self.canvas.itemconfigure(self.rect, outline="red", width=5)
            self.canvas.tag_raise(self.rect)
            self.canvas.tag_raise(self.text)

        if self.mouse_on:
            self.show_info(self.info)

    def world_coords(self) -> tuple[int, int]:
        return (self.world_x, self.world_y)


CANVAS_SIZE = 600


class GUI:
    program: Program
    window: Tk
    filename: str

    status: ProgramStatus
    runner: Generator[None]
    running: bool = False

    status_label: Label
    line_label: Label
    holding_label: Label
    step_button: Button
    step_time_label: Label
    step_time_button: Button
    run_button: Button
    canvas: Canvas
    output_box: Label

    step_wait: int = 1000
    tiles: list[Tile]
    canvas_offset: CanvasOffset = CanvasOffset()

    def __init__(self, filename: str) -> None:
        self.filename = filename

        program = Program()

        with open(filename, encoding="utf-8") as f:
            program.parse_lines(f.readlines())

        self.program = program

        self.program.output = self.output
        self.program.input_char = self.input_char
        self.program.input_int = self.input_int
        self.program.error = self.error

        self.window = Tk()

        self.tiles = []

        frame = Frame(self.window, padding=10)
        frame.grid()

        self.status_label = Label(frame, text="")
        self.status_label.grid(column=0, row=0)
        self.line_label = Label(frame, text="")
        self.line_label.grid(column=0, row=1)
        self.holding_label = Label(frame, text="")
        self.holding_label.grid(column=0, row=2)
        self.status = ProgramStatus.Running

        self.hover_label = Label(frame, text="")
        self.hover_label.grid(column=0, row=3, sticky="W")

        self.runner = self.program.run_iter()

        # Label(frame, text="moo").grid(column=-1, row=0)

        center_frame = Frame(frame)
        center_frame.grid(column=0, row=4)

        self.canvas = Canvas(center_frame, width=CANVAS_SIZE, height=CANVAS_SIZE)
        self.canvas.grid(column=0, row=0)
        self.canvas.bind("<Leave>", lambda _: self.show_hover_text(""))

        button_frame = Frame(center_frame, padding=10)
        button_frame.grid(column=1, row=0, sticky="N")

        Button(button_frame, text="Reset", command=self.reset).grid(column=0, row=0)

        self.run_button = Button(button_frame, text="Run", command=self.toggle_run)
        self.run_button.grid(column=0, row=1)

        self.step_button = Button(button_frame, text="Step forwards", command=self.step)
        self.step_button.grid(column=0, row=2)

        self.step_time_label = Label(button_frame, text="")
        self.step_time_label.grid(column=0, row=3, pady=(20, 5))

        self.step_time_button = Button(button_frame, text="Change step time", command=self.change_step_time)
        self.step_time_button.grid(column=0, row=4)

        self.update_status_label()

        Label(button_frame, text="Output:").grid(column=0, row=5, sticky="W", pady=(20, 5))
        self.output_box = Label(button_frame, text="")
        self.output_box.grid(column=0, row=6, sticky="W")

        tile_num = ceil(CANVAS_SIZE / TILE_SIZE)
        
        self.canvas_offset.offset = ((tile_num - 1) // 2, (tile_num - 1) // 2)

        for i, j in product(
            range(tile_num), range(tile_num)
        ):
            self.tiles.append(
                Tile(
                    self.canvas, self.program, self.show_hover_text, self.canvas_offset
                ).set_world_coords(i - self.canvas_offset[0], j - self.canvas_offset[1])
            )

        self.window.mainloop()

    def show_hover_text(self, text: str) -> None:
        self.hover_label["text"] = text

    def update(self):
        self.update_status_label()
        for tile in self.tiles:
            tile.update()
        bucket = self.program.current_bucket
        if bucket is not None:
            if bucket.water == 0:
                self.holding_label["text"] = (
                    f"Holding an empty {bucket.capacity // 100} pint bucket with {bucket.holes} holes"
                )
            else:
                self.holding_label["text"] = (
                    f"Carrying {bucket.water / 100} pints in a {bucket.capacity // 100} pint bucket with {bucket.holes} holes"
                )
        elif self.program.lines[self.program.line_counter] == "put wellies on":
            self.holding_label["text"] = (
                f"Putting wellies on. I am now wearing {self.program.wellies_count} pairs of wellies"
            )
        elif self.program.lines[self.program.line_counter] == "take wellies off":
            self.holding_label["text"] = (
                f"Taking wellies off. I am now wearing {self.program.wellies_count} pairs of wellies"
            )
        else:
            self.holding_label["text"] = (
                f"My hands are empty. I am wearing {self.program.wellies_count} pairs of wellies"
            )

    def change_step_time(self):
        new_time = simpledialog.askinteger("Leaky buckets", "Step wait time (ms):", minvalue=1)
        if new_time is not None:
            self.step_wait = new_time

    def update_status_label(self):
        self.status_label["text"] = (
            f"{self.status}: {self.filename} @ L{self.program.line_counter}"
        )
        if self.program.line_counter < len(self.program.lines):
            self.line_label["text"] = self.program.lines[self.program.line_counter]  # type: ignore
        else: self.line_label["text"] = ""
        self.step_time_label["text"] = f"Step wait time: {self.step_wait}ms"

    def reset(self):
        self.program.__init__()
        self.step_button["state"] = "enabled"
        self.running = False
        self.run_button["text"] = "Run"
        self.runner = self.program.run_iter()
        self.update()

    def step(self):
        self.update()
        try:
            next(self.runner)
        except StopIteration:
            self.status = ProgramStatus.Terminated
            self.step_button["state"] = "disabled"
            if self.running:
                self.toggle_run()
        self.update()

    def run(self) -> None:
        if self.running:
            self.step()
            self.window.after(self.step_wait, self.run)

    def toggle_run(self) -> None:
        self.running = not self.running
        if not self.running:
            self.run_button["text"] = "Run"
        else:
            self.run_button["text"] = "Pause"
            self.run()

    def output(self, output: str | int | float):
        if isinstance(output, str):
            self.output_box["text"] += output
        else:
            self.output_box["text"] += f"\n{output}"

    def input_char(self, prompt: str = "Enter a character:") -> int:
        char = simpledialog.askstring("Leaky buckets input", prompt)
        if char is None:
            return self.input_char("Enter a character (got None last time):")
        return ord(char)

    def input_int(self, prompt: str = "Enter an integer:") -> int:
        i = simpledialog.askinteger("Leaky buckets input", prompt)
        if i is None:
            return self.input_int("Enter an integer (got None last time):")
        return i

    def error(self, error: str, line_num: int | None = None, type: str = "") -> Never:
        if line_num is None:
            stacktrace = ""
        else:
            stacktrace = f"\n\tat line {line_num}"
        self.status = ProgramStatus.Error
        messagebox.showerror(
            title="An error occurred",
            message=f"{type}Error: {error}{stacktrace}",
        )
        exit(1)
