# -*- coding: utf-8 -*-
#
#  lucicat_utils - Lucicat helper module
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

import ConfigParser
import os.path
import sys
import unicodedata
import xml.dom.pulldom

language_hash = {}

def read_config(inname):
    config = ConfigParser.RawConfigParser({'db_type': '', 'db_host': '',
                                           'db_name': '', 'db_user': '',
                                           'db_pass': '', 'db_prefix': '',
                                           'arabic': 'list', 'cjk': 'list',
                                           'cyrillic': 'list', 'greek': 'list',
                                           'hebrew': 'list', 'latin': 'list',
                                           'other': 'group', 'digits': 'list'})
    if not inname:
        inname = 'lucicat.ini'
    config.read(inname)
    autoinc = 'AUTO_INCREMENT'
    ph = "%s"
    if config.get('Database', 'db_type') == 'sqlite':
        autoinc = "AUTOINCREMENT"
        ph = "?"
    return {'db_type': config.get('Database', 'db_type'),
            'db_host': config.get('Database', 'db_host'),
            'db_name': config.get('Database', 'db_name'),
            'db_user': config.get('Database', 'db_user'),
            'db_pass': config.get('Database', 'db_pass'),
            'db_prefix': config.get('Database', 'db_prefix'),
            'arabic': config.get('Alphabet', 'arabic'),
            'cjk': config.get('Alphabet', 'cjk'),
            'cyrillic': config.get('Alphabet', 'cyrillic'),
            'greek': config.get('Alphabet', 'greek'),
            'hebrew': config.get('Alphabet', 'hebrew'),
            'latin': config.get('Alphabet', 'latin'),
            'other': config.get('Alphabet', 'other'),
            'digits': config.get('Alphabet', 'digits'),
            'autoinc': autoinc,
            'ph': ph}

def get_create_tables(db_prefix, autoinc):
    yield "CREATE TABLE " + db_prefix + "books (id INTEGER PRIMARY KEY " + autoinc + ", xid TEXT NOT NULL, author TEXT, title TEXT NOT NULL, language TEXT, publisher TEXT, issued TEXT, rights TEXT, summary TEXT, summary_html TEXT, updated TEXT(30), popularity MEDIUMINT);"
    yield "CREATE TABLE " + db_prefix + "authors (id INTEGER PRIMARY KEY " + autoinc + ", name TEXT NOT NULL, uri TEXT, email TEXT, file_as TEXT, initial TEXT);"
    yield "CREATE TABLE " + db_prefix + "authors_books (id INTEGER PRIMARY KEY " + autoinc + ", author INTEGER NOT NULL, book INTEGER NOT NULL);"
    yield "CREATE TABLE " + db_prefix + "links (id INTEGER PRIMARY KEY " + autoinc + ", href TEXT NOT NULL, rel TEXT, type TEXT, title TEXT, book INTEGER NOT NULL);"
    yield "CREATE TABLE " + db_prefix + "categories (id INTEGER PRIMARY KEY " + autoinc + ", term TEXT NOT NULL, scheme TEXT, label TEXT, is_subject SMALLINT, book INTEGER NOT NULL);"
    yield "CREATE TABLE " + db_prefix + "titles (book INTEGER PRIMARY KEY, initial TEXT NOT NULL);"
    yield "CREATE TABLE " + db_prefix + "featured (book INTEGER PRIMARY KEY, featured MEDIUMINT NOT NULL);"
    yield "CREATE TABLE " + db_prefix + "languages (code CHAR(12) PRIMARY KEY, label TEXT, count MEDIUMINT);"

def get_create_indexes(db_prefix):
    yield "CREATE INDEX " + db_prefix + "i1 ON " + db_prefix + "authors_books (author);"
    yield "CREATE INDEX " + db_prefix + "i2 ON " + db_prefix + "authors_books (book);"
    yield "CREATE INDEX " + db_prefix + "i3 ON " + db_prefix + "links (book);"
    yield "CREATE INDEX " + db_prefix + "i4 ON " + db_prefix + "categories (book);"

def get_drop_tables(db_prefix):
    yield "DROP TABLE IF EXISTS " + db_prefix + "books;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "authors;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "authors_books;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "links;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "categories;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "titles;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "featured;"
    yield "DROP TABLE IF EXISTS " + db_prefix + "languages;"

def reset_database(conn, config):
    db_prefix = config['db_prefix']

    if config['db_type'] == "mysql":
        try:
            conn.select_db(config['db_name'])
        except:
            c = conn.cursor()
            c.execute("CREATE DATABASE " + config['db_name'] +
                      " CHARACTER SET utf8")
            c.close()
            conn.select_db(config['db_name'])

    c = conn.cursor()

    for stat in get_drop_tables(db_prefix):
        c.execute(stat)
    for stat in get_create_tables(db_prefix, config['autoinc']):
        c.execute(stat)
    for stat in get_create_indexes(db_prefix):
        c.execute(stat)

    conn.commit()
    c.close()

def update_author(conn, config, author_id):
    db_prefix = config['db_prefix']
    ph = config['ph']

    c = conn.cursor()
    c.execute("SELECT name, file_as FROM " + db_prefix +
              "authors WHERE id = " + ph, (author_id,))
    row = c.fetchone()
    if not row:
        return False

    file_as = row[1]
    if not file_as:
        file_as = row[0]
    initial = get_initial(config, file_as)

    c.execute("UPDATE " + db_prefix + "authors SET file_as = " + ph +
              ", initial = " + ph + " WHERE id = " + ph,
              (file_as, initial, author_id))
    c.close()
    conn.commit()

def update_title(conn, config, book_id):
    db_prefix = config['db_prefix']
    ph = config['ph']

    c = conn.cursor()
    c.execute("SELECT title FROM " + db_prefix + "books WHERE id = " + ph,
              (book_id,))
    row = c.fetchone()
    if not row:
        return False

    initial = get_initial(config, row[0])
    c.execute("DELETE FROM " + db_prefix + "titles WHERE book = " + ph,
              (book_id,))
    c.execute("INSERT INTO " + db_prefix + "titles (book, initial) VALUES (" +
              ph + ", " + ph + ")", (book_id, initial))
    c.close()
    conn.commit()

def update_book(conn, config, book_id):
    db_prefix = config['db_prefix']
    ph = config['ph']

    c = conn.cursor()

    name = ""
    c.execute("SELECT name, file_as FROM " + db_prefix + "authors INNER JOIN " +
              db_prefix + "authors_books ON " + db_prefix + "authors.id = " +
              db_prefix + "authors_books.author WHERE book = " + ph,
              (book_id,))
    for aut in c:
        if name:
            name += " "
        if aut[1]:
            name += aut[1]
        else:
            name += aut[0]
    c.execute("UPDATE " + db_prefix + "books SET author = " + ph +
              " WHERE id = " + ph, (name, book_id))
    c.close()
    conn.commit()

def get_initial(config, st):
    for ch in st:
        ch = ch.upper()
        try:
            name = unicodedata.name(ch).split(" ")[0]
        except:
            continue
        category = unicodedata.category(ch)[0]
        if category == "L":
            if name == "ARABIC":
                if config['arabic'] == "list":
                    return ch
                elif config['arabic'] == "group":
                    return "Arabic"
            elif name == "CJK":
                if config['cjk'] == "list":
                    return ch
                elif config['cjk'] == "group":
                    return "Chinese"
            elif name == "CYRILLIC":
                if config['cyrillic'] == "list":
                    return ch
                elif config['cyrillic'] == "group":
                    return "Cyrillic"
            elif name == "GREEK":
                if config['greek'] == "list":
                    return ch
                elif config['greek'] == "group":
                    return "Greek"
            elif name == "HEBREW":
                if config['hebrew'] == "list":
                    return ch
                elif config['hebrew'] == "group":
                    return "Hebrew"
            elif name == "LATIN":
                if config['latin'] == "list":
                    return ch
                elif config['latin'] == "group":
                    return "Latin"
            else:
                if config['other'] == "group":
                    return "Other"
                print("Warning: Unknown alphabet " + name)
        elif category == "N":
            if config['digits'] == "list":
                return ch
            elif config['digits'] == "group":
                return "Numerical"
    return "Unknown"

def increase_language(config, conn, code):
    if 2 <= code.find("_") <= 3:
        code = code[:code.find("_")]

    db_prefix = config['db_prefix']
    ph = config['ph']
    c = conn.cursor()
    c.execute("SELECT count FROM " + db_prefix + "languages WHERE code = " + ph,
              (code,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE " + db_prefix + "languages SET count = " + ph +
                  " WHERE code = " + ph, (row[0] + 1, code))
    else:
        lang = get_language(code)
        if not lang:
            lang = code
            print("Warning: Unknown language: " + code)
        c.execute("INSERT INTO " + db_prefix +
                  "languages (code, label, count) VALUES (" +
                  ph + ", " + ph + ", " + ph + ")", (code, lang, 1))
    c.close()
    conn.commit()

def decrease_language(code):
    if 2 <= code.indexOf("_") <= 3:
        code = code[:code.indexOf("_")]

    db_prefix = config['db_prefix']
    ph = config['ph']
    c = conn.cursor()
    c.execute("SELECT count FROM " + db_prefix + "languages WHERE code = " + ph,
              (code,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE " + db_prefix + "languages SET count = " + ph +
                  " WHERE code = " + ph, (max(row[0] - 1, 0), code))
    c.close()
    conn.commit()

def get_language(code):
    if code in language_hash:
        return language_hash[code]
    return None

__all__ = (read_config,
           get_create_tables,
           get_create_indexes,
           reset_database,
           update_author,
           update_title,
           update_book,
           get_language)

def get_text(node):
    rc = ""
    for nod in node.childNodes:
        if nod.nodeType == nod.TEXT_NODE:
            rc = rc + nod.nodeValue
        elif nod.nodeType == nod.ELEMENT_NODE:
            rc = rc + get_text(nod)
    return rc.strip()

def read_langs(infile):
    events = xml.dom.pulldom.parse(infile)
    for (event, node) in events:
        if event == "START_ELEMENT" and node.tagName == "language":
            events.expandNode(node)
            subtag = None
            description = None
            for child in node.childNodes:
                if child.nodeType != node.ELEMENT_NODE:
                    continue
                if child.tagName == "subtag":
                    subtag = get_text(child)
                elif child.tagName == "description":
                    description = get_text(child)
            if subtag and description:
                language_hash[subtag] = description

read_langs(os.path.join(sys.path[0], "language-subtags.en.xml"))
read_langs(os.path.join(sys.path[0], "language-tags-extra.en.xml"))
