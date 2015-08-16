DBXSLHOME=/usr/share/xml/docbook/stylesheet/docbook-xsl
DB2EPUB=dbtoepub
EPUBTWEAK=../lucidor/tools/epubtweak.py
SOURCE=lucicat-source
MAKEFILE_SOURCE=Makefile
TDIR=/tmp/Lucicat-tmp

all:

zip:
	-rm -rf ${TDIR}
	mkdir -p ${TDIR}/${SOURCE}/
	cd ${TDIR}/${SOURCE}/ ; mkdir server tools distfiles examples manual
	cp -a server/lucicat.php server/lucicatAtom.php server/lucicat.xsl server/lucicat.css ${TDIR}/${SOURCE}/server
	chmod a-w ${TDIR}/${SOURCE}/server/*
	cp -a tools/lite2my.py tools/lucicat-atom.py tools/lucicat-epub.py tools/lucicat-export.py tools/lucicat-gutenberg.py tools/lucicat-tool.py tools/lucicat_utils.py tools/opds-crawl.py tools/language-subtags.en.xml tools/language-tags-extra.en.xml ${TDIR}/${SOURCE}/tools
	cp -a distfiles/lucicat_settings.php.dist distfiles/lucicat.ini.dist ${TDIR}/${SOURCE}/distfiles
	cp -a examples/lucidor.atom ${TDIR}/${SOURCE}/examples
	cp -a manual/lucicat-manual.xml manual/manual.xsl manual/fdl-1.3.xml ${TDIR}/${SOURCE}/manual
	cp -a lucicat-manual.epub Readme.txt Changes.txt agpl-3.0.txt ${TDIR}/${SOURCE}/
	cp -a ${MAKEFILE_SOURCE} ${TDIR}/${SOURCE}/Makefile
	cp -a ${TDIR}/${SOURCE}/distfiles/lucicat_settings.php.dist ${TDIR}/${SOURCE}/server/lucicat_settings.php
	cp -a ${TDIR}/${SOURCE}/distfiles/lucicat.ini.dist ${TDIR}/${SOURCE}/lucicat.ini
	-rm -f server/${SOURCE}.zip
	cd ${TDIR} ; zip -r -9 ${SOURCE}.zip ${SOURCE}
	mv ${TDIR}/${SOURCE}.zip server/${SOURCE}.zip
	rm -rf ${TDIR}

lucidor: examples/lucidor.atom
	tools/lucicat-atom.py -r $<

gutenberg: gutenberg.atom
	tools/lucicat-atom.py -r $<

gutenberg.atom: catalog.rdf epub_urls.txt
	tools/lucicat-gutenberg.py -o $@ catalog.rdf epub_urls.txt

epub_urls.txt: tmp_cat
	cat tmp_cat/www.gutenberg.org/etext/* | grep -o "http://www.gutenberg.org/cache/epub/.*/pg.*.epub" | sort -u > $@

catalog.rdf: tmp_cat
	unzip tmp_cat/www.gutenberg.org/feeds/catalog.rdf.zip
	touch catalog.rdf

tmp_cat: offline-package.tar.bz2
	-rm -rf tmp_cat
	mkdir tmp_cat
	tar -x --bzip2 -f offline-package.tar.bz2 -C tmp_cat

offline-package.tar.bz2:
	echo "You must download the file http://www.gutenberg.org/feeds/offline-package.tar.bz2 before you can create the Project Gutenberg catalog."
	exit 1

lucicat-manual.epub: manual/lucicat-manual.xml manual/manual.xsl manual/fdl-1.3.xml manual/docbook-xsl
	${DB2EPUB} -s ${PWD}/manual/manual.xsl ${PWD}/manual/lucicat-manual.xml
	${EPUBTWEAK} --uuid lucicat-manual.epub

manual/docbook-xsl:
	ln -sf ${DBXSLHOME} manual/docbook-xsl

HOST=`grep db_host lucicat.ini | cut -f 2 -d' '`
NAME=`grep db_name lucicat.ini | cut -f 2 -d' '`
USER=`grep db_user lucicat.ini | cut -f 2 -d' '`
PASS=`grep db_pass lucicat.ini | cut -f 2 -d' '`

dump-my:
	mysqldump --add-drop-table -h${HOST} -u${USER} -p${PASS} ${NAME} > ${NAME}.sql
	gzip -9 ${NAME}.sql

dump-lite:
	sqlite3 ${NAME}.sqlite .dump > temp.sql
	tools/lucicat-export.py temp.sql ${NAME}.sql
	gzip -9 ${NAME}.sql
	rm temp.sql

clean:
	-find -name '*~' -print0 | xargs -n1 -0 rm
	-rm -f manual/docbook-xsl
	-rm -f tools/*.pyc

realclean: clean
	-rm -rf tmp_cat catalog.rdf epub_urls.txt
