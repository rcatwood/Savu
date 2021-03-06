# Copyright 2015 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Created on 21 May 2015

@author: ssg37927
'''

import os

from savu.data.plugin_list import PluginList
from savu.plugins import utils as pu
import pkgutil
import savu
import readline
import re

RE_SPACE = re.compile('.*\s+$', re.M)
histfile = os.path.join(os.path.expanduser("~"), ".savuhist")
try:
    readline.read_history_file(histfile)
    readline.set_history_length(1000)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)


class Content(object):

    def __init__(self, filename):
        self.plugin_list = PluginList()
        self.filename = filename
        if os.path.exists(filename):
            print "Opening file %s" % (filename)
            self.plugin_list._populate_plugin_list(filename, activePass=True)

    def display(self, **kwargs):
        print '\n', self.plugin_list._get_string(**kwargs), '\n'

    def save(self, filename):
        if filename == "":
            filename = self.filename
        else:
            self.filename = filename
        print "Saving file %s" % (filename)
        self.plugin_list._save_plugin_list(filename)

    def value(self, arg):
        value = ([''.join(arg.split()[1:])][0]).split()[0]
        tuning = True if value.count(';') else False
        if not tuning:
            try:
                exec("value = " + value)
            except (NameError, SyntaxError):
                exec("value = " + "'" + value + "'")

        return value

    def add(self, name, pos):
        plugin = pu.plugins[name]()
        plugin._populate_default_parameters()
        self.insert(plugin, pos)
        self.display()

    def modify(self, element, subelement, value):
        data_elements = self.plugin_list.plugin_list[element-1]['data']
        try:
            position = int(subelement) - 1
            data_elements[data_elements.keys()[position]] = value
        except:
            if subelement in data_elements.keys():
                data_elements[subelement] = value
            else:
                print("Sorry, element %i does not have a %s parameter" %
                      (element, subelement))

    def convert_to_ascii(self, value):
        ascii_list = []
        for v in value:
            ascii_list.append(v.encode('ascii', 'ignore'))
        return ascii_list

    def on_and_off(self, element, index):
        if index < 2:
            print "switching plugin", element, "ON"
            self.plugin_list.plugin_list[element-1]['active'] = True
        else:
            print "switching plugin", element, "OFF"
            self.plugin_list.plugin_list[element-1]['active'] = False

    def insert(self, plugin, pos):
        process = {}
        process['name'] = plugin.name
        process['id'] = "savu.plugins." + plugin.__module__
        process['data'] = plugin.parameters
        process['active'] = True
        self.plugin_list.plugin_list.insert(pos, process)

    def get(self, pos):
        return self.plugin_list.plugin_list[pos]

    def remove(self, pos):
        self.plugin_list.plugin_list.pop(pos)

    def size(self):
        return len(self.plugin_list.plugin_list)


def _help(content, arg):
    """Display the help information"""
    for key in commands.keys():
        print "%4s : %s" % (key, commands[key].__doc__)
    return content


def _open(content, arg):
    """Opens or creates a new configuration file with the given filename"""
    ct = Content(arg)
    ct.display()
    return ct


def _disp(content, arg):
    """Displays the process in the current list.
       Optional arguments:
            i(int): Display the ith item in the list.
            i(int) j(int): Display list items i to j.
            names: Display process names only."""
    idx = {'start': 0, 'stop': -1}
    if arg:
        split_arg = arg.split(' ')
        len_args = len(split_arg)
        if len_args > 0:
            if split_arg[0] == 'names':
                idx['params'] = False
            else:
                try:
                    idx['start'] = int(split_arg[0]) - 1
                    idx['stop'] = \
                        idx['start']+1 if len_args == 1 else int(split_arg[1])
                except ValueError:
                    print("The arguments %s are unknown", arg)
    content.display(**idx)
    return content


def _list(content, arg):
    """List the plugins which have been registered for use.
       Optional arguments:
            type(str): Display 'type' plugins. Where type can be 'loaders',
            'corrections', 'filters', 'reconstructions' or 'savers'.
            type(str) names: Display type selection with process names only.
    """
    if arg:
        arg = arg.split(' ')
        if len(arg) == 2:
            if arg[1] != 'names':
                print("The arguments %s are unknown", arg)
                return content

    print "-----------------------------------------"
    for key, value in pu.plugins_path.iteritems():
        if not arg:
            print key
        elif value.split('.')[0] == arg[0]:
            print key
            if len(arg) < 2:
                plugin = pu.plugins[key]()
                plugin._populate_default_parameters()
                for p_key in plugin.parameters.keys():
                    print("    %20s : %s" % (p_key, plugin.parameters[p_key]))
    print "-----------------------------------------"
    return content


def _params(content, arg):
    """Displays the parameters of the specified plugin.
    """
    try:
        plugin = pu.plugins[arg]()
        plugin._populate_default_parameters()
        print "-----------------------------------------"
        print arg
        for p_key in plugin.parameters.keys():
            print("    %20s : %s" % (p_key, plugin.parameters[p_key]))
        print "-----------------------------------------"
        return content
    except:
        print("Sorry I can't process the argument '%s'" % (arg))
    return content


def _save(content, arg):
    """Save the current list to disk with the filename given"""
    content.save(arg)
    return content


def _mod(content, arg):
    """Modifies the target value e.g. 'mod 1.value 27' and turns the plugins on
    and off e.g 'mod 1.on' or 'mod 1.off'
    """
    on_off_list = ['ON', 'on', 'OFF', 'off']
    try:
        element,  subelement = arg.split()[0].split('.')
        if subelement in on_off_list:
            content.on_and_off(int(element), on_off_list.index(subelement))
        else:
            value = content.value(arg)
            content.modify(int(element), subelement, value)

        content.display()
    except:
        print("Sorry I can't process the argument '%s'" % (arg))
    return content


def _add(content, arg):
    """Adds the named plugin before the specified location 'MedianFilter 2'"""
    try:
        args = arg.split()
        name = args[0]
        pos = None
        if len(args) == 2:
            pos = args[1]
        else:
            pos = content.size()+1
        if name in pu.plugins.keys():
            content.add(name, int(pos)-1)
        else:
            print("Sorry the plugin %s is not in my list, pick one from list" %
                  (name))
    except:
        print("Sorry I can't process the argument '%s'" % (arg))
    return content


def _ref(content, arg):
    """Refreshes the plugin, replacing it with itself (updating any changes).
       Optional arguments:
            -r: Keep parameter values (if the parameter still exists).
                Without this flag the parameters revert to default values.
    """

    if not arg:
        print "ref requires the process number or * as argument"
        print "e.g. 'ref 1' refreshes process 1"
        print "e.g. 'ref *' refreshes ALL processes"
        return content

    kwarg = None
    if len(arg.split()) > 1:
        arg, kwarg = arg.split()

    if arg is '*':
        positions = range(len(content.plugin_list.plugin_list))
    else:
        positions = [int(arg) - 1]

    for pos in positions:
        if pos < 0 or pos >= len(content.plugin_list.plugin_list):
            print("Sorry %s is out of range" % (arg))
            return content
        name = content.plugin_list.plugin_list[pos]['name']
        old_entry = content.get(pos)
        content.remove(pos)

        if kwarg:
            plugin = pu.plugins[name]()
            plugin._populate_default_parameters()
            content.insert(plugin, pos)
            old_params = old_entry['data']
            new_params = plugin.parameters
            union_params = set(old_params).intersection(set(new_params))
            for param in union_params:
                content.modify(pos+1, param, old_params[param])
            content.display()
        else:
            content.add(name, pos)

    return content


def _rem(content, arg):
    """Remove the numbered item from the list"""
    pos = int(arg)-1
    if pos < 0 or pos >= len(content.plugin_list.plugin_list):
            print("Sorry %s is out of range" % (arg))
            return content
    content.remove(pos)
    content.display()
    return content

commands = {'open': _open,
            'help': _help,
            'disp': _disp,
            'list': _list,
            'save': _save,
            'mod': _mod,
            'add': _add,
            'rem': _rem,
            'ref': _ref,
            'params': _params}

list_commands = ['loaders',
                 'corrections',
                 'filters',
                 'reconstructions',
                 'savers']


class Completer(object):

    def _listdir(self, root):
        "List directory 'root' appending the path separator to subdirs."
        res = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                name += os.sep
            res.append(name)
        return res

    def _complete_path(self, path=None):
        "Perform completion of filesystem path."
        if not path:
            return self._listdir('.')
        dirname, rest = os.path.split(path)
        tmp = dirname if dirname else '.'
        res = [os.path.join(dirname, p)
               for p in self._listdir(tmp) if p.startswith(rest)]
        # more than one match, or single match which does not exist (typo)
        if len(res) > 1 or not os.path.exists(path):
            return res
        # resolved to a single directory, so return list of files below it
        if os.path.isdir(path):
            return [os.path.join(path, p) for p in self._listdir(path)]
        # exact file match terminates this completion
        return [path + ' ']

    def path_complete(self, args):
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])

    def complete_open(self, args):
        "Completions for the open commands."
        return self.path_complete(args)

    def complete_save(self, args):
        "Completions for the save commands."
        return self.path_complete(args)

    def complete_list(self, args):
        if not args[0]:
            return list_commands
        return [x for x in list_commands if x.startswith(args[0])]

    def complete_params(self, args):
        if not args[0]:
            return pu.plugins.keys()
        return [x for x in pu.plugins.keys() if x.startswith(args[0])]

    def complete(self, text, state):
        "Generic readline completion entry point."
        read_buffer = readline.get_line_buffer()
        line = readline.get_line_buffer().split()
        # show all commands
        if not line:
            return [c + ' ' for c in commands.keys()][state]
        # account for last argument ending in a space
        if RE_SPACE.match(read_buffer):
            line.append('')
        # resolve command to the implementation function
        cmd = line[0].strip()
        if cmd in commands.keys():
            impl = getattr(self, 'complete_%s' % cmd)
            args = line[1:]
            if args:
                return (impl(args) + [None])[state]
            return [cmd + ' '][state]
        results = \
            [c + ' ' for c in commands.keys() if c.startswith(cmd)] + [None]
        return results[state]

def main():
    print "Starting Savu Config tool (please wait for prompt)"

    comp = Completer()
    # we want to treat '/' as part of a word, so override the delimiters
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(comp.complete)

    # load all the packages in the plugins directory to register classes
    plugins_path = savu.plugins.__path__
    for loader, module_name, is_pkg in pkgutil.walk_packages(plugins_path):
        try:
            module = loader.find_module(module_name).load_module(module_name)
        except:
            pass

    # set up things
    input_string = "startup"
    content = Content("")

    while True:
        input_string = raw_input(">>> ").strip()

        if len(input_string) == 0:
            command = 'help'
            arg = ""
        else:
            command = input_string.split()[0]
            arg = ' '.join(input_string.split()[1:])

        if 'exit' in command:
            break

        # try to run the command
        if command in commands.keys():
            content = commands[command](content, arg)
        else:
            print "I'm sorry, thats not a command I recognise, try help"

    print "Thanks for using the application"

if __name__ == '__main__':
    main()
