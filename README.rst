SYNOPSIS
========

*pypstats* is for retrieving monthly download statistics for packages 
distributed via `PyPI <http://pypi.python.org/pypi>`_.  Statistics are 
downloaded from http://pypi.python.org/stats/months/.  This page contains 
monthly statistics in compressed files starting from June 2010.  These
files contains information on releases that are removed from PyPI, so
you will get more complete statistics for packages that were released 
after June 2010. 

INSTALLATION
============

Download **pypstats-1.{x}.tar.gz**. Extract tarball contents and run 
**setup.py** as follows::
  
  $ tar -xzf pypstats-1.x.tar.gz
  $ cd pypstats-1.x
  $ python setup.py install

Or, if if you have `Easy Install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_
installed, type the following::

  $ easy_install -U pypstats

USAGE
=====

First use
---------

Before statistics can be printed or plotted, you need to retrieve statistics 
and save them locally using **pypstats update** command::

  $ pypstats update ProDy
  Fetching content from 'http://pypi.python.org/stats/months/'.
  Parsing monthly statistics file details.
  Updating statistics for 2010-06.
  ...
  Updating statistics for 2012-01.
  Package statistics are updated (ProDy_stats.pkl).

Retrieving statistics at the first use will take some time, since all 
monthly stats files are downloaded.


Monthly stats
-------------

Monthly statistics can be printed using **pypstats release** command::

  $ pypstats.py monthly ProDy_stats.pkl 
  Loading statistics from 'ProDy_stats.pkl'.
  Month	Downloads
  2010-11	286
  ...
  2012-01	1041
  Total	  10664

This information can also be plotted and saved in a :file:`.csv` file as 
follows::

  $ pypstats.py monthly -o monthly.csv -p monthly.png ProDy_stats.pkl
  Loading statistics from 'ProDy_stats.pkl'.
  Monthly statistics are written in 'monthly.csv'.
  Monthly downloads plot is saved as 'monthly.png'.

Release stats
-------------

Release statistics can be printed using **pypstats release** command::

Total downloads
---------------

Total number of downloads can be printed using **pypstats total** command::

  $ pypstats.py total -q ProDy_stats.pkl 
  10664

Current release
---------------

Current release information can be retrieved using **pypstats current** 
command::

  $ pypstats.py release ProDy_stats.pkl 
  Loading statistics from 'ProDy_stats.pkl'.
  Release	Downloads
  0.1.0	397
  ...
  0.9.2	328
  Total	10664

Updates
-------

Local statistics file can be updated using **pypstats update** command::

  $ pypstats update ProDy
  Fetching content from 'http://pypi.python.org/stats/months/'.
  Parsing monthly statistics file details.
  Nothing to update.

This command will make an incremental update by downloading the files that
changed since the last update.

LICENSE
=======
  
*pypstats* is available under GNU General Public License version 3.  See 
LICENSE.txt for more details. 


SOURCE
======

http://github.com/abakan/pypstats


REPORT ISSUES
=============

https://github.com/abakan/pypstats/issues
  
