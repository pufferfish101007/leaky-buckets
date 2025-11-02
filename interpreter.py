#! /usr/bin/python3

# The leaky bucket interpreter

from sys import argv
import re
from dataclasses import dataclass
from typing import Never, Literal

# the following definition of getch (get character) is from
# https://code.activestate.com/recipes/134892/


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""

    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self):  # type: ignore
        return self.impl()  # type: ignore


class _GetchUnix:
    def __init__(self):
        import tty, sys  # type: ignore

    def __call__(self):
        import sys, tty, termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt  # type: ignore

    def __call__(self):  # type: ignore
        import msvcrt

        return msvcrt.getch()  # type: ignore


_getch = _Getch()


def getch():  # type: ignore
    ch = _getch()  # type: ignore
    print(ch, end="")  # type: ignore
    return ch  # type: ignore


def error(error: str, line_num: int | None = None, type: str = "") -> Never:
    if line_num is None:
        stacktrace = ""
    else:
        stacktrace = f"\n\tat line {line_num}"
    print(f"{type}Error: {error}{stacktrace}")
    exit(1)


def unreachable(line_num: int | None = None) -> Never:
    error("unreachable", line_num)


facing = "(in front of me|to my left|behind me|to my right)"


def facing_to_relative_dir(facing: str):
    match facing:
        case "in front of me":
            return "N"
        case "behind me":
            return "S"
        case "to my right":
            return "E"
        case "to my left":
            return "W"
        case _:
            unreachable()


type Direction = Literal["N"] | Literal["E"] | Literal["S"] | Literal["W"]

directions: list[Direction] = ["N", "E", "S", "W"]

type Pos = tuple[int, int]


def relative_direction_to_absolute(
    current_dir: Direction, relative_dir: Direction
) -> Direction:
    return directions[
        (directions.index(current_dir) + directions.index(relative_dir)) % 4
    ]


def direction_to_relative_pos(absolute_dir: Direction) -> Pos:
    return [(0, 1), (1, 0), (0, -1), (-1, 0)][directions.index(absolute_dir)]


def add_pos(pos1: Pos, pos2: Pos):
    return (pos1[0] + pos2[0], pos1[1] + pos2[1])


def mul_pos(scalar: int, pos: Pos):
    return (scalar * pos[0], scalar * pos[1])


@dataclass
class Bucket:
    """capacity in centipints"""

    capacity: int
    holes: int = 0
    """water level in centipints"""
    water: int = 0


@dataclass
class Branch:
    n: int


@dataclass
class Program:
    buckets: dict[Pos, Bucket]
    water: dict[Pos, int]  # pos -> centipints
    pos: Pos
    direction: Direction
    depot_pos: Pos
    tap_pos: Pos
    pond_pos: Pos
    current_bucket: Bucket | None
    mode: str
    mode_changed: bool
    wellies_count: int
    wellies_stack: list[tuple[int, Pos, Direction]]
    time: int

    def __init__(self):
        self.buckets = dict()
        self.water = dict()
        self.pos = (0, 0)
        self.depot_pos = (0, 1)
        self.tap_pos = (1, 1)
        self.pond_pos = (-1, 1)
        self.depot_inited = False
        self.tap_inited = False
        self.pond_inited = False
        self.current_bucket = None
        self.direction = "N"
        self.mode = "num"
        self.mode_changed = False
        self.wellies_count = 0
        self.wellies_stack = []
        self.time = 0

    def leak_water_onto(self, pos: Pos, water: int) -> None:
        if pos in self.water:
            self.water[pos] += water
        else:
            self.water[pos] = water

    def pos_is_occupied(self, pos: Pos):
        return (pos in self.buckets) or (
            pos in [self.depot_pos, self.tap_pos, self.pond_pos]
        )

    def run_line(self, line: str, line_num: int) -> Branch | int | None:
        # print(line)
        # print(self.pos, self.direction, self.buckets)
        self.mode_changed = False
        for pos in list(self.water):
            self.water[pos] = max(0, self.water[pos] - 1)
            if self.water[pos] == 0:
                del self.water[pos]
        for pos, bucket in self.buckets.items():
            if bucket.holes == 0:
                continue
            bucket.water = max(0, bucket.water - bucket.holes)
            even_water = int(min(bucket.holes, bucket.water) // 4)
            self.leak_water_onto(
                add_pos(pos, direction_to_relative_pos(directions[self.time % 4])),
                min(bucket.holes, bucket.water) % 4,
            )
            for direction in directions:
                self.leak_water_onto(
                    add_pos(pos, direction_to_relative_pos(direction)), even_water
                )
        if self.current_bucket is not None and self.current_bucket.holes != 0:
            self.current_bucket.water = max(
                0, self.current_bucket.water - self.current_bucket.holes
            )
            self.leak_water_onto(self.pos, min(self.current_bucket.holes, self.current_bucket.water))
        next_line = self.eval_line(line, line_num)
        if not self.mode_changed:
            self.mode = "num"
        self.time += 1
        return next_line

    def eval_line(self, line: str, line_num: int) -> Branch | int | None:
        if match := re.match(
            r"collect a (\d+|max) pint bucket( with (\d+) holes)?", line
        ):
            if match.lastindex is not None and match.lastindex > 1:
                holes = int(match[3])
            else:
                holes = 0
            if (
                add_pos(self.pos, direction_to_relative_pos(self.direction))
                != self.depot_pos
            ):
                error(
                    "must be facing bucket depot in order to collect a bucket",
                    type="Runtime",
                )
            if self.current_bucket is not None:
                error(
                    "cannot collect a bucket; already holding one", line_num, "Runtime"
                )
            if match[1] == "max":
                capacity = 100 * (pow(2, 32) - 1)
            else:
                capacity = 100 * int(match[1])
            self.current_bucket = Bucket(capacity, holes)
            return
        if match := re.match(r"turn (left|right|around|all the way around)", line):
            if self.current_bucket is not None:
                error("cannot turn around while holding a bucket", line_num, "Runtime")
            # print(self.pos in self.water and self.water[self.pos])
            if self.pos in self.water and self.water[self.pos] >= 100:
                n = int(self.water[self.pos] // 100)
                if self.mode == "wellies_loop":
                    if self.wellies_count == 0:
                        error("fell over with no wellies on")
                    # print("fell over; looping")
                    loop_start = self.wellies_stack.pop()
                    self.pos = loop_start[1]
                    self.direction = loop_start[2]
                    return loop_start[0]
                else:
                    if n > self.wellies_count:
                        error("fell over and didn't have enough wellies on", line_num, "Runtime")
                    # print(f"fell over; branching {n}")
                    return Branch(n)
            match match[1]:
                case "left":
                    rel_dir = "W"
                case "right":
                    rel_dir = "E"
                case "around":
                    rel_dir = "S"
                case "all the way around":
                    rel_dir = "N"
                case _:
                    error("unreachable", line_num)
            self.direction = relative_direction_to_absolute(self.direction, rel_dir)
            return
        if match := re.match(r"fill the bucket to the top", line):
            if (
                add_pos(self.pos, direction_to_relative_pos(self.direction))
                != self.tap_pos
            ):
                error(
                    "must be facing the tap in order to fill a bucket",
                    line_num,
                    "Runtime",
                )
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to fill it", line_num, "Runtime"
                )
            self.current_bucket.water = self.current_bucket.capacity
            return
        if match := re.match(r"let god fill the bucket as he wishes", line):
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to fill it", line_num, "Runtime"
                )
            if self.mode == "ascii_in":
                new_water = 100 * ord(getch())  # type: ignore
            else:
                new_water = 100 * int(input())
            if self.current_bucket.water + new_water > self.current_bucket.capacity:
                error("exceeded capacity of bucket when filling", line_num, "Runtime")
            self.current_bucket.water += new_water
            return
        if match := re.match(r"fill the bucket with (\d+) pints of water", line):
            if (
                add_pos(self.pos, direction_to_relative_pos(self.direction))
                != self.tap_pos
            ):
                error(
                    "must be facing the tap in order to fill a bucket",
                    line_num,
                    "Runtime",
                )
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to fill it", line_num, "Runtime"
                )
            if match[1] == "max":
                water = 100 * pow(2, 32) - 1
            else:
                water = 100 * int(match[1])
            if self.current_bucket.water + water > self.current_bucket.capacity:
                error("exceeded capacity of bucket when filling", line_num, "Runtime")
            self.current_bucket.water += water
            return
        if match := re.match(rf"place the bucket down {facing}", line):
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to put it down",
                    line_num,
                    "Runtime",
                )
            bucket_pos = add_pos(
                self.pos,
                direction_to_relative_pos(
                    relative_direction_to_absolute(
                        self.direction, facing_to_relative_dir(match[1])
                    )
                ),
            )
            if self.pos_is_occupied(bucket_pos):
                error(
                    "cannot place a bucket in an occupied position", line_num, "Runtime"
                )
            self.buckets[bucket_pos] = self.current_bucket
            self.current_bucket = None
            return
        if match := re.match(rf"pick up the bucket {facing}", line):
            if self.current_bucket is not None:
                error(
                    "must not be holding a bucket in order to pick one up",
                    line_num,
                    "Runtime",
                )
            bucket_pos = add_pos(
                self.pos,
                direction_to_relative_pos(
                    relative_direction_to_absolute(
                        self.direction, facing_to_relative_dir(match[1])
                    )
                ),
            )
            if bucket_pos not in self.buckets:
                error(
                    "cannot pick up a bucket from an unoccupied position",
                    line_num,
                    "Runtime",
                )
            self.current_bucket = self.buckets[bucket_pos]
            del self.buckets[bucket_pos]
            return
        if match := re.match(
            rf"empty the bucket on ?to the square {facing}( without overflow)?", line
        ):
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to empty it", line_num, "Runtime"
                )
            empty_pos = add_pos(
                self.pos,
                direction_to_relative_pos(
                    relative_direction_to_absolute(
                        self.direction, facing_to_relative_dir(match[1])
                    )
                ),
            )
            if empty_pos in self.buckets:
                other_bucket = self.buckets[empty_pos]
                remaining_capacity = other_bucket.capacity - other_bucket.water
                if remaining_capacity > self.current_bucket.water:
                    other_bucket.water += self.current_bucket.water
                    self.current_bucket.water = 0
                elif match.lastindex is not None and match.lastindex > 1:
                    other_bucket.water = other_bucket.capacity
                    self.current_bucket.water -= remaining_capacity
                else:
                    other_bucket.water = other_bucket.capacity
                    overflowed = self.current_bucket.water - remaining_capacity
                    even_water = int(overflowed // 4)
                    for direction in directions:
                        self.leak_water_onto(
                            add_pos(empty_pos, direction_to_relative_pos(direction)),
                            even_water,
                        )
                    self.leak_water_onto(
                        add_pos(
                            self.pos,
                            direction_to_relative_pos(directions[self.time % 4]),
                        ),
                        even_water,
                    )
                    self.current_bucket.water = 0
            elif empty_pos == self.pond_pos:
                if match.lastindex is not None and match.lastindex > 1:
                    error(
                        "it is not a valid instruction to empty into the pond without overflow",
                        line_num,
                        "Runtime",
                    )
                match self.mode:
                    case "num":
                        if self.current_bucket.water % 100 == 0:
                            print(int(self.current_bucket.water // 100))
                        else:
                            print(self.current_bucket.water * 0.01)
                    case "ascii":
                        if self.current_bucket.water % 100 == 0:
                            if self.current_bucket.water // 100 < 128:
                                print(chr(self.current_bucket.water // 100))
                            else:
                                error(
                                    "couldn't print as ascii bucket for which water level was > 127",
                                    line_num,
                                    "Runtime",
                                )
                        else:
                            error(
                                "couldn't print as ascii bucket for which water level was not an integer",
                                line_num,
                                "Runtime",
                            )
                    case "void" | "wellies_loop" | "ascii_in":
                        pass
                    case _:
                        unreachable(line_num)
                self.current_bucket.water = 0
            else:
                if match.lastindex is not None and match.lastindex > 1:
                    error(
                        "it is not a valid instruction to empty onto the floor without overflow",
                        line_num,
                        "Runtime",
                    )
                if empty_pos in self.water:
                    self.water[empty_pos] += self.current_bucket.water
                else:
                    self.water[empty_pos] = self.current_bucket.water
                self.current_bucket.water = 0
            return
        if match := re.match(rf"empty the bucket here", line):
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to empty it", line_num, "Runtime"
                )
            if self.pos in self.water:
                self.water[self.pos] += self.current_bucket.water
            else:
                self.water[self.pos] = self.current_bucket.water
            self.current_bucket.water = 0
            return
        if match := re.match(rf"move ((1) step|((\d)+) steps)", line):
            length = int(match[2] or match[3])
            route = [
                add_pos(self.pos, mul_pos(s, direction_to_relative_pos(self.direction)))
                for s in range(1, length + 1)
            ]
            if any(map(self.pos_is_occupied, route)):
                error("tripped over an occupied position :(", line_num, "Runtime")
            self.pos = add_pos(
                self.pos,
                mul_pos(length, direction_to_relative_pos(self.direction)),
            )
            return
        if match := re.match(rf"shrink my bucket", line):
            if self.current_bucket is None:
                error(
                    "must be holding a bucket in order to shrink it",
                    line_num,
                    "Runtime",
                )
            self.current_bucket.capacity = self.current_bucket.water
            return
        if match := re.match(rf"i wish to scream in ?to the void", line):
            self.mode = "void"
            self.mode_changed = True
            return
        if match := re.match(rf"i wish to speak to god", line):
            self.mode = "ascii"
            self.mode_changed = True
            return
        if match := re.match(rf"i wish to hear from god", line):
            self.mode = "ascii_in"
            self.mode_changed = True
            return
        if match := re.match(rf"i wish to have my wellies returned", line):
            self.mode = "wellies_loop"
            self.mode_changed = True
            return
        if match := re.match(rf"put wellies on", line):
            self.wellies_count += 1
            self.wellies_stack.append((line_num - 1, self.pos, self.direction))
            return
        if match := re.match(rf"take wellies off", line):
            if self.wellies_count == 0:
                error(
                    "can't take off wellies when you have no wellies on",
                    line_num,
                    "Runtime",
                )
            self.wellies_count -= 1
            self.wellies_stack.pop()
            return
        if match := re.match(r"evaporate ((1) pint|(\d+) pints)", line):
            if self.pos in self.water:
                self.water[self.pos] = max(0, self.water[self.pos] - 100 * int(match[2] or match[3]))
            return
        error("unknown instruction", line_num)


if __name__ == "__main__":
    program = Program()
    if len(argv) > 1:
        filename = argv[1]
        with open(filename, encoding="utf-8") as f:
            lines = [
                re.sub("--.+$", "", line.strip().lower()) for line in f.readlines()
            ]
            i = 0
            branch_countdown = 0
            while i < len(lines):
                if lines[i] != "":
                    if branch_countdown > 0:
                        if lines[i] == "take wellies off":
                            branch_countdown -= 1
                        i += 1
                        continue
                    next_line = program.run_line(re.sub(r"\s+", " ", lines[i]), i + 1)
                    if isinstance(next_line, Branch):
                        branch_countdown = next_line.n
                        i += 1
                    elif next_line is not None:
                        i = next_line
                    else:
                        i += 1
                else:
                    i += 1
            if branch_countdown > 0:
                error("terminated without finding correct branch to take off wellies")
    else:
        error("expected there to be an input of a file name")
