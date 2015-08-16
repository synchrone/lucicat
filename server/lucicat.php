<?php

  /*
    Lucicat - OPDS catalog system
    Copyright © 2009  Mikael Ylikoski

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
  */

require_once 'lucicatAtom.php';
require_once basename($_SERVER['SCRIPT_NAME'], '.php') . '_settings.php';

/*
 * Disable magic_quotes_gpc at runtime
 * From: http://en.php-resource.de/handbuch/security.magicquotes.disabling.htm
 */
if (get_magic_quotes_gpc()) {
    function stripslashes_deep($value) {
        $value = is_array($value) ?
	    array_map('stripslashes_deep', $value) :
	    stripslashes($value);
        return $value;
    }

    //$_POST = array_map('stripslashes_deep', $_POST);
    $_GET = array_map('stripslashes_deep', $_GET);
    //$_COOKIE = array_map('stripslashes_deep', $_COOKIE);
    //$_REQUEST = array_map('stripslashes_deep', $_REQUEST);
}

if (!$config_host)
    $config_host = 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['PHP_SELF'];
if (!$config_main)
    $config_main = $config_host;

/*
 * Get parameters
 */
$browse = urldecode($_GET['browse']);
if ($browse == 'opensearch') {
    generate_opensearch();
    exit();
}
$query = $_GET['query'];
$searchTerms = urldecode($query);
$sort = $_GET['sort'];
$language = $_GET['language'];
$xlanguage = $_GET['xlanguage'];
$locale = $_GET['locale'];
$ipp = $_GET['ipp'];
$limit = $ipp;	// $limit is always numeric
if (!$limit || !is_numeric($limit) || ($limit > 50))
    $limit = 20;
$first = $_GET['fi'];	// $first is always numeric
if (!$first || !is_numeric($first))
    $first = 1;
$style = $_GET['style'];

$use_stylesheet = FALSE;
$accept = $_SERVER['HTTP_ACCEPT'];
if ((strpos($accept, 'application/xml') >= 0) &&
    (strpos($accept, 'application/atom+xml') === FALSE))
    $use_stylesheet = TRUE;

$start_url = $config_host;
$base_template = $config_host . '?';
if ($style == 'html') {
    $base_template .= 'style=html&';
    $start_url .= '?style=html';
}

// Dictionary to use as cache for code=>language pairs
$language_cache = array();

/*
 * Get mode
 */

$mode = 'main';
$subtitle = '';
if (array_key_exists('query', $_GET)) {
    $mode = 'query';
    $subtitle = 'Search: ' . $searchTerms;
}

if ($browse) {
    $parameter = 'Luci';	// Default nonsense value
    if ($browse == 'authors') {
	$mode = 'author_initials';
	$subtitle = 'Authors';
    } elseif (substr($browse, 0, 8) == 'authors:') {
	$mode = 'authors';
	if (strlen($browse) >= 9)
	    $parameter = substr($browse, 8);
	$subtitle = 'Authors: ' . $parameter;
    } elseif ($browse == 'titles') {
	$mode = 'title_initials';
	$subtitle = 'Titles';
    } elseif (substr($browse, 0, 7) == 'titles:') {
	$mode = 'titles';
	if (strlen($browse) >= 8)
	    $parameter = substr($browse, 7);
	$subtitle = 'Titles: ' . $parameter;
    } elseif ($browse == 'languages') {
	$mode = 'languages';
	$subtitle = 'Languages';
    } elseif ($browse == 'subjects') {
	$mode = 'subjects';
	$subtitle = 'Subjects';
    } elseif ($browse == 'crawlable') {
	$mode = 'crawlable';
	$limit = $ipp;
	if (!$limit || !is_numeric($limit) || ($limit > 500))
	    $limit = 500;
	$subtitle = 'Crawlable';
    } elseif ($browse == 'all') {
	// NOTE 'all' is equal to 'titles:*'
	$mode = 'all';
	$subtitle = 'All';
    } elseif (substr($browse, 0, 5) == 'book:') {
	$mode = 'book';
	if (strlen($browse) >= 6)
	    $parameter = substr($browse, 5);
    // if ($browse == 'opensearch') has already been checked
    }
    if ($mode != 'query')
	$query = $browse;
}

/*
 * Connect to database
 */
$mysqli = new mysqli($db_addr, $db_user, $db_pass, $db_name);
if ($mysqli->connect_error)
    exit();
$mysqli->set_charset('UTF8');

/*
 * Handle simple cases
 */
if ($mode == 'main') {
    $opds = generate_main_feed();
    $mysqli->close();
    output($opds);
    exit();
} elseif ($mode == 'book') {
    $opds = generate_book($parameter);
    $mysqli->close();
    output($opds);
    exit();
}

/*
 * Parse query and construct SQL statement
 */
if ($mode == 'query') {
    $ql = parse_compound_query($searchTerms);
    if ($language)
	$ql[] = array(0 => 'language', 1 => $language);
    if ($xlanguage)
	$ql[] = array(0 => 'xlanguage', 1 => $xlanguage);
    $stat = get_sql_for_query($ql);
} elseif ($mode == 'author_initials') {
    $stat = get_sql_for_author_initials();
} elseif ($mode == 'authors') {
    $stat = get_sql_for_authors($parameter);
} elseif ($mode == 'title_initials') {
    $stat = get_sql_for_title_initials();
} elseif ($mode == 'titles') {
    $stat = get_sql_for_titles($parameter);
} elseif ($mode == 'languages') {
    $stat = get_sql_for_languages();
} elseif ($mode == 'subjects') {
    $stat = get_sql_for_subjects();
} elseif ($mode == 'crawlable' || $mode == 'all') {
    $stat = 'SELECT * FROM ' . $db_prefix . 'books';
}

/*
 * Execute database query to get number of results
 */
$result = $mysqli->query($stat);
$numrows = $result->num_rows;
$result->close();
$last = max(min($first + $limit - 1, $numrows), 0);
if ($first > $last)
    $first = $last;

$opds = create_feed($first, $last, $limit, $numrows, $mode, $query, $subtitle);

$order = '';
if ($sort == 'new')
    $order = 'ORDER BY updated DESC';
elseif ($sort == 'popular')
    $order = 'ORDER BY popularity ASC';

if ($mode == 'query') {
    if (!$order)
	$order = 'ORDER BY author ASC';
    add_entries_query($opds, $stat, $first, $limit, $order);
} elseif ($mode == 'author_initials') {
    add_entries_initials($opds, $stat, $first, $limit, $mode);
} elseif ($mode == 'authors') {
    add_entries_authors($opds, $stat, $first, $limit);
} elseif ($mode == 'title_initials') {
    add_entries_initials($opds, $stat, $first, $limit, $mode);
} elseif ($mode == 'titles') {
    if (!$order)
	$order = 'ORDER BY title ASC';
    add_entries_query($opds, $stat, $first, $limit, $order);
} elseif ($mode == 'languages') {
    add_entries_languages($opds, $stat, $first, $limit);
} elseif ($mode == 'subjects') {
    add_entries_subjects($opds, $stat, $first, $limit);
} elseif ($mode == 'crawlable') {
    if (!$order)
	$order = 'ORDER BY updated DESC';
    add_entries_query($opds, $stat, $first, $limit, $order);
} elseif ($mode == 'all') {
    if (!$order)
	$order = 'ORDER BY title ASC';
    add_entries_query($opds, $stat, $first, $limit, $order);
}

$mysqli->close();
output($opds);
exit();

/*
 * Get catalog url
 */
function get_url($kind, $searchTerms, $firstIndex = '', $order = '') {
    global $base_template, $sort, $limit;

    if (!$order)
	$order = $sort;
    $url = $base_template;
    if ($kind == 'query')
	$url .= 'query=' . $searchTerms;
    else
	$url .= 'browse=' . $searchTerms;
    #$url .= '&language=' . $language;
    #$url .= '&xlanguage=' . $xlanguage;
    #$url .= '&locale=' . $locale;
    $url .= '&sort=' . $order;
    $url .= '&ipp=' . $limit;
    $url .= '&fi=' . $firstIndex;
    return $url;
}

/*
 * Parse query string
 */
function parse_compound_query($searchTerms) {
    $res = array();
    while ($searchTerms) {
	$prefix = '';
	$phrase = '';
	if (preg_match('/^[a-z]+:/', $searchTerms, $matches)) {
	    $prefix = $matches[0];
	    $searchTerms = substr($searchTerms, strlen($matches[0]));
	}
	if (preg_match("/^\"(.*?[^\\\\])\"/", $searchTerms, $matches)) {
	    $phrase = $matches[1];
	    $searchTerms = substr($searchTerms, strlen($matches[0]));
	} elseif (preg_match('/^"(.*)/', $searchTerms, $matches)) {
	    // Missing ending "
	    $phrase = $matches[1];
	    $searchTerms = '';
	} elseif (preg_match('/^[^ \t\n]*/', $searchTerms, $matches)) {
	    $phrase = $matches[0];
	    $searchTerms = substr($searchTerms, strlen($matches[0]));
	}
	$phrase = str_replace(array("\\\"", "\\\\"), array("\"", "\\"), $phrase);
	if ($prefix or $phrase)
	    $res[] = array(0 => $prefix, 1 => $phrase);
	$searchTerms = preg_replace('/^[ \t\n]+/', '', $searchTerms, 1);
    }
    return $res;
}

/*
 * Create SQL statement from query
 */
function get_sql_for_query($ql) {
    global $mysqli, $db_prefix;

    $stat = 'SELECT * FROM ' . $db_prefix . 'books WHERE TRUE';

    foreach ($ql as &$value) {
	$st = $mysqli->real_escape_string($value[1]);

	if ($value[0] == 'author:') {
	    $stat .= ' AND (id IN (SELECT ' .
		$db_prefix . 'authors_books.book FROM ' .
		$db_prefix . 'authors INNER JOIN ' .
		$db_prefix . 'authors_books ON ' .
		$db_prefix . 'authors.id = ' .
		$db_prefix . "authors_books.author WHERE name LIKE '%" .
		$st . "%'))";
	} elseif ($value[0] == 'authoreq:') {
	    $stat .= ' AND (id IN (SELECT ' .
		$db_prefix . 'authors_books.book FROM ' .
		$db_prefix . 'authors INNER JOIN ' .
		$db_prefix . 'authors_books ON ' .
		$db_prefix . 'authors.id = ' .
		$db_prefix . "authors_books.author WHERE BINARY name = '" .
		$st . "'))";
	} elseif ($value[0] == 'title:') {
	    $stat .= " AND (title LIKE '%" . $st . "%')";
	} elseif ($value[0] == 'subject:') {
	    // FIXME maybe check label too
	    $stat .= ' AND (id IN (SELECT book FROM ' .
		$db_prefix . "categories WHERE term LIKE '%" . $st . "%'))";
	} elseif ($value[0] == 'subjecteq:') {
	    $stat .= ' AND (id IN (SELECT book FROM ' .
		$db_prefix . "categories WHERE BINARY term = '" . $st . "'))";
	} elseif ($value[0] == 'language:') {
	    $stat .= " AND (language LIKE '%|" . $st .
		"|%' OR language LIKE '%|" . $st . "-%')";
	} elseif ($value[0] == 'language') {
	    if ($st != '*')
		$stat .= " AND (language LIKE '%|" . $st .
		    "|%' OR language LIKE '%|" . $st . "-%')";
	} elseif ($value[0] == 'xlanguage') {
	    $langs = explode(' ', $value[1]);
	    $lang_st = 'FALSE';
	    foreach ($langs as &$lang) {
		if ($lang == '*') {
		    $lang_st = 'TRUE';
		    break;
		} else {
		    $st = $mysqli->real_escape_string($lang);
		    $lang_st .= " OR language LIKE '%|" . $st .
			"|%' OR language LIKE '%|" . $st . "-%'";
		}
	    }
	    unset($lang);
	    if ($lang_st == 'FALSE')
		$lang_st = 'TRUE';
	    $stat .= ' AND (' . $lang_st . ')';
	} elseif ($value[0] == '') {
	    if ($st == 'AND' || $st == 'OR') {
		// FIXME Just ignore them for now
	    } else {
		$stat .= " AND (author LIKE '%" . $st .
		    "%' OR title LIKE '%". $st ."%')";
	    }
	} else {	// Unknown filter
	    $stat .= ' AND FALSE';
	}
    }
    unset($value);
    return $stat;
}

/*
 * Create SQL statement
 */
function get_sql_for_author_initials() {
    global $db_prefix;

    return 'SELECT DISTINCT initial FROM ' . $db_prefix . 'authors';
}

/*
 * Create SQL statement
 */
function get_sql_for_authors($parameter) {
    global $mysqli, $db_prefix;

    if ($parameter == '*')
	return 'SELECT * FROM ' . $db_prefix . 'authors';
    else
	return "SELECT * FROM " . $db_prefix . "authors WHERE initial = '" .
	    $mysqli->real_escape_string($parameter) . "'";
}

/*
 * Create SQL statement
 */
function get_sql_for_title_initials() {
    global $db_prefix;

    return 'SELECT DISTINCT initial FROM ' . $db_prefix . 'titles';
}

/*
 * Create SQL statement
 */
function get_sql_for_titles($parameter) {
    global $mysqli, $db_prefix;

    if ($parameter == '*')
	return 'SELECT * FROM ' . $db_prefix . 'books';
    else
	return 'SELECT * FROM ' . $db_prefix . 'titles INNER JOIN ' .
	    $db_prefix . 'books ON ' .
	    $db_prefix . 'titles.book = ' .
	    $db_prefix . "books.id WHERE initial = '" .
	    $mysqli->real_escape_string($parameter) . "'";
}

/*
 * Create SQL statement
 */
function get_sql_for_languages() {
    global $db_prefix;

    return 'SELECT code, label FROM ' . $db_prefix . 'languages';
}

/*
 * Create SQL statement
 */
function get_sql_for_subjects() {
    global $db_prefix;

    return 'SELECT DISTINCT term FROM ' . $db_prefix . 'categories';
}

/*
 * Create feed
 */
function create_feed($first, $last, $limit, $numrows, $mode, $query, $subtitle) {
    global $base_template;
    global $start_url;
    global $config_main;
    global $config_icon;
    global $config_source;
    global $config_title;

    $opds = new Lucicat_Feed();
    $opds->set_source_uri($config_source);
    $opds->add_dcterms_namespace();
    $opds->add_luci_namespace();
    $opds->add_opensearch_namespace();
    $opds->add_xsi_namespace();
    $opds->set_title($config_title);
    if ($subtitle)
	$opds->set_subtitle($subtitle);
    $opds->set_id();	// FIXME Should create id from uri instead
    $opds->set_updated();
    $opds->add_author('Lucicat', NULL, 'http://lucidor.org/lucicat/');

    if ($config_icon)
	$opds->set_icon($config_icon);

    $opds->add_link($base_template . 'browse=opensearch', 'search',
		    'application/opensearchdescription+xml');

    $opds->add_link($start_url, 'start', 'application/atom+xml');

    if ($first > 1) {
	$uri = get_url($mode, $query, $firstIndex = '1');
	$opds->add_link($uri, 'first', 'application/atom+xml');

	$pfirst = $first - $limit;
	if ($pfirst < 1)
	    $pfirst = 1;
	$uri = get_url($mode, $query, $firstIndex = $pfirst);
	$opds->add_link($uri, 'previous', 'application/atom+xml');
    }

    if ($last < $numrows) {
	$uri = get_url($mode, $query, $firstIndex = $first + $limit);
	$opds->add_link($uri, 'next', 'application/atom+xml');

	$uri = get_url($mode, $query, $firstIndex = floor(($numrows - 1) / $limit) * $limit + 1);
	$opds->add_link($uri, 'last', 'application/atom+xml');
    }

    $opds->set_opensearch($limit, $first, 0, $numrows);
    return $opds;
}

/*
 * Escape string for use in quoted phrase
 */
function escape_phrase($phrase) {
    return str_replace(array("\\", "\""), array("\\\\", "\\\""), $phrase);
}

function get_language_label($code) {
    global $mysqli, $db_prefix, $language_cache;

    if ($language_cache[$code])
	return $language_cache[$code];

    $label = $code;
    $result = $mysqli->query('SELECT label FROM ' . $db_prefix .
			     "languages WHERE code = '" .
			     $mysqli->real_escape_string($code) . "'");
    if ($result) {
	$obj = $result->fetch_object();
	$label = $obj->label;
	$result->close();
    }
    $language_cache[$code] = $label;
    return $label;
}

function populate_entry(Lucicat_Entry $entry, $obj, $partial = FALSE) {
    global $mysqli, $db_prefix;

    $entry->set_id($obj->xid);
    $entry->set_title($obj->title);
    $entry->set_updated($obj->updated);
    if ($obj->language) {
	$langs = explode('|', $obj->language);
	foreach ($langs as &$lang) {
	    if ($lang) {
		$label = get_language_label($lang);
		$entry->add_dcterms_language($lang, $label);
	    }
	}
	unset($lang);
    }
    if ($obj->publisher)
	$entry->set_publisher($obj->publisher);
    if ($obj->rights)
	$entry->set_rights($obj->rights);
    if ($obj->issued)
	$entry->set_issued($obj->issued);
    if ($obj->summary)
    	$entry->add_summary($obj->summary, 'text');
    if ($obj->summary_html)
    	$entry->add_summary($obj->summary_html, 'html');

    $book_id = $mysqli->real_escape_string($obj->id);

    $result = $mysqli->query('SELECT * FROM ' . $db_prefix .
			     'links WHERE book = ' . $book_id);
    if ($result) {
	while ($obj = $result->fetch_object())
	    $entry->add_link($obj->href, $obj->rel, $obj->type, $obj->title);
	$result->close();
    }

    $result = $mysqli->query('SELECT * FROM ' . $db_prefix .
			     'authors INNER JOIN ' . $db_prefix .
			     'authors_books ON ' . $db_prefix .
			     'authors.id = ' . $db_prefix .
			     'authors_books.author WHERE book = ' . $book_id);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry->add_author($obj->name);

	    $uri = get_url('query', 'authoreq:' .
			   urlencode('"' . escape_phrase($obj->name) . '"'),
			   $firstIndex = '1');
	    $entry->add_link($uri, 'related',
			     'application/atom+xml',
			     'Show books by ' . $obj->name);
	}
	$result->close();
    }

    $result = $mysqli->query('SELECT * FROM ' . $db_prefix .
			     'categories WHERE book = ' . $book_id);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    if ($obj->is_subject == 1)
		$entry->add_subject($obj->term, $obj->scheme);
	    else
		$entry->add_category($obj->term, $obj->scheme, $obj->label);
	}
	$result->close();
    }
}

/*
 * Add entries
 */
function add_entries_query(Lucicat_Feed $opds, $stat, $first, $limit, $order) {
    global $mysqli;

    $result = $mysqli->query($stat . ' ' . $order . ' LIMIT ' .
			     ($first - 1) . ', ' . $limit);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry = $opds->create_entry();
	    populate_entry($entry, $obj);
	}
	$result->close();
    }
}

/*
 * Add author entries
 */
function add_entries_authors(Lucicat_Feed $opds, $stat, $first, $limit) {
    global $mysqli;

    $result = $mysqli->query($stat . ' ORDER BY name ASC LIMIT ' .
			     ($first - 1) . ', ' . $limit);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry = $opds->create_entry();
	    $entry->set_title($obj->name);
	    $uri = get_url('query', 'authoreq:' .
			   urlencode('"' . escape_phrase($obj->name) . '"'),
			   $firstIndex = '1');
	    $entry->set_id($uri . '&cat=entry');
	    $entry->set_updated();
	    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
	}
	$result->close();
    }
}

/*
 * Add subject entries
 */
function add_entries_subjects(Lucicat_Feed $opds, $stat, $first, $limit) {
    global $mysqli;

    $result = $mysqli->query($stat . ' ORDER BY term ASC LIMIT ' .
			     ($first - 1) . ', ' . $limit);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry = $opds->create_entry();
	    $entry->set_title($obj->term);
	    $uri = get_url('query', 'subjecteq:' .
			   urlencode('"' . escape_phrase($obj->term) . '"'),
			   $firstIndex = '1');
	    $entry->set_id($uri . '&cat=entry');
	    $entry->set_updated();
	    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
	}
	$result->close();
    }
}

/*
 * Add language entries
 */
function add_entries_languages(Lucicat_Feed $opds, $stat, $first, $limit) {
    global $mysqli;

    $result = $mysqli->query($stat . ' ORDER BY label ASC LIMIT ' .
			     ($first - 1) . ', ' . $limit);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry = $opds->create_entry();
	    $entry->set_title($obj->label);
	    $uri = get_url('query', 'language:' .
			   urlencode('"' . escape_phrase($obj->code) . '"'),
			   $firstIndex = '1');
	    $entry->set_id($uri . '&cat=entry');
	    $entry->set_updated();
	    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
	}
	$result->close();
    }
}

function add_entries_initials(Lucicat_Feed $opds, $stat, $first, $limit, $mode) {
    global $mysqli;

    $result = $mysqli->query($stat . ' ORDER BY initial ASC LIMIT ' .
			     ($first - 1) . ', ' . $limit);
    if ($result) {
	while ($obj = $result->fetch_object()) {
	    $entry = $opds->create_entry();
	    $entry->set_title($obj->initial);
	    if ($mode == 'author_initials')
		$uri = get_url('browse', 'authors:' . urlencode($obj->initial),
			       $firstIndex = '1');
	    else	// title_initials
		$uri = get_url('browse', 'titles:' . urlencode($obj->initial),
			       $firstIndex = '1');
	    $entry->set_id($uri . '&cat=entry');
	    $entry->set_updated();
	    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
	}
	$result->close();
    }
}

/*
 * Generate main feed
 */
function generate_main_feed() {
    global $mysqli;
    global $db_prefix;
    global $base_template;
    global $start_url;
    global $config_host;
    global $config_icon;
    global $config_popular;
    global $config_source;
    global $config_subtitle;
    global $config_title;

    $opds = new Lucicat_Feed();
    $opds->set_source_uri($config_source);
    $opds->set_title($config_title);
    $opds->set_id($config_host);
    if ($config_subtitle)
	$opds->set_subtitle($config_subtitle);
    $opds->set_updated();
    $opds->add_author('Lucicat', NULL, 'http://lucidor.org/lucicat/');

    if ($config_icon)
	$opds->set_icon($config_icon);

    $opds->add_link($base_template . 'browse=opensearch',
		    'search',
		    'application/opensearchdescription+xml');

    /*
    $opds->add_link($start_url,
		    'start',
		    'application/atom+xml');
    */

    $opds->add_link($base_template . 'browse=crawlable',
		    'http://opds-spec.org/crawlable',
		    'application/atom+xml');

    $opds->add_link($base_template . 'browse=all&sort=new',
		    'http://opds-spec.org/sort/new',
		    'application/atom+xml');

    if ($config_popular)
	$opds->add_link($base_template . 'browse=all&sort=popular',
			'http://opds-spec.org/sort/popular',
			'application/atom+xml');

    /*
    $result = $mysqli->query("SHOW TABLES LIKE '" . $db_prefix . "_featured'");
    if ($result->num_rows == 1)
	$opds->add_link($base_template . 'browse=featured',
			'http://opds-spec.org/sort/featured',
			'application/atom+xml');
    $result->close();
    */

    /* Authors link */
    $entry = $opds->create_entry();
    $entry->set_title('Authors');
    $uri = $base_template . 'browse=authors:*';
    $result = $mysqli->query('SELECT id FROM ' . $db_prefix . 'authors');
    if ($result->num_rows > 20)
	$uri = $base_template . 'browse=authors';
    $result->close();
    $entry->set_id($uri . '&cat=entry');
    $entry->set_updated();
    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);

    /* Titles link */
    $entry = $opds->create_entry();
    $entry->set_title('Titles');
    $uri = $base_template . 'browse=titles:*';
    $result = $mysqli->query('SELECT id FROM ' . $db_prefix . 'books');
    if ($result->num_rows > 20)
	$uri = $base_template . 'browse=titles';
    $result->close();
    $entry->set_id($uri . '&cat=entry');
    $entry->set_updated();
    $entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);

    /* Subjects link */
    $result = $mysqli->query('SELECT id FROM ' . $db_prefix . 'categories');
    if ($result->num_rows > 1) {
	$entry = $opds->create_entry();
	$entry->set_title('Subjects');
	$uri = $base_template . 'browse=subjects';
	$entry->set_id($uri . '&cat=entry');
	$entry->set_updated();
	$entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
    }
    $result->close();

    /* Languages link */
    $result = $mysqli->query('SELECT code FROM ' . $db_prefix . 'languages');
    if ($result->num_rows > 1) {
	$entry = $opds->create_entry();
	$entry->set_title('Languages');
	$uri = $base_template . 'browse=languages';
	$entry->set_id($uri . '&cat=entry');
	$entry->set_updated();
	$entry->add_link($uri, 'alternate', 'application/atom+xml', NULL);
    }
    $result->close();

    return $opds;
}

function generate_book($bid) {
    global $db_prefix;
    global $mysqli;
    global $config_source;

    $result = $mysqli->query('SELECT * FROM ' . $db_prefix .
			     "books WHERE xid = '" .
			     $mysqli->real_escape_string($bid) . "'");
    if ($result) {
	if ($obj = $result->fetch_object()) {
	    $entry = new Lucicat_Entry();
	    $entry->set_source_uri($config_source);
	    $entry->add_dcterms_namespace();
	    $entry->add_opensearch_namespace();
	    $entry->add_xsi_namespace();
	    populate_entry($entry, $obj);
	}
	$result->close();
    }
    return $entry;
}

function output(&$opds) {
    global $style;
    global $use_stylesheet;
    global $config_stylesheet;

    if (!$opds) {
	// FIXME
    } elseif ($style == 'html' and $config_stylesheet) {
	$var = '';
	$opds->output(FALSE, $var);
	$doc = new DOMDocument();
	$doc->loadXML($var);
	$var = '';
	$xsl = new DOMDocument();
	$xsl->load($config_stylesheet);
	$proc = new XSLTProcessor();
	$proc->importStyleSheet($xsl);
	$proc->setParameter(NULL, 'style', $style);
	header('Content-Type: application/xhtml+xml');
	echo $proc->transformToXML($doc);
    } else {
	if ($use_stylesheet and $config_stylesheet)
	    $opds->set_stylesheet($config_stylesheet);
	$opds->output();
    }
}

function generate_opensearch() {
    global $config_host;
    global $config_title;
    global $config_icon;

    header('Content-Type: application/xml');
    echo "<?xml version='1.0' encoding='UTF-8'?>\n";
    echo "<OpenSearchDescription xmlns='http://a9.com/-/spec/opensearch/1.1/' xmlns:luci='http://lucidor.org/-/x-opds/'>\n";
    echo "  <ShortName>" . $config_title . "</ShortName>\n";
    #if ($config_description)
    #	echo "  <Description>" . $config_description . "</Description>\n";
    echo "  <InputEncoding>UTF-8</InputEncoding>\n";
    echo "  <OutputEncoding>UTF-8</OutputEncoding>\n";
    if ($config_icon)
	echo "  <Image>" . $config_icon . "</Image>\n";

    $str = "?query={searchTerms}";
    #if ($config_plain_language)
    #	$str .= "&language={language?}";
    #else
    #	$str .= "&xlanguage={luci:language?}";

    echo "  <Url type='application/atom+xml' template='" . $config_host . $str . "' luci:querysyntax='compound author title subject language'/>\n";
    //echo "  <Url type='application/atom+xml' template='" . $config_host . "?query={searchTerms}&language={luci:language?}&locale={luci:locale?}' luci:querysyntax='compound author title language'/>\n";
    if ($config_plain_language) {
	// FIXME unique Language elements
    }
    echo "</OpenSearchDescription>\n";
}

?>
