import pygame as pg
from pygame.locals import *
import random as rd
import copy
import time
import datetime

case_size = 50
pg.init()
screen = pg.display.set_mode((9 * case_size + 2, 9 * case_size + 2))
pg.display.set_caption("Sudoku solver")

FONT = pg.font.SysFont('Arial', 26)
SMALL_FONT = pg.font.SysFont('Arial', 12)
WHITE = 255, 255, 255
BLACK = 0, 0, 0
YELLOW = 255, 255, 100
YELLOW_DARK = 255, 255, 0
GREY = 220, 220, 220
RED = 220, 10, 10
GREYELLOW = 235, 235, 150
GREYELLOW_2 = 235, 235, 50


class Case:

    def __init__(self, value=None):
        self.value = value           # Contained value
        self.is_highlighted = False  # Used for display
        self.is_locked = False       # Set at beginning
        self.is_selected = False     # Used for display
        self.is_wrong = False        # Contains a wrong value
        self.blacklist = []          # Numbers that can't be used

    def set(self, value=None):
        """
        Set value contained in the case. If sure, of type int (one value).
        Else, of type list, when listing different possibilities.
        :param value: int or list
        :return: void
        """
        self.value = value

    def get_surface(self):
        """
        Blits the pygame surface
        :return: The pygame surface representing the case
        """
        surface = pg.Surface((case_size, case_size))
        surface.fill(WHITE)
        if self.is_locked:
            surface.fill(GREY)
        if self.is_highlighted:
            surface.fill(YELLOW)
        if self.is_locked and self.is_highlighted:
            surface.fill(GREYELLOW)
        if self.is_locked and self.is_selected:
            surface.fill(GREYELLOW_2)
        if self.is_selected:
            surface.fill(YELLOW_DARK)
        if self.is_wrong:
            surface.fill(RED)
        if self.value is not None:
            if isinstance(self.value, type(0)):
                text = FONT.render(str(self.value), True, BLACK)
                surface.blit(text, [case_size / 2 - text.get_width() / 2,
                                    case_size / 2 - text.get_height() / 2])
            elif isinstance(self.value, type([])):
                small_case_size = case_size // 3
                for k in range(1, 10):
                    if k in self.value:
                        text = SMALL_FONT.render(str(k), True, BLACK)
                        surface.blit(text, [((k-1) % 3) * small_case_size
                                            + small_case_size / 2
                                            - text.get_width() / 2,
                                            ((k - 1) // 3) * small_case_size
                                            + small_case_size / 2
                                            - text.get_height() / 2])
        return surface


class Sudoku:

    def __init__(self):
        self.grid = []                     # Matrix of cases
        self.set_history = []              # Whole history of value setting
        self.choice_history = []           # History of choices
        self.minimum_possibilities = None  # Minimum of cases list value length

        for i in range(9):
            self.grid.append([])
            for j in range(9):
                self.grid[i].append(Case())

    def set_case(self, i, j, value, lock=False, record=True):
        """
        Set a value to a case.
        :param i: Row of the case
        :param j: Column of the case
        :param value: Value to set.
        :param lock: Lock the case
        :param record: Append change to set_history
        :return: void
        """
        if record:
            self.set_history.append((i, j, value))
        self.grid[i][j].set(value)
        if lock:
            self.grid[i][j].is_locked = True

    def remove_random_case(self):
        """
        Reset the value of a random case from the grid, and unlock it, if it
        does not contain a list.
        :return: The position and the value of reset case.
        """
        while True:
            i, j = rd.randint(0, 8), rd.randint(0, 8)
            value = self.get_value(i, j)
            if isinstance(value, type(0)):
                self.grid[i][j].value = None
                self.grid[i][j].is_locked = False
                return i, j, value

    def get_value(self, i, j):
        return self.grid[i][j].value

    def get_possibilities(self, i, j):
        """
        Given a case, check its blacklist, its square, its column and its row to
        build the list of possible values.
        :param i: Row of the case
        :param j: Column of the case
        :return: The list of possible numbers, sorted in ascendant order
        """
        relatives = get_relatives(i, j)
        possibilities = [q for q in range(1, 10)
                         if q not in self.grid[i][j].blacklist]
        for (k, p) in relatives:
            if isinstance(self.get_value(k, p), type(0))\
                    and self.get_value(k, p) in possibilities:
                possibilities.remove(self.get_value(k, p))
        possibilities.sort()
        return possibilities

    def set_possibilities(self):
        """
        For each empty case or list case, sets its possibilities as value, and
        then update the minimum possibilities.
        :return: void
        """
        self.minimum_possibilities = 9
        for i in range(9):
            for j in range(9):
                if self.get_value(i, j) is None \
                   or isinstance(self.get_value(i, j), type([])):
                    self.set_case(i, j, self.get_possibilities(i, j),
                                  record=False)
                    self.minimum_possibilities\
                        = min(self.minimum_possibilities,
                              len(self.get_possibilities(i, j)))

    def choose_random_case(self):
        """
        Selects a random case, sets its value from the list of its
        possibilities, and locks it. Used for generation.
        :return: void
        """
        while True:
            i, j = rd.randint(0, 8), rd.randint(0, 8)
            if not self.grid[i][j].is_locked:
                self.set_case(i, j, rd.choice(self.get_possibilities(i, j)),
                              lock=True, record=False)
                break

    def set_sure_values(self):
        """
        For each case, if its value is a list of exactly one number, use it as
        value.
        :return: void
        """
        for i in range(9):
            for j in range(9):
                if isinstance(self.get_value(i, j), type([]))\
                        and len(self.get_value(i, j)) == 1:
                    self.set_case(i, j, self.grid[i][j].value[0])

    def backtrack(self, verbosity=False):
        """
        Remove last choice, adds it to the case blacklist, and removes all
        changes since then (resetting cases).
        :param verbosity: Display print message
        :return: void
        """
        i0, j0, error_value = self.choice_history.pop()
        if verbosity:
            print("WRONG CHOICE: ", i0, j0, error_value)
        self.grid[i0][j0].blacklist.append(error_value)
        run = True
        while run:
            i, j, value = self.set_history.pop()
            self.set_case(i, j, None, record=False)
            if (i, j) == (i0, j0):
                run = False
            else:
                self.grid[i][j].blacklist = []

    def step_solve(self, verbosity=False):
        """
        Set all posibilities.
        If an error is detected, then backtracks.
        If at least one case has 1 possibility, set all values.
        Else, finds a case with least possible possibilities in the grid, and
        choose one of its values.
        :param verbosity: Display print messages
        :return: void
        """
        self.set_possibilities()
        if self.is_wrong() or self.minimum_possibilities <= 0:
            self.backtrack()
        elif self.minimum_possibilities == 1:
            self.set_sure_values()
        elif self.minimum_possibilities > 1:
            # Finding the case with minimum possibilities
            i0, j0 = -1, -1
            i = 0
            run = True
            while run and i < 9:
                j = 0
                while run and j < 9:
                    if (not isinstance(self.get_value(i, j), type(0)))\
                            and len(self.get_possibilities(i, j))\
                            == self.minimum_possibilities:
                        i0, j0 = i, j
                        run = False
                    j += 1
                i += 1
            # Choosing its value, and appends it to blacklist to avoid it being
            # selected later on.
            possibilities = self.get_possibilities(i0, j0)
            k = rd.randint(0, len(possibilities)-1)
            if verbosity:
                print("CHOICE: ", i0, j0, possibilities[k])
            self.choice_history.append((i0, j0, possibilities[k]))
            self.set_case(i0, j0, possibilities[k])
            self.grid[i0][j0].blacklist.append(possibilities[k])

    def solve(self, verbosity=True, display=None):
        """
        Solves the whole sudoku.
        :param verbosity: Display print message
        :param display: A reference to the DisplaySudoku, if wanted for gui
        :return: Wether a solution has been found
        """
        if verbosity:
            print("Solving sudoku...", end='')

        attempt = 0
        t0 = time.time()
        while not self.is_solved():
            attempt += 1
            try:
                self.step_solve()
                if display is not None:
                    display.update_display()
                if verbosity:
                    print("\rSolving sudoku..." + str(self.completed_cases())
                          + "/81 ", end='')
            except Exception as e:
                print(e)
                if verbosity:
                    print("\nNo solution found. ET:"
                          + str_time(time.time() - t0))
                return False
        if verbosity:
            print("\nSudoku solved with " + str(len(self.choice_history))
                  + " choices in " + str_time(time.time() - t0))
        return True

    def second_solve(self, verbosity=True):
        """
        Removes last choice and solve the sudoku again.
        :param verbosity: Display print message.
        :return: Wether a second solution exists.
        """
        try:
            self.backtrack()
            return self.solve(verbosity)
        except Exception as e:
            print(e)
            if verbosity:
                print("--NO OTHER SOLUTION FOUND--")
            return False

    def exists_second_sol(self, verbosity=True):
        """
        Try to solve the same sudoku twice with different choices.
        :param verbosity: Display print message
        :return: If at least two solutions are found
        """
        if self.solve(verbosity):
            return self.second_solve(verbosity)
        return False

    def completed_cases(self):
        """
        :return: The number of cases in the grid that have a sure value
        """
        completed_cases = 0
        for i in range(9):
            for j in range(9):
                if isinstance(self.get_value(i, j), type(0)):
                    completed_cases += 1
        return completed_cases

    def is_complete(self):
        """
        :return: Wether the sudoku is complete or not
        """
        return self.completed_cases() == 81

    def relative_values(self, i, j):
        """
        Returns the list of values encountered around the case i, j
        :param i: Row of the case
        :param j: Column of the case
        :return: List of its relative values
        """
        return [self.get_value(k, p) for (k, p) in get_relatives(i, j)
                if isinstance(self.get_value(k, p), type(0))
                and (i, j) != (k, p)]

    def case_error(self, i, j):
        """
        Check if an error is detected at case i, j
        :param i: Row of the case
        :param j: Column of the case
        :return: True if its value is in its relatives value
        """
        relatives = self.relative_values(i, j)
        if isinstance(self.get_value(i, j), type(0))\
                and self.get_value(i, j) in relatives:
            return True
        return False

    def is_wrong(self):
        """
        Checks the whole grid for an error..
        :return: True if at least one error is encountered.
        """
        for i in range(9):
            for j in range(9):
                if self.case_error(i, j):
                    return True
        return False

    def is_solved(self):
        return self.is_complete() and not self.is_wrong()


class DisplaySudoku:

    def __init__(self, sudoku, screen, case_size=50):
        self.sudoku = sudoku
        self.screen = screen
        self.case_size = case_size
        self.selected_case = None

    def unselect_all_cases(self):
        for i in range(9):
            for j in range(9):
                self.sudoku.grid[i][j].is_highlighted = False
                self.sudoku.grid[i][j].is_selected = False

    def select_case(self, i, j):
        self.selected_case = i, j
        self.unselect_all_cases()
        for (k, p) in get_relatives(i, j):
            self.sudoku.grid[k][p].is_highlighted = True
        self.sudoku.grid[i][j].is_selected = True

    def highlight_error(self):
        for i in range(9):
            for j in range(9):
                self.sudoku.grid[i][j].is_wrong = self.sudoku.case_error(i, j)
        self.update_display()

    def move_cursor(self, key):
        if self.selected_case is None:
            self.select_case(0, 0)
        else:
            i, j = self.selected_case
            if key == K_DOWN and i < 8:
                self.select_case(i + 1, j)
            elif key == K_UP and i > 0:
                self.select_case(i - 1, j)
            elif key == K_LEFT and j > 0:
                self.select_case(i, j - 1)
            elif key == K_RIGHT and j < 8:
                self.select_case(i, j + 1)

    def get_surface(self):
        surface = pg.Surface((9 * self.case_size + 2, 9 * self.case_size + 2))
        surface.fill(WHITE)
        for i in range(9):
            for j in range(9):
                surface.blit(self.sudoku.grid[i][j].get_surface(),
                             [j * self.case_size, i * self.case_size])
        for i in range(10):
            w = 1
            if i % 3 == 0:
                w = 2
            pg.draw.line(surface, BLACK, (i * self.case_size, 0),
                         (i * self.case_size, 9 * self.case_size + 2), w)
            pg.draw.line(surface, BLACK, (0, i * self.case_size),
                         (9 * self.case_size + 2, i * self.case_size), w)
        return surface

    def update_display(self):
        self.screen.blit(self.get_surface(), [0, 0])
        pg.display.flip()


def matrix_from_string(string):
    matrix = []
    for row in string.split('\n'):
        matrix.append([])
        for figure in row:
            if figure == ' ':
                matrix[-1].append(None)
            else:
                matrix[-1].append(int(figure))
    return matrix


def string_from_matrix(m):
    s = ""
    for i in range(9):
        for j in range(9):
            if m[i][j] is None:
                s += " "
            else:
                s += str(m[i][j])
        s += "\n"
    return s


def sudoku_from_matrix(m):
    s = Sudoku()
    for i in range(9):
        for j in range(9):
            if m[i][j] is not None:
                s.set_case(i, j, m[i][j], True, False)
    return s


def matrix_from_sudoku(s):
    m = []
    for i in range(9):
        m.append([])
        for j in range(9):
            m[i].append(s.grid[i][j].value)
    return m


def get_clicked_case(pos):
    x, y = pos
    return y // case_size, x // case_size


def get_relatives(i, j):

    def get_row(i):
        return [(i, k) for k in range(9)]

    def get_column(j):
        return [(k, j) for k in range(9)]

    def get_square(i, j):
        return [(k, p) for k in range(9)
                for p in range(9)
                if i//3 == k//3 and j//3 == p//3]

    return [pos for pos in get_row(i) + get_square(i, j) + get_column(j)
            if pos != (i, j)]


def get_empty_matrix():
    m = []
    for i in range(9):
        m.append([])
        for j in range(9):
            m[i].append(None)
    return m


def generate_naive_sudoku(empty_cases=40):
    s = sudoku_from_matrix(get_empty_matrix())
    s.solve(verbosity=False)
    for k in range(empty_cases):
        s.remove_random_case()
    return sudoku_from_matrix(matrix_from_sudoku(s))


def generate_easy_sudoku():
    s = generate_naive_sudoku(0)
    while not copy.deepcopy(s).exists_second_sol():
        i, j, value = s.remove_random_case()
    s.grid[i][j].value = value
    s.grid[i][j].is_locked = True
    return s


def generate_long_sudoku(verbosity=True):
    if verbosity:
        print("Generating sudoku...", end='')
    t0 = time.time()
    added_cases = 0
    s = sudoku_from_matrix(get_empty_matrix())
    while copy.deepcopy(s).exists_second_sol(verbosity=False):
        s.choose_random_case()
        added_cases += 1
        if verbosity:
            print("\rGenerating sudoku... "
                  + str(added_cases) + " cases added.", end='')
    if copy.deepcopy(s).solve(verbosity=False):
        if verbosity:
            print("\rSudoku generated: " + str(added_cases)
                  + "cases in " + str_time(time.time() - t0))
        return s
    if verbosity:
        print("\rError generating sudou, retrying...")
    return generate_sudoku()


def generate_sudoku(verbosity=True):
    if verbosity:
        print("Generating sudoku...", end='')
    t0 = time.time()
    added_cases = 0
    ref = generate_naive_sudoku(0)
    s = sudoku_from_matrix(get_empty_matrix())
    while copy.deepcopy(s).exists_second_sol(verbosity=False):
        i, j = get_semi_random_empty_position(s)
        s.set_case(i, j, ref.get_value(i, j), lock=True, record=False)
        added_cases += 1
        if verbosity:
            print("\rGenerating sudoku... "
                  + str(added_cases) + " cases added.", end='')
    if copy.deepcopy(s).solve(verbosity=False):
        if verbosity:
            print("\rSudoku generated: " + str(added_cases)
                  + " cases in " + str_time(time.time() - t0))
        return s
    if verbosity:
        print("\rError generating sudou, retrying...")
    return generate_long_sudoku()


def get_semi_random_empty_position(sudoku):

    def is_empty(i, j):
        return not isinstance(sudoku.get_value(i, j), type(0))

    def choose_x(table):
        total = 0
        for k in range(9):
            total += table[k]
        p = rd.random()
        possibilities = 0
        for k in range(9):
            possibilities += table[k]
            if p < possibilities/total:
                return k
        return 8

    cases_per_row = [len([k for k in range(9) if is_empty(i, k)])
                     for i in range(9)]
    cases_per_column = [len([k for k in range(9) if is_empty(k, j)])
                        for j in range(9)]
    total_cases = 0
    for k in range(9):
        total_cases += cases_per_row[k]

    while True:
        i, j = choose_x(cases_per_row), choose_x(cases_per_column)
        if is_empty(i, j):
            return i, j


def str_time(t):
    return str(int(t * 100) / 100) + "s"


libe = "1  94 768\n" \
     + "     7439\n" \
     + "497   125\n" \
     + "7 82 4  1\n" \
     + "  17  842\n" \
     + "942581673\n" \
     + "274    86\n" \
     + " 1 4    7\n" \
     + "    76214"


# s = DisplaySudoku(sudoku_from_matrix(matrix_from_string(libe)),
#                   screen, case_size)

s = DisplaySudoku(generate_long_sudoku(), screen, case_size)

run = True
while run:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        elif event.type == MOUSEBUTTONUP:
            i, j = get_clicked_case(event.pos)
            s.select_case(i, j)
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                s.unselect_all_cases()
            elif event.key == K_p:
                s.sudoku.set_possibilities()
            elif event.key == K_s:
                s.sudoku.step_solve()
            elif event.key == K_d:
                s.sudoku.solve(display=s)
            elif event.key == K_r:
                s.sudoku.remove_random_case()
            elif event.key == K_e:
                s.highlight_error()
                if s.selected_case is not None:
                    i, j = s.selected_case
                    print("Case " + str(i) + " " + str(j) + " error: "
                          + str(s.sudoku.case_error(i, j)))
            elif event.key == K_f:
                s.sudoku.second_solve()
            elif event.key == K_g:
                filename = "sudoku_" + datetime.datetime\
                    .fromtimestamp(time.time())\
                    .strftime('%Y_%m_%d_%H_%M_%S')\
                           + ".txt"
                file = open(filename, 'w')
                file.write(string_from_matrix(matrix_from_sudoku(s.sudoku)))
                file.close()
                print("Sudoku saved at", filename)
            elif event.key in [K_BACKSPACE, K_DELETE]:
                if s.selected_case is not None:
                    i, j = s.selected_case
                    if not s.sudoku.grid[i][j].is_locked:
                        s.sudoku.grid[i][j].value = None
            elif event.key in [K_DOWN, K_UP, K_RIGHT, K_LEFT]:
                s.move_cursor(event.key)
            elif event.key in [K_KP1, K_KP2, K_KP3, K_KP4, K_KP5, K_KP6, K_KP7,
                               K_KP8, K_KP9]:
                if s.selected_case is not None:
                    i, j = s.selected_case
                    if not s.sudoku.grid[i][j].is_locked:
                        pressed = pg.key.get_pressed()
                        shiftDown = pressed[K_SPACE]
                        if shiftDown:
                            if s.sudoku.get_value(i, j) is None \
                               or isinstance(s.sudoku.get_value(i, j), type(0)):
                                s.sudoku.grid[i][j].value = [int(event.key)-256]
                            else:
                                if int(event.key)-256\
                                        in s.sudoku.grid[i][j].value:
                                    s.sudoku.grid[i][j].value\
                                        .remove(int(event.key) - 256)
                                else:
                                    s.sudoku.grid[i][j].value\
                                        .append(int(event.key) - 256)
                        else:
                            s.sudoku.set_case(i, j, int(event.key) - 256)

    screen.blit(s.get_surface(), [0, 0])
    pg.display.flip()
