#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lucicat-tool - Lucicat helper tool
#  Copyright © 2009  Mikael Ylikoski
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import optparse
import sqlite3

import lucicat_utils

def connect():
    global conn, autoinc, ph

    if config['db_type'] == 'mysql':
        import MySQLdb
        try:
            conn = MySQLdb.connect(host = config['db_host'],
                                   user = config['db_user'],
                                   passwd = config['db_pass'], charset = 'utf8')
        except:
            print("Error: Can't connect to server")
            exit(-1)
        autoinc = "AUTO_INCREMENT"
        ph = "%s"
    else:
        conn = sqlite3.connect(config['db_name'] + ".sqlite")
        autoinc = "AUTOINCREMENT"
        ph = "?"

def do_dump_tables():
    for stat in lucicat_utils.get_create_tables(db_prefix, "AUTO_INCREMENT"):
        print(stat)
    for stat in lucicat_utils.get_create_indexes(db_prefix):
        print(stat)

def do_reset_database():
    lucicat_utils.reset_database(conn, config)

def do_create_authors():
    c = conn.cursor()
    c.execute("SELECT id, name, file_as FROM " + db_prefix + "authors")
    d = conn.cursor()
    for row in c:
        file_as = row[2]
        if not file_as:
            file_as = row[1]
        initial = lucicat_utils.get_initial(config, file_as)
        d.execute("UPDATE " + db_prefix + "authors SET file_as = " + ph +
                  ", initial = " + ph + " WHERE id=" + ph,
                  (file_as, initial, row[0]))
    d.close()
    c.close()
    conn.commit()

def do_create_titles():
    c = conn.cursor()
    c.execute("SELECT id, title FROM " + db_prefix + "books")
    d = conn.cursor()
    for row in c:
        initial = lucicat_utils.get_initial(config, row[1])
        d.execute("DELETE FROM " + db_prefix + "titles WHERE book = " + ph,
                  (row[0],))
        d.execute("INSERT INTO " + db_prefix + "titles (book, initial) VALUES (" + ph + ", " + ph + ")", (row[0], initial))
    d.close()
    c.close()
    conn.commit()

def do_create_books():
    c.execute("SELECT id FROM " + db_prefix + "books")
    d = conn.cursor()
    for row in c:
        book_id = str(row[0])
        name = ""
        d.execute("SELECT name, file_as FROM " + db_prefix +
                  "authors INNER JOIN " +
                  db_prefix + "authors_books ON " + db_prefix + "authors.id=" +
                  db_prefix + "authors_books.author WHERE book=" + book_id)
        for aut in d:
            if name:
                name += " "
            if aut[1]:
                name += aut[1]
            else:
                name += aut[0]
        d.execute("UPDATE " + db_prefix + "books SET author=" + ph +
                  " WHERE id=" + ph, (name, book_id))
    conn.commit()
    d.close()

def display_commands():
    print("Available commands:")
    print("  authors - fill in 'initial' and 'file_as' columns in luci_authors")
    print("  books   - fill in 'author' column in luci_books from luci_authors")
    print("  dump    - dump create tables")
    print("  reset   - reset and initialize empty database")
    print("  sync    - synonym for 'authors books titles'")
    print("  titles  - create luci_titles from 'title' column in luci_books")

if __name__ == "__main__":
    global config, db_prefix

    version = "lucicat-tool 0.5"
    usage = "Usage: %prog [options] <command>..."

    parser = optparse.OptionParser(usage=usage, version=version)
    parser.add_option("-c", action = "store", dest = "config",
                      help = "use specified configuration file")
    parser.add_option("-l", action = "store_true", dest = "show",
                      help = "display a list of available commands")
    (options, args) = parser.parse_args()

    if options.show:
        display_commands()
        exit()

    if len(args) < 1:
        parser.error("incorrect number of arguments")

    config = lucicat_utils.read_config(options.config)
    db_prefix = config['db_prefix']

    reset_database = False
    create_books = False
    create_authors = False
    create_titles = False
    dump_tables = False

    for arg in args:
        if arg == "reset":
            reset_database = True
        elif arg == "books":
            create_books = True
        elif arg == "authors":
            create_authors = True
        elif arg == "titles":
            create_titles = True
        elif arg == "sync":
            create_books = True
            create_authors = True
            create_titles = True
        elif arg == "dump":
            dump_tables = True
        else:
            print("Unknown command: " + arg)
            display_commands()
            exit()

    if dump_tables:
        do_dump_tables()
        exit()

    connect()

    if reset_database:
        do_reset_database()
        exit()

    if config['db_type'] == "mysql":
        try:
            conn.select_db(config['db_name'])
        except:
            print("Error: Can't select database")
            exit(-1)

    c = conn.cursor()

    if create_authors:
        do_create_authors()

    if create_books:
        do_create_books()

    if create_titles:
        do_create_titles()

    conn.commit()
    c.close()
