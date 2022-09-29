# -- coding: utf-8 --
import logging
import textwrap
from pathlib import Path

lg = logging.getLogger('schemaparser')

LANG_NAME = "C#"

NS_PREFIX_MAP = {
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/1999/xlink": "xlink",
    "http://www.isocat.org/ns/dcr": "datcat"
}

AUTHORS = "Anna Plaksin"

ATT_FILE = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;

{license}

namespace mei
{{
    {interfaces}

    {ext_classes}
}}"""

ATT_METHODS = """#region {attNameLower}
    {ns_decl}
    public{static} void Set{attNameUpper}({interfaceParamDefSet}string _val)
    {{
      MeiAtt_controller.SetAttribute({interfaceParamInvoke}, {attConst}, _val);
    }}

    public{static} XAttribute Get{attNameUpper}Attribute({interfaceParamDef})
    {{
      return MeiAtt_controller.GetAttribute({interfaceParamInvoke}, {attConst});
    }}
    
    public{static} string Get{attNameUpper}Value({interfaceParamDef})
    {{
      return MeiAtt_controller.GetAttributeValue({interfaceParamInvoke}, {attConst});
    }}
    
    public{static} bool Has{attNameUpper}({interfaceParamDef})
    {{
      return MeiAtt_controller.HasAttribute({interfaceParamInvoke}, {attConst});
    }}

    public{static} void Remove{attNameUpper}({interfaceParamDef})
    {{
      MeiAtt_controller.RemoveAttribute({interfaceParamInvoke}, {attConst});
    }}
    #endregion
"""

ATTGROUP_EXTENSION_CLASS = """/// <summary>
  /// Extension methods for {attGroupName}
  /// </summary>
  public static class Att{attGroupNameUpper}_extensions
  {{
    {methods}
  }}
"""

ATTGROUP_INTERFACE = """/// <summary>
  /// Interface for {attGroupName}
  /// </summary>
  public interface IAtt{attGroupNameUpper} : IMEiAtt{members}
  {{

  }}
"""

ELEMENT_FILE = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;

{license}

namespace mei
{{
    /// <summary>
    /// <{elementName}/>
    /// </summary>
    public class {elementNameUpper} : MeiElement{attClassInterfaces}
    {{
        {constructors}

        {attribute_methods}
    }}
}}
"""

NS_DECLARATION = """private static readonly XNamespace ns_{objectName} = "{ns}";
"""

ELEMENT_CONSTRUCTORS = """{ns_decl}
        public {elementNameUpper}() : base({elementConst}) {{ }}

        public {elementNameUpper}(object _content) : base({elementConst}, _content) {{ }}

        public {elementNameUpper}(params object[] _content) : base({elementConst}, _content) {{ }}
"""

LICENSE = """/////////////////////////////////////////////////////////////////////////////
// Authors:     Anna Plaksin
// Created:     2017
// Copyright (c) Authors and others. All rights reserved.
//
// Code generated using a modified version of libmei
// by Andrew Hankinson, Alastair Porter, and Others
/////////////////////////////////////////////////////////////////////////////"""

# globals
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0",
          "rng": "http://relaxng.org/ns/structure/1.0"}


def windll_getAttClassMembers(schema, group):
    # returns a list of members of an attribute class
    memberList = schema.xpath(
        "//tei:classSpec[@type=$att][@ident=$nm]/tei:classes/tei:memberOf/@key", att="atts", nm=group, namespaces=TEI_NS)

    if "att.id" in memberList:
        memberList.remove("att.id")

    members = []

    for member in memberList:
        if member not in members:
            members.append(member)

    return (members)


def windll_getElementNS(schema, element):
    # returns non-mei namespaces
    ns = schema.xpath(
        "//tei:elementSpec[@ident=$el]/@ns", el=element, namespaces=TEI_NS)

    if "http://www.music-encoding.org/ns/mei" in ns:
        ns.remove("http://www.music-encoding.org/ns/mei")

    return (ns)


def windll_writeAttMethods(attribute, atgroup, schema):
    # writes attribute methods for the defined attribute
    prefix = ""
    exp_ns = ""
    att_name = ""
    att_const = ""
    ns_decl = ""

    # check, if attribute is namespaced
    if len(attribute.split("|")) > 1:
        ns, attribute = attribute.split("|")

        # check, if namespace is already in prefix list
        if ns in NS_PREFIX_MAP:
            prefix = NS_PREFIX_MAP[ns]
        else:
            exp_ns = ns

    att_name = "{0}:{1}".format(
        prefix, attribute) if prefix != "" else "{0}".format(attribute)

    # build readonly for explicit namespaces
    if exp_ns != "":
        ns_strings = {
            "ns": exp_ns,
            "objectName": att_name,
        }
        ns_decl += NS_DECLARATION.format(**ns_strings)

    att_const = "\"{0}\"".format(
        att_name) if exp_ns == "" else "\"{0}\", ns_{0}".format(att_name)

    # Set interface parameter for an attribute of an attribute class or an element
    interfaceParamDef = ""
    interfaceParamInvoke = ""
    interfaceParamDefSet = ""
    static = ""
    if atgroup != "":
        interfaceParamDef = "this IAtt{0} e".format(
            schema.cc(schema.strpatt(atgroup)))
        interfaceParamDefSet = "this IAtt{0} e, ".format(
            schema.cc(schema.strpatt(atgroup)))
        interfaceParamInvoke = "e"
        static = " static"
    else:
        interfaceParamDef = ""
        interfaceParamDefSet = ""
        interfaceParamInvoke = "this"

    # if att_name == "type":
    #    att_name = "typeAttribute"

    att_strings = {
        "ns_decl": ns_decl,
        "attNameUpper": schema.cc(schema.strpatt(attribute)),
        "attConst": att_const,
        "interfaceParamDef": interfaceParamDef,
        "interfaceParamInvoke": interfaceParamInvoke,
        "interfaceParamDefSet": interfaceParamDefSet,
        "attNameLower": att_name,
        "static": static,
    }

    att_methods = ATT_METHODS.format(**att_strings)

    return (att_methods)


def create(schema, outdir):
    lg.debug("Begin C# Output ... ")
    __create_att_classes(schema, outdir)
    __create_element_classes(schema, outdir)

    lg.debug("Success!")


def __get_docstr(text, indent=0):
    """ Format a docstring. Take the first sentence (. followed by a space)
        and use it for the brief. Then put the rest of the text after a blank
        line if there is text there
    """
    text = text.strip()

    dotpos = text.find(". ")
    if dotpos > 0:
        brief = text[:dotpos+1]
        content = text[dotpos+2:]
    else:
        brief = text
        content = ""
    if indent == 0:
        istr = ""
    else:
        istr = "{0:{1}}".format(" ", indent)

    brief = "\n{0} *  ".format(istr).join(textwrap.wrap(brief, 80))
    content = "\n{0} *  ".format(istr).join(textwrap.wrap(content, 80))
    docstr = "{0}/** \\brief {1}".format(istr, brief)
    if len(content) > 0:
        docstr += "\n{0} * \n{0} *  {1}".format(istr, content)
    docstr += "\n{0} */".format(istr)
    return docstr


def __create_att_classes(schema, outdir):
    lg.debug("Creating Attribute Classes")

    outdir_att = Path(outdir, "atts")
    outdir_att.mkdir()

    for module, atgroup in sorted(schema.attribute_group_structure.items()):
        fullout = ""

        if not atgroup:
            # continue if we don't have any attribute groups in this module
            continue

        for gp, atts in sorted(atgroup.items()):

            extension_classes = ""
            interfaces = ""

            methods = ""

            gp_members = windll_getAttClassMembers(schema.schema, gp)

            for att in atts:
                if len(methods) > 0:
                    methods += "\n    "

                methods += windll_writeAttMethods(att, gp, schema)

            clsubstrings = {
                "methods": methods,
                "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                "attGroupName": gp,
            }
            # add List of members
            members = ""
            for member in gp_members:
                members += ", I{0}".format(schema.cc(member))

            intstrings = {
                "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                "attGroupName": gp,
                "members": members
            }

            if methods != "":
                # if attribute class doesn't contain attributes itself, skip creation of extension class
                extension_classes += ATTGROUP_EXTENSION_CLASS.format(
                    **clsubstrings)

            interfaces += ATTGROUP_INTERFACE.format(**intstrings)

            tplvars = {
                "license": LICENSE.format(authors=AUTHORS),
                "ext_classes": extension_classes,
                "interfaces": interfaces
            }

            fullout = ATT_FILE.format(**tplvars)

            fmh = Path(outdir_att, "att_{0}.cs".format(
                schema.cc(schema.strpatt(gp)).lower()))
            fmh.write_text(fullout)
            lg.debug("\tCreated att_{0}.cs".format(
                schema.cc(schema.strpatt(gp)).lower()))


def __create_element_classes(schema, outdir):
    lg.debug("Creating Element Classes")

    outdir_el = Path(outdir, "elements")
    outdir_el.mkdir()

    for module, elements in sorted(schema.element_structure.items()):

        if not elements:
            continue

        for element, atgroups in sorted(elements.items()):
            fullout = ""
            at_interfaces = ""
            ns_nonmei = ""
            class_constuctors = ""
            at_methods = ""
            interfaces = []

            # Look for attribute classes and attributes within elementSpec
            for attribute in atgroups:
                if isinstance(attribute, list):
                    # self-defined attributes
                    for sda in attribute:
                        if len(at_methods) > 0:
                            at_methods += "\n        "
                        at_methods += windll_writeAttMethods(sda, "", schema)

                else:
                    if attribute not in interfaces:
                        at_interfaces += ", I{0}".format(schema.cc(attribute))
                        interfaces.append(attribute)

            # Build constructors
            # First, look for non-mei namespaces
            ns_nonmei = windll_getElementNS(schema.schema, element)
            ns_readonly = ""
            if len(ns_nonmei) > 0:
                ns_strings = {
                    "objectName": element,
                    "ns": ns_nonmei[len(ns_nonmei)-1]
                }
                ns_readonly += NS_DECLARATION.format(**ns_strings)

            element_const = "\"{0}\"".format(
                element) if ns_readonly == "" else "ns_{0}, \"{0}\"".format(element)

            const_strings = {
                "ns_decl": ns_readonly,
                "elementConst": element_const,
                "elementNameUpper": schema.cc(element)
            }

            class_constuctors += ELEMENT_CONSTRUCTORS.format(**const_strings)

            # In the case of self-defined attributes, implementing IMeiAtt is not necessary,
            # because used methods of XElement are already available within element class.

            el_docstrings = {
                "elementName": element,
                "elementNameUpper": schema.cc(element),
                "attClassInterfaces": at_interfaces,
                "constructors": class_constuctors,
                "attribute_methods": at_methods,
                "license": LICENSE.format(authors=AUTHORS),
            }

            fullout += ELEMENT_FILE.format(**el_docstrings)

            fmi = Path(outdir_el, "{0}.cs".format(schema.cc(element)))
            fmi.write_text(fullout)
            lg.debug("\tCreated {0}.cs".format(schema.cc(element)))
