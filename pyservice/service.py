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

import sys
import platform
import pyservice

system = platform.system()

if "Linux" in system:
    from .linux import PyServiceLinux as PlatformService
elif "Windows" in system:
    from .windows import PyServiceWindows as PlatformService
else:
    raise RuntimeError("Unsupported platform: {}".format(system))

class PyService(PlatformService):
    """Interface for classes who wish to represent a service.

    By overriding virtual methods, the deriving class that perform
    actions when certain event occur, such as a starting or stopping of the
    service, or install and uninstalling it.

    By passing the program's command line arguments, PyService can take care
    of handling parameters such as `--start` and `--install`.

    """

    def __init__(self, name, description, auto_start):
        """Initializes a new instance of the PyService class.

        This will parse specified command line options and will handle the
        following command line parameters:

        * --install
        * --uninstall
        * --start
        * --stop
        * --run

        Based on the specified command line parameters, the associated action
        will be taken.

        If none of the command line parameters above is specified, it will default
        to `--run` which will run the program without being installed as a service.

        Args:
            name (str):
                The name of the service, this name is used when installing or looking
                for the service.
            description (str):
                Small sentence, describing this service.
            auto_start (bool):
                True when this service needs to be started automatically when the system
                starts or when the service crashes.

        """
        super(PyService, self).__init__(name, description, auto_start)

    def handle_cli(self, argv=None):
        argv = sys.argv[1:] if argv is None else argv
        
        parser = argparse.ArgumentParser(
            description="Service control script for {}.".format(self.name),
            suffix="Only one option is allowed at any time" 
        )
        
        parser.add_argument(
            "--install",
            action="store_true",
            help="Install {} as a service".format(self.name))
        parser.add_argument(
            "--uninstall", 
            action="store_true",
            help="uninstall {} as a service".format(self.name))
        parser.add_argument(
            "--start", 
            action="store_true",
            help="start {} service, if installed".format(self.name))
        parser.add_argument(
            "--stop", 
            action="store_true",
            help="stop {} service, if installed and running".format(self.name))
        parser.add_argument(
            "--run",
            action="store_true",
            help="run {} service without installing it first"
        )

        args = parser.parse_args(argv)
        
        if len(filter(lambda x: x, vars(args).values())) > 1:
            # More than one option specified
            raise RuntimeError("Only one option can be specified at a time.")
        
        if not any(vars(args).values()):
            # Nothing was provided, run without installing
            args.run = True
        
        def run_or_exit_with_1(func):
            if not func():
                sys.exit(1)
    
        if args.run:
            run_or_exit_with_1(self.started)
        elif args.install:
            run_or_exit_with_1(self.install)
        elif args.uninstall:
            run_or_exit_with_1(self.uninstall)
        elif args.start:
            run_or_exit_with_1(self.start)
        elif args.stop:
            run_or_exit_with_1(self.stop)

    def started(self):
        """Virtual, to be overridden by the derived class.

        Called when the service is starting, the derived class should
        start some kind of blocking loop now to prevent the service
        from stopping.
        """

        raise NotImplementedError('`started` not implemented in derived class')

    def stopped(self):
        """Virtual, to be overridden by the derived class.

        Called when the service is stopping, the derived class should attempt
        to stop the blocking loop it created/started when the service was
        starting.
        """

        raise NotImplementedError('`stopped` not implemented in derived class')

    def installed(self):
        """Virtual, to be overridden by the derived class.

        Called when the service is being installed, this gives the derived class
        the chance to prepare some stuff.
        """

        raise NotImplementedError('`installed` not implemented in derived class')

    def uninstalled(self):
        """Virtual, to be overridden by the derived class.

        Called when the service is being uninstalled, this gives the derived class
        the chance to reverse anything that was installed during the installation.
        """

        raise NotImplementedError('`uninstalled` not implemented in derived class')


    def start(self):
        """Starts this service.

        Handles this by requesting a start from the platform specific implementation.

        Returns:
            True when starting the service was a success and false when it failed.
        """

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
        self.started()
        return result

    def stop(self):
        """Stop this service.

        Handles this by requesting a stop from the platform specific implementation.

        Returns:
            True when stopping the service was a success and false when it failed.
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

    def install(self):
        """Installs this service.

        Handles this by requesting an installation from the platform specific implementation.

        Returns:
            True when installing the service was a success and false when it failed.
        """

        # Make sure the service is not already installed
        if self.is_installed():
            print('* Already installed')
            return False

        # Attempt to install the service
        print('* Installing %s' % self.name)
        result = self._install()
        if not result:
            return False

        # Call event handler
        return self.installed()

    def uninstall(self):
        """Uninstalls this service.

        Handles this by requesting an un-installation from the platform specific implementation.

        Returns:
            True when un-installing the service was a success and false when it failed.
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

