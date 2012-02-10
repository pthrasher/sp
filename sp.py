#!/usr/bin/env python
"""
sp.py - find out who's hoggin ur shit.

Created by Philip Thrasher on 2012-02-1.
TODO:
    - add exclusions - regex, etc

"""

import os
import sys
import re
import optparse

from decimal import Decimal

__version__ = '1.1.1'
__description__ = """sp is a simple command with only a few options. It will let you know where
your worst disk space offenders reside. It will either output to stdout,
or optionally, you can specify an out file as your last argument, and it
will write the results there."""


DEFAULT_EXCLUDES = (
    r"^\.git$",
    r"^\.svn$",
    r"^.DS_Store$"
)


class InvalidThresholdMultiplierError(Exception):
    def __init__(self, multiplier):
        self.multiplier = multiplier


class InvalidThresholdError(Exception):
    pass


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


class PathScanner(object):
    """
    Class that will scan a file system from a given starting point, finding all
    files larger than a threshold, and detailing their location so that you can
    see where your largest disk consumption is.
    """
    def __init__(self, working_dir=None, file_threshold="1k", folder_threshold="1m",
                    limit=25, max_depth=None, max_list_depth=None, follow_links=False, follow_mounts=False):
        if not working_dir:
            working_dir = os.getcwd()

        self.summary_tree = {}
        self.working_dir = working_dir
        self.limit = limit
        self.max_depth = max_depth
        self.max_list_depth = max_list_depth
        self.follow_links = follow_links
        self.follow_mounts = follow_mounts

        try:
            self.file_threshold = self._parse_filesize(file_threshold)
            self.folder_threshold = self._parse_filesize(folder_threshold)
        except InvalidThresholdMultiplierError, e:
            raise Usage("You specified an in invalid threshold multiplier. You said: '%s'. Your choices are 'k', 'm', or 'g'" % e.multiplier)
        except InvalidThresholdError, e:
            raise Usage("The threshold you gave is invalid.")

    def _parse_filesize(self, size_str):
        """
        Over complicated method that just allows input of threshold sizes in a
        couple different ways. This parses it, and converts it into bytes.
        """
        human_pattern = re.compile(r"^(?P<quantity>\d+)(?P<multiplier>[a-zA-Z]{1})$")
        long_pattern = re.compile(r"^(\d+)$")

        multipliers = {
            "k": 1024,
            "m": 1048576,
            "g": 1073741824
        }

        m = human_pattern.match(size_str)
        if m:
            q, m = m.groups()
            quantity = float(q)
            multiplier = multipliers.get(m.lower())
            if multiplier:
                self.multiplier_key = m.lower()
                self.multiplier = multiplier
                return quantity * multiplier
            else:
                raise InvalidThresholdMultiplierError(m)

        m = long_pattern.match(size_str)
        if m:
            self.multiplier = 1
            self.multiplier_key = ""
            try:
                return float(m.groups()[0])
            except ValueError:
                raise InvalidThresholdError

    def _filter_from_excludes(self, lst):
        tmp = []
        for item in lst:
            for exclude in DEFAULT_EXCLUDES:
                if re.match(exclude, item):
                    break
            else:
                tmp.append(item)
        return tmp

    def _stat_node(self, node_path):
        """

        """
        _dirs = []
        _files = []

        for item in self._filter_from_excludes(os.listdir(node_path)):
            name = item
            item = os.path.join(node_path, name)
            if os.path.ismount(item):
                if self.follow_mounts:
                    _stat = os.stat(item)
                    _item = {
                        'name': name,
                        'full_path': item,
                        'size': _stat.st_size
                    }
                    _dirs.append(_item)
            elif os.path.isdir(item) and os.path.islink(item):
                if self.follow_links:
                    _stat = os.stat(item)
                    _item = {
                        'name': name,
                        'full_path': item,
                        'size': _stat.st_size
                    }
                    _dirs.append(_item)
            elif os.path.isdir(item):
                _stat = os.stat(item)
                _item = {
                    'name': name,
                    'full_path': item,
                    'size': _stat.st_size
                }
                _dirs.append(_item)
            elif os.path.isfile(item) and not os.path.islink(item):
                _stat = os.stat(item)
                _item = {
                    'name': name,
                    'full_path': item,
                    'size': _stat.st_size
                }
                _files.append(_item)

        return {
            'full_path': node_path,
            'name': os.path.basename(node_path),
            'dirs': _dirs,
            'files': _files
        }

    def _get_human_value(self, bytes, places=2):
        """
        Convert bytes back into something more readable.
        """
        one_gig = 1073741824
        one_meg = 1048576
        one_k = 1024

        divisor = None
        label = "bytes"

        if bytes >= one_gig:
            label = "GB"
            divisor = one_gig
        elif bytes >= one_meg:
            label = "MB"
            divisor = one_meg
        elif bytes >= one_k:
            label = "KB"
            divisor = one_k
        if divisor:
            bytes = round(Decimal(str(float(bytes) / float(divisor))), places)
        return "%s %s" % (bytes, label)

    def _fill_node(self, full_path, node, dirs, files, depth=0):
        """
        Where the magic happens. This recursive method traverses the file
        system, and figures out file sizes, directory sizes in terms of files,
        etc.
        """
        if self.max_depth != None and depth > self.max_depth:
            return None

        dir_size = 0
        hv_widths = []

        _dirs = []
        _files = []

        for dir_obj in dirs:
            _dir_obj = self._stat_node(dir_obj['full_path'])
            dir_contents = self._fill_node(_dir_obj['full_path'], _dir_obj['name'],
                                            _dir_obj['dirs'], _dir_obj['files'], depth=depth + 1)
            if dir_contents:
                dir_contents['size'] += dir_obj['size']
                dir_size += dir_contents['size']

                if dir_contents['size'] >= self.folder_threshold:
                    if self.max_list_depth == None or \
                        (self.max_list_depth != None and depth <= self.max_list_depth):

                        dir_contents['human_size'] = self._get_human_value(dir_contents['size'])
                        hv_widths.append(dir_contents['max_width'])
                        hv_widths.append(len(dir_contents['human_size']))

                        _dirs.append(dir_contents)

        for f in files:
            dir_size += f['size']
            if f['size'] >= self.file_threshold:
                if self.max_list_depth == None or (self.max_list_depth != None and depth <= self.max_list_depth):
                    f['human_size'] = self._get_human_value(f['size'])
                    hv_widths.append(len(f['human_size']))

                    _files.append(f)

        human_size = self._get_human_value(dir_size)
        hv_widths.append(len(human_size))

        return {
            'full_path': full_path,
            'name': node,
            'dirs': _dirs,
            'files': _files,
            'size': dir_size,
            'human_size': human_size,
            'max_width': max(hv_widths)
        }

    def _print_data(self, data, max_width=0, depth=0):
        """
        Does just what it's name suggests. This just pretty prints the data
        in a readable way.
        """
        tmp = ""
        tmp += "[%s] %s\n" % (data['human_size'], data['full_path'])
        if len(data['dirs']):
            tmp += "Directories:\n"
            _dirs = sorted(data['dirs'], key=lambda d: d['size'], reverse=True)
            for d in _dirs:
                tmp += "\t[%s] %s\n" % (d['human_size'].rjust(max_width), d['name'])
        else:
            tmp += " - No Directories -\n"

        if len(data['files']):
            tmp += "Files:\n"
            _files = sorted(data['files'], key=lambda f: f['size'], reverse=True)[:self.limit]
            for f in _files:
                tmp += "\t[%s] %s\n" % (f['human_size'].rjust(max_width), f['name'])
        else:
            tmp += " - No Files -\n"
        tmp += "\n\n"

        if self.max_list_depth == None or (self.max_list_depth != None and depth < self.max_list_depth):
            for d in sorted(data['dirs'], key=lambda d: d['size'], reverse=True):
                tmp += self._print_data(d, max_width=max_width, depth=depth + 1)
        return tmp

    def scan(self):
        """
        Kicks off the recursion and sets the results on the class.
        """
        do = self._stat_node(self.working_dir)
        self.all_data = self._fill_node(do['full_path'], do['name'], do['dirs'], do['files'])

    def results(self):
        return self._print_data(self.all_data, max_width=self.all_data['max_width'])


def sp_main(argv=None):
    """
    CLI entry point
    """
    if not argv:
        argv = sys.argv
    parser = optparse.OptionParser(version=__version__, usage="%prog [options] [out file]", prog='sp', description=__description__)
    parser.add_option('-d', '--dir', action="store", default=None, dest='working_dir', help="Root directory to perform the search from. Defaults to current working directory.")
    parser.add_option('-T', '--dir-threshold', action="store", default="500k", dest='dir_threshold', help="Minimum directory size to be listed.(ex. 1m, 13k, 2k, 5g, 12332828) Default is 500k.")
    parser.add_option('-t', '--file-threshold', action="store", default="1k", dest='file_threshold', help="Minimum file size to be listed.(ex. 1m, 13k, 2k, 5g, 12332828) Default is 1k")
    parser.add_option('-r', '--max-files-shown', action="store", default=-1, dest='max_file_results', type='int', help="The maximum number of files to list per directory. Files are sorted largest to smallest. -1 = all")
    parser.add_option('-m', '--max-traverse-depth', action="store", default=None, dest='max_depth', type='int', help="The maximum depth to traverse.")
    parser.add_option('-x', '--max-list-depth', action="store", default=None, dest='max_list_depth', type='int', help="The maximum to list -- can still traverse deeper.")
    parser.add_option('-M', '--follow-mount-points', action="store_true", dest='follow_mounts', help="Whether or not to drill down into mount points.")
    parser.add_option('-l', '--follow-links', action="store_true", dest='follow_links', help="Whether or not to drill down into sym links.")

    options, values = parser.parse_args(argv[1:])
    try:
        pe = PathScanner(options.working_dir, options.file_threshold, options.dir_threshold, options.max_file_results, options.max_depth, options.max_list_depth)
        pe.scan()
        if len(values):
            # They have specified a file name to write to.
            f = open(values[0], "w")
            f.write(pe.results())
            f.close()
        else:
            print pe.results()
        sys.exit(0)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(0)
    except IOError, e:
        if 'Broken pipe' in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    sp_main()
