#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  lucicat-epub - Lucicat helper tool
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

import codecs
import datetime
import optparse
import os.path
import re
import sys
import urlparse
import uuid
import xml.dom.minidom
import xml.sax.saxutils
import zipfile

atom_ns = "http://www.w3.org/2005/Atom"
dc_ns = "http://purl.org/dc/elements/1.1/"
dcterms_ns = "http://purl.org/dc/terms/"
ocf_ns = "urn:oasis:names:tc:opendocument:xmlns:container"
opf_ns = "http://www.idpf.org/2007/opf"
xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"

version = "lucicat-epub 0.5"
usage = "Usage: %prog [options] <EPUB file>..."
parser = optparse.OptionParser(usage = usage, version = version)
parser.add_option("--base-url", action = "store", type = "string",
                  dest = "baseurl", help = "set base URL")
parser.add_option("--file-id", action = "store_true", dest = "file_id",
                  help = "use file url as id")
parser.add_option("-o", "--output", action = "store", type = "string",
                  dest = "output", help = "set output file")
parser.add_option("--updated", action = "store_true", dest = "updated",
                  help = "add updated values")
(options, args) = parser.parse_args()
if len(args) < 1:
    parser.error("incorrect number of arguments")

impl = xml.dom.getDOMImplementation()
doc = impl.createDocument(atom_ns, "feed", None)
feed = doc.documentElement
feed.setAttribute("xmlns", atom_ns)
feed.setAttribute("xmlns:dcterms", dcterms_ns)
feed.setAttribute("xmlns:xsi", xsi_ns)

def get_text(node):
    rc = ""
    for nod in node.childNodes:
        if nod.nodeType == nod.TEXT_NODE:
            rc = rc + nod.nodeValue
        elif nod.nodeType == nod.ELEMENT_NODE:
            rc = rc + get_text(nod)
    return rc.strip()

def get_opf(epub):
    zf = zipfile.ZipFile(epub, "r")

    opfname = None
    contfile = zf.open("META-INF/container.xml")
    cont = xml.dom.minidom.parse(contfile)
    contfile.close()
    for el in cont.getElementsByTagNameNS(ocf_ns, "rootfile"):
        if el.hasAttribute("media-type") and el.hasAttribute("full-path") and \
                el.getAttribute("media-type") == "application/oebps-package+xml":
            opfname = el.getAttribute("full-path")
            break

    if not opfname:
        return None

    opffile = zf.open(opfname)
    opf = xml.dom.minidom.parse(opffile)
    opffile.close()
    return opf

def add_book(book):
    entry = doc.createElementNS(atom_ns, "entry")
    feed.appendChild(entry)

    if "id" in book:
        elem = doc.createElementNS(atom_ns, "id")
        entry.appendChild(elem)
        text = doc.createTextNode(book["id"])
        elem.appendChild(text)

    if "title" in book:
        elem = doc.createElementNS(atom_ns, "title")
        entry.appendChild(elem)
        text = doc.createTextNode(book["title"])
        elem.appendChild(text)

    if "author" in book:
        for aut in book["author"]:
            author = doc.createElementNS(atom_ns, "author")
            entry.appendChild(author)
            elem = doc.createElementNS(atom_ns, "name")
            author.appendChild(elem)
            text = doc.createTextNode(aut)
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
        elem = doc.createElementNS(dcterms_ns, "rights")
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

    if "epub" in book:
         elem = doc.createElementNS(atom_ns, "link")
         entry.appendChild(elem)
         elem.setAttribute("href", book["epub"])
         elem.setAttribute("rel", "http://opds-spec.org/acquisition")
         elem.setAttribute("type", "application/epub+zip")

    if "updated" in book:
        elem = doc.createElementNS(atom_ns, "updated")
        entry.appendChild(elem)
        text = doc.createTextNode(book["updated"])
        elem.appendChild(text)

for epub in args:
    try:
        opf = get_opf(epub)
        metadata = opf.getElementsByTagNameNS(opf_ns, "metadata")[0]
    except:
        print("Warning: Could not process file: " + epub)
        continue

    book = {}
    if options.baseurl:
        book["epub"] = urlparse.urljoin(options.baseurl, os.path.basename(epub))
    else:
        book["epub"] = os.path.basename(epub)
    if options.file_id:
        if options.baseurl:
            book["id"] = book["epub"]
        else:
            book["id"] = urlparse.urljoin("http://example.com/", book["epub"])
    else:
        book["id"] = "urn:uuid:" + str(uuid.uuid4())
    if options.updated:
        book["updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    book["author"] = []
    book["language"] = []
    book["subject"] = []
    for child in metadata.childNodes:
        if child.nodeType != metadata.ELEMENT_NODE:
            continue
        if child.namespaceURI == dc_ns:
            if child.localName == "creator":
                role = None
                if child.hasAttributeNS(opf_ns, "role"):
                    role = child.getAttributeNS(opf_ns, "role")
                if not role in ["producer"]:
                    book["author"].append(get_text(child))
            elif child.localName == "date":
                # FIXME
                #book["issued"] = get_text(child)
                None
            elif child.localName == "language":
                book["language"].append(get_text(child))
            elif child.localName == "publisher":
                book["publisher"] = get_text(child)
            elif child.localName == "rights":
                book["rights"] = get_text(child)
            elif child.localName == "subject":
                subject = get_text(child)
                typ = None
                if child.hasAttributeNS(xsi_ns, "type"):
                    typ = child.getAttributeNS(xsi_ns, "type")
                book["subject"].append([subject, typ])
            elif child.localName == "title":
                if not "title" in book:
                    book["title"] = get_text(child)

    add_book(book)

def pretty_print(doc, writer, addindent = "", newl = "", encoding = ""):
    def write_element(elem, writer, indent, addindent, newl):
        string = indent + "<" + elem.tagName
        for i in range(0, elem.attributes.length):
            attr = elem.attributes.item(i)
            if attr.value:
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
                write_element(child, writer, indent = indent + addindent,
                              addindent = addindent, newl = newl)
            else:
                child.writexml(writer)
        if has_elements:
            writer.write(indent)
        writer.write('</' + elem.tagName + '>' + newl)

    string = '<?xml version="1.0"'
    if encoding:
        string += ' encoding="UTF-8"'
    string += '?>' + newl
    writer.write(string)
    write_element(doc.documentElement, writer, indent = "",
                  addindent = addindent, newl = newl)

if options.output:
    writer = codecs.open(options.output, "wb", "UTF-8")
else:
    writer = sys.stdout
#doc.writexml(writer, addindent = "  ", newl = "\n", encoding = "UTF-8")
#doc.writexml(writer, encoding = "UTF-8")
pretty_print(doc, writer, addindent = "  ", newl = "\n", encoding = "UTF-8")
