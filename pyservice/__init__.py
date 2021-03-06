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
"""This is the __init__.py file for pyservice. This will import "service"
and "handle_cli" for the current platform, otherwise a RuntimeError will
be raised if the current platform is unsupported.
"""
import platform

system = platform.system()

if "Linux" in system:
    from .linux import service, handle_cli
elif "Windows" in system:
    from .windows import service, handle_cli
else:
    raise RuntimeError("Unsupported platform: {}".format(system))

