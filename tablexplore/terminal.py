#!/usr/bin/env python
"""
    Implements some dialog utilities for tableexplore
    Created Feb 2019
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import os, sys, platform
import atexit
if platform.system() in ['Linux','Darwin']:
    import readline
elif platform.system() == 'Windows':
    from pyreadline.rlmain import Readline
    readline = Readline()
import rlcompleter
from .qt import *

AUTOCOMPLETE_LIMIT = 20
AUTOCOMPLETE_SEPARATOR = "\n"

style = '''
    QPlainTextEdit {
        background-color: #20262c;
        color: white;
        font-family: Consolas, Monaco, monospace;
    }
    '''

class QueueReceiver(QtCore.QObject):
    sent = QtCore.Signal(str)

    def __init__(self, queue, *args, **kwargs):
        QtCore.QObject.__init__(self,*args,**kwargs)
        self.queue = queue

    @QtCore.Slot()
    def run(self):
        while True:
            text = self.queue.get()
            self.sent.emit(text)


class ExecThread(QtCore.QObject):
    finished = QtCore.Signal()
    def_to_run = None
    cmd = None
    @QtCore.Slot()
    def run(self):
        try:
            self.def_to_run(self.cmd)
        except:
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)
        self.finished.emit()

class Terminal(QPlainTextEdit):

    # signal to connect at the interpreter run code
    press_enter = QtCore.Signal(str)

    def __init__(self, parent=None, hist_file=None):
        """
        Micmic python terminal interpreter from a QPlainTextEdit. Can be override for app integration.
        Readline history is implemented, it's possible to change hist file path by define
        Terminal.hist_file attr.
        :param parent: parent widget
        """
        QPlainTextEdit.__init__(self, parent)
        self.setGeometry(50, 75, 600, 400)
        #self.setWordWrapMode(QTextOption.WrapAnywhere)
        self.setUndoRedoEnabled(False)
        font = QFont("Monospace")
        font.setPointSize(10)
        self.setFont(font)

        self.prompt = None
        self.cursor_line = None
        if hist_file == None:
            self.hist_file = os.path.join(os.path.expanduser("~"), ".pyTermHist")
        else:
            self.hist_file = hist_file
        self.init_history(self.hist_file)
        self.history_index = readline.get_current_history_length()
        self.completer = rlcompleter.Completer()
        self.def_to_run_code = None
        self.thread = None
        self.setTabStopWidth(4)
        # connection cursor line position
        self.cursorPositionChanged.connect(self.count_cursor_lines)
        # connect press enter
        self.press_enter.connect(self.exec_code)
        self.setStyleSheet(style)
        return

    def active_queue_thread(self, queue):

        self.thread_q = QtCore.QThread()
        self.receiver = QueueReceiver(queue)
        self.receiver.sent.connect(self.write)
        self.receiver.moveToThread(self.thread_q)
        self.thread_q.started.connect(self.receiver.run)
        self.thread_q.start()

    def contextMenuEvent(self, event):

        menu = QMenu(self)
        menu.addAction("Copy", lambda: self.copy())
        menu.addAction("Paste", lambda: self.paste())
        menu.addAction("Clear", lambda: self.clear())
        menu.addSeparator()
        menu.addAction("Zoom In", lambda: self.zoom(1))
        menu.addAction("Zoom Out", lambda: self.zoom(-1))
        style_menu = QMenu("Style", menu)
        menu.addAction(style_menu.menuAction())
        style_menu.addAction('Light', lambda: self.setStyle('light'))
        style_menu.addAction('Dark', lambda: self.setStyle('dark'))
        action = menu.exec_(self.mapToGlobal(event.pos()))

    def setStyle(self, style='default'):

        if style == 'light':
            ss = """background-color: #FBFBF8;
                        color: black;"""
        else:
            ss = """background-color: #20262c;
                        color: white;"""
        self.setStyleSheet(ss)
        return

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(1)

    def init_history(self, hist_file):
        """
        History initialisation with readline GNU, and use hook atexit for save history when program closing.
        :param hist_file: history file path
        :return:
        """
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(hist_file)
            except IOError:
                pass
            atexit.register(self.save_history, hist_file)

    def save_history(self, hist_file):
        """
        Hook def execute by atexit.
        :param hist_file: history file path
        :return:
        """
        readline.set_history_length(1000)
        readline.write_history_file(hist_file)

    def write(self, data):
        """
        Append text to the Terminal. And keep cursor at the end.
        :param data: str data to write.
        :return:
        """

        self.appendPlainText(data)
        self.moveCursor(QTextCursor.End)

    def write_prompt(self, data):
        """
        Append text to the Terminal. And keep cursor at the end.
        :param data: str data to write.
        :return:
        """
        import time
        time.sleep(4)
        self.appendPlainText(data)
        # self.moveCursor(QTextCursor.End)
        # self.remove_last_line()

    def raw_input(self, prompt=None):
        """
        Use to write the prompt command.
        :param prompt: str prompt
        :return:
        """
        if prompt is None:
            prompt = self.prompt
        self.write(prompt)

    def get_command(self):
        """
        Get command, read last line and remove prompt length.
        :return: str command
        """
        doc = self.document()
        current_line = (doc.findBlockByLineNumber(self.get_last_line() - 1).text())
        current_line = current_line.rstrip()
        current_line = current_line[len(self.prompt):]
        return current_line

    def get_last_line(self):
        """
        Get last terminal line.
        :return: str last line
        """
        doc = self.document()
        last_line = doc.lineCount()
        return last_line

    def get_cursor_position(self):
        """
        Get cursor position
        :return: int line cursor position.
        """
        return self.textCursor().columnNumber() - len(self.prompt)

    def remove_last_line(self):
        # cursor = QTextCursor(self.document().findBlockByLineNumber(self.get_last_line()-5))
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Up)
        cursor.movePosition(QTextCursor.Up)
        cursor.movePosition(QTextCursor.Up)
        cursor.movePosition(QTextCursor.Up)
        cursor.movePosition(QTextCursor.Up)
        self.setTextCursor(cursor)

    def remove_last_command(self):
        """
        Remove current command. Useful for display history navigation.
        :return:
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self.setTextCursor(cursor)

    def get_previous_history(self):
        """
        Get previous history in the readline GNU history file.
        :return: str history
        """
        self.history_index += 1
        if self.history_index >= readline.get_current_history_length():
            self.history_index = readline.get_current_history_length()
        return readline.get_history_item(self.history_index)

    def get_next_history(self):
        """
        Get next history in the readline GNU history file.
        :return: str history
        """
        if self.history_index <= 1:
            self.history_index = 1
        hist = readline.get_history_item(self.history_index)
        self.history_index -= 1
        return hist

    def autocomplete(self, command):
        """
        Ask different possibility from command arg, proposition is limited by AUTOCOMPLETE_LIMIT constant
        :param command: str
        :return: list of proposition
        """
        propositions = []
        completer = self.completer
        for i in range(AUTOCOMPLETE_LIMIT):
            ret = completer.complete(command, i)
            if ret:
                propositions.append(ret)
            else:
                break
        return propositions

    def write_autocomplete(self, command):
        """
        Prepare text to write.
        :param command: str command
        :return:
        """
        # Is = or space inside ?
        text_after_eq = command.split("=")[-1]
        text_strip = text_after_eq.strip()
        command_strip = text_strip.split(" ")[-1]
        propositions = self.autocomplete(command_strip)
        buffer = "--\n" + AUTOCOMPLETE_SEPARATOR.join(propositions)
        buffer = buffer.strip()
        if len(propositions) > 1:
            self.remove_last_command()
            self.write(buffer)
            self.raw_input(self.prompt + command)
        elif len(propositions) == 1:
            self.remove_last_command()
            # Replace text by last proposition
            command = command.replace(command_strip, propositions[0])
            self.write(self.prompt + command)
        else:
            return

    @Slot()
    def count_cursor_lines(self):
        """
        Slot def keep tracking cursor position line number. Useful to compare position to know if it is an
        editable line or not.
        :return:
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        lines = 1
        while cursor.positionInBlock() > 0:
            cursor.movePosition(QTextCursor.Up)
            lines += 1
        block = cursor.block().previous()
        while block.isValid():
            lines += block.lineCount()
            block = block.previous()
        self.cursor_line = lines

    def exec_code(self, cmd):

        self.thread = QtCore.QThread()
        self.exec_thread = ExecThread()
        self.exec_thread.cmd = cmd
        self.exec_thread.def_to_run = self.def_to_run_code
        self.exec_thread.moveToThread(self.thread)
        self.thread.started.connect(self.exec_thread.run)
        self.exec_thread.finished.connect(self.thread.quit)
        self.thread.start()

    def keyPressEvent(self, event):
        """
        Override to manage key board event.
        :param event: event key.
        :return:
        """
        # Is an editable line ? if not go to the last line.
        if self.cursor_line != self.get_last_line() and not self.textCursor().hasSelection():
            self.moveCursor(QTextCursor.End)
        # Enter key pressed to run code.
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            cmd = self.get_command()
            self.press_enter.emit(cmd)
            # add to the history.
            if bool(cmd and cmd.strip()):
                readline.add_history(cmd)
                self.history_index = readline.get_current_history_length()
            return
        # Avoid delete prompt or text before.
        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
            if self.get_cursor_position() == 0:
                return
        # History navigation.
        elif event.key() == QtCore.Qt.Key_Down:
            self.remove_last_command()
            self.raw_input(self.prompt + self.get_previous_history())
            return
        elif event.key() == QtCore.Qt.Key_Up:
            self.remove_last_command()
            self.raw_input(self.prompt + self.get_next_history())
            return
        # Tab autocomplete
        elif event.key() == QtCore.Qt.Key_Tab:
            cmd = self.get_command()
            if bool(cmd and cmd.strip()):
                self.write_autocomplete(cmd)
            #else:
            #    self.write_prompt("    ")
            return
        super(Terminal, self).keyPressEvent(event)

    def closeEvent(self, event):

        self.thread_q.stop()
        self.thread_q.exit()
