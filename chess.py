#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *
from copy import deepcopy

PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

BLACK = 1 << 3
MASK = BLACK - 1

board = [[0] * 8 for _ in range(8)]


def square_value(n):
    return n & MASK


def square_string(n):
    if n == 0:
        return "　"
    return chr(0x2660 - square_value(n))


def alg_to_pos(alg):
    return ord(alg[0]) - ord("a"), 8 - int(alg[1])


def darken(n):
    return n | BLACK


def is_black(n):
    return bool(n & BLACK)


def init_board():
    board[0] = [darken(n) for n in [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]]
    board[1] = [darken(n) for n in [PAWN] * 8]
    board[6] = [PAWN] * 8
    board[7] = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]


col_white = ("#eee", "#ccc")
col_black = ("#bbb", "#999")
size_square = 64
size_window = size_square * 10
font = ("Segoe UI", -size_square)
font_text = ("Segoe UI", -32)
drawn = False
board_last = None
last_mouse = (-1, -1)
is_moving = False
square_move = -1, -1
square_targets = []
turn_black = False
castle_stat = [[True, True], [True, True]]
is_check = [False, False]


def draw_board():
    global drawn, board_last, last_mouse
    mx = (root.winfo_pointerx() - root.winfo_rootx()) // size_square
    my = (root.winfo_pointery() - root.winfo_rooty()) // size_square

    if board_last == board and last_mouse == (mx, my):
        return
    canvas.delete(ALL)
    canvas.create_image(2, 2, anchor="nw", image=board_image)
    flip = True
    for x in range(1, 9):
        flip = not flip
        for y in range(1, 9):
            ox = x * size_square
            oy = y * size_square
            flip = not flip
            square = board[y - 1][x - 1]
            if is_check[is_black(square)] and square_value(square) == KING:
                canvas.create_rectangle(
                    ox,
                    oy,
                    ox + size_square,
                    oy + size_square,
                    fill="red"
                )
            elif mx == x and my == y:
                canvas.create_rectangle(
                    ox,
                    oy,
                    ox + size_square,
                    oy + size_square,
                    fill=(col_white if flip else col_black)[1]
                )

            if not square & BLACK:
                canvas.create_text(
                    ox + size_square / 2 + 1,
                    oy + size_square / 2 + 1,
                    text=square_string(square),
                    fill="#000",
                    font=font
                )
            canvas.create_text(
                ox + size_square / 2,
                oy + size_square / 2,
                text=square_string(square),
                fill="#000" if square & BLACK else "#fff",
                font=font
            )

            if square_move == (x - 1, y - 1):
                canvas.create_rectangle(
                    ox + 3,
                    oy + 3,
                    ox - 2 + size_square,
                    oy - 2 + size_square,
                    outline="yellow",
                    width=4
                )
    for x, y in square_targets:
        ox = (x + 1) * size_square
        oy = (y + 1) * size_square
        canvas.create_rectangle(
            ox + 3,
            oy + 3,
            ox - 2 + size_square,
            oy - 2 + size_square,
            outline="blue",
            width=4
        )
    drawn = True
    board_last = deepcopy(board)
    last_mouse = mx, my


def motion(_):
    draw_board()


def xy_valid(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def square_filter(squares):
    return [(x, y) for x, y in squares if xy_valid(x, y)]


def non_empty(squares):
    return [(x, y) for x, y in square_filter(squares) if board[y][x] != 0]


def empty(squares):
    return [(x, y) for x, y in square_filter(squares) if board[y][x] == 0]


def king_position(black):
    for y in range(8):
        for x in range(8):
            if square_value(board[y][x]) == KING and is_black(board[y][x]) == black:
                return x, y


def pieces(black):
    for y in range(8):
        for x in range(8):
            if is_black(board[y][x]) == black:
                yield x, y


def check(noir):
    pos = king_position(noir)
    for y in range(8):
        for x in range(8):
            if is_black(board[y][x]) == (not noir) and pos in possible_squares(x, y, False):
                return True
    return False


def possible_squares(x, y, check_check=True):
    square = board[y][x]
    black = is_black(square)
    direction = 1 if black else -1
    piece_kind = square_value(square)
    res = []
    if piece_kind == PAWN:
        res.append((x, y + direction))
        if (not black and y == 6) or (black and y == 1):
            res.append((x, y + 2 * direction))
        res = empty(res)
        res_m = non_empty([(x + 1, y + direction), (x - 1, y + direction)])
        res.extend(res_m)
    if piece_kind in [ROOK, QUEEN]:
        # right
        for xm in range(x + 1, 8):
            res.append((xm, y))
            if board[y][xm] != 0:
                break
        # left
        for xm in range(x - 1, -1, -1):
            res.append((xm, y))
            if board[y][xm] != 0:
                break
        # top
        for ym in range(y - 1, -1, -1):
            res.append((x, ym))
            if board[ym][x] != 0:
                break
        # bottom
        for ym in range(y + 1, 8):
            res.append((x, ym))
            if board[ym][x] != 0:
                break
    if piece_kind in [BISHOP, QUEEN]:
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                xm, ym = x, y
                while True:
                    xm += dx
                    ym += dy
                    if not xy_valid(xm, ym):
                        break
                    res.append((xm, ym))
                    if board[ym][xm]:
                        break
    if piece_kind == KING:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    res.append((x + dx, y + dy))
        if check_check and not check(black):
            if castle_stat[black][0]:
                for dx in range(1, x):
                    if board[y][dx] != 0:
                        break
                else:
                    res.append((x - 2, y))
            if castle_stat[black][1]:
                for dx in range(x + 1, 7):
                    if board[y][dx] != 0:
                        break
                else:
                    res.append((x + 2, y))
    if piece_kind == KNIGHT:
        res.append((x - 1, y - 2))
        res.append((x - 2, y - 1))
        res.append((x - 1, y + 2))
        res.append((x - 2, y + 1))
        res.append((x + 1, y - 2))
        res.append((x + 2, y - 1))
        res.append((x + 1, y + 2))
        res.append((x + 2, y + 1))

    res = [(x, y) for x, y in square_filter(res) if board[y][x] == 0 or (is_black(board[y][x]) != black)]
    if check_check:
        res = [(rx, ry) for rx, ry in res if not gives_check(x, y, rx, ry)]
    return res


def gives_check(x, y, rx, ry):
    global board
    bak = deepcopy(board)
    board[ry][rx] = board[y][x]
    board[y][x] = 0
    res = check(is_black(board[ry][rx]))
    board = bak
    return res


def reset_move():
    global square_move, square_targets, is_moving
    square_targets = []
    square_move = -1, -1
    is_moving = False


def flatten_squares():
    return ((x, y, board[y][x]) for y in range(8) for x in range(8))


def checkmate(black):
    global board
    if not check(black):
        return False
    pieces = ((x, y) for x, y, val in flatten_squares() if val != 0 and is_black(val) == black)
    squares = ((x, y, possible_squares(x, y)) for x, y in pieces)
    moves = {}
    for x, y, c in squares:
        for cc in c:
            moves[cc] = x, y
    bak = deepcopy(board)
    for (cx, cy), (x, y) in moves.items():
        board = deepcopy(bak)
        board[cy][cx] = board[y][x]
        board[y][x] = 0
        if not check(black):
            res = False
            break
    else:
        res = True
    board = bak
    return res

def rclick(event):
    x = event.x // size_square - 1
    y = event.y // size_square - 1

    if not 0 <= x < 8 and 0 <= y < 8:
        return

    backup_board()

    board[y][x] = 0

    draw_board()

def backup_board():
    global board_last
    board_last = deepcopy(board)

def cancel(event):
    global board, board_last
    if board_last is None:
        return
    board = board_last
    board_last = None
    draw_board()

def click(event):
    global square_move, square_targets, is_moving, turn_black
    x = event.x // size_square - 1
    y = event.y // size_square - 1

    if not 0 <= x < 8 and 0 <= y < 8:
        return
    if is_moving and (x, y) in square_targets:
        backup_board()
        mx, my = square_move
        if square_value(board[my][mx]) == ROOK and my == (not turn_black * 7) and mx in [0, 7]:
            castle_stat[turn_black][mx == 7] = False
        if square_value(board[my][mx]) == KING:
            castle_stat[turn_black] = [False, False]
            if mx - x == -2:
                board[y][mx + 1] = board[y][mx + 3]
                board[y][mx + 3] = 0
            elif mx - x == 2:
                board[y][mx - 1] = board[y][mx - 4]
                board[y][mx - 4] = 0
        if square_value(board[my][mx]) == PAWN and y == turn_black * 7:
            print("PROMOTION")
            while True:
                prom = input("N,B,R,Q ?  ").upper()
                hm = {"N": KNIGHT, "B": BISHOP, "R": ROOK, "Q": QUEEN}
                if prom in hm:
                    board[my][mx] = hm[prom] | (BLACK * turn_black)
                    break

        board[y][x] = board[my][mx]
        board[my][mx] = 0
        is_check[turn_black] = check(turn_black)
        turn_black = not turn_black
        is_check[turn_black] = check(turn_black)
        print(("BLACK" if turn_black else "WHITE") + "'S TURN")
        reset_move()
        if checkmate(turn_black):
            print("CHECKMATE")
        if not check(turn_black) \
            and all(gives_check(px, py, x, y) for px, py in pieces(turn_black) for x, y in possible_squares(px, py, False)):
            print("STALEMATE")
    elif board[y][x] != 0 and is_black(board[y][x]) == turn_black:
        square_move = x, y
        square_targets = possible_squares(x, y)
        is_moving = True
    else:
        reset_move()

    draw_board()


root = Tk()
root.resizable(False, False)
root.geometry("%dx%d" % (size_window, size_window))
canvas = Canvas(root, background="#ffffff")
board_image = PhotoImage(file="chess.png")
init_board()
draw_board()

canvas.pack(fill=BOTH, expand=1)
root.bind_all('<Motion>', motion)
root.bind_all("<Button-1>", click)
root.bind_all("<Button-3>", rclick)
root.bind_all("<Left>", cancel)
canvas.focus_set()
root.mainloop()
