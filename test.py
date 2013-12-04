#!/usr/bin/python

# an eXtensible Syntax LANGuage experiment
# Copyright (C) 2013 Sosedkin Alexander <monk@unboiled.info>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from xslang import XInterpreter
import sys, os, traceback

if __name__ == '__main__':
    TESTFILES = os.listdir('tests')
    failed = []
    sys.stdout.write('%d: ' % len(TESTFILES))
    for i, testfile in enumerate(TESTFILES):
        testfile = os.path.join('tests', testfile)
        c, r = file(testfile).read().split('###', 1)
        c, r = c.strip(), r.strip()
        try:
            e = XInterpreter(c).eval()
        except Exception, ex:
            print
            print 'WHILE EVALUATING', testfile
            print c
            print traceback.format_exc(ex)
            e = 'XException(%s)' % ex
            failed.append(testfile)
        if not str(e) == r:
            print
            print 'A test failed:      ', c
            print 'Evaluation returned:', e
            print 'Expected:           ', r
            failed.append(testfile)
        if not failed:
            sys.stdout.write('+')
    print
    for f in failed:
        print 'TEST FAILED:', testfile
    else:
        print 'All tests passed OK'
        sys.exit(0)
    sys.exit(1)

