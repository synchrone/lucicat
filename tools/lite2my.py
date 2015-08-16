#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lite2my - convert SQLite dump to MySQL syntax
#  Copyright © 2009  Mikael Ylikoski
#
#  Copying and distribution of this file, with or without modification,
#  are permitted in any medium without royalty provided the copyright
#  notice and this notice are preserved.  This file is offered as-is,
#  without any warranty.
#

import fileinput
import re
import sys

def transform(files, output, remove_create = False, add_drop = False):
    for line in fileinput.input(files):
        if re.search(r"sqlite_sequence", line) or \
                re.match(r"^BEGIN TRANSACTION;", line) or \
                re.match(r"^PRAGMA", line) or \
                re.match(r"^COMMIT;", line):
            continue
        if remove_create and re.match(r"^CREATE", line):
            continue
        m = re.match(r"^CREATE TABLE ([^ ]+)", line)
        if m:
            if add_drop:
                output.write("DROP TABLE IF EXISTS `" + m.group(1) + "`;\n")
            line = line.replace("AUTOINCREMENT", "AUTO_INCREMENT", 1)
        else:
            line = re.sub(r'^INSERT INTO "([^"]+)"', 'INSERT INTO `\\1`', line)
        output.write(line.rstrip() + "\n")

if __name__ == "__main__":
    transform(None, sys.stdout)
