import win32serviceutil
import servicemanager
import win32service
import win32event
from functools import partial, wraps

handle_cli = win32serviceutil.HandleCommandLine


def service(func):
    
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
            self.main(self)
            
    return WindowsService

