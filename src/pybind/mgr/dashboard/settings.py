# -*- coding: utf-8 -*-
from __future__ import absolute_import

import errno
from ast import literal_eval
from typing import Any, List

from mgr_module import CLICheckNonemptyFileInput, Option

from . import mgr


class OptionCommandTool:  # Todo refactoring name

    def __init__(self, options: List[Option]):
        self._OPTIONS_COMMAND_MAP = self._options_command_map(options)

    def _options_command_map(self, options: List[Option]):
        cmd_map = {}
        for o in options:
            if o['name'].startswith('_'):
                continue
            key_get = 'dashboard get-{}'.format(o['name'].lower().replace('_', '-'))
            key_set = 'dashboard set-{}'.format(o['name'].lower().replace('_', '-'))
            key_reset = 'dashboard reset-{}'.format(o['name'].lower().replace('_', '-'))
            cmd_map[key_get] = {'name': o['name'], 'type': None, 'default': o['default']}
            cmd_map[key_set] = {'name': o['name'], 'type': o['type']}
            cmd_map[key_reset] = {'name': o['name'], 'type': None, 'default': o['default']}
        return cmd_map

    def options_command_list(self):
        """
        This function generates a list of ``get`` and ``set`` commands
        for each declared configuration option in class ``Options``.
        """
        def py2ceph(pytype):
            if pytype == str:
                return 'CephString'
            elif pytype == int:
                return 'CephInt'
            return 'CephString'

        cmd_list = []
        for cmd, opt in self._OPTIONS_COMMAND_MAP.items():
            if cmd.startswith('dashboard get'):
                cmd_list.append({
                    'cmd': '{}'.format(cmd),
                    'desc': 'Get the {} option value'.format(opt['name']),
                    'perm': 'r'
                })
            elif cmd.startswith('dashboard set'):
                cmd_entry = {
                    'cmd': '{} name=value,type={}'
                           .format(cmd, py2ceph(opt['type'])),
                    'desc': 'Set the {} option value'.format(opt['name']),
                    'perm': 'w'
                }
                if self.handles_secret(cmd):
                    cmd_entry['cmd'] = cmd
                    cmd_entry['desc'] = '{} read from -i <file>'.format(cmd_entry['desc'])
                cmd_list.append(cmd_entry)
            elif cmd.startswith('dashboard reset'):
                desc = 'Reset the {} option to its default value'.format(
                    opt['name'])
                cmd_list.append({
                    'cmd': '{}'.format(cmd),
                    'desc': desc,
                    'perm': 'w'
                })

        return cmd_list

    def handle_option_command(self, cmd, inbuf):
        if cmd['prefix'] not in self._OPTIONS_COMMAND_MAP:
            return -errno.ENOSYS, '', "Command not found '{}'".format(cmd['prefix'])

        opt = self._OPTIONS_COMMAND_MAP[cmd['prefix']]

        if cmd['prefix'].startswith('dashboard reset'):
            mgr.set_module_option(opt['name'], opt['default'])
            return 0, 'Option {} reset to default value "{}"'.format(
                opt['name'], mgr.get_module_option(opt['name'], opt['default'])), ''
        elif cmd['prefix'].startswith('dashboard get'):
            return 0, str(mgr.get_module_option(opt['name'], opt['default'])), ''
        elif cmd['prefix'].startswith('dashboard set'):
            if self.handles_secret(cmd['prefix']):
                value, stdout, stderr = self.get_secret(inbuf=inbuf)
                if stderr:
                    return value, stdout, stderr
            else:
                value = cmd['value']
            r = mgr.set_module_option(opt['name'], str(value))
            return (0, 'Option {} updated'.format(opt['name']), '') if r is None else r

    def handles_secret(self, cmd: str) -> bool:
        return bool([cmd for secret_word in ['password', 'key'] if (secret_word in cmd)])

    @CLICheckNonemptyFileInput(desc='password/secret')
    def get_secret(inbuf=None):
        return inbuf, None, None

    def types_as_str(self):
        return ','.join([x.__name__ for x in self.types])

    def cast(self, value):
        for type_index, setting_type in enumerate(self.types):
            try:
                if setting_type.__name__ == 'bool' and str(value).lower() == 'false':
                    return False
                elif setting_type.__name__ == 'dict':
                    return literal_eval(value)
                return setting_type(value)
            except (SyntaxError, TypeError, ValueError) as error:
                if type_index == len(self.types) - 1:
                    raise error
