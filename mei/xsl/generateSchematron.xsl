<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
    xmlns:mei="http://www.music-encoding.org/ns/mei"
    xmlns:sch="http://purl.oclc.org/dsdl/schematron"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:uuid="java:java.util.UUID"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns:local="no:where"
    exclude-result-prefixes="xs math xd mei tei uuid sch local"
    version="3.0">
    <xd:doc scope="stylesheet">
        <xd:desc>
            <xd:p><xd:b>Created on:</xd:b> Sep 9, 2015</xd:p>
            <xd:p><xd:b>Author:</xd:b> Johannes Kepper</xd:p>
            <xd:p>
                This stylesheet is operated on mei-page-based.xml.odd in rism-ch/libmei/mei/2013-11-05.
            </xd:p>
            <xd:p>
                It reads in rism-ch/libmei/tools/includes/vrv/config.yml, translates it into XML, and
                generates an ODD customization out of it. This ODD is then used to generate a corresponding
                RNG in a separate process.
            </xd:p>
        </xd:desc>
    </xd:doc>
    
    <xsl:output method="xml" indent="yes"/>
    
    <!-- this specifies the path to the config.yml file -->
    <xsl:param name="config.path.to.config.yml" select="'../../tools/includes/vrv/config.yml'" as="xs:string"/>
    
    <!-- this specifies the path to the mei source file (compiled odd) -->
    <xsl:param name="config.path.to.mei.source" select="'../2013-11-05/mei-page-based.xml.odd'" as="xs:string"/>
    
    <!-- complain about unsupported elements: -->
    <xsl:param name="complain.on.elements" select="false()" as="xs:boolean"/>
    
    <!-- complain about unsupported attributes: -->
    <xsl:param name="complain.on.attributes" select="true()" as="xs:boolean"/>
    
    <!-- comment on attributes: -->
    <xsl:param name="comment.on.attributes" select="false()" as="xs:boolean"/>
    
    
    <!-- this tries to read in the required files -->
    <xsl:variable name="config.yml" select="$config.path.to.config.yml" as="xs:string?"/>
    <xsl:variable name="mei.source" select="doc($config.path.to.mei.source)" as="node()?"/>
    
    <xsl:template match="/">
        <xsl:if test="not($config.yml)">
            <xsl:message terminate="yes" select="'config.yml is not available at ' || $config.path.to.config.yml || '. Processing terminated'"/>
        </xsl:if>
        <xsl:if test="not($mei.source)">
            <xsl:message terminate="yes" select="'mei source file is not available at ' || $config.path.to.mei.source || '. Processing terminated'"/>
        </xsl:if>
        
        <!-- convert config.yml to a simple xml dialect, without hierarchies first -->
        <xsl:variable name="prep1.config.xml" as="node()">
            <config>
                <!-- iterate over all lines of config.yml -->
                <xsl:for-each select="tokenize(unparsed-text($config.yml,'utf-8'),'\n')">
                    
                    <!-- if the line contains text (other than just three dashes), create a <line> element  -->
                    <xsl:if test="string-length(.) gt 0 and not(. = '---') and not(position() = 1)">
                        <line xml:id="{'g'||uuid:randomUUID()}">
                            
                            <xsl:attribute name="raw" select="."/>
                            
                            <xsl:variable name="normalized" select="normalize-space(.)" as="xs:string"/>
                            <xsl:variable name="indent.level" select="string-length(substring-before(.,$normalized))" as="xs:integer"/>
                            
                            <xsl:choose>
                                <xsl:when test="$indent.level = 0 and starts-with($normalized,'defaults:')">
                                    <xsl:attribute name="section" select="'defaults'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 0 and starts-with($normalized,'modules:')">
                                    <xsl:attribute name="section" select="'modules'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 0 and starts-with($normalized,'att-classes:')">
                                    <xsl:attribute name="section" select="'att-classes'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 0 and starts-with($normalized,'interfaces:')">
                                    <xsl:attribute name="section" select="'interfaces'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 0 and starts-with($normalized,'classes:')">
                                    <xsl:attribute name="section" select="'classes'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 2 and starts-with($normalized,'-')">
                                    <xsl:attribute name="id" select="replace(substring(.,9),'[^a-zA-Z\.\d]','')"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 4 and starts-with($normalized,'attributes:')">
                                    <xsl:attribute name="type" select="'attributes'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 4 and starts-with($normalized,'interfaces:')">
                                    <xsl:attribute name="type" select="'interfaces'"/>
                                </xsl:when>
                                <xsl:when test="$indent.level = 4 and starts-with($normalized,'att-classes:')">
                                    <xsl:attribute name="type" select="'att-classes'"/>
                                </xsl:when>
                                <xsl:when test="($indent.level = 4 or $indent.level = 6) and starts-with($normalized,'-')">
                                    <xsl:attribute name="type" select="'value'"/>
                                    <xsl:choose>
                                        <xsl:when test="contains($normalized,'[')">
                                            <xsl:variable name="entries" as="xs:string*">
                                                <xsl:analyze-string select="$normalized" regex='"([^"]*)"'>
                                                    <xsl:matching-substring>
                                                        <xsl:value-of select="regex-group(1)"/>
                                                    </xsl:matching-substring>
                                                </xsl:analyze-string>
                                            </xsl:variable>
                                            
                                            <value id="{$entries[1]}" comment="{$entries[2]}" schematron="{$entries[3]}"/>
                                            
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <value id="{if(contains(substring($normalized,3),' ')) then(substring-before(substring($normalized,3),' ')) else(substring($normalized,3))}" comment="{substring-after($normalized,'#')}" schematron=""/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                            </xsl:choose>
                        </line>
                    </xsl:if>
                </xsl:for-each>
            </config>
        </xsl:variable>
        
        <xsl:variable name="prep2.config.xml" as="node()">
            <xsl:apply-templates select="$prep1.config.xml" mode="prep2.config.xml"/>
        </xsl:variable>
        
        <xsl:variable name="config.xml" as="node()">
            <xsl:apply-templates select="$prep2.config.xml" mode="prep3.config.xml"/>
        </xsl:variable>
        
        
        <!-- all supported elements are listed -->
        <!-- all supported attribute classes are listed -->
        <!-- within attribute classes, only those attributes with restrictions are listed -->
        
        <xsl:variable name="all.elements" select="$mei.source//tei:elementSpec" as="node()*"/>
        <xsl:variable name="unsupported.elements" select="$all.elements[not(@ident = $config.xml//element/@ident)]" as="node()*"/>
        <xsl:variable name="supported.elements" select="$all.elements[@ident = $config.xml//element/@ident]" as="node()*"/>
        
        <xsl:variable name="commented.attributes" select="$config.xml//att-class/att[string-length(@desc) gt 0]" as="node()*"/>
        
        <xsl:variable name="schematron">
            <schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
                <ns uri="http://www.music-encoding.org/ns/mei" prefix="mei"/>
                <ns uri="http://www.w3.org/1999/xlink" prefix="xlink"/>
                <pattern>
                    
                    <!-- write schematron rules for elements -->
                    <xsl:if test="$complain.on.elements">
                        <xsl:for-each select="$unsupported.elements">
                            <!-- exlude mei and meiHead from checking -->
                            <xsl:if test="not(@ident = ('mei','meiHead','facsimile','front','back'))">
                                <!-- complain only about elements used outside of the header -->
                                <rule context="mei:{@ident}">
                                    <assert test="ancestor::mei:meiHead or ancestor::mei:facsimile or ancestor::mei:front or ancestor::mei:back">The element <xsl:value-of select="@ident"/> is currently not supported by Verovio.</assert>
                                </rule>
                            </xsl:if>
                            
                        </xsl:for-each>
                    </xsl:if>
                    
                    <!-- write schematron rules for unsupported attributes -->
                    <xsl:if test="$complain.on.attributes">
                        <xsl:for-each select="$supported.elements">
                            <xsl:variable name="current.element" select="." as="node()"/>
                            <xsl:variable name="element.config" select="$config.xml//element[@ident = $current.element/@ident]" as="node()"/>
                            <xsl:variable name="all.classes" select="local:getAttribute.classes($current.element)"/>
                            <xsl:variable name="supported.classes" as="xs:string*">
                                <xsl:sequence select="$element.config/supports[('att.' || @ident) = $all.classes]"/>
                                <xsl:for-each select="$element.config/supports[@ident = $config.xml//interface/@ident]">
                                    <xsl:variable name="interface.ident" select="@ident" as="xs:string"/>
                                    <xsl:variable name="interface" select="$config.xml//interface[@ident = $interface.ident]" as="node()"/>
                                    <xsl:for-each select="$interface/att-class">
                                        <xsl:value-of select="'att.' || @ident"/>
                                    </xsl:for-each>
                                </xsl:for-each>
                            </xsl:variable>
                            <xsl:variable name="unsupported.classes" select="$all.classes[not(. = $supported.classes)]" as="xs:string*"/>
                            <xsl:variable name="unsupported.attributes" as="xs:string*">
                                <xsl:for-each select="$unsupported.classes">
                                    <xsl:variable name="current.class.ident" select="." as="xs:string"/>
                                    <xsl:variable name="current.class" select="$mei.source//tei:classSpec[@ident = $current.class.ident]" as="node()"/>
                                    <xsl:sequence select="$current.class//tei:attDef/@ident"/>
                                </xsl:for-each>
                            </xsl:variable>
                            
                            <xsl:for-each select="$unsupported.attributes">
                                <xsl:variable name="current.attribute" select="." as="xs:string"/>
                                <xsl:message select="'attribute ' || $current.attribute || ' on ' || $current.element/@ident || ' is not supported'"></xsl:message>
                                <rule context="mei:{$current.element/@ident}/@{$current.attribute}">
                                    <assert test="false()">The attribute <xsl:value-of select="$current.attribute"/> on <xsl:value-of select="$current.element/@ident"/> is currently not supported by Verovio.</assert>
                                </rule>
                            </xsl:for-each>
                            
                        </xsl:for-each>
                    </xsl:if>
                    
                    <!-- write schematron rules for attributes  -->
                    <!-- TODO: this currently ignores the attribute classes -->
                    <xsl:if test="$comment.on.attributes">
                        <xsl:for-each select="$commented.attributes">
                            <rule context="@{@ident}">
                                <!-- when there is a schematron rule, use it. otherwise just expose a warning (instead of an error) -->
                                <xsl:choose>
                                    <xsl:when test="string-length(@schematron) gt 0">
                                        <assert test="@schematron"><xsl:value-of select="@desc"/></assert>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <assert test="false()" role="warn"><xsl:value-of select="@desc"/></assert>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </rule>
                        </xsl:for-each>
                    </xsl:if>
                    
                </pattern>
            </schema>
        </xsl:variable>
        
        <!-- write the schematron file to checkForSupport.sch -->
        <xsl:result-document href="../sch/checkVerovioCompatibility.sch">
            <xsl:copy-of select="$schematron"/>    
        </xsl:result-document>
        
    </xsl:template>
    
    <!-- this mode adds basic hierarchy to config.xml -->
    <xsl:template match="line" mode="prep2.config.xml">
        <xsl:if test="@section and @section = ('att-classes','interfaces','classes')">
            <xsl:variable name="current.id" select="@xml:id" as="xs:string"/>
            <xsl:variable name="next.id" select="(following-sibling::line[@section])[1]/@xml:id" as="xs:string?"/>
            <xsl:element name="{string(@section)}">
                <xsl:choose>
                    <xsl:when test="exists($next.id)">
                        <xsl:copy-of select="following-sibling::line[following-sibling::line[@xml:id = $next.id]]"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="following-sibling::line"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
        </xsl:if>
    </xsl:template>
    
    <!-- this mode will convert line elements to final hierarchies -->
    <xsl:template match="line" mode="prep3.config.xml">
        <xsl:variable name="this.id" select="@xml:id" as="xs:string"/>
        <xsl:choose>
            <xsl:when test="parent::att-classes and @id">
                <att-class ident="{@id}">
                    <xsl:for-each select="following-sibling::line[preceding-sibling::line[@id][1]/@xml:id = $this.id]/value">
                        <att ident="{@id}" desc="{@comment}" schematron="{@schematron}"/>
                    </xsl:for-each>
                </att-class>
            </xsl:when>
            <xsl:when test="parent::interfaces and @id">
                <interface ident="{@id}">
                    <xsl:for-each select="following-sibling::line[preceding-sibling::line[@id][1]/@xml:id = $this.id]/value">
                        <att-class ident="{@id}" desc="{@comment}" schematron="{@schematron}"/>
                    </xsl:for-each>
                </interface>
            </xsl:when>
            <xsl:when test="parent::classes and @id">
                <element ident="{@id}">
                    <xsl:for-each select="following-sibling::line[preceding-sibling::line[@id][1]/@xml:id = $this.id]/value">
                        <supports ident="{@id}">
                            
                        </supports>
                    </xsl:for-each>
                </element>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="@raw" mode="prep3.config.xml"/>
    
    <xsl:function name="local:getAttribute.classes" as="xs:string*">
        <xsl:param name="elem" as="node()"/>
        <xsl:variable name="direct.classes" select="$elem//tei:memberOf[starts-with(@key,'att.')]/@key" as="xs:string*"/>
        
        <xsl:sequence select="$direct.classes"/>
        <xsl:for-each select="$direct.classes">
            <xsl:variable name="current.class" select="." as="xs:string"/>
            <xsl:if test="$mei.source//mei:classSpec[@ident = $current.class]">
                <xsl:sequence select="local:getAttribute.classes($mei.source//mei:classSpec[@ident = $current.class])"/>
            </xsl:if>
            
        </xsl:for-each>
        
    </xsl:function>
    
    <xsl:template match="node() | @*" mode="#all">
        <xsl:copy>
            <xsl:apply-templates select="node() | @*" mode="#current"/>
        </xsl:copy>
    </xsl:template>
    
    
</xsl:stylesheet>