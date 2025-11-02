# Leaky Buckets v0.0.1

Leaky Buckets is an esolang created for the Oxford CompSoc EsoLang Hackathon in October 2025.

This file gives a somewhat formal specification of the language, but please note that [interpreter.py](./interpreter.py) is the authoritative resource.

## File extension

Leaky Buckets files must have the `.buckets` file extension.

## Syntax

Leaky Buckets is whitespace agnostic, with the exception of newlines, which are compulsory to separate instruction. Additional newlines do nothing. It is also case-insensitive; all syntax is presented as lowercase but this is not necessary.

```
program := (instruction? comment? "\n")*

comment := "--" followed by anything

instruction := movement | turn | bucketAction | invocation | wellies

movement := "move" ("1 step" | int "steps")

turn := "turn" turnDirection 

turnDirection :=
    "right"
    | "left" 
    | "around" 
    | "all the way around"

facing := 
    "in front of me"
    | "to my left"
    | "to my right"
    | "behind me"

int := 0 | 1 | 2 | 3 | ... | 2^32 - 1

"max" := 2^32 - 1

bucketAction :=
    ("collect a" int "pint bucket" ("with" int "holes")?)
    | "fill the bucket to the top"
    | ("fill the bucket with" int "pints of water")
    | "let god fill the bucket as he wishes" 
    | ("pick up the bucket" facing)
    | ("place the bucket down" facing)
    | "empty the bucket"
        ("here" | ("onto the square" facing))
        "without overflow"?
    | "shrink my bucket"
    | "move until my bucket is empty"

invocation :=
    "i wish to speak with god"
    | "i wish to hear from god"
    | "i wish to scream into the void"
    | "i wish to have my wellies returned to me"

wellies := "put wellies on" | "take wellies off"
```

## Execution

The program takes place on a square grid that is assumed to be infinitely large (we don't know of anyone who's fallen off the edge yet). On the grid, we have a bucket depot, which is able to produce an infinite buckets of arbitrary size (so long as the capacity is a positive integer number of pints), a tap, which is capable of producing an infinite amount of water, and a pond, which seems to be able to hold as much water as you want, and never seems to fill up. Each of these only takes up one square on the grid. You begin by facing an arbitrary direction, but it doesn't really matter which direction that is as it all ends up being relative to that (internally the initial direction is north). At the beginning, the bucket depot is directly in front of you; the pond is to the left of the bucket depot; and the tap is to the right of the bucket depot.

Time progresses by one unit each time any instruction is carried out. To progress time without doing anything, you can "turn all the way around". 

You can only move in the direction you are facing. If you walk into a bucket, the tap, the bucket depot or the pond, you will fall over and the program will crash. You can only turn if you are not holding a bucket (you need your hands free to stabilise yourself). You cannot pick up, put down or empty a bucket behind you.

You can wear wellies to protect yourself from slipping on wet floors. Put them on my saying "put wellies on", and take one pair of wellies off by saying "take wellies off". You can have as many pairs of wellies on as you like, as you own particularly stretchy wellies.

Buckets have a capacity, and a (possibly zero) integer number of holes; water is lost from each hole at a rate of 1 centipint per unit of time, and gathers on the floor tile directly underneath where it leaked, if it is being carried, or gathers on the four tiles directly next to the bucket, if it is on the floor (here the water spreads roughly equally across the four tiles, in a deterministic but non-specified manner). Water evaporates from the floor (but not from buckets or the pond) at a rate of 1 centipint per unit of time, per grid square. If you try to turn in any direction while standing on a square with more than or equal to `n` pints of water lying on it, where `n` is a positive integer, you will slip out of your outermost `n` pairs of wellies; if you are wearing fewer than `n` wellies, you fall over and the program crashes. Wellies can only be put on if you are not holding a bucket, as you need your hands free to put them on.

When you slip out of wellies, by default the program will skip ahead to when you were planning on taking those wellies off, as presumably you carried out a risk assessment beforehand and the intermediate instructions are not safe to complete without wellies. If however you'd like another chance with your wellies, if you said "i wish to have my wellies returned to me" immediately before the instruction in which you slipped, you will only lose the outermost pair of wellies, and you will be returned to the point at which you put those wellies on. Note that program state is not reset here, only your position, direction, and number of wellies. Please be aware that you might get into an infinite welly loop and the program will never terminate. This is typically not seen to be acceptable.

Buckets can be emptied where you are standing; you cannot empty a bucket halfway. They can also be emptied onto a square immediately next to you (including in front and behind) - if there happens to be a bucket or the pond there, the water will go in there.

Buckets can be overfilled; water will seep onto the four squares immediately around the bucket (water can't travel diagonally), in equal proportions. If there is an amount of water that cannot be shared out equally, it will leak onto the square you are standing on. If there is a bucket in any of those immediately surrounding squares, the water will go into those buckets (as well as on the floor).

If you don't want to overfill a bucket, just say so: e.g. "empty the bucket to my left without overflow". If you run the risk of overflowing the bucket, you will stop emptying the bucket at the appropriate moment. Attempting to empty onto the floor or into the pond without overflow is invalid and leads to a runtime error.

If you're not too sure how much water you want to put in a bucket, you can "let god fill the bucket as he wishes", which will take user input (must be a valid integer, possibly zero) and fill the bucket with that many pints of water. Alternatively, if you'd like text (ASCII only) input, you can say "i wish to hear from god" immediately beforehand to get one character of input into your bucket. You don't need to be at the tap to carry out this command; at all other times, you need to be facing the tap to fill up a bucket.

If at any point you feel your bucket is just a bit too big, you can ask to "shrink my bucket" and your bucket will be shrunk to the smallest capacity such that it holds all the water currently in it, but no more.

Emptying a bucket into the pond prints the amount of water that was in the bucket (in pints) to standard output, unless you have made a specific request beforehand:
- "i wish to speak with god" causes emptying into the pond to print out the corresponding ascii character, as long as the amount of water is an integer number of pints between 0 and 127 inclusive. If it is not, god will reject your application to speak to him and the program will crash.
- "i wish to scream into the void" just empties the bucket into the pond and does nothing.

Emptying into the pond without overflow is an invalid instruction.


## Example programs

Examples can be found in the [`examples` directory](./examples/)
