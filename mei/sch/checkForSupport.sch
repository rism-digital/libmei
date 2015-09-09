<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        queryBinding="xslt2">
   <ns uri="http://www.music-encoding.org/ns/mei" prefix="mei"/>
   <ns uri="http://www.w3.org/1999/xlink" prefix="xlink"/>
   <pattern>
      <rule context="mei:barLine/@label">
         <assert test="false()">The attribute label on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@n">
         <assert test="false()">The attribute n on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@xml:base">
         <assert test="false()">The attribute xml:base on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@facs">
         <assert test="false()">The attribute facs on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@xlink:actuate">
         <assert test="false()">The attribute xlink:actuate on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@xlink:role">
         <assert test="false()">The attribute xlink:role on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@xlink:show">
         <assert test="false()">The attribute xlink:show on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@target">
         <assert test="false()">The attribute target on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@targettype">
         <assert test="false()">The attribute targettype on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@xlink:title">
         <assert test="false()">The attribute xlink:title on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:barLine/@rend">
         <assert test="false()">The attribute rend on barLine is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@label">
         <assert test="false()">The attribute label on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@n">
         <assert test="false()">The attribute n on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@xml:base">
         <assert test="false()">The attribute xml:base on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@facs">
         <assert test="false()">The attribute facs on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@headshape">
         <assert test="false()">The attribute headshape on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@oct.ges">
         <assert test="false()">The attribute oct.ges on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@pname.ges">
         <assert test="false()">The attribute pname.ges on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:note/@pnum">
         <assert test="false()">The attribute pnum on note is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:beam/@label">
         <assert test="false()">The attribute label on beam is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:beam/@n">
         <assert test="false()">The attribute n on beam is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:beam/@xml:base">
         <assert test="false()">The attribute xml:base on beam is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:beam/@facs">
         <assert test="false()">The attribute facs on beam is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:app/@label">
         <assert test="false()">The attribute label on app is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:app/@n">
         <assert test="false()">The attribute n on app is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:app/@xml:base">
         <assert test="false()">The attribute xml:base on app is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:app/@type">
         <assert test="false()">The attribute type on app is currently not supported by Verovio.</assert>
      </rule>
      <rule context="mei:app/@subtype">
         <assert test="false()">The attribute subtype on app is currently not supported by Verovio.</assert>
      </rule>
   </pattern>
</schema>
