from typing import Final
from enum import Enum
from collections import deque

import tkinter as tk
from tkinter import messagebox
import sys

class HalmaColor(Enum):
    RED   = "red"
    GREEN = "green"

class HalmaBoardSize(Enum):
    SMALL  = (8,  [4, 3, 2, 1])
    MEDIUM = (10, [5, 4, 3, 2, 1])
    LARGE  = (16, [5, 5, 4, 3, 2])

    def __init__(self, board_width: int, initial_num_pieces_per_row: list[int]):
        self.board_width:                Final[int]       = board_width
        self.initial_num_pieces_per_row: Final[list[int]] = (
            initial_num_pieces_per_row
        )

class HalmaPiece:
    def __init__(self, color: HalmaColor, space: HalmaBoardSpace, curr_score: float):
        self.color:      Final[HalmaColor] = color
        self.space:      HalmaBoardSpace   = space
        self.tk_id:      int               = -1
        self.curr_score: float             = curr_score

class HalmaBoardSpace:
    def __init__(
        self,
        row_index: int,
        col_index: int,
        default_color: str,
    ) -> None:
        assert row_index >= 0, "Row index must be >= 0"
        assert col_index >= 0, "Column index must be >= 0"

        self.default_color: str               = default_color
        self.row_index:     Final[int]        = row_index
        self.col_index:     Final[int]        = col_index
        self.tk_id:         int               = -1
        self.piece:         HalmaPiece | None = None

class HalmaBoard:
    def __init__(self, size: HalmaBoardSize, turn_time: int) -> None:
        self._size: Final[HalmaBoardSize]              = size
        self._grid: Final[list[list[HalmaBoardSpace]]] = [
            [
                HalmaBoardSpace(
                    row_index,
                    col_index,
                    "white"
                ) for col_index in range(size.board_width)
            ] for row_index in range(size.board_width)
        ]
        self.selected_space:    HalmaBoardSpace | None = None
        self.possible_move_ids: list[int] | None       = None
        self.curr_turn:         HalmaColor             = HalmaColor.GREEN
        self.turn_time:         Final[int]             = turn_time
        self.turn_time_left:    float                  = turn_time

        assert turn_time > 0

        # setup grid
        for camp_space in self._get_camp_spaces(HalmaColor.RED):
            camp_space.piece = HalmaPiece(
                HalmaColor.RED,
                camp_space,
                self._get_score(HalmaColor.RED, camp_space)
            )

            camp_space.default_color = "#cfa1a1"

        for camp_space in self._get_camp_spaces(HalmaColor.GREEN):
            camp_space.piece = HalmaPiece(
                HalmaColor.GREEN,
                camp_space,
                self._get_score(HalmaColor.GREEN, camp_space)
            )

            camp_space.default_color = "#a8bfa3"

    def _get_camp_spaces(self, color: HalmaColor) -> list[HalmaBoardSpace]:
        camp_spaces: list[HalmaBoardSpace] = []

        if color == HalmaColor.RED:
            for row_index in range(len(self._size.initial_num_pieces_per_row)):
                for col_index in range(self._size.initial_num_pieces_per_row[row_index]):
                    camp_spaces.append(self._grid[row_index][col_index])
        else:
            for row_index in range(len(self._size.initial_num_pieces_per_row)):
                num_pieces_in_row = self._size.initial_num_pieces_per_row[row_index]
                reflected_row = self._size.board_width - row_index - 1

                for col_index in range(num_pieces_in_row):
                    reflected_col = self._size.board_width - col_index - 1
                    camp_spaces.append(self._grid[reflected_row][reflected_col])

        return camp_spaces

    def print(self) -> None:
        for row in self._grid:
            for cell in row:
                if cell.piece is None:
                    print("* ", end = "")
                else:
                    print(f"{cell.piece.color.value[0]} ", end = "")
            print()

    @property
    def width(self) -> int:
        return self._size.board_width

    def display(self) -> None:
        # setup
        win_width:         Final[int] = 800
        win_height:        Final[int] = 1000
        win_padding:       Final[int] = 25
        canvas_width:      Final[int] = win_width - win_padding * 2
        box_width:         Final[int] = round(canvas_width / self._size.board_width)
        piece_radius:      Final[int] = round(box_width / 3)

        # create root
        tk_root = tk.Tk()
        tk_root.title("Halma Board")
        tk_root.geometry(f"{win_width}x{win_height}")

        tk_status_frame = tk.Frame(tk_root)
        tk_status_frame.pack(fill="x")

        # create status bar
        items = [f"Current turn: {self.curr_turn}", f"Time remaining: {self.turn_time_left}"]
        for col_index, item in enumerate(items):
            tk_status_frame.grid_columnconfigure(col_index, weight=1)

            tk_label = tk.Label(
                tk_status_frame,
                text=item,
                padx=10,
                pady=5,
                relief="solid"
            )
            tk_label.grid(row=0, column=col_index, padx=5, pady=10)

        # create canvas
        tk_canvas = tk.Canvas(
            tk_root,
            width               = win_width,
            height              = win_width,
            bg                  = "white",
            highlightthickness  = 1,
            highlightbackground = "black"
        )

        tk_canvas.pack(padx=win_padding, pady=win_padding)

        # create board
        tag_index: int = 0
        for row_index in range(self.width):
            for col_index in range(self.width):
                board_space = self._grid[row_index][col_index]
                
                top_left_x = box_width * col_index
                top_left_y = box_width * row_index
                board_space.tk_id = (
                    tk_canvas.create_rectangle(
                        top_left_x,
                        top_left_y,
                        top_left_x + box_width,
                        top_left_y + box_width,
                        fill    = board_space.default_color,
                        outline = "grey",
                        width   = 2,
                    )
                )

                if board_space.piece is None:
                    continue

                oval_tag = f"piece{tag_index}"
                tag_index += 1

                oval_id = tk_canvas.create_oval(
                    top_left_x + (box_width / 2 - piece_radius),
                    top_left_y + (box_width / 2 - piece_radius),
                    top_left_x + (box_width / 2 + piece_radius),
                    top_left_y + (box_width / 2 + piece_radius),
                    fill    = board_space.piece.color.value,
                    outline = "black",
                    width   = 2,
                    tags    = oval_tag,
                )

                board_space.piece.tk_id = oval_id

                # bind on click functions
                def select_piece_handler(event: tk.Event, piece = board_space.piece):
                    if piece.color != self.curr_turn:
                        return

                    # handle selection
                    self._hide_possible_moves(tk_canvas)

                    if self.selected_space is not None:
                        tk_canvas.itemconfig(
                            self.selected_space.tk_id,
                            fill = self.selected_space.default_color,
                        )

                    if self.selected_space == piece.space:
                        self.selected_space = None
                        return

                    tk_canvas.itemconfig(piece.space.tk_id, fill = "yellow")
                    self.selected_space = piece.space

                    # show possible moves
                    possible_moves = self._get_possible_moves(piece)
                    self.possible_move_ids = []
                    for space_index in range(len(possible_moves)):
                        space = possible_moves[space_index]
                        move_tag = f"move{space_index}"
                        top_left_x = space.col_index * box_width
                        top_left_y = space.row_index * box_width
                        possible_move_id = tk_canvas.create_oval(
                            top_left_x + (box_width / 2 - piece_radius),
                            top_left_y + (box_width / 2 - piece_radius),
                            top_left_x + (box_width / 2 + piece_radius),
                            top_left_y + (box_width / 2 + piece_radius),
                            fill    = "lightgrey",
                            outline = "grey",
                            tags    = move_tag,
                        )
                        self.possible_move_ids.append(possible_move_id)
                        
                        def select_move_handler(
                            event,
                            moved_to_space = space,
                            moved_piece = piece,
                        ):
                            self._move_piece(
                                moved_piece,
                                moved_to_space,
                                tk_canvas,
                                box_width,
                                piece_radius
                            )
                            self._hide_possible_moves(tk_canvas)
                            tk_canvas.itemconfig(
                                self.selected_space.tk_id,
                                fill = self.selected_space.default_color,
                            )
                            self.selected_space = None

                            self.curr_turn = (
                                HalmaColor.RED 
                                if self.curr_turn == HalmaColor.GREEN
                                else HalmaColor.GREEN
                            )

                            self._check_for_win(tk_root)

                        tk_canvas.tag_bind(
                            move_tag,
                            "<Button-1>",
                            select_move_handler
                        )

                tk_canvas.tag_bind(oval_tag, "<Button-1>", select_piece_handler)

        tk_root.mainloop()

    def _check_for_win(self, tk_root) -> None:
        green_spaces = self._get_camp_spaces(HalmaColor.GREEN)
        red_spaces = self._get_camp_spaces(HalmaColor.RED)

        def is_green_win() -> bool:
            for green_space in green_spaces:
                if green_space.piece == None or green_space.piece.color == HalmaColor.GREEN:
                    return False
            return True

        def is_red_win() -> bool:
            for red_space in red_spaces:
                if red_space.piece == None or red_space.piece.color == HalmaColor.RED:
                    return False
            return True

        if is_green_win():
            messagebox.showinfo("Game end", "Green wins!")
            tk_root.destroy()
        elif is_red_win():
            messagebox.showinfo("Game end", "Red wins!")
            tk_root.destroy()

    def _get_score(self, piece_color: HalmaColor, space: HalmaBoardSpace) -> float:
        enemy_camp_spaces: list[HalmaBoardSpace] = []

        # find nearest enemy camp square
        if piece_color == HalmaColor.RED:
            enemy_camp_spaces = self._get_camp_spaces(HalmaColor.GREEN)
        else:
            enemy_camp_spaces = self._get_camp_spaces(HalmaColor.RED)

        if space in enemy_camp_spaces:
            return 1
        
        shortest_distance: float = -1
        for enemy_camp_space in enemy_camp_spaces:
            distance = ((enemy_camp_space.col_index - space.col_index)**2 + (enemy_camp_space.row_index - space.row_index)**2)**0.5
            if shortest_distance < 0 or distance < shortest_distance:
                shortest_distance = distance

        return 1 / shortest_distance


    def _get_possible_moves(self, piece: HalmaPiece) -> list[HalmaBoardSpace]:
        possible_moves: list[HalmaBoardSpace] = []
        jump_queue: Final[deque[HalmaBoardSpace]] = deque()

        # adjacent squares
        piece_row_index = piece.space.row_index
        piece_col_index = piece.space.col_index
        for delta_row in [-1, 0, 1]:
            new_row_index = piece_row_index + delta_row
            if new_row_index >= self.width or new_row_index < 0:
                continue

            for delta_col in [-1, 0, 1]:
                new_col_index = piece_col_index + delta_col
                if delta_row == 0 and delta_col == 0:
                    continue
                if new_col_index >= self.width or new_col_index < 0:
                    continue

                space = self._grid[new_row_index][new_col_index]
                if space.piece is None:
                    possible_moves.append(space)
                    continue

                jump_row_index = new_row_index + delta_row
                jump_col_index = new_col_index + delta_col
                if (
                    jump_row_index < 0 
                    or jump_row_index >= self.width
                    or jump_col_index < 0
                    or jump_col_index >= self.width
                ):
                    continue

                jumped_space = self._grid[jump_row_index][jump_col_index]
                if jumped_space.piece is None:
                    jump_queue.append(jumped_space)

        # jumps
        checked_spaces: list[HalmaBoardSpace] = [piece.space]
        while len(jump_queue) > 0:
            space = jump_queue.popleft()

            for delta_row in [-1, 0, 1]:
                new_row_index = space.row_index + delta_row
                if new_row_index >= self.width or new_row_index < 0:
                    continue

                for delta_col in [-1, 0, 1]:
                    new_col_index = space.col_index + delta_col
                    if delta_row == 0 and delta_col == 0:
                        continue
                    if new_col_index >= self.width or new_col_index < 0:
                        continue

                    jumped_over_space = self._grid[new_row_index][new_col_index]
                    if jumped_over_space.piece is None:
                        continue

                    jump_row_index = new_row_index + delta_row
                    jump_col_index = new_col_index + delta_col
                    if (
                        jump_row_index < 0 
                        or jump_row_index >= self.width
                        or jump_col_index < 0
                        or jump_col_index >= self.width
                    ):
                        continue

                    jumped_space = self._grid[jump_row_index][jump_col_index]

                    if jumped_space.piece is None and jumped_space not in checked_spaces:
                        jump_queue.append(jumped_space)

            checked_spaces.append(space)
            if space not in possible_moves:
                possible_moves.append(space)

        # return and only get forward moves
        curr_score = self._get_score(piece.color, piece.space)

        def is_forward(move: HalmaBoardSpace) -> bool:
            enemy_color = (
                HalmaColor.RED
                if piece.color == HalmaColor.GREEN
                else HalmaColor.GREEN
            )

            enemy_camp_spaces = self._get_camp_spaces(enemy_color)
            piece_camp_spaces = self._get_camp_spaces(piece.color)
            move_score = self._get_score(piece.color, move)

            if piece.space in enemy_camp_spaces:
                return move in enemy_camp_spaces

            if piece.space in piece_camp_spaces:
                return move_score > curr_score

            return move_score >= curr_score

        return list(filter(is_forward, possible_moves))
    
    def _hide_possible_moves(self, tk_canvas: tk.Canvas):
        if self.possible_move_ids is None:
            return

        for tk_id in self.possible_move_ids:
            tk_canvas.delete(tk_id)

        self.possible_move_ids = None

    def _move_piece(
        self,
        piece:        HalmaPiece,
        space:        HalmaBoardSpace,
        tk_canvas:    tk.Canvas,
        box_width:    int,
        piece_radius: int,
    ):
        assert space.piece is None, "Cannot move to a non-empty square"

        piece.space.piece = None

        space.piece = piece
        piece.space = space
        top_left_x = space.col_index * box_width
        top_left_y = space.row_index * box_width
        tk_canvas.coords(
            piece.tk_id,
            top_left_x + (box_width / 2 - piece_radius),
            top_left_y + (box_width / 2 - piece_radius),
            top_left_x + (box_width / 2 + piece_radius),
            top_left_y + (box_width / 2 + piece_radius),
        )

        tk_canvas.tag_raise(piece.tk_id)
        
if __name__ == "__main__":
    assert len(sys.argv) >= 1 and len(sys.argv) <= 3

    board_size: HalmaBoardSize
    move_time: int

    if len(sys.argv) <= 1:
        board_size = HalmaBoardSize.SMALL
    else:
        assert int(sys.argv[1]) in [8, 10, 16]

        match int(sys.argv[1]):
            case 8:
                board_size = HalmaBoardSize.SMALL
            case 10:
                board_size = HalmaBoardSize.MEDIUM
            case 16:
                board_size = HalmaBoardSize.LARGE

    if len(sys.argv) == 3:
        move_time = int(sys.argv[2])
        assert move_time > 0
    else:
        move_time = 15

    board = HalmaBoard(board_size, move_time)
    board.display()
