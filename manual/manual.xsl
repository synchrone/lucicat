<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:h="http://www.w3.org/1999/xhtml"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:import href="docbook-xsl/epub/docbook.xsl"/>
  <xsl:param name="generate.toc"/>

  <xsl:template match="application">
    <h:span style="font-variant: small-caps;"><xsl:call-template name="inline.charseq"/></h:span>
  </xsl:template>
</xsl:stylesheet>
