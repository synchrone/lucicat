#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  opds-crawl - Lucicat helper tool
#  Copyright © 2009  Mikael Ylikoski
#
#  Copying and distribution of this file, with or without modification,
#  are permitted in any medium without royalty provided the copyright
#  notice and this notice are preserved.  This file is offered as-is,
#  without any warranty.
#

import os.path
import sys
import urllib2
import xml.dom.minidom

headers = {'Accept': 'application/atom+xml',
           'User-Agent': 'Lucicat-Crawl/0.5'}

if len(sys.argv) != 3:
    print('Usage: %s <URL> <folder name>' % sys.argv[0])
    exit(1)

url = sys.argv[1]
folder = sys.argv[2]
do_zip = False

if os.path.exists(folder):
    print('Error: Folder path exists')
    exit(1)
if do_zip and os.path.exists(folder + '.zip'):
    print('Error: File path exists')
    exit(1)

req = urllib2.Request(url = url, headers = headers)
try:
    inp = urllib2.urlopen(req)
except:
    print('Error: Could not open URL: ' + url)
    exit(1)
dom = xml.dom.minidom.parse(inp)
url = None
for link in dom.getElementsByTagName('link'):
    if link.hasAttribute('rel') and link.hasAttribute('href') and \
            (link.getAttribute('rel') == 'http://opds-spec.org/crawlable'):
        url = link.getAttribute('href')
        break

if not url:
    print("Error: Could not find crawlable link")
    exit (1)

try:
    os.mkdir(folder)
except:
    print('Error: Could not create folder')
    exit(1)

page = 1
while url:
    req = urllib2.Request(url = url, headers = headers)
    try:
        inp = urllib2.urlopen(req)
    except:
        print('Error: Could not open URL: ' + url)
        exit(1)

    filename = "page-" + str(page).zfill(3) + ".atom"
    filename = os.path.join(folder, filename)
    out = open(filename, "wb")
    out.write(inp.read())
    out.close()
    inp.close()

    dom = xml.dom.minidom.parse(filename)
    url = None
    for link in dom.getElementsByTagName('link'):
        if link.hasAttribute('rel') and link.hasAttribute('href') and \
                (link.getAttribute('rel') == 'next'):
            url = link.getAttribute('href')
            break

    page += 1

if do_zip:
    # FIXME
    None
