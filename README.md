# Leaky Buckets

Leaky Buckets is an esolang created for the Oxford CompSoc EsoLang Hackathon in October 2025.

## Syntax

Leaky Buckets is whitespace agnostic, with the exception of newlines, which are compulsory to separate instruction. Additional newlines do nothing. It is also case-insensitive; all syntax is presented as lowercase but this is not necessary.

```
program := init ("\n" instruction? comment?)*

comment := "--" followed by anything

init := "the bucket depot is" relativeLocation "\n the tap is" relativeLocation "\n the pond is"

relativeLocation := ... (TODO)

instruction := movement | turn | bucketAction | invocation

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

invocation :=
    "i wish to speak with god"
    | "i wish to hear from god"
    | "i wish to scream into the void"
```

## Execution

The program takes place on a square grid that is assumed to be infinitely large (we don't know of anyone who's fallen off the edge yet). On the grid, we have a bucket depot, which is able to produce an infinite buckets of arbitrary size (so long as the capacity is a positive integer number of pints), a tap, which is capable of producing an infinite amount of water, and a pond, which seems to be able to hold as much water as you want, and never seems to fill up. Each of these only takes up one square on the grid, and their locations must be specified at the beginning of the programme. You begin by facing an arbitrary direction, but it doesn't really matter which direction that is as it all ends up being relative to that.

You can ask for your bucket to have holes, so long as it's a positive integer. Buckets lose water at a rate of 1 centipint per hole per unit time. You don't have to have holes in your bucket though.

Time progresses by one unit each time any instruction is carried out. To progress time without doing anything, you can "turn all the way around".

All instructions after the initial "I am facing [direction]" statement are written in the imperative. You can "move n steps [direction]", so long as you don't walk into the bucket depot, tap, pond, or any buckets - you will fall over if you do so. (More about falling over later).

When buckets leak, they leak directly on to the floor. This is fine except the floor is perfectly smooth, and water stays exactly in the square on which it was dropped (surface tension is so cool). Water does evaporate from each square of the ground (but not from buckets or the pond) at a rate of 1 centipint per second. If you try to turn in any direction while standing on a square with more than one pint of water lying on it, you will slip and fall.

Buckets can be emptied where you are standing; you cannot empty a bucket halfway. They can also be emptied onto a square immediately next to you (including in front and behind) - if there happens to be a bucket or the pond there, the water will go in there.

Buckets can be overfilled; water will seep onto the four squares immediately around the bucket (water can't travel diagonally), in equal proportions. If there is an amount of water that cannot be shared out equally, it will leak north first, the east, then south. If there is a bucket in any of those immediately surrounding squares, the water will go into those buckets (as well as on the floor).

If you don't want to overfill a bucket, just say so: e.g. "empty the bucket here without overflow". If you run the risk of overflowing the bucket, or emptying on to the floor, you will stop emptying the bucket at the appropriate moment.

If you're not too sure how much water you want to put in a bucket, you can "let god fill the bucket as he wishes", which will take user input (must be a valid integer, possibly zero) and fill the bucket with that many pints of water. Alternatively, if you'd like text (ASCII only) input, you can say "i wish to hear from god" beforehand to get one character of input into your bucket. You don't need to be at the tap to carry out this command; at all other times, you need to be facing the tap to fill up a bucket.

If at any point you feel your bucket is just a bit too big, you can ask to "shrink my bucket" and your bucket will be shrunk to the smallest capacity such that it holds all the water currently in it, but no more.

Emptying a bucket into the pond prints the amount of water that was in the bucket (in pints) to standard output, unless you have made a specific request beforehand:
- "i wish to speak with god" causes emptying into the pond to print out the corresponding ascii character, as long as the amount of water is an integer number of pints between 0 and 127 inclusive. If it is not, god will reject your application to speak to him and the program will crash.
- "i wish to scream into the void" just empties the bucket into the pond and does nothing.


## Example programs

Examples can be found in the [`examples` directory](./examples/)
