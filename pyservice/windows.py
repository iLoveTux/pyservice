######################################################################################
#
#   This file is part of PyService.
#
#   PyService is free software: you can redistribute it and/or modify it under the
#   terms of the GNU General Public License as published by the Free Software
#   Foundation, version 2.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program; if not, write to the Free Software Foundation, Inc., 51
#   Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#   Copyright: Swen Kooij (Photonios) <photonios@outlook.com>
#
#####################################################################################
"""This module implements the service decorator for Windows based systems.

The symbols "handle_cli" and "service" are imported from this module if
this code is run on a Windows system, and the same tokens are imported from
"pyservice/linux.py" if this code is executed on a Linux based system.

In either case, "service" is a decorator which will turn a callable object
into a service on the current system, in this way you can simply write one
function which can be installed, started, stopped and removed for both
Linux and Windows.

Your code will automatically be cross platform and the differences will
be handled by this library.
"""
import win32serviceutil
import servicemanager
import win32service
import win32event
import threading
from time import sleep
from functools import partial, wraps

handle_cli = win32serviceutil.HandleCommandLine
handle_cli.__doc__ = """This is a thin wrapper around
win32serviceutil.HandleCommandLine
"""

def service(func):
    """decorator which will turn func into a windows service
    
    :param func: The function to turn into a windows service
    :type func: callable
    """
    
    @wraps(func)
    class WindowsService(win32serviceutil.ServiceFramework):
        _svc_name_ = func.__name__
        _svc_display_name_ = func.__name__
        

        def __init__(self, args):
            """Initialize the service.
            """
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.stop_requested = False
            self.main = func

        def SvcStop(self):
            """Stop the service.
            """
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.stop_requested = True

        def SvcDoRun(self):
            """Run the service.
            """
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            child = threading.Thread(target=self.main, args=(self, ))
            child.daemon = True
            child.start()
            while not self.stop_requested:
                sleep(1)
            
    return WindowsService

