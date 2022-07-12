import random
import sys
from copy import deepcopy
from typing import List

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


STYLE_BUTTON = "background-color: rgb(225, 225, 225);"
STYLE_BUTTON_PRESSED = "background-color: rgb(180, 180, 180);"
STYLE_BUTTON_BOMB = "background-color: rgb(200, 64, 64);"


class Field:
    def __init__(self, game, x, y):
        self.x, self.y = x, y
        self.game = game
        self.q_push_button: QPushButton = QPushButton('')
        self.q_push_button.setFixedSize(32, 32)
        self.q_push_button.setFont(QFont("Arial", 15))
        self.q_push_button.setStyleSheet(STYLE_BUTTON)
        self.q_push_button.clicked.connect(self.on_click)
        self.q_push_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.q_push_button.customContextMenuRequested.connect(self.toggle_mark)

        self.is_bomb = False
        self.is_pressed = False
        self.is_marked = False

    def set_label(self, label):
        if not self.is_pressed:
            self.q_push_button.setText(label)

    def toggle_mark(self):
        if not self.is_pressed:
            self.is_marked = not self.is_marked
            if self.is_marked:
                self.q_push_button.setText("!")
            else:
                self.q_push_button.setText(" ")

    def get_neighbours_ranges(self):
        table_size = len(self.game.table)
        start_x, start_y = max(0, self.x-1), max(0, self.y-1)
        end_x, end_y = min(table_size, self.x+2), min(table_size, self.y+2)
        return start_x, start_y, end_x, end_y

    def get_neighbours_score(self):
        score = 0
        start_x, start_y, end_x, end_y = self.get_neighbours_ranges()
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if self.game.table[x][y].is_bomb:
                    score += 1
        return score

    def click_all_neighbours(self):
        start_x, start_y, end_x, end_y = self.get_neighbours_ranges()
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                self.game.table[x][y].trigger_field(rippled=True)

    def trigger_field(self, trigger_events=True, rippled=False):
        if not self.is_pressed and not self.is_marked:
            self.is_pressed = True
            neighbours_score = self.get_neighbours_score()
            self.q_push_button.setText(str(neighbours_score))
            if neighbours_score == 0 and trigger_events:
                self.click_all_neighbours()
            if self.is_bomb:
                self.q_push_button.setStyleSheet(STYLE_BUTTON_BOMB)
                if trigger_events:
                    self.game.finish_game(False)
            else:
                self.q_push_button.setStyleSheet(STYLE_BUTTON_PRESSED)
            self.q_push_button.setDisabled(True)
            if self.game.is_game_solved() and trigger_events and not rippled:
                self.game.finish_game(True)

    def on_click(self):
        self.trigger_field()  # Bug fix, altfel parametrii devin null/False


class Game(QDialog):
    def __init__(self, size, mines, time_limit):
        super(Game, self).__init__()
        self.setWindowTitle("Minesweeper")
        self.q_timer = None
        self.game_finished = False
        self.game_size = size
        self.mines = mines
        self.time_limit = time_limit
        self.table: List[List[Field]] = [list() for _ in range(self.game_size)]

        self.layout = QGridLayout()
        self.layout.setHorizontalSpacing(1)
        self.layout.setVerticalSpacing(1)
        self.setLayout(self.layout)

        self.time_left = time_limit
        self.time_left_label = QLabel("Time Left: {}".format(self.time_left))
        self.time_left_label.setAlignment(Qt.AlignCenter)

        self.draw_table()
        self.start_timer()

        self.show()

    def is_game_solved(self):
        for x in range(self.game_size):
            for y in range(self.game_size):
                field = self.table[x][y]
                if field.is_pressed:
                    continue
                if field.is_marked and field.is_bomb:
                    continue
                return False
        return True

    def game_finished_popup_clicked(self, msg):
        if msg.text() == "Retry":
            for x in range(self.game_size):
                for y in range(self.game_size):
                    self.table[x][y].q_push_button.setHidden(True)
                    self.table[x][y].q_push_button.deleteLater()
            self.game_finished = False
            self.table: List[List[Field]] = [list() for _ in range(self.game_size)]
            self.time_left = self.time_limit
            self.time_left_label.setText("Time Left: {}".format(self.time_left))
            self.draw_table()
            self.start_timer()
            self.show()
        elif msg.text() == "Close":
            self.done(0)

    def finish_game(self, game_won_bool):
        if self.game_finished:
            return
        self.game_finished = True
        for x in range(self.game_size):
            for y in range(self.game_size):
                field = self.table[x][y]
                if not field.is_pressed:
                    field.trigger_field()
                if field.is_marked and not field.is_bomb:
                    field.toggle_mark()
                    field.trigger_field(trigger_events=False)

        msg = QMessageBox()
        msg.setWindowTitle("Game Ended!")
        msg.setText("You {}".format(
            "won!" if game_won_bool else "lost!{}".format(
                "\nYour time ran out!" if self.time_left == 0 else "")))
        msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Close)
        msg.buttonClicked.connect(self.game_finished_popup_clicked)
        x = msg.exec_()

    def start_timer(self):
        self.time_left = self.time_limit

        self.q_timer = QTimer()
        self.q_timer.timeout.connect(self.timer_timeout)
        self.q_timer.start(1000)

    def timer_timeout(self):
        self.time_left -= 1

        self.time_left_label.setText("Time Left: {}".format(self.time_left))
        if self.time_left == 0:
            self.q_timer.stop()
            self.finish_game(False)

    def draw_table(self):
        self.layout.addWidget(self.time_left_label, 0, 0, 1, self.game_size)

        for x in range(self.game_size):
            for y in range(self.game_size):
                new_field = Field(self, x, y)
                self.table[x].append(new_field)
                self.layout.addWidget(new_field.q_push_button, x+1, y)

        for _ in range(self.mines):
            mine_x, mine_y = random.randint(0, self.game_size - 1), random.randint(0, self.game_size - 1)
            while self.table[mine_x][mine_y].is_bomb:
                mine_x, mine_y = random.randint(0, self.game_size - 1), random.randint(0, self.game_size - 1)
            self.table[mine_x][mine_y].is_bomb = True

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.q_timer.stop()


class StartMenu(QDialog):
    def __init__(self):
        super(StartMenu, self).__init__()
        self.setWindowTitle("Minesweeper")

        self.layout = QGridLayout()
        self.layout.setHorizontalSpacing(1)
        self.layout.setVerticalSpacing(1)
        self.setLayout(self.layout)

        self.draw_window()
        self.show()

    def draw_window(self):
        # Table size input
        self.table_size_label = QLabel("Table Size ")
        self.layout.addWidget(self.table_size_label, 0, 0)

        self.table_size_edit = QLineEdit()
        self.table_size_edit.setText("16")
        self.table_size_edit.setValidator(QIntValidator())
        self.layout.addWidget(self.table_size_edit, 0, 1)

        # Table bombs input
        self.table_bombs_label = QLabel("Table Bombs ")
        self.layout.addWidget(self.table_bombs_label, 1, 0)

        self.table_bombs_edit = QLineEdit()
        self.table_bombs_edit.setText("40")
        self.table_bombs_edit.setValidator(QIntValidator())
        self.layout.addWidget(self.table_bombs_edit, 1, 1)

        # Game time limit input
        self.game_time_limit_label = QLabel("Game Time Limit (seconds)")
        self.layout.addWidget(self.game_time_limit_label, 2, 0)

        self.game_time_limit_edit = QLineEdit()
        self.game_time_limit_edit.setText("300")
        self.game_time_limit_edit.setValidator(QIntValidator())
        self.layout.addWidget(self.game_time_limit_edit, 2, 1)

        # Start game button
        self.start_game_button = QPushButton("Start Game")
        self.start_game_button.clicked.connect(self.start_game)
        self.layout.addWidget(self.start_game_button, 3, 0, 1, 2)

    def exit(self):
        self.done(0)

    def start_game(self):
        self.start_game_button.setEnabled(False)
        # Check game starting values!
        table_size = int(self.table_size_edit.text())
        bombs = int(self.table_bombs_edit.text())
        time_limit = int(self.game_time_limit_edit.text())

        if 4 <= table_size <= 30 and 4 <= bombs <= int(max(4, table_size ** 2 / 4)) and time_limit >= 1:
            exit_code = Game(table_size, bombs, time_limit).exec_()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Error!")
            msg.setText("Table Size must be in range [4, 30], bombs in range [4, {}] and time limit >= 1s".format(
                int(max(4, table_size ** 2 / 4))))
            msg.setStandardButtons(QMessageBox.Ok)
            x = msg.exec_()
        self.start_game_button.setEnabled(True)


def enable_pyqt5_debugging():
    sys._excepthook = sys.excepthook

    def my_exception_hook(exctype, value, traceback):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook


def main():
    # Start the software
    app = QApplication(sys.argv)
    game_start_menu = StartMenu()
    # Add the close feature at the program with the X

    enable_pyqt5_debugging()
    try:
        sys.exit(app.exec_())
    except:
        print("Exiting...")


if __name__ == '__main__':
    main()
