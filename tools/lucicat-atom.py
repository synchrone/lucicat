#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lucicat-atom - Lucicat helper tool
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

import datetime
import optparse
import os.path
import re
import sqlite3
import sys
import xml.dom.pulldom
import xml.sax.saxutils

import lucicat_utils

atom_ns = "http://www.w3.org/2005/Atom"
dcterms_ns = "http://purl.org/dc/terms/"
lucicat_ns = "http://lucidor.org/-/lucicat/"
xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"

version = "lucicat-atom 0.5.1"
usage = "Usage: %prog [options] <Atom file>..."
parser = optparse.OptionParser(usage = usage, version = version)
parser.add_option("-c", action = "store", dest = "config",
                  help = "use specified configuration file")
parser.add_option("-r", "--reset", action = "store_true", dest = "reset",
                  help = "reset database before")
(options, args) = parser.parse_args()
if len(args) < 1:
    parser.error("incorrect number of arguments")
if not options.reset:
    print "You must use the '-r' option"
    exit(1)

config = lucicat_utils.read_config(options.config)
db_prefix = config['db_prefix']
ph = config['ph']

if config['db_type'] == "mysql":
    import MySQLdb
    try:
        conn = MySQLdb.connect(host = config['db_host'],
                               user = config['db_user'],
                               passwd = config['db_pass'],
                               db = config['db_name'], charset = "utf8")
    except:
        print("Error: Can't connect to database")
        exit(-1)
else:
    conn = sqlite3.connect(config['db_name'] + ".sqlite")

if options.reset:
    lucicat_utils.reset_database(conn, config);

c = conn.cursor()

def get_text(node):
    rc = ""
    for nod in node.childNodes:
        if nod.nodeType == nod.TEXT_NODE:
            rc = rc + nod.nodeValue
        elif nod.nodeType == nod.ELEMENT_NODE:
            rc = rc + get_text(nod)
    return rc.strip()

for atom_file in args:
    events = xml.dom.pulldom.parse(atom_file)
    for (event, node) in events:
        if event == "START_ELEMENT" and node.namespaceURI == atom_ns and \
                node.localName == "entry":

            xid = None
            author = None
            authors = []
            title = "[Untitled]"
            rights = None
            updated = None
            summary_text = None
            summary_html = None
            links = []
            languages = []
            language = ""
            publisher = None
            issued = None
            categories = []
            featured = None
            popularity = None

            events.expandNode(node)

            for child in node.childNodes:
                if child.nodeType != node.ELEMENT_NODE:
                    continue
                if child.namespaceURI == atom_ns:
                    if child.localName == "author":
                        aut = { "uri": None, "email": None, "file-as": None }
                        for ch in child.childNodes:
                            if ch.namespaceURI == atom_ns:
                                if ch.localName == "name":
                                    aut["name"] = get_text(child)
                                    if ch.hasAttributeNS(lucicat_ns, "file-as"):
                                        aut["file-as"] = ch.getAttributeNS(lucicat_ns, "file-as")
                                    else:
                                        aut["file-as"] = aut["name"]
                                elif ch.localName == "uri":
                                    aut["uri"] = get_text(child)
                                elif ch.localName == "email":
                                    aut["email"] = get_text(child)
                        if "name" in aut:
                            authors.append(aut)
                        else:
                            print("Warning: Ignoring author.")
                    elif child.localName == "category":
                        if child.hasAttribute("term"):
                            term = child.getAttribute("term")
                            scheme = None
                            label = None
                            if child.hasAttribute("scheme"):
                                scheme = child.getAttribute("scheme")
                            if child.hasAttribute("label"):
                                label = child.getAttribute("label")
                            categories.append((term, scheme, label, 0))
                        else:
                            print("Warning: Ignoring category.")
                    elif child.localName == "id":
                        xid = get_text(child)
                    elif child.localName == "link":
                        if child.hasAttribute("type") and \
                                child.hasAttribute("href"):
                            rel = "alternate"
                            if child.hasAttribute("rel"):
                                rel = child.getAttribute("rel")
                            tit = None
                            if child.hasAttribute("title"):
                                tit = child.getAttribute("title")
                            link = (child.getAttribute("href"), rel, \
                                        child.getAttribute("type"), tit)
                            if link[1] == "http://opds-spec.org/acquisition":
                                epub_file = link[0]
                            links.append(link)
                        else:
                            print("Warning: Ignoring link.")
                    elif child.localName == "rights":
                        rights = get_text(child)
                    elif child.localName == "summary":
                        ty = "text"
                        if child.hasAttribute("type"):
                            ty = child.getAttribute("type")
                        if ty == "html" or ty == "xhtml":
                            summary_html = get_text(child)
                        elif ty == "text":
                            summary_text = get_text(child)
                        else:
                            print("Warning: Ignoring summary: " + ty)
                    elif child.localName == "title":
                        title = get_text(child)
                    elif child.localName == "updated":
                        updated = get_text(child)
                    else:
                        print("Warning: Ignoring element: " + child.tagName)
                elif child.namespaceURI == dcterms_ns:
                    if child.localName == "issued":
                        issued = get_text(child)
                    elif child.localName == "language":
                        lang = get_text(child)
                        if lang.find("_") >= 0:
                            print("Warning: Incorrect language tag: " + lang)
                        if len(lang) > 12:
                            lang = lang[:12]
                            print("Warning: Language tag too long: " + lang)
                        languages.append(lang)
                        if not language:
                            language = "|"
                        language += lang + "|"
                    elif child.localName == "publisher":
                        publisher = get_text(child)
                    elif child.localName == "subject":
                        subject = get_text(child)
                        typ = None
                        if child.hasAttributeNS(xsi_ns, "type"):
                            typ = child.getAttributeNS(xsi_ns, "type")
                        categories.append((subject, typ, None, 1))
                    else:
                        print("Warning: Ignoring element: " + child.tagName)
                elif child.namespaceURI == lucicat_ns:
                    if child.localName == "featured":
                        try:
                            featured = int(get_text(child))
                        except:
                            print("Warning: featured with non-integer value")
                    elif child.localName == "popularity":
                        try:
                            popularity = int(get_text(child))
                        except:
                            print("Warning: popularity with non-integer value")
                    else:
                        print("Warning: Ignoring element: " + child.tagName)
                else:
                    print("Warning: Ignoring element: " + child.tagName)

            if not title:
                print("Warning: No title. Ignoring entry.")
                continue

            if not epub_file:
                print("Warning: No acquisition link: " + title)

            if not xid:
                if epub_file:
                    xid = epub_file
                    print("Warning: Using '" + epub_file + "' as id.")
                else:
                    print("Warning: No id: " + title)

            if not updated:
                #print("Warning: No updated value. Using current time.")
                updated = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Check if the entry has been changed
            if not options.reset:
                c.execute("SELECT id, title, language, publisher, issued, rights, summary, summary_html FROM " + db_prefix + "books WHERE xid=" + ph,
                          (xid,))
                row = c.fetchone()
                while (row):
                    bid = row[0]
                    if not (row[1] == title and \
                                row[2] == language and \
                                row[3] == publisher and \
                                row[4] == issued and \
                                row[5] == rights and \
                                row[6] == summary_text and \
                                row[7] == summary_html):
                        break
                    # Check authors
                    c.execute("SELECT name FROM " + db_prefix + "authors INNER JOIN " + db_prefix + "authors_books ON " + db_prefix + "authors.id = " + db_prefix + "authors_books.author WHERE " + db_prefix + "authors_books.book = " + str(bid))
                    oks = [ False ] * len(authors)
                    #while row = c.fetchone():
                    #    if row[0] == author[0] and row[1] == author[1] and \
                    #            row[2] == author[2]:
                    #        oks[0] = True

                    # Check links
                    # Check categories
                    print("Not updated")
                    break

            name = ""
            for aut in authors:
                if name:
                    name += " "
                name += aut["file-as"]

            c.execute("INSERT INTO " + db_prefix + "books (id, xid, author, title, language, publisher, issued, rights, summary, summary_html, updated, popularity) VALUES (NULL" + (", " + ph) * 11 + ")", \
                          (xid, name, title, language, publisher, issued, rights, summary_text, summary_html, updated, popularity))
            book_id = c.lastrowid

            for aut in authors:
                c.execute("SELECT * FROM " + db_prefix +
                          "authors WHERE name=" + ph +
                          " AND (uri=" + ph + " OR uri IS NULL AND " +
                          ph + " IS NULL)" +
                          " AND (email=" + ph + " OR email IS NULL AND " +
                          ph + " IS NULL)",
                          (aut["name"], aut["uri"], aut["uri"],
                           aut["email"], aut["email"]))
                row = c.fetchone()
                author_id = -1
                if row:
                    author_id = row[0]
                else:
                    initial = lucicat_utils.get_initial(config, aut["file-as"])
                    c.execute("INSERT INTO " + db_prefix + "authors (id, name, uri, email, file_as, initial) VALUES (NULL" + (", " + ph) * 5 + ")", (aut["name"], aut["uri"], aut["email"], aut["file-as"], initial))
                    author_id = c.lastrowid
                c.execute("INSERT INTO " + db_prefix + "authors_books (id, author, book) VALUES (NULL" + (", " + ph) * 2 + ")", (author_id, book_id))

            for link in links:
                c.execute("INSERT INTO " + db_prefix + "links (id, href, rel, type, title, book) VALUES (NULL" + (", " + ph) * 5 + ")", (link[0], link[1], link[2], link[3], book_id))

            for category in categories:
                c.execute("INSERT INTO " + db_prefix + "categories (id, term, scheme, label, is_subject, book) VALUES (NULL" + (", " + ph) * 5 + ")", (category[0], category[1], category[2], category[3], book_id))

            if featured:
                c.execute("INSERT INTO " + db_prefix + "featured (book, featured) VALUES (" + ph + ", " + ph + ")", (book_id, featured))

            initial = lucicat_utils.get_initial(config, title)
            c.execute("INSERT INTO " + db_prefix + "titles (book, initial) VALUES (" +
                      ph + ", " + ph + ")", (book_id, initial))
            for lang in languages:
                lucicat_utils.increase_language(config, conn, lang)

conn.commit()
c.close()
