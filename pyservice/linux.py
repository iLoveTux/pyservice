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
"""This module implements the service decorator for Linux based systems.

The symbols "handle_cli" and "service" are imported from this module if
this code is run on a Linux system, and the same tokens are imported from
"pyservice/windows.py" if this code is executed on a Windows based system.

In either case, "service" is a decorator which will turn a callable object
into a service on the current system, in this way you can simply write one
function which can be installed, started, stopped and removed for both
Linux and Windows.

Your code will automatically be cross platform and the differences will
be handled by this library.
"""
import os
import stat
import sys
import pwd
import atexit
import signal
import argparse
import time
import textwrap
from functools import wraps

def handle_cli(_service, argv=None):
    """This will parse the options specified on the command line
    and call the associated function:

    Valid subcommands: install, remove, start, stop, run

    If none of the command line parameters above is specified, it
    will default to `run` which will run the program in the foreground
    without being installed as a service.
    
    :param _service: The service class for which to create the CLI
    :param argv: A list of arguments in the form of sys.argv (defaults to sys.argv)
    :type argv: list
    :type _service: pyservice.LinuxService
    :rtype: None
    """
    argv = sys.argv[1:] if argv is None else argv
    
    parser = argparse.ArgumentParser(
        description="Service control script for {}.".format(_service.name),
        epilog="Only one option is allowed at any time" 
    )
    subparsers = parser.add_subparsers()
    
    install = subparsers.add_parser("install",
                                    help="Install the {} service".format(_service.name))
    install.add_argument("--user", help="the user to run as", required=True)
    install.set_defaults(func=_service.install)
    
    remove = subparsers.add_parser("remove",
                                    help="Uninstall the {} service".format(_service.name))
    remove.set_defaults(func=_service.uninstall)
    
    start = subparsers.add_parser("start",
                                    help="Start the {} service".format(_service.name))
    start.add_argument("--user", help="the user to run as", required=True)
    start.set_defaults(func=_service.start)
    
    stop = subparsers.add_parser("stop",
                                    help="Stop the {} service".format(_service.name))
    stop.set_defaults(func=_service.stop)
    
    run = subparsers.add_parser("run",
                                help="Run {} in the foreground without installing as a service".format(_service.name))
    run.set_defaults(func=_service.started)

    args = parser.parse_args(argv)
    kwargs = vars(args)

    if "func" not in kwargs:
        kwargs["func"] = _service.started 
    func = kwargs.pop("func")

    if not func(**kwargs):
        sys.exit(1)


# , service, name, description, auto_start
def service(func):
    """Decorator to turn a function into a Linux service.
    
    Handles runas, daemonization and installation as a service
    
    :param func: The function to turn into a service
    :type func: callable 
    """
    
    class LinuxService(object):
        """Implements service functionality (using daemons) on Linux.
        """
        def __init__(self):
            """Initializes a new instance pyservice.LinuxService.
            """

            self.name = func.__name__
            self.description = getattr(
                    func,
                    "__doc__", 
                    "A cross-platform service powered by PyService")
            self.stop_requested = False

            # We store a start script in /etc/init.d, for now we don't support
            # system who don't have it
            if not os.path.exists('/etc/init.d'):
                raise RuntimeError('`/etc/init.d` does not exists, this '
                                   'platform is unsupported.')

            pid_files_directory = os.path.join("/var", "run")

            # Build up some paths
            self.pid_file = os.path.join(pid_files_directory, self.name + '.pid')
            self.control_script = '/etc/init.d/%s' % self.name

        def started(self, user):
            """Runs the actual business logic of the service
            
            :param user: The user to run as
            :type user: str
            :returns: None
            :rtype: None
            """
            uid = pwd.getpwnam(user)
            try:
                os.setuid(uid.pw_uid)
            except KeyError:
                raise RuntimeError("* user {} does not seem to exist.".format(user))
            func(self)

        def start(self, user):
            """Starts this service.

            :param user: the user to run as
            :type user: str
            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """
            if not self.is_installed():
                print('* Not Installed')
                return False

            # Make sure the service is not already running
            if self.is_running():
                print('* Already running')
                return False

            # Attempt to start the service
            print('* Starting %s' % self.name)
            result = self._start()
            if not result:
                return False

            # Call event handler
            self.started(user)
            return result

        def stop(self):
            """Stop this service.

            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """
            # Make sure that the service is running
            if not self.is_running():
                print('* Not running')
                return False

            # Attempt to stop the service
            print('* Stopping %s' % self.name)
            result = self._stop()
            if not result:
                return False

            # We do not call the event handler (self.stop()) here because we are killing a forked
            # process, stopped() will be called when the python script exits
            return result

        def install(self, user):
            """Installs this service.

            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """

            # Make sure the service is not already installed
            if self.is_installed():
                print('* Already installed')
                return False

            # Attempt to install the service
            print('* Installing %s' % self.name)
            result = self._install(user)
            if not result:
                return False

            # Call event handler
            return self.installed()

        def uninstall(self):
            """Uninstalls this service.

            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """

            # Make sure the service is installed
            if not self.is_installed():
                print('* Not installed')
                return False

            # If the service is running, stop it first
            if self.is_running():
                if not self.stop():
                    return False

            # Attempt to uninstall the service
            print('* Uninstalling %s' % self.name)
            result = self._uninstall()
            if not result:
                return False

            # Call event handler
            self.uninstalled()
            return result

        def _start(self):
            """Starts the service (if it's installed and not running).

            :returns: True when successful and false otherwise.
            :rtype: Boolean
            """

            # Attempt to fork parent process (double fork)
            try:
                pid = os.fork()
                if pid > 0:
                        sys.exit(0)
            except OSError as error:
                print('* Unable to fork parent process (1): %s' % format(error))
                return False

            # Decouple from parent environment
            os.setsid()
            os.umask(0)

            # Do the second fork
            try:
                pid = os.fork()
                if pid > 0:
                        sys.exit(0)
            except OSError as error:
                print('* Unable to fork parent process (2): %s' % format(error))
                return False

            # Write the PID file
            pid = str(os.getpid())
            try:
                file = open(self.pid_file, 'w')
                file.write(str(pid) + '\n')
                file.close()
            except Exception as error:
                print('* Unable to write PID file to `%s`: %s' %(self.pid_file, format(error)))
                return False

            # Register cleanup function
            atexit.register(self._clean)
            atexit.register(self.service.stopped)

            # Redirect standard file descriptors to /dev/null
            sys.stdout.flush()
            sys.stdin.flush()
            standard_in = open(os.devnull, 'r')
            standard_out = open(os.devnull, 'a+')
            standard_error = open(os.devnull, 'a+')

            os.dup2(standard_in.fileno(), sys.stdin.fileno())
            os.dup2(standard_out.fileno(), sys.stdout.fileno())
            os.dup2(standard_error.fileno(), sys.stderr.fileno())
            return True

        def _stop(self):
            """Stops the service (if it's installed and running).

            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """
            self.stop_requested = True

            # Attempt to read the PID from the pid file
            file = open(self.pid_file, 'r')

            try:
                pid = int(file.read().strip())
            except:
                print("* Unable to read PID file")
                return False

            file.close()

            # Remove the PID file already to indicate that this is a stop
            # and not abnormal program termination, when the PID file is still
            # the service will handle this as abnormal program termination
            # and will restart the service if auto-start is enabled
            os.remove(self.pid_file)

            # Attempt to kill the process, continue to attempt to kill it until
            # the process has died with a maximum of 5 attempts
            attempts = 0
            try:

                while attempts < 5:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.2)
                    attempts += 1

            except OSError as error:
                error_message = str(error.args)

                # Check the error message, if it contains the text below,
                # the process is no longer running and we have thus killed the process
                if error_message.find("No such process") > 0:
                    return True
                else:
                    print("* Unable to kill the process %s" % error_message)
                    return False

            # We were unable to kill the process due to an unknown reason
            print("* Unable to kill the process due to an unknown reason")
            return False

        def _install(self, user):
            """Installs the service so it can be started and stopped (if it's not installed yet).

            :param user: The user the service should run as
            :type user: str
            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """

            # Make sure we're running with administrative privileges
            if os.getuid() != 0:
                raise RuntimeError('Insufficient privileges to install service, '
                                   'Please run with administrative rights.')

            # Simple bash script to write to /etc/init.d
            start_script = "#!/bin/bash"
            start_script += textwrap.dedent("""
                            PYTHON_PATH="%PYTHON_PATH%"
                            SERVICE_PATH="%SERVICE_PATH%"

                            case $1 in
                                start)
                                    $PYTHON_PATH $SERVICE_PATH start --user {0}
                                    ;;

                                stop)
                                    $PYTHON_PATH $SERVICE_PATH stop
                                    ;;

                                restart)
                                    $PYTHON_PATH $SERVICE_PATH stop
                                    $PYTHON_PATH $SERVICE_PATH start --user {0}
                                    ;;

                                *)
                                    echo 'Unknown action, try; start/stop/restart\\n'
                            esac""".format(user))

            # Determine the path of the current script and the path to the python interpreter
            service_path = os.path.join(os.getcwd(), sys.argv[0])
            python_path = sys.executable

            # Replace the python path and the path to our service in the start script
            start_script = start_script.replace('%PYTHON_PATH%', python_path)
            start_script = start_script.replace('%SERVICE_PATH%', service_path)

            # Write the control script to file (/etc/init.d)
            file = open(self.control_script, 'w')
            file.write(start_script)
            file.close()

            # Make the file executable (chmod +x)
            stat = os.stat(self.control_script)
            os.chmod(self.control_script, stat.st_mode | 0o0111)
            return True

        def _uninstall(self):
            """Uninstalls the service so it can no longer be used (if it's installed).

            :returns: True when successful and False otherwise.
            :rtype: Boolean
            """

            # Make sure we're running with administrative privileges
            if os.getuid() != 0:
                raise RuntimeError('Insufficient privileges to install service, '
                                   'Please run with administrative rights.')

            # Remove the control script from /etc/init.d
            try:
                os.remove(self.control_script)
            except Exception as error:
                print("* Unable to uninstall, failed to remove control script: %s" % str(error))
                return False

            return True

        def is_installed(self):
            """Determines whether this service is installed on this system.

            :returns: True when this service is installed and False otherwise.
            :rtype: Boolean
            """

            return os.path.exists(self.control_script)

        def is_running(self):
            """Determines whether this service is running on this system.

            :returns: True when this service is running False otherwise.
            :rtype: Boolean
            """

            return os.path.exists(self.pid_file)

        def _clean(self):
            """This is the cleanup function we register for the forked process.

            This function is called when the process ends. This way we can clean
            up stuff etc.

            By checking whether the PID file still exists, we can detect whether
            this is a normal stop, or whether we're dealing with abnormal program
            termination.

            Note: This does not prevent SIGKILL, if SIGKILL is signalled, we're dead
            for real. The only way we can back up then is the cron job
            """

            # If the PID file still exists, we're dealing with abnormal program
            # termination and we'll restart ourselves if auto-start is enabled
            if os.path.exists(self.pid_file):
                service_path = os.path.join(os.getcwd(), sys.argv[0])
                os.remove(self.pid_file)
                time.sleep(1)
                os.system(sys.executable + ' ' + service_path + ' --start')

            # Normal program termination (aka service stopped)
            return

        def installed(self):
            """If overridden, this function will be called after service
            is installed
            """
            pass
        
        def uninstalled(self):
            """If overridden, this function will be called after service
            is uninstalled
            """
            pass 

        def stopped(self):
            """If overridden, this function will be called after service
            is stopped
            """
            pass 

    return LinuxService()
