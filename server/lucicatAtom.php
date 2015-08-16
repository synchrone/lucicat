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

class Lucicat_Container {
    protected $namespaces = array();
    protected $stylesheet = NULL;
    protected $source_uri = NULL;
    protected $id = NULL;
    protected $title = NULL;
    protected $subtitle = NULL;
    protected $updated = NULL;
    protected $rights = NULL;
    protected $icon = NULL;
    protected $authors = array();
    protected $links = array();
    protected $languages = array();
    protected $custom = array();

    public function add_namespace($prefix, $uri) {
	$this->namespaces[] = array("prefix" => $prefix,
				    "uri" => $uri);
    }

    public function add_dcterms_namespace() {
	$this->namespaces[] = array("prefix" => "dcterms",
				    "uri" => "http://purl.org/dc/terms/");
    }

    public function add_luci_namespace() {
	$this->namespaces[] = array("prefix" => "luci",
				    "uri" => "http://lucidor.org/-/x-opds/");
    }

    public function add_opensearch_namespace() {
	$this->namespaces[] = array("prefix" => "opensearch",
				    "uri" => "http://a9.com/-/spec/opensearch/1.1/");
    }

    public function add_xsi_namespace() {
	$this->namespaces[] = array("prefix" => "xsi",
				    "uri" => "http://www.w3.org/2001/XMLSchema-instance");
    }

    public function set_stylesheet($stylesheet) {
	$this->stylesheet = $stylesheet;
    }

    public function set_source_uri($uri) {
	$this->source_uri = $uri;
    }

    public function set_id($id = NULL) {
	if ($id)
	    $this->id = $id;
	else
	    $this->id = "urn:uuid:" . uuid4_gen();
    }

    public function set_title($title) {
        $this->title = $title;
    }

    public function set_subtitle($subtitle) {
        $this->subtitle = $subtitle;
    }

    public function set_updated($date = NULL) {
	if ($date)
	    $this->updated = $date;
	else
	    $this->updated = date(DATE_ATOM);
    }

    public function set_rights($rights) {
        $this->rights = $rights;
    }

    public function set_icon($uri) {
        $this->icon = $uri;
    }

    public function add_author($name, $email = NULL, $uri = NULL) {
	$this->authors[] = array("name" => $name,
				 "email" => $email,
				 "uri" => $uri);
    }

    public function add_link($href, $rel = NULL, $type, $title = NULL) {
	$this->links[] = array("href" => $href,
			       "rel" => $rel,
			       "type" => $type,
			       "title" => $title);
    }

    public function add_dcterms_language($lang, $label = NULL) {
	$this->languages[] = array("lang" => $lang,
				   "label" => $label);
    }

    public function add_custom($custom) {
	$this->custom[] = $custom;
    }

    protected function output_header($pp, &$var) {
	if ($var !== NULL)
	    return;

	if ($this->stylesheet)
	    // Needed to prevent web browsers from ignoring the stylesheet
	    header("Content-Type: application/xml");
	else
	    header("Content-Type: application/atom+xml");

	echo "<?xml version='1.0' encoding='UTF-8'?>\n";
	if ($this->stylesheet) {
	    echo "<?xml-stylesheet type='text/xsl' href='" .
		my_escape($this->stylesheet) . "'?>\n";
	}

	$text = "";
	if ($this->source_uri) {
	    $text = "     This feed was created with Lucicat (http://lucidor.org/lucicat/).\n" .
		"     Lucicat is released under the GNU Affero General Public License.\n" .
		"     The source code for this application is available from\n" .
		"     " . my_escape($this->source_uri) . "\n";
	}

	if ($this->stylesheet || $text) {
	    /* This comment is needed to prevent certain idiotic
	       web browsers from ignoring the stylesheet. */
	    echo "<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n";
	    $n = 0;
	    $st = "";
	    if ($this->stylesheet) {
		$st = "     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n";
		$n = ceil((512 - strlen($text) - strlen($st) * 2) / strlen($st) / 2);
		echo str_repeat($st, $n);
	    }
	    echo $text;
	    echo str_repeat($st, $n);
	    echo "     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->\n";
	}
    }

    protected function output_container($pp, $level, &$var) {
	if ($this->id)
	    pretty_print("<id>" . my_escape($this->id) . "</id>",
			 $pp, $level, $var);
	if ($this->title)
	    pretty_print("<title>" . my_escape($this->title) . "</title>",
			 $pp, $level, $var);
	if ($this->subtitle)
	    pretty_print("<subtitle>" . my_escape($this->subtitle) .
			 "</subtitle>", $pp, $level, $var);

	foreach ($this->authors as &$author) {
	    pretty_print("<author>", $pp, $level, $var);
	    pretty_print("<name>" . my_escape($author["name"]) . "</name>",
			 $pp, $level + 1, $var);
	    if ($author["email"])
		pretty_print("<email>" . my_escape($author["email"]) .
			     "</email>", $pp, $level + 1, $var);
	    if ($author["uri"])
		pretty_print("<uri>" . my_escape($author["uri"]) . "</uri>",
			     $pp, $level + 1, $var);
	    pretty_print("</author>", $pp, $level, $var);
	}
	unset($author);

	if ($this->updated)
	    pretty_print("<updated>" . my_escape($this->updated) . "</updated>",
			 $pp, $level, $var);

	if ($this->rights)
	    pretty_print("<rights>" . my_escape($this->rights) . "</rights>",
			 $pp, $level, $var);

	if ($this->icon)
	    pretty_print("<icon>" . my_escape($this->icon) . "</icon>",
			 $pp, $level, $var);

	foreach ($this->links as &$link) {
	    $str = "<link href='" . my_escape($link["href"]) . "'";
	    if ($link["rel"])
		$str .= " rel='" . my_escape($link["rel"]) . "'";
	    if ($link["type"])
		$str .= " type='" . my_escape($link["type"]) . "'";
	    if ($link["title"])
		$str .= " title='" . my_escape($link["title"]) . "'";
	    $str .= "/>";
	    pretty_print($str, $pp, $level, $var);
	}
	unset($link);

	foreach ($this->languages as &$lang) {
	    $str = "<dcterms:language";
	    if ($lang["label"])
		$str .= " luci:label='" . my_escape($lang["label"]) . "'";
	    $str .= ">" . my_escape($lang["lang"]) . "</dcterms:language>";
	    pretty_print($str, $pp, $level, $var);
	}
	unset($lang);

	foreach ($this->custom as &$custom)
	    pretty_print($custom, $pp, $level, $var);
	unset($custom);
    }
}

class Lucicat_Feed extends Lucicat_Container {
    protected $entries = array();

    public function set_opensearch($ipp, $si, $sp, $total) {
	$this->opensearch = array("itemsPerPage" => $ipp,
				  "startIndex" => $si,
				  "startPage" => $sp,
				  "totalResults" => $total);
    }

    public function create_entry() {
	$entry = new Lucicat_Entry();
	$this->entries[] = $entry;
	return $entry;
    }

    public function output($pp = TRUE, &$var = NULL) {
	parent::output_header($pp, $var);

	$str = "<feed xmlns='http://www.w3.org/2005/Atom'";
	foreach ($this->namespaces as &$ns)
	    $str .= " xmlns:" . $ns["prefix"] . "='" . $ns["uri"] . "'";
	unset($ns);
	$str .= ">";
	pretty_print($str, $pp, 0, $var);

	$str = "<generator uri='http://lucidor.org/lucicat/'>Lucicat</generator>";
	pretty_print($str, $pp, 1, $var);

	parent::output_container($pp, 1, $var);

	if ($this->opensearch) {
	    if ($this->opensearch["itemsPerPage"])
		pretty_print("<opensearch:itemsPerPage>" .
			     $this->opensearch["itemsPerPage"] .
			     "</opensearch:itemsPerPage>", $pp, 1, $var);
	    if ($this->opensearch["startIndex"])
		pretty_print("<opensearch:startIndex>" .
			     $this->opensearch["startIndex"] .
			     "</opensearch:startIndex>", $pp, 1, $var);
	    if ($this->opensearch["startPage"])
		pretty_print("<opensearch:startPage>" .
			     $this->opensearch["startPage"] .
			     "</opensearch:startPage>", $pp, 1, $var);
	    if ($this->opensearch["totalResults"])
		pretty_print("<opensearch:totalResults>" .
			     $this->opensearch["totalResults"] .
			     "</opensearch:totalResults>", $pp, 1, $var);
	}

	foreach ($this->entries as &$ent)
	    $ent->output_entry($pp, 1, $var);
	unset($ent);

	pretty_print("</feed>", $pp, 0, $var);
    }
}

class Lucicat_Entry extends Lucicat_Container {
    protected $issued = NULL;
    protected $publisher = NULL;
    protected $categories = array();
    protected $subjects = array();
    protected $summaries = array();

    public function set_issued($date) {
	$this->issued = $date;
    }

    public function set_publisher($publisher) {
        $this->publisher = $publisher;
    }

    public function add_category($term, $scheme = NULL, $label = NULL) {
	$this->categories[] = array("term" => $term,
				    "scheme" => $scheme,
				    "label" => $label);
    }

    public function add_subject($subject, $type = NULL) {
	$this->subjects[] = array("subject" => $subject,
				  "type" => $type);
    }

    public function add_summary($summary, $type = "text") {
	$this->summaries[] = array("summary" => $summary,
				   "type" => $type);
    }

    public function output($pp = TRUE, &$var = NULL) {
	parent::output_header($pp, $var);

	$str = "<entry xmlns='http://www.w3.org/2005/Atom'";
	foreach ($this->namespaces as &$ns)
	    $str .= " xmlns:" . $ns["prefix"] . "='" . $ns["uri"] . "'";
	unset($ns);
	$str .= ">";
	pretty_print($str, $pp, 0, $var);

	$str = "<generator uri='http://lucidor.org/lucicat/'>Lucicat</generator>";
	pretty_print($str, $pp, 1, $var);

	$this->output_container($pp, 0, $var);

	pretty_print("</entry>", $pp, 0, $var);
    }

    public function output_entry($pp, $level, &$var) {
	pretty_print("<entry>", $pp, $level, $var);
	$this->output_container($pp, $level, $var);
	pretty_print("</entry>", $pp, $level, $var);
    }

    protected function output_container($pp, $level, &$var) {
	parent::output_container($pp, $level + 1, $var);
	if ($this->issued)
	    pretty_print("<dcterms:issued>" . $this->issued .
			 "</dcterms:issued>", $pp, $level + 1, $var);
	if ($this->publisher)
	    pretty_print("<dcterms:publisher>" . my_escape($this->publisher) .
			 "</dcterms:publisher>", $pp, $level + 1, $var);
	foreach ($this->categories as &$category) {
	    $str = "<category term='" . my_escape($category["term"]) . "'";
	    if ($category["scheme"])
		$str .= " scheme='" . my_escape($category["scheme"]) . "'";
	    if ($category["label"])
		$str .= " label='" . my_escape($category["label"]) . "'";
	    $str .= "/>";
	    pretty_print($str, $pp, $level + 1, $var);
	}
	unset($category);
	foreach ($this->subjects as &$subject) {
	    if ($subject["type"])
		pretty_print("<dcterms:subject xsi:type='" . $subject["type"] .
			     "'>" . my_escape($subject["subject"]) .
			     "</dcterms:subject>",
			     $pp, $level + 1, $var);
	    else
		pretty_print("<dcterms:subject>" .
			     my_escape($subject["subject"]) .
			     "</dcterms:subject>", $pp, $level + 1, $var);
	}
	unset($subject);
	foreach ($this->summaries as &$summary) {
	    pretty_print("<summary type='" . $summary["type"] . "'>" .
			 my_escape($summary["summary"]) . "</summary>",
			 $pp, $level + 1, $var);
	}
	unset($summary);
    }
}

/*
 * Generate uuid version 4
 * From http://www.ajaxray.com/blog/2008/02/06/php-uuid-generator-function/comment-page-1/#comment-2667
 * Can be initialized with: mt_srand(intval(microtime(TRUE) * 1000));
 * An alternative would be uuid_create() from the PECL uuid extension
 */
function uuid4_gen() {
    $b = md5(uniqid(mt_rand(), TRUE), TRUE);
    $b[6] = chr((ord($b[6]) & 0x0F) | 0x40);
    $b[8] = chr((ord($b[8]) & 0x3F) | 0x80);
    return implode("-", unpack("H8a/H4b/H4c/H4d/H12e", $b));
}

/*
 * Escape special html characters
 */
function my_escape($data) {
    return htmlspecialchars($data, ENT_QUOTES, "UTF-8");
}

/*
 * Output string with indentation
 */
function pretty_print($str, $pp, $level, &$var = NULL) {
    if ($var === NULL) {
	if ($pp)
	    echo str_repeat("  ", $level) . $str . "\n";
	else
	    echo $str;
    } else {
	if ($pp)
	    $var .= str_repeat("  ", $level) . $str . "\n";
	else
	    $var .= $str;
    }
}

?>
