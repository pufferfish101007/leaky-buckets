#! /usr/bin/python

# The leaky bucket interpreter

from sys import argv
import re
from dataclasses import dataclass
from typing import Never


def error(error: str, linenum: int | None = None, type: str = "") -> Never:
    if linenum is None:
        stacktrace = ""
    else:
        stacktrace = f"\n\tat line {linenum}"
    print(f"{type}Error: {error}{stacktrace}")
    exit(1)


facing = "(in front of me|to my left|behind me|to my right)"


def facing_to_relative_dir(facing):
    match facing:
        case "in front of me":
            return "N"
        case "behind me":
            return "S"
        case "to my right":
            return "E"
        case "to my left":
            return "W"


dirs = "NESW"


def relative_direction_to_absolute(current_dir, relative_dir):
    return dirs[(dirs.index(current_dir) + dirs.index(relative_dir)) % 4]


def direction_to_relative_pos(absolute_dir):
    return [(0, 1), (1, 0), (0, -1), (-1, 0)][dirs.index(absolute_dir)]


def add_pos(pos1: tuple[int, int], pos2: tuple[int, int]):
    return (pos1[0] + pos2[0], pos1[1] + pos2[1])


def mul_pos(scalar: int, pos: tuple[int, int]):
    return (scalar * pos[0], scalar * pos[1])


@dataclass
class Bucket:
    capacity: int
    water: int = 0


@dataclass
class Program:
    buckets: dict[tuple[int, int], Bucket]
    pos: tuple[int, int]
    direction: str
    depot_pos: tuple[int, int]
    tap_pos: tuple[int, int]
    pond_pos: tuple[int, int]
    depot_inited: bool
    tap_inited: bool
    pond_inited: bool
    current_bucket: Bucket | None
    print_mode: str
    print_mode_changed: bool

    def __init__(self):
        self.buckets = dict()
        self.pos = (0, 0)
        self.depot_pos = (0, 0)
        self.tap_pos = (0, 0)
        self.pond_pos = (0, 0)
        self.depot_inited = False
        self.tap_inited = False
        self.pond_inited = False
        self.current_bucket = None
        self.direction = "N"
        self.print_mode = "num"
        self.print_mode_changed = False

    def pos_init(self, loc, line, line_num):
        pos_match = re.match(f"the {loc} is {facing}", line)
        if pos_match is None:
            error(f"expected {loc} position initialisation", line_num, "Assertion")
        else:
            return direction_to_relative_pos(facing_to_relative_dir(pos_match[1]))

    def pos_is_occupied(self, pos):
        return (pos in self.buckets) or (
            pos in [self.depot_pos, self.tap_pos, self.pond_pos]
        )

    def run_line(self, line, line_num):
        if not self.depot_inited:
            self.depot_pos = self.pos_init("bucket depot", line, line_num)
            self.depot_inited = True
            return
        if not self.tap_inited:
            self.tap_pos = self.pos_init("tap", line, line_num)
            self.tap_inited = True
            return
        if not self.pond_inited:
            self.pond_pos = self.pos_init("pond", line, line_num)
            self.pond_inited = True
            return
        self.print_mode_changed = False
        self.eval_line(line, line_num)
        if not self.print_mode_changed:
            self.print_mode = "num"

    def eval_line(self, line, line_num):
        if match := re.match(
            r"collect a (\d+|max) pint bucket( with (\d+) holes)?", line
        ):
            if match.lastindex is not None and match.lastindex > 1:
                error("unimplemented: buckets with holes")
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
                capacity = pow(2, 32) - 1
            else:
                capacity = int(match[1])
            self.current_bucket = Bucket(capacity)
            return
        if match := re.match(r"turn (left|right|around|all the way around)", line):
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
                    error("unreachable")
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
            new_water = int(input())
            if self.current_bucket.water + new_water > self.current_bucket.capacity:
                error("exceeded capaicty of bucket when filling", line_num, "Runtime")
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
                water = pow(2, 32) - 1
            else:
                water = int(match[1])
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
            elif empty_pos == self.pond_pos:
                match self.print_mode:
                    case "num":
                        print(self.current_bucket.water)
                    case "ascii":
                        if self.current_bucket.water < 128:
                            print(chr(self.current_bucket.water))
                        else:
                            error(
                                "couldn't print as ascii bucket for which water level was > 127",
                                line_num,
                                "Runtime",
                            )
                    case "void":
                        pass
                self.current_bucket.water = 0
            else:
                error(
                    "cannot empty a bucket onto a square that is not a bucket or the pond",
                    line_num,
                    "Runtime",
                )
            return
        if match := re.match(rf"move (\d+) steps", line):
            self.pos = add_pos(
                self.pos,
                mul_pos(int(match[1]), direction_to_relative_pos(self.direction)),
            )
            # TODO: check for obstructions before moving
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
            self.print_mode = "void"
            self.print_mode_changed = True
            return
        error("unimplemented", line_num)


if __name__ == "__main__":
    program = Program()
    if len(argv) > 1:
        filename = argv[1]
        if not isinstance(filename, str):
            error("Expected file name to be a string")
        with open(filename, encoding="utf-8") as f:
            for line_num, line in enumerate(f.readlines()):
                line = line.strip().lower()
                line = re.sub("--.+$", "", line)
                if line != "":
                    program.run_line(re.sub(r"\s+", " ", line), line_num + 1)
    else:
        error("expected there to be an input of a file name")
