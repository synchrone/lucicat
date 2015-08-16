#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lucicat-export - Lucicat helper tool
#  Copyright © 2009  Mikael Ylikoski
#
#  Copying and distribution of this file, with or without modification,
#  are permitted in any medium without royalty provided the copyright
#  notice and this notice are preserved.  This file is offered as-is,
#  without any warranty.
#

import re
import sys
import lite2my
import lucicat_utils

if not (2 <= len(sys.argv) <= 3):
    print("Usage: " + sys.argv[0] + " <input.sql> [<output.sql>]")
    exit(-1)

inname = sys.argv[1]
outname = None
if len(sys.argv) == 3:
    outname = sys.argv[2]

db_prefix = -1
i = 0
infile = open(inname, "rb")
for line in infile:
    #m = re.match(r"^INSERT INTO .sqlite_sequence. VALUES\('(.*)authors',", line)
    m = re.match(r"^CREATE TABLE (.*)books \(id", line)
    if m:
        db_prefix = m.group(1)
        break
    i += 1
    if i > 20:
        break
infile.close()
if db_prefix == -1:
    print("Error in input.")
    exit(-1)

outfile = sys.stdout
if outname:
    outfile = open(outname, "wb")

for stat in lucicat_utils.get_drop_tables(db_prefix):
    outfile.write(stat + "\n")
for stat in lucicat_utils.get_create_tables(db_prefix, "AUTO_INCREMENT"):
    outfile.write(stat + "\n")
for stat in lucicat_utils.get_create_indexes(db_prefix):
    outfile.write(stat + "\n")
lite2my.transform(inname, outfile, True)
