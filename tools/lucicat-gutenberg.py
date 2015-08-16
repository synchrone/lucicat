#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lucicat-gutenberg - Lucicat helper tool
#  Copyright © 2009  Mikael Ylikoski
#
#  Copying and distribution of this file, with or without modification,
#  are permitted in any medium without royalty provided the copyright
#  notice and this notice are preserved.  This file is offered as-is,
#  without any warranty.
#

import codecs
import datetime
import optparse
import re
import sys
import xml.dom.pulldom
import xml.sax.saxutils

version = "lucicat-gutenberg 0.5.1"
usage = "Usage: %prog [options] <catalog.rdf> <epub_urls.txt>"
parser = optparse.OptionParser(usage = usage, version = version)
parser.add_option("-o", "--output", action = "store", type = "string",
                  dest = "output", help = "set output file")
parser.add_option("-t", "--test", action = "store_true",
                  dest = "test", help = "test with a small subset")
(options, args) = parser.parse_args()
if len(args) != 2:
    parser.error("incorrect number of arguments")

atom_ns = "http://www.w3.org/2005/Atom"
dcterms_ns = "http://purl.org/dc/terms/"
xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"

def pretty_print_element(elem, writer, indent, addindent, newl):
    string = indent + "<" + elem.tagName
    for i in range(0, elem.attributes.length):
        attr = elem.attributes.item(i)
        string += " " + attr.name + "=" + xml.sax.saxutils.quoteattr(attr.value)

    if len(elem.childNodes) == 0:
        string += "/>" + newl
        writer.write(string)
        return

    string += ">"
    writer.write(string)

    has_elements = False
    for child in elem.childNodes:
        if child.nodeType == elem.ELEMENT_NODE:
            has_elements = True
            break
    if has_elements:
        writer.write(newl)
    for child in elem.childNodes:
        if child.nodeType == elem.ELEMENT_NODE:
            pretty_print_element(child, writer, indent = indent + addindent,
                                 addindent = addindent, newl = newl)
        else:
            child.writexml(writer)
    if has_elements:
        writer.write(indent)
    writer.write('</' + elem.tagName + '>' + newl)

def pretty_print(doc, writer, addindent = "", newl = "", encoding = ""):
    string = '<?xml version="1.0"'
    if encoding:
        string += ' encoding="UTF-8"'
    string += '?>' + newl
    writer.write(string)
    pretty_print_element(doc.documentElement, writer, indent = "",
                         addindent = addindent, newl = newl)

def get_text(node):
    rc = ""
    for nod in node.childNodes:
        if nod.nodeType == nod.TEXT_NODE:
            rc = rc + nod.nodeValue
        elif nod.nodeType == nod.ELEMENT_NODE:
            rc = rc + get_text(nod)
    return rc.strip()

def get_bag(node):
    bag = []
    for child in node.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            if child.tagName == "rdf:Bag":
                for nod in child.childNodes:
                    if nod.nodeType == nod.ELEMENT_NODE and nod.tagName == "rdf:li":
                        bag.append(get_text(nod))
                return bag
    bag.append(get_text(node))
    return bag

def get_type_bag(node):
    bag = []
    for child in node.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            if child.tagName == "rdf:Bag":
                for nod in child.childNodes:
                    if nod.nodeType == nod.ELEMENT_NODE and nod.tagName == "rdf:li":
                        typ = None
                        if nod.firstChild.namespaceURI == dcterms_ns:
                            typ = nod.firstChild.localName
                        bag.append((get_text(nod), typ))
                return bag
    typ = None
    if node.firstChild.namespaceURI == dcterms_ns:
        typ = node.firstChild.localName
    bag.append((get_text(node), typ))
    return bag

impl = xml.dom.getDOMImplementation()
doc = impl.createDocument(atom_ns, "feed", None)
#feed = doc.documentElement
#feed.setAttribute("xmlns", atom_ns)
#feed.setAttribute("xmlns:dcterms", dcterms_ns)
#feed.setAttribute("xmlns:xsi", xsi_ns)

def create_entry(book):
    entry = doc.createElementNS(atom_ns, "entry")

    if "author" in book:
        for aut in book["author"]:
            author = doc.createElementNS(atom_ns, "author")
            entry.appendChild(author)
            elem = doc.createElementNS(atom_ns, "name")
            author.appendChild(elem)
            text = doc.createTextNode(aut)
            elem.appendChild(text)
    if "title" in book:
        elem = doc.createElementNS(atom_ns, "title")
        entry.appendChild(elem)
        text = doc.createTextNode(book["title"])
        elem.appendChild(text)
    if "language" in book:
        for lang in book["language"]:
            elem = doc.createElementNS(dcterms_ns, "dcterms:language")
            entry.appendChild(elem)
            text = doc.createTextNode(lang)
            elem.appendChild(text)
    if "publisher" in book:
        elem = doc.createElementNS(dcterms_ns, "dcterms:publisher")
        entry.appendChild(elem)
        text = doc.createTextNode(book["publisher"])
        elem.appendChild(text)
    if "issued" in book:
        elem = doc.createElementNS(dcterms_ns, "dcterms:issued")
        entry.appendChild(elem)
        text = doc.createTextNode(book["issued"])
        elem.appendChild(text)
    if "rights" in book:
        elem = doc.createElementNS(atom_ns, "rights")
        entry.appendChild(elem)
        text = doc.createTextNode(book["rights"])
        elem.appendChild(text)
    if "subject" in book:
        for sub in book["subject"]:
            elem = doc.createElementNS(dcterms_ns, "dcterms:subject")
            if sub[1]:
                elem.setAttributeNS(xsi_ns, "xsi:type", sub[1])
            entry.appendChild(elem)
            text = doc.createTextNode(sub[0])
            elem.appendChild(text)
    if "tableOfContents" in book:
        elem = doc.createElementNS(atom_ns, "summary")
        entry.appendChild(elem)
        text = doc.createTextNode(book["tableOfContents"])
        elem.appendChild(text)

    elem = doc.createElementNS(atom_ns, "updated")
    entry.appendChild(elem)
    updated = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    text = doc.createTextNode(updated)
    elem.appendChild(text)

    elem = doc.createElementNS(atom_ns, "link")
    entry.appendChild(elem)
    elem.setAttribute("href", "http://www.gutenberg.org/etext/" + book["id"])
    elem.setAttribute("type", "text/html")
    elem.setAttribute("rel", "alternate")

    entries = []
    for epub_file in epub_files[book["id"]]:
        ent = entry.cloneNode(True)
        entries.append(ent)

        if "-images." in epub_file:
            elems = ent.getElementsByTagNameNS(atom_ns, "title")
            if elems:
                text = doc.createTextNode(" [With images]")
                elems[0].appendChild(text)

        elem = doc.createElementNS(atom_ns, "id")
        ent.appendChild(elem)
        text = doc.createTextNode(epub_file)
        elem.appendChild(text)

        elem = doc.createElementNS(atom_ns, "link")
        ent.appendChild(elem)
        elem.setAttribute("href", epub_file)
        elem.setAttribute("type", "application/epub+zip")
        elem.setAttribute("rel", "http://opds-spec.org/acquisition")
    return entries

epub_files = {}

exp = re.compile(r"epub/([0-9]+)/pg")
inp = file(args[1])
for line in inp:
    m = exp.search(line)
    num = m.group(1)
    if not num in epub_files:
        epub_files[num] = []
    epub_files[num].append(line.strip())

writer = sys.stdout
if options.output:
    writer = codecs.open(options.output, "wb", "UTF-8")

writer.write('<?xml version="1.0" encoding="UTF-8"?>\n')
writer.write('<feed xmlns="' + atom_ns + '" xmlns:dcterms="' + dcterms_ns +
             '" xmlns:xsi="' + xsi_ns + '">\n')

count = 0
events = xml.dom.pulldom.parse(args[0])
for (event, node) in events:
    if event == "START_ELEMENT" and node.tagName == "pgterms:etext":
        count += 1
        if options.test and count > 100:
            break

        events.expandNode(node)
        nid = node.getAttribute("rdf:ID")
        nid = nid[5:]
        if not nid in epub_files:
            continue

        book = {}
        book["id"] = nid
        book["subject"] = []
        for child in node.childNodes:
            if child.nodeType != node.ELEMENT_NODE:
                continue
            if child.tagName == "dc:publisher":
                book["publisher"] = get_text(child)
            elif child.tagName == "dc:title":
                book["title"] = get_text(child)
            elif child.tagName == "pgterms:friendlytitle":
                if not "title" in book:
                    book["title"] = get_text(child)
            elif child.tagName == "dc:creator":
                book["author"] = get_bag(child)
            elif child.tagName == "dc:contributor":
                book["contributor"] = get_bag(child)
                if not "author" in book:
                    book["author"] = book["contributor"]
            elif child.tagName == "dc:language":
                book["language"] = get_bag(child)
            elif child.tagName == "dc:subject":
                book["subject"] += get_type_bag(child)
            elif child.tagName == "dc:created":
                book["issued"] = get_text(child)
            elif child.tagName == "dc:rights":
                if child.hasAttribute("rdf:resource"):
                    book["rights"] = child.getAttribute("rdf:resource")
                else:
                    book["rights"] = get_text(child)
            elif child.tagName == "dc:tableOfContents":
                book["tableOfContents"] = get_text(child)
            # Other elements: "dc:alternative", "dc:description", "dc:type"

        entries = create_entry(book)
        for entry in entries:
            #feed.appendChild(entry)
            pretty_print_element(entry, writer, indent = "  ",
                                 addindent = "  ", newl = "\n")

writer.write("</feed>\n")

#doc.writexml(writer, addindent = "  ", newl = "\n", encoding = "UTF-8")
#doc.writexml(writer, encoding = "UTF-8")
#pretty_print(doc, writer, addindent = "  ", newl = "\n", encoding = "UTF-8")
