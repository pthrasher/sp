#!/usr/bin/env python
"""
sp.py - find out who's hoggin ur shit.

Created by Philip Thrasher on 2012-02-1.
"""

import os
import sys
import re
import optparse

from decimal import Decimal

__version__ = '1.0.0'


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
    def __init__(self, working_dir=None, file_threshold="1k", folder_threshold="1m", limit=25):
        if not working_dir:
            working_dir = os.getcwd()
        self.summary_tree = {}
        self.working_dir = working_dir
        self.limit = limit
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

    def _stat_files(self, root, files):
        """
        Get the info for each file in a list. We only return the size in bytes,
        and the file name -- of each file.
        """
        stat_objs = []
        for f in files:
            try:
                stat_objs.append([f, os.lstat(os.path.join(root, f))])
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                # one of the few times we don't care about the error.
                # we'll just skip the file.
                pass

        return [{'name':f, 'size': s.st_size} for f, s in stat_objs]

    def _stat_node(self, node):
        """
        os.walk was written in an unusable way. I only want to know about the
        current directory in question.
        """
        return os.walk(node).next()

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

    def _fill_node(self, full_path, node, dirs, files):
        """
        Where the magic happens. This recursive method traverses the file
        system, and figures out file sizes, directory sizes in terms of files,
        etc.
        """
        dir_size = 0
        tmp = {'full_path': full_path, 'name': node, 'dirs': [], 'files': []}
        for dir_name in dirs:
            _full_path, _dirs, _files = self._stat_node(os.path.join(full_path, dir_name))
            _name = os.path.basename(_full_path)
            contents = self._fill_node(_full_path, _name, _dirs, _files)
            if contents:
                dir_size += contents['size']
                if contents['size'] >= self.folder_threshold:
                    tmp['dirs'].append(contents)

        for f in self._stat_files(full_path, files):
            dir_size += f['size']
            if f['size'] >= self.file_threshold:
                tmp['files'].append({'name': f['name'], 'size': f['size']})

        tmp['size'] = dir_size
        return tmp

    def _print_data(self, data):
        """
        Does just what it's name suggests. This just pretty prints the data
        in a readable way.
        """
        print "[%s] %s" % (self._get_human_value(data['size']), data['full_path'])
        if len(data['dirs']):
            print "Directories:"
            for d in sorted(data['dirs'], key=lambda d: d['size'], reverse=True):
                print "\t[%s] %s" % (self._get_human_value(d['size']), d['name'])
        else:
            print " - No Directories -"

        if len(data['files']):
            print "Files:"
            for f in sorted(data['files'], key=lambda f: f['size'], reverse=True)[:self.limit]:
                print "\t[%s] %s" % (self._get_human_value(f['size']), f['name'])
        else:
            print " - No Files -"
        print "\n"
        for d in sorted(data['dirs'], key=lambda d: d['size'], reverse=True):
            self._print_data(d)

    def scan(self):
        """
        Kicks off the recursion and prints the results.
        """
        _full_path, _dirs, _files = self._stat_node(self.working_dir)
        _name = os.path.basename(_full_path)
        all_data = self._fill_node(_full_path, _name, _dirs, _files)
        self._print_data(all_data)


def sp_main(argv=None):
    """
    CLI entry point
    """
    if not argv:
        argv = sys.argv
    parser = optparse.OptionParser()
    parser.add_option('-d', action="store", default=None, dest='working_dir', help="Root directory to perform the search from.")
    parser.add_option('-T', action="store", default="1m", dest='dir_threshold', help="Minimum directory size to be listed.(ex. 1m, 13k, 2k, 5g, 12332828)")
    parser.add_option('-t', action="store", default="1k", dest='file_threshold', help="Minimum file size to be listed.(ex. 1m, 13k, 2k, 5g, 12332828)")
    parser.add_option('-l', action="store", default=25, dest='max_file_results', type='int', help="The maximum number of files to list per directory. Files are sorted largest to smallest. -1 = all")
    options, values = parser.parse_args(argv)
    try:
        pe = PathScanner(options.working_dir, options.file_threshold, options.dir_threshold, options.max_file_results)
        pe.scan()
        sys.exit(0)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(0)
    except IOError as e:
        if 'Broken pipe' in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    sp_main()
