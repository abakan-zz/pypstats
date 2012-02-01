#!/usr/bin/python
# pypstats: Retrieve Python package download statistics from PyPI
# 
# Copyright (C) 2011-2012 Ahmet Bakan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
"""Retrieve Python package download statistics from PyPI.

Information: 

  * http://pypi.python.org/stats/months/
  * http://www.python.org/dev/peps/pep-0381/

"""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2011-2012 Ahmet Bakan'

__version__ = '1.1'

import sys
import csv
import bz2
import cPickle
import logging
import os.path
import urllib2
import datetime
from HTMLParser import HTMLParser
from collections import defaultdict

LOGGER = logging.getLogger('.pypstats')
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

class PyPIStatsFile(object):
    
    def __init__(self, url, month, modified=None, size=None):
        
        self.url = url
        self.month = month
        self.modified = modified
        self.size = size
    
    def read(self):
        url = urllib2.urlopen(self.url)
        stats = bz2.decompress(url.read())
        url.close()
        return stats
                

class PyPIStatsURLParser(HTMLParser):

    def __init__(self, url):
        
        HTMLParser.__init__(self)
        self.url = url
        self.files = []
        self._temp = None
    
    def handle_starttag(self, tag, attrs):
        
        if tag == 'a':
            self._temp = None

    def handle_endtag(self, tag):
        
        pass

    def handle_data(self, data):
        
        data = data.strip()
        if data:
            if self._temp:
                items = data.split()
                if len(items) == 3:
                    _ = ' '.join(items[:2])
                    date = datetime.datetime.strptime(_, '%d-%b-%Y %H:%M')
                    self.files.append(
                        PyPIStatsFile(self.url + self._temp,
                        os.path.splitext(self._temp)[0],
                        date, int(items[2]))
                    )               
            elif data.startswith('2') and data.endswith('.bz2'):
                self._temp = data
        
def fetchURLs(url='http://pypi.python.org/stats/months/'):

    LOGGER.info("Fetching content from '{0:s}'.".format(url))
    import urllib2
    stats_months = urllib2.urlopen(url)
    feed = stats_months.read()
    stats_months.close()
    
    LOGGER.info("Parsing monthly statistics file details.")
    parser = PyPIStatsURLParser(url)
    parser.feed(feed)
    return parser


def package_filename(package):
    
    return package + '_stats.pkl'

def load_stats(filename):
    """Load package stats dictionary from filename.  If file is not found, 
    return a default dictionary."""

    # Gather download statistics
    if filename and os.path.isfile(filename):
        LOGGER.info("Loading statistics from '{0:s}'.".format(filename))
        pkl = open(filename)
        stats = cPickle.load(pkl)
        pkl.close()
        return stats
    else:
        from collections import defaultdict
        return defaultdict(int)

def save_stats(filename, stats):
    """Pickle package stats dictionary."""

    pkl = open(filename, 'wb')
    cPickle.dump(stats, pkl)
    pkl.close()
    return filename

def get_version(package, filename):
    """Get package version from filename."""
    
    ndot = 0
    version = ''
    i = len(package) + 1
    while i < len(filename):
        char = filename[i]
        if char == '.':
            if not filename[i+1].isdigit():
                break
        version += char
        i += 1
    return version

def update_stats(args):
    """Update package stats from http://pypi.python.org/stats/months/."""
    
    package, filename = args.pkg, args.s
    if filename is None:
        filename = package_filename(package)
    stats = load_stats(filename)
    p = fetchURLs()
    noupdates = True
    for f in p.files:
        if f.month in stats and stats[f.month]['modified'] == f.modified: 
            continue
        noupdates = False
        LOGGER.info("Updating statistics for " + f.month + '.')
        stats[f.month] = defaultdict(int)
        month = stats[f.month]
        month['modified'] = f.modified
        for line in f.read().split('\n'):
            if not line.startswith(package):
                continue
            items = line.split(',')
            version = get_version(package, items[1])
            count = int(items[-1])
            month[version] += count
    if noupdates:
        LOGGER.info("Nothing to update.")
    else:
        save_stats(filename, stats)
        LOGGER.info("Package statistics are updated ({0:s}).".format(filename))
        return filename
    
def release_stats(args):
    """Output download stats by release."""
    
    stats, outname, delimiter = args.pkl, args.o, args.d
    
    stats = load_stats(stats)
    releases = defaultdict(int)
    for month in stats.itervalues(): 
        for key, value in month.iteritems():
            if key == 'modified':
                continue
            releases[key] += value
    releases = releases.items()
    releases.sort()

    if outname:
        ostream = open(outname, 'wb')
    else:
        ostream = sys.stdout

    out = csv.writer(ostream, delimiter=delimiter)
    total = 0
    out.writerow(['Release', 'Downloads'])
    for rel in releases:
        out.writerow(rel)
        total += rel[1]
    out.writerow(['Total', total])


    if outname:
        LOGGER.info("Release statistics are written in '{0:s}'."
                    .format(outname))
        

def total_downloads(args):
    """Output number of total downloads."""

    stats = load_stats(args.pkl)
    total = 0
    for month in stats.itervalues(): 
        for key, value in month.iteritems():
            if key == 'modified':
                continue
            total += value
    sys.stdout.write(str(total) + '\n')

def monthly_stats(args):
    """Output download stats by month."""

    stats = load_stats(args.pkl)
    months = []
    for month, stats in stats.iteritems(): 
        counts = 0
        for key, value in stats.iteritems():
            if key == 'modified':
                continue
            counts += value
        if counts > 0:
            months.append((month, counts))
    months.sort()
    if not months:
        LOGGER.warning("Empty or no stats file: '{0:s}'".format(args.pkl))
        return

    if args.o:
        ostream = open(args.o, 'wb')
    else:
        ostream = sys.stdout
    total = 0
    out = csv.writer(ostream, delimiter=args.d)
    out.writerow(['Month', 'Downloads'])
    for month in months:
        out.writerow(month)
        total += month[1]
    out.writerow(['Total', total])
    if args.o:
        ostream.close()
        LOGGER.info("Monthly statistics are written in '{0:s}'."
                    .format(args.o))

    if args.p:
        labels = []
        counts = []
        for m, c in months:
            labels.append(m)
            counts.append(c)
        import numpy as np
        import matplotlib.pyplot as plt
        plt.figure(figsize=(7.5,4))
        plt.bar(range(len(counts)), counts, color='black')
        plt.xticks(np.arange(len(labels))[::args.mlabelstep]+0.5, 
                   labels[::args.mlabelstep], rotation=15, fontsize=10)
        plt.yticks(plt.yticks()[0], fontsize=10)
        plt.grid()
        plt.title('Monthly downloads (total={0:d})'
                  .format(sum(counts)), fontsize=12)
        plt.ylabel('Number of downloads', fontsize=11)
        plt.savefig(args.p, dpi=args.dpi)
        LOGGER.info("Monthly downloads plot is saved as '{0:s}'."
                    .format(args.p))


def latest_release(package):
    """Retrieve latest released data."""
        
    url = 'http://pypi.python.org/pypi'
    LOGGER.info("Connecting to '{0:s}'.".format(url))
    import xmlrpclib
    pypi = xmlrpclib.Server(url)
    
    show_hidden = False
    releases = pypi.package_releases(package, show_hidden)
    
    for release in releases:
        urls = pypi.release_urls(package, release)
        return urls

def latest_release_csv(args):
    """Output latest released data."""
    
    package, outname, delimiter, rst = args.pkg, args.o, args.d, args.rst
    
    urls = latest_release(package)
    if not urls:
        LOGGER.warning('Latest release information for {0:s} could not be '
                       'retrieved.'.format(package))
        return

    if outname:
        ostream = open(outname, 'wb')
    else:
        ostream = sys.stdout
    out = csv.writer(ostream, delimiter=delimiter)
    
    # Write a CSV file with info on and links to the latest downloads 
    packagetype_map = {'sdist': 'Source', 
                       'bdist_wininst': 'MS Windows installer'}
    python_version_map = {'source': ''} 
    if rst:
        out.writerow(['File', 'Type', 'Py Version', 'Size', 'Downloads'])
    else:
        out.writerow(['File', 'URL', 'md5', 'Type', 
                      'Py Version', 'Size', 'Downloads'])
    for url in urls:
        url['packagetype'] = packagetype_map.get(url['packagetype'], 
                                                 url['packagetype'])
        url['python_version'] = python_version_map.get(url['python_version'], 
                                                       url['python_version'])
        if rst:
            out.writerow(
                ['`{0[filename]:s} <{0[url]:s}>`_ '
                 '(`md5 <http://pypi.python.org/pypi?:action=show_md5&'
                 'digest={0[md5_digest]:s}>`_)'.format(url),
                 '{0[packagetype]:s}'.format(url),
                 '{0[python_version]:s}'.format(url),
                 '{0:d}KB'.format(int(url['size']/1024)),
                 '{0[downloads]:d}'.format(url)]            
            )
        else:
            out.writerow(
                ['{0[filename]:s}'.format(url),
                 '{0[url]:s}'.format(url),
                 '{0[md5_digest]:s}'.format(url),
                 '{0[packagetype]:s}'.format(url),
                 '{0[python_version]:s}'.format(url),
                 '{0:d}KB'.format(int(url['size']/1024)),
                 '{0[downloads]:d}'.format(url)]            
            )
    if outname:
        ostream.close()
        LOGGER.info("Latest release details are written to '{0:s}'."
                    .format(outname))
    return outname


import argparse
parser = argparse.ArgumentParser(
    description="Fetch package download statistics from Python Package "
                "Index (PyPI). Package needs to be distributed via PyPI.",
    epilog="See 'pypstats <command> -h' for more information on a specific "
           "command."
    )#usage='%(prog)s [--help] <command> [options] pkg')
    
subparsers = parser.add_subparsers(
    title='subcommands')
        
# UPDATE
        
subparser = subparsers.add_parser('update', 
    help='retrieve or update download statistics')

subparser.add_argument('-q', '--quiet', help="suppress stderr log messages",
    action='store_true', default=False)
    
subparser.add_argument('-s', default=None, metavar='FILENAME',
    help="filename for storing package statistics (default: 'pkg_stats.pkl')")

subparser.add_argument('pkg', help='Python package name')

subparser.set_defaults(func=update_stats)

# LATEST

subparser = subparsers.add_parser('latest', 
    help='retrieve and output latest release information')

subparser.add_argument('-q', '--quiet', help="suppress stderr log messages",
    action='store_true', default=False)

subparser.add_argument('-o', default=None, metavar='FILENAME',
    help="output CSV filename, if not provided print to stdout")
             
subparser.add_argument('-d', default='\t', metavar='DELIMITER',
        help="CSV file column delimiter (default: '%(default)s')")

subparser.add_argument('--rst', default=False, action='store_true',
        help="write reStructured text")

subparser.add_argument('pkg', help='Python package name')

subparser.set_defaults(func=latest_release_csv)

# MONTHLY

subparser = subparsers.add_parser('monthly', 
    help='write/plot monthly download statistics')

subparser.add_argument('-q', '--quiet', help="suppress stderr log messages",
    action='store_true', default=False)

subparser.add_argument('-o', metavar='FILENAME', type=str,
    help="output CSV filename, if not provided print to stdout")
             
subparser.add_argument('-d', default='\t', metavar='DELIMITER',
        help="output column delimiter (default: '%(default)s')")

subparser.add_argument('-p', metavar='FILENAME', type=str,
    help="figure filename, requires Matplotlib")
             
subparser.add_argument('--dpi', metavar='INT', type=int, default=72, 
    help="figure resolution (default: %(default)s)")

subparser.add_argument('--mlabelstep', metavar='INT', type=int, default=2, 
    help="figure month label step (default: %(default)s)")

subparser.add_argument('pkl', help='package statistics filename')

subparser.set_defaults(func=monthly_stats)

# RELEASE

subparser = subparsers.add_parser('release', 
    help='output download statistics by release')

subparser.add_argument('-q', '--quiet', help="suppress stderr log messages",
    action='store_true', default=False)

subparser.add_argument('-o', metavar='FILENAME', type=str, 
    help="output CSV filename (default: '%(default)s')")
             
subparser.add_argument('-d', default='\t', metavar='DELIMITER',
        help="output column delimiter (default: '%(default)s')")

subparser.add_argument('pkl', help='package statistics filename')

subparser.set_defaults(func=release_stats)

# TOTAL

subparser = subparsers.add_parser('total',
    help='output total number of downloads')

subparser.add_argument('-q', '--quiet', help="suppress stderr log messages",
    action='store_true', default=False)

subparser.set_defaults(func=total_downloads)

subparser.add_argument('pkl', help='package statistics filename')

def main():
    if len(sys.argv) == 1:    
        parser.print_help()
    else:
        args = parser.parse_args()
        if args.quiet: 
            LOGGER.setLevel(logging.WARNING)
        args.func(args)


if __name__ == '__main__':

    main()
