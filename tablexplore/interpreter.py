#!/usr/bin/env python
"""
    Implements a Python interpreter
    From original code from https://github.com/col-one/thonside

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

import sys
import code
from io import StringIO
from queue import Queue
from contextlib import redirect_stdout
from . import terminal

class TerminalPython(terminal.Terminal):
    def __init__(self, parent=None, table=None, app=None):
        super(TerminalPython, self).__init__(parent=parent)
        # Init interpreter and add globals to context that give access from it.
        self.interpreter = Interpreter(extra_context=globals().copy(), table=table, app=app,
                            stream_err=True, stream_out=True)
        # active queue thread with queue interpreter
        self.active_queue_thread(self.interpreter.queue)
        # define prompt
        self.prompt = self.interpreter.prompt
        # rename interpreter
        self.interpreter.inter_name = "ThonSide Interpreter"
        self.def_to_run_code = self.interpreter.run
        # start interpreter
        self.interpreter.interact()

class Streamer(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        if bool(text and text.strip()):
            #text = text.replace("\n", "")
            self.queue.put(text)

    def flush(self):
        pass


class Interpreter(code.InteractiveConsole):
    def __init__(self, extra_context=dict(), stream_out=True, stream_err=True,
            table=None, app=None):
        """
        Init an interpreter, get globals and locals from current context.
        Define classic python prompt style.
        """
        context = globals().copy()
        context.update(locals().copy())
        context.update(extra_context.copy())
        #
        super(Interpreter, self).__init__(context)
        self.inter_name = self.__class__.__name__
        self.queue = Queue()
        self.streamer_out = Streamer(self.queue)
        self.streamer_err = Streamer(self.queue)
        sys.stdout = self.streamer_out if stream_out else sys.__stdout__
        sys.stderr = self.streamer_err if stream_err else sys.__stderr__
        self.write_slot = self.queue.put
        self.input_slot = self.queue.put
        self.more = 0
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        self.prompt = sys.ps1
        #reference to table
        self.table = table
        self.app = app
        context.update({'df':table.model.df})
        import pandas as pd
        context.update({'pd':pd})
        return

    def write(self, data):
        """
        Override InteractiveConsole.write method to add a 'slot' connection,
        useful for different view implementation.
        :param data: str data to write
        :return:
        """
        if hasattr(self.write_slot, "__call__"):
            self.write_slot(data)
        else:
            super(Interpreter, self).write(data)

    def raw_input(self, prompt=""):
        """
        Override InteractiveConsole.raw_input method to add a 'slot' connection,
        useful for different view implementation.
        :param prompt: str prompt to write
        :return:
        """
        if hasattr(self.input_slot, "__call__"):
            self.input_slot(prompt)
        else:
            super(Interpreter, self).raw_input(prompt)

    def interact(self, banner=None, exitmsg=None):
        """
        Starting point for the interpreter. It is override for avoid while loop as classic shell.
        In this context interpreter doesn't use this functionality.
        :param banner: starter text
        :param exitmsg: no used
        :return:
        """
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" % (sys.version, sys.platform, cprt, self.inter_name))
        elif banner:
            self.write("%s\n" % str(banner))
        # run first prompt input.
        self.raw_input(self.prompt)

    def run(self, code):
        """
        Manage run code, like continue if : or ( with prompt switch >>> to ...
        :param code: str code to run
        :return:
        """
        self.more = self.push(code)
        if self.more:
            self.prompt = sys.ps2
        else:
            self.prompt = sys.ps1
        self.raw_input(self.prompt)

    def runcode(self, code):
        """
        Override InteractiveConsole.runcode method to manage stdout as a buffer.
        Useful for view implementation.
        :param code: str code to run
        :return:
        """
        super(Interpreter, self).runcode(code)
        # with sys.stdout as buf, redirect_stdout(buf):
        #     output = buf.getvalue()
        #     if bool(output and output.strip()):
        #         self.write(output)
        # with sys.stderr as buf, redirect_stdout(buf):
        #     output = buf.getvalue()
        #     if bool(output and output.strip()):
        #         self.write(output)
        # sys.stdout = old_stdout
