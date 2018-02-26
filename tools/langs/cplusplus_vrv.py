 # -- coding: utf-8 --

import sys
import os
import re
import codecs
import textwrap
import logging
import types
lg = logging.getLogger('schemaparser')
import pdb

import yaml

LANG_NAME="C++"

NS_PREFIX_MAP = {
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/1999/xlink": "xlink"
}

AUTHORS = "Andrew Hankinson, Alastair Porter, and Others"

METHODS_HEADER_TEMPLATE = """    void Set{attNameUpper}({attType} {attNameLowerJoined}{attTypeName}_) {{ m_{attNameLowerJoined}{attTypeName} = {attNameLowerJoined}{attTypeName}_; }}
    {attType} Get{attNameUpper}() const {{ return m_{attNameLowerJoined}{attTypeName}; }}
    bool Has{attNameUpper}() const;
    """

METHODS_HEADER_TEMPLATE_ALTERNATE = """/** Getter for reference (for alternate type only) */
    {attType} *Get{attNameUpper}Alternate() {{ return &m_{attNameLowerJoined}{attTypeName}; }}
    """

MEMBERS_HEADER_TEMPLATE = """{documentation}
    {attType} m_{attNameLowerJoined}{attTypeName};
"""

DEFAULTS_IMPL_TEMPLATE = """m_{attNameLowerJoined}{attTypeName} = {attDefault};"""

READS_IMPL_TEMPLATE = """if (element.attribute("{attNameLower}")) {{
        this->Set{attNameUpper}({converterRead}(element.attribute("{attNameLower}").value()));
        element.remove_attribute("{attNameLower}");
        hasAttribute = true;
    }}"""

WRITES_IMPL_TEMPLATE = """if (this->Has{attNameUpper}()) {{
        element.append_attribute("{attNameLower}") = {converterWrite}(this->Get{attNameUpper}()).c_str();
        wroteAttribute = true;
    }}"""

CHECKERS_IMPL_TEMPLATE = """bool Att{attGroupNameUpper}::Has{attNameUpper}() const
{{
    return (m_{attNameLowerJoined}{attTypeName} != {attDefault});
}}

"""

CHECKERS_IMPL_TEMPLATE_ALTERNATE = """bool Att{attGroupNameUpper}::Has{attNameUpper}() const
{{
    return (m_{attNameLowerJoined}{attTypeName}.HasValue());
}}

"""

#
# These templates the list of enum for att classes ids
#

ENUM_GRP_START = """

#ifndef __VRV_ATT_CLASSES_H__
#define __VRV_ATT_CLASSES_H__

//----------------------------------------------------------------------------

namespace vrv {

enum AttClassId {
    ATT_CLASS_min = 0,
"""

ENUM_GRP_END = """    ATT_CLASS_max
};

} // vrv namespace

#endif // __VRV_ATT_CLASSES_H__
"""

#
# These templates the type definintions
#

TYPE_GRP_START = """

#ifndef __VRV_ATT_TYPES_H__
#define __VRV_ATT_TYPES_H__

//----------------------------------------------------------------------------

namespace vrv {

"""

TYPE_GRP_END = """
} // vrv namespace

#endif // __VRV_ATT_TYPES_H__
"""

TYPE_START = """/**
 * MEI {meitype}
 */
enum {vrvtype} {{
    {val_prefix}_NONE = 0,"""

TYPE_VALUE = """
    {val_prefix}_{value},"""

TYPE_END = """
    {val_prefix}_MAX
}};

"""

#
# These templates generate converter methods
#

CONVERTER_HEADER_TEMPLATE_START = """

#ifndef __VRV_ATT_CONVERTER_H__
#define __VRV_ATT_CONVERTER_H__

#include <string>

//----------------------------------------------------------------------------

#include "attdef.h"

namespace vrv {

//----------------------------------------------------------------------------
// AttConverter
//----------------------------------------------------------------------------

class AttConverter {
public:"""

CONVERTER_HEADER_TEMPLATE = """
    std::string {fname}ToStr({type} data) const;
    {type} StrTo{fname}(std::string value, bool logWarning = true) const;
"""

CONVERTER_HEADER_TEMPLATE_END = """};

} // vrv namespace

#endif // __VRV_ATT_CONVERTER_H__
"""

CONVERTER_IMPL_TEMPLATE_START = """

#include "attconverter.h"

//----------------------------------------------------------------------------

#include <assert.h>

//----------------------------------------------------------------------------

#include "vrv.h"

namespace vrv {

//----------------------------------------------------------------------------
// AttConverter
//----------------------------------------------------------------------------
"""

CONVERTER_IMPL_TEMPLATE_METHOD1_START = """
std::string AttConverter::{fname}ToStr({type} data) const
{{
    std::string value;
    switch (data) {{"""

CONVERTER_IMPL_TEMPLATE_METHOD2_START = """
{type} AttConverter::StrTo{fname}(std::string value, bool logWarning) const
{{"""

CONVERTER_IMPL_TEMPLATE_METHOD1 = """
        case {value}: value = "{string}"; break;"""

CONVERTER_IMPL_TEMPLATE_METHOD2 = """
    if (value == "{string}") return {value};"""

CONVERTER_IMPL_TEMPLATE_METHOD1_END = """
        default:
            LogWarning("Unknown value '%d' for {type}", data);
            value = "";
            break;
    }}
    return value;
}}
"""

CONVERTER_IMPL_TEMPLATE_METHOD2_END = """
    if (logWarning && !value.empty())
        LogWarning("Unsupported value '%s' for {type}", value.c_str());
    return {prefix}_NONE;
}}
"""

CONVERTER_IMPL_TEMPLATE_END = """
} // vrv namespace
"""


#
# These templates generate a module level static method for setting attribute on an unspcified Object
#

SETTERS_IMPL_TEMPLATE_START = """bool Att::Set{moduleNameCap}(Object *element, std::string attrType, std::string attrValue)
{{
"""

SETTERS_IMPL_TEMPLATE_GRP_START = """    if (element->HasAttClass({attId})) {{
        Att{attGroupNameUpper} *att = dynamic_cast<Att{attGroupNameUpper} *>(element);
        assert(att);
"""

SETTERS_IMPL_TEMPLATE = """        if (attrType == "{attNameLower}{attTypeName}") {{
            att->Set{attNameUpper}(att->{converterRead}(attrValue));
            return true;
        }}
"""

SETTERS_IMPL_TEMPLATE_GRP_END = """    }}
"""

SETTERS_IMPL_TEMPLATE_END = """
    return false;
}}

"""

#
# These templates generate a module level static method for getting attributes of an unspcified Object
#

GETTERS_IMPL_TEMPLATE_START = """void Att::Get{moduleNameCap}(const Object *element, ArrayOfStrAttr *attributes)
{{
"""

GETTERS_IMPL_TEMPLATE_GRP_START = """    if (element->HasAttClass({attId})) {{
        const Att{attGroupNameUpper} *att = dynamic_cast<const Att{attGroupNameUpper} *>(element);
        assert(att);
"""

GETTERS_IMPL_TEMPLATE = """        if (att->Has{attNameUpper}()) {{
            attributes->push_back(std::make_pair("{attNameLower}{attTypeName}", att->{converterWrite}(att->Get{attNameUpper}())));
        }}
"""

GETTERS_IMPL_TEMPLATE_GRP_END = """    }}
"""

GETTERS_IMPL_TEMPLATE_END = """}}

}} // vrv namespace
"""

NAMESPACE_TEMPLATE = """MeiNamespace *s = new MeiNamespace("{prefix}", "{href}");\n    """

CLASSES_IMPL_TEMPLATE = """{license}

#include "{moduleNameLower}.h"

//----------------------------------------------------------------------------

#include <assert.h>

//----------------------------------------------------------------------------

#include "object.h"

/* #include_block */

namespace vrv {{

{elements}

"""

CLASSES_HEAD_TEMPLATE = """{license}

#ifndef __VRV_{moduleNameCaps}_H__
#define __VRV_{moduleNameCaps}_H__

#include "att.h"
#include "attdef.h"
#include "pugixml.hpp"

//----------------------------------------------------------------------------

{includes}

namespace vrv {{

{elements}

}} // vrv namespace

#endif // __VRV_{moduleNameCaps}_H__
"""

MIXIN_CLASS_HEAD_TEMPLATE = """
//----------------------------------------------------------------------------
// Att{attGroupNameUpper}
//----------------------------------------------------------------------------

class Att{attGroupNameUpper} : public Att {{
public:
    Att{attGroupNameUpper}();
    virtual ~Att{attGroupNameUpper}();

    /** Reset the default values for the attribute class **/
    void Reset{attGroupNameUpper}();

    /** Read the values for the attribute class **/
    bool Read{attGroupNameUpper}(pugi::xml_node element);

    /** Write the values for the attribute class **/
    bool Write{attGroupNameUpper}(pugi::xml_node element);

    /**
     * @name Setters, getters and presence checker for class members.
     * The checker returns true if the attribute class is set (e.g., not equal
     * to the default value)
     **/
    ///@{{
{methods}///@}}

private:
{members}
    /* include <{attNameLower}> */
}};
"""

MIXIN_CLASS_IMPL_CONS_TEMPLATE = """
//----------------------------------------------------------------------------
// Att{attGroupNameUpper}
//----------------------------------------------------------------------------

Att{attGroupNameUpper}::Att{attGroupNameUpper}() : Att()
{{
    Reset{attGroupNameUpper}();
}}

Att{attGroupNameUpper}::~Att{attGroupNameUpper}()
{{
}}

void Att{attGroupNameUpper}::Reset{attGroupNameUpper}()
{{
    {defaults}
}}

bool Att{attGroupNameUpper}::Read{attGroupNameUpper}(pugi::xml_node element)
{{
    bool hasAttribute = false;
    {reads}
    return hasAttribute;
}}

bool Att{attGroupNameUpper}::Write{attGroupNameUpper}(pugi::xml_node element)
{{
    bool wroteAttribute = false;
    {writes}
    return wroteAttribute;
}}

{checkers}/* include <{attNameLower}> */
"""

LICENSE = """/////////////////////////////////////////////////////////////////////////////
// Authors:     Laurent Pugin and Rodolfo Zitellini
// Created:     2014
// Copyright (c) Authors and others. All rights reserved.
//
// Code generated using a modified version of libmei
// by Andrew Hankinson, Alastair Porter, and Others
/////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////
// NOTE: this file was generated with the Verovio libmei version and
// should not be edited because changes will be lost.
/////////////////////////////////////////////////////////////////////////////"""

def vrv_member_cc(name):
    cc = "".join([n[0].upper() + n[1:] for n in name.split(".")])
    return cc[0].lower() + cc[1:]
    
def vrv_member_cc_upper(name):
    return "".join([n[0].upper() + n[1:] for n in name.split(".")])
    
def vrv_converter_cc(name):
    [l, r] = name.split('_', 1)
    r = "".join([n[0].upper() + n[1:].lower() for n in r.split("_")])
    if l == "data":
        return r
    return l[0].upper() + l[1:] + r

# globals
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0", "rng": "http://relaxng.org/ns/structure/1.0"}

def vrv_load_config(includes_dir):
    """ Load the vrv attribute overrides into CONFIG."""
    global CONFIG
    
    if not includes_dir:
        return
        
    config = os.path.join(includes_dir, "config.yml")
    if not os.path.isfile(config):
        return
    
    f = open(config, "r")
    CONFIG = yaml.load(f)
    f.close()
    
def vrv_get_att_config(module, gp, att):
    if not module in CONFIG["modules"] or not gp in CONFIG["modules"][module]:
        return None
    if not att in CONFIG["modules"][module][gp]:
        return None
    return CONFIG["modules"][module][gp][att]
    
def vrv_get_type_default(type):
    if not type in CONFIG["defaults"]:
        return "{0}_NONE".format(re.sub(r'^data_', "",type))
    return CONFIG["defaults"][type]
    
def vrv_is_excluded_type(type):
    if not type in CONFIG["excludes"]:
        return False
    return True
    
def vrv_is_alternate_type(type):
    if not type in CONFIG["alternates"]:
        return False
    return True

def vrv_get_att_config_type(module, gp, att):
    """ Get the att type."""
    att_config = vrv_get_att_config(module, gp, att)
    if att_config is None or "type" not in att_config:
        return None, "" 
    att = att_config["type"]
    return (att, "")
    
def vrv_get_att_config_default(module, gp, att):
    """ Get the att default value."""
    att_config = vrv_get_att_config(module, gp, att)
    # nothing in the module/att
    if att_config is None or "default" not in att_config:
        return None
    # return the module/att default 
    return att_config["default"]
    
def vrv_getformattedtype(type):
    if type in CONFIG["mapped"]:
        return CONFIG["mapped"][type]
    return type.replace(".","_")

def vrv_getformattedvallist(att, vallist):
    return "{0}_{1}".format(vrv_member_cc(att.replace("att.","")), vallist.upper().replace(".","").replace(":",""))

def vrv_getatttype(schema, module, gp, aname, includes_dir = ""):   
    """ returns the attribut type for element name, or string if not detectable."""
    
    # Look up if there is an override for this type in the current module, and return it
    # Note that we do not honor pseudo-hungarian notation
    attype, hungarian = vrv_get_att_config_type(module, gp, aname)
    if attype:
        return (attype, hungarian)
    
    # No override, get it from the schema
    # First numbers
    el = schema.xpath("//tei:attDef[@ident=$name]/tei:datatype/rng:data/@type", name=aname, namespaces=TEI_NS)
    if el:
        if el[0] == "nonNegativeInteger" or el[0] == "positiveInteger":
            return ("int", "")
        elif el[0] == "decimal":
            return ("double", "")
    # The data types
    ref = schema.xpath("//tei:classSpec[@ident=$gp]//tei:attDef[@ident=$name]/tei:datatype/rng:ref/@name", gp=gp, name=aname, namespaces=TEI_NS)
    if ref:
        return (vrv_getformattedtype("{0}".format(ref[0])), "")
    # Finally from val lists
    vl = schema.xpath("//tei:classSpec[@ident=$gp]//tei:attDef[@ident=$name]/tei:valList[@type=\"closed\"]", gp=gp, name=aname, namespaces=TEI_NS)
    if vl:
        element = vl[0].xpath("./ancestor::tei:classSpec", namespaces=TEI_NS)
        attName = vl[0].xpath("./parent::tei:attDef/@ident", namespaces=TEI_NS)
        if element:
            return(vrv_getformattedvallist(element[0].get("ident"),attName[0]), "")
            #data_list = "{0}.{1}".format(element[0].get("ident"),attName[0])
        #elif attName:
        #    elName = vl[0].xpath("./ancestor::tei:elementSpec/@ident", namespaces=TEI_NS)
        #    lg.debug("VALLIST {0} --- {1}".format(elName[0],attName[0]))
    
    # Otherwise as string
    return ("std::string", "")

def vrv_getattdefault(schema, module, gp, aname, includes_dir = ""):        
    """ returns the attribute default value for element name, or string if not detectable."""
    
    attype, hungarian = vrv_getatttype(schema, module, gp, aname, includes_dir)
    default = vrv_get_att_config_default(module, gp, aname)
    
    if attype == "int":
        if default == None:
            default = 0
        return ("{0}".format(default), "", ["StrToInt", "IntToStr"])
    elif attype == "char":
        if default == None:
            default = 0
        return ("{0}".format(default), "", ["StrToInt", "IntToStr"])
    elif attype == "double":
        if default == None:
            default = 0.0
        return ("{0}".format(default), "", ["StrToDbl", "DblToStr"])
    elif attype == "std::string": 
        return ("\"\"", "", ["StrToStr", "StrToStr"])  
    else:
        if default == None:
            default = vrv_get_type_default(attype)
        cname = vrv_converter_cc(attype)
        return ("{0}".format(default), "", ["StrTo{0}".format(cname), "{0}ToStr".format(cname)])

def create(schema, outdir, includes_dir = ""):
    lg.debug("Begin Verovio C++ Output ... ")
    
    vrv_load_config(includes_dir)
    __create_att_classes(schema, outdir, includes_dir)
    
    lg.debug("Success!")

def __get_docstr(text, indent=0):
    """ Format a docstring. Take the first sentence (. followed by a space)
        and use it for the brief. Then put the rest of the text after a blank
        line if there is text there
    """
    # string handling is handled differently in Python 3+
    if sys.version_info >= (3, 0):
        text = text.strip()
    else:
        text = text.strip().encode("utf-8")
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
    
    if len(brief) > 1:
        brief = brief[0].upper() + brief[1:]
    else:
        brief = "---"
    brief = "\n{0} * ".format(istr).join(textwrap.wrap(brief, 80))
    content = "\n{0} * ".format(istr).join(textwrap.wrap(content, 80))
    docstr = "{0}/**".format(istr)
    if len(content) > 0 or brief.count("\n"):
        docstr += "\n{0} *".format(istr)
    docstr += " {0}".format(brief)
    if brief.count("\n") and len(content) == 0: 
        docstr += "\n{0}".format(istr)
    if len(content) > 0: 
        docstr += "\n{0} * {1}\n{0}".format(istr, content)
    docstr += " **/".format(istr)
    return docstr

def __create_att_classes(schema, outdir, includes_dir):
    ###########################################################################
    # Header
    ###########################################################################
    lg.debug("Creating Mixin Headers.")
    enum = ""
    
    for module, atgroup in sorted(schema.attribute_group_structure.items()):
        fullout = ""
        classes = ""
        methods = ""
        
        if not atgroup:
            # continue if we don't have any attribute groups in this module
            continue
        
        for gp, atts in sorted(atgroup.items()):
            if not atts:
                continue
            
            members = ""
            methods = ""
            for att in atts:
                if len(att.split("|")) > 1:
                    ns,att = att.split("|")
                atttype, atttypename = vrv_getatttype(schema.schema, module, gp, att, includes_dir)
                docstr = __get_docstr(schema.getattdocs(att), indent=4)
                substrings = {
                    "attNameUpper": schema.cc(schema.strpatt(att)),
                    "attNameLower": att,
                    "attNameLowerJoined": vrv_member_cc(att),
                    "documentation": docstr,
                    "attType": atttype,
                    "attTypeName": atttypename,
                }
                if len(methods) > 0:
                    methods += "//\n"
                methods += METHODS_HEADER_TEMPLATE.format(**substrings)
                if (vrv_is_alternate_type(atttype)):
                    methods += METHODS_HEADER_TEMPLATE_ALTERNATE.format(**substrings)
                members += MEMBERS_HEADER_TEMPLATE.format(**substrings)
                
            clsubstr = {
                "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                "methods": methods,
                "members": members,
                "attNameLower": "att{0}".format(att)
            }
            classes += MIXIN_CLASS_HEAD_TEMPLATE.format(**clsubstr)
            enum += "    ATT_{0},\n".format(schema.cc(schema.strpatt(gp)).upper())
        
        tplvars = {
            "includes": "#include <string>",
            'license': LICENSE.format(authors=AUTHORS),
            'moduleNameCaps': "ATTS_{0}".format(module.upper()),
            'elements': classes.strip()
        }
        
        fullout = CLASSES_HEAD_TEMPLATE.format(**tplvars)
        fmh = open(os.path.join(outdir, "atts_{0}.h".format(module.lower())), 'w')
        fmh.write(fullout)
        fmh.close()
        lg.debug("\tCreated atts_{0}.h".format(module.lower()))
        
        
    lg.debug("Creating Mixin Implementations")
    ########################################################################### 
    # Implementation
    ###########################################################################
    for module, atgroup in sorted(schema.attribute_group_structure.items()):
        fullout = ""
        classes = ""
        methods = ""
        setters = ""
        getters = ""
        
        if not atgroup:
            continue
        
        for gp, atts in sorted(atgroup.items()):
            if not atts:
                continue
            methods = ""
            defaults = ""
            reads = ""
            writes = ""
            checkers = ""
            prefix = ""
            setters += SETTERS_IMPL_TEMPLATE_GRP_START.format(**{
                                                              "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                                                              "attId": "ATT_{0}".format(schema.cc(schema.strpatt(gp)).upper()) })
            getters += GETTERS_IMPL_TEMPLATE_GRP_START.format(**{
                                                              "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                                                              "attId": "ATT_{0}".format(schema.cc(schema.strpatt(gp)).upper()) })

            for att in atts:
                if len(att.split("|")) > 1:
                    # we have a namespaced attribute
                    ns,att = att.split("|")
                    prefix = NS_PREFIX_MAP[ns]
                    #nssubstr = {
                    #    "prefix": NS_PREFIX_MAP[ns],
                    #    "href": ns
                    #}
                    #nsDef = NAMESPACE_TEMPLATE.format(**nssubstr)
                    attrNs = "s, "
                else:
                    nsDef = ""
                    attrNs = ""
                atttype, atttypename = vrv_getatttype(schema.schema, module, gp, att, includes_dir)
                attdefault, atttypename, converters = vrv_getattdefault(schema.schema, module, gp, att, includes_dir)
                
                attsubstr = {
                    "className": "{0}MixIn".format(schema.cc(schema.strpatt(gp))),
                    "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                    "attNameUpper": schema.cc(att),
                    "attNameLower": "{0}:{1}".format(prefix, att) if prefix != "" else "{0}".format(att),
                    "attNameLowerJoined": vrv_member_cc(att),
                    "attDefault": attdefault,
                    "attTypeName": atttypename,
                    "converterRead": converters[0],
                    "converterWrite": converters[1]
                }
                if len(defaults) > 0:
                    defaults += "\n    "
                    reads += "\n    "
                    writes += "\n    "
                defaults += DEFAULTS_IMPL_TEMPLATE.format(**attsubstr)
                reads += READS_IMPL_TEMPLATE.format(**attsubstr)
                writes += WRITES_IMPL_TEMPLATE.format(**attsubstr)
                if (vrv_is_alternate_type(atttype)):
                    checkers += CHECKERS_IMPL_TEMPLATE_ALTERNATE.format(**attsubstr)
                else:
                    checkers += CHECKERS_IMPL_TEMPLATE.format(**attsubstr)
                setters += SETTERS_IMPL_TEMPLATE.format(**attsubstr)
                getters += GETTERS_IMPL_TEMPLATE.format(**attsubstr)
            
            clsubstr = {
                "attGroupNameUpper": schema.cc(schema.strpatt(gp)),
                "defaults": defaults,
                "reads": reads,
                "writes": writes,
                "checkers": checkers,
                "attNameLower": "att{0}".format(att)
            }
            classes += MIXIN_CLASS_IMPL_CONS_TEMPLATE.format(**clsubstr)
            setters += SETTERS_IMPL_TEMPLATE_GRP_END.format(**attsubstr)
            getters += GETTERS_IMPL_TEMPLATE_GRP_END.format(**attsubstr)
            
        tplvars = {
            "license": LICENSE.format(authors=AUTHORS),
            "moduleNameLower": "atts_{0}".format(module.lower()),
            "moduleNameCap": format(module.capitalize()),
            "elements": classes.strip()
        }
        fullout = CLASSES_IMPL_TEMPLATE.format(**tplvars)
        fmi = open(os.path.join(outdir, "atts_{0}.cpp".format(module.lower())), 'w')
        fmi.write(fullout)
        fmi.write(SETTERS_IMPL_TEMPLATE_START.format(**tplvars))
        fmi.write(setters)
        fmi.write(SETTERS_IMPL_TEMPLATE_END.format(**tplvars))
        fmi.write(GETTERS_IMPL_TEMPLATE_START.format(**tplvars))
        fmi.write(getters)
        fmi.write(GETTERS_IMPL_TEMPLATE_END.format(**tplvars))
        fmi.close()
        lg.debug("\tCreated atts_{0}.cpp".format(module.lower()))

    lg.debug("Writing classes enum")
    ########################################################################### 
    # Classes enum
    ###########################################################################
    fmi = open(os.path.join(outdir, "attclasses.h".format(module.lower())), 'w')
    fmi.write(LICENSE)
    fmi.write(ENUM_GRP_START)
    fmi.write(enum)
    fmi.write(ENUM_GRP_END)
    fmi.close()
    lg.debug("\tCreated attclasses.h")
    
    lg.debug("Writing data types and lists")
    ########################################################################### 
    # Classes enum
    ###########################################################################
    fmi = open(os.path.join(outdir, "atttypes.h".format(module.lower())), 'w')
    fmi.write(LICENSE)
    fmi.write(TYPE_GRP_START)
    
    for data_type, values in sorted(schema.data_types.items()):
        if vrv_is_excluded_type(data_type) == True:
            lg.debug("Skipping {0}".format(data_type))
            continue
        
        vstr = ""
        val_prefix =  vrv_getformattedtype(data_type).replace("data_","")
        tpsubstr = {
            "meitype": data_type,
            "vrvtype": vrv_getformattedtype(data_type),
            "val_prefix":  val_prefix
        }
        vstr += TYPE_START.format(**tpsubstr)
        for v in values:
            tpsubstr = { 
                "val_prefix": val_prefix,
                "value": v.replace('.','_').replace('-','_').replace(',','_').replace('+','plus')
            }
            vstr += TYPE_VALUE.format(**tpsubstr)
          
        tpsubstr = { 
            "val_prefix": val_prefix,
            "test": "test"
        }
        vstr += TYPE_END.format(**tpsubstr)
        fmi.write(vstr)
        
    for list_type, values in sorted(schema.data_lists.items()):
        if vrv_is_excluded_type(list_type) == True:
            lg.debug("Skipping {0}".format(list_type))
            continue
        
        vstr = ""
        
        val_prefix =  vrv_getformattedvallist(list_type.rsplit('@')[0], list_type.rsplit('@')[1])
        tpsubstr = {
            "meitype": list_type,
            "vrvtype": val_prefix,
            "val_prefix":  val_prefix
        }
        vstr += TYPE_START.format(**tpsubstr)
        for v in values:
            tpsubstr = { 
                "val_prefix": val_prefix,
                "value": v.replace('.','_').replace('-','_').replace(',','_').replace('+','plus')
             }
            vstr += TYPE_VALUE.format(**tpsubstr)
          
        tpsubstr = {
            "val_prefix": val_prefix
        }
        vstr += TYPE_END.format(**tpsubstr)
        fmi.write(vstr)

    fmi.write(TYPE_GRP_END)
    
    fmi.close()
    lg.debug("\tCreated atttypes.h".format(module.lower()))
    
    lg.debug("Writing libmei att converter class")
    ########################################################################### 
    # Classes enum
    ###########################################################################
    fmi = open(os.path.join(outdir, "attconverter.h".format(module.lower())), 'w')
    fmi.write(LICENSE)
    fmi.write(CONVERTER_HEADER_TEMPLATE_START)
    fmi_cpp = open(os.path.join(outdir, "attconverter.cpp".format(module.lower())), 'w')
    fmi_cpp.write(LICENSE)
    fmi_cpp.write(CONVERTER_IMPL_TEMPLATE_START)
    
    for data_type, values in sorted(schema.data_types.items()):
        if vrv_is_excluded_type(data_type) == True:
            lg.debug("Skipping {0}".format(data_type))
            continue
        
        vrvtype = vrv_getformattedtype(data_type);
        val_prefix =  vrvtype.replace("data_","")
        vrvfname = vrv_converter_cc(vrvtype)
        tpsubstr = {
            "type": vrvtype,
            "fname": vrvfname
        }
        vstr = CONVERTER_HEADER_TEMPLATE.format(**tpsubstr)
        fmi.write(vstr)
        
        vstr1 = CONVERTER_IMPL_TEMPLATE_METHOD1_START.format(**tpsubstr)
        vstr2 = CONVERTER_IMPL_TEMPLATE_METHOD2_START.format(**tpsubstr)
        for v in values:
            tpsubstr = {
                "value": "{0}_{1}".format(val_prefix, v.replace('.','_').replace('-','_').replace(',','_').replace('+','plus')),
                "string": v
             }
            vstr1 += CONVERTER_IMPL_TEMPLATE_METHOD1.format(**tpsubstr)
            vstr2 += CONVERTER_IMPL_TEMPLATE_METHOD2.format(**tpsubstr)
         
        tpsubstr = {
            "prefix": val_prefix,
            "type": data_type
        }
        vstr1 += CONVERTER_IMPL_TEMPLATE_METHOD1_END.format(**tpsubstr)
        vstr2 += CONVERTER_IMPL_TEMPLATE_METHOD2_END.format(**tpsubstr)
        fmi_cpp.write(vstr1)
        fmi_cpp.write(vstr2)
        
    for list_type, values in sorted(schema.data_lists.items()):
        if vrv_is_excluded_type(list_type) == True:
            lg.debug("Skipping {0}".format(list_type))
            continue
        
        val_prefix =  vrv_getformattedvallist(list_type.rsplit('@')[0], list_type.rsplit('@')[1])
        vrvtype = val_prefix
        vrvfname = vrv_converter_cc(vrvtype)
        tpsubstr = {
            "type": vrvtype,
            "fname": vrvfname
        }
        vstr = CONVERTER_HEADER_TEMPLATE.format(**tpsubstr)
        fmi.write(vstr)
        
        vstr1 = CONVERTER_IMPL_TEMPLATE_METHOD1_START.format(**tpsubstr)
        vstr2 = CONVERTER_IMPL_TEMPLATE_METHOD2_START.format(**tpsubstr)
        for v in values:
            tpsubstr = {
                "value": "{0}_{1}".format(val_prefix, v.replace('.','_').replace('-','_').replace(',','_').replace('+','plus')),
                "string": v
             }
            vstr1 += CONVERTER_IMPL_TEMPLATE_METHOD1.format(**tpsubstr)
            vstr2 += CONVERTER_IMPL_TEMPLATE_METHOD2.format(**tpsubstr)
         
        tpsubstr = {
            "prefix": val_prefix,
            "type": list_type
        }
        vstr1 += CONVERTER_IMPL_TEMPLATE_METHOD1_END.format(**tpsubstr)
        vstr2 += CONVERTER_IMPL_TEMPLATE_METHOD2_END.format(**tpsubstr)
        fmi_cpp.write(vstr1)
        fmi_cpp.write(vstr2)
    
    fmi.write(CONVERTER_HEADER_TEMPLATE_END)
    fmi.close()
    fmi_cpp.write(CONVERTER_IMPL_TEMPLATE_END)
    fmi_cpp.close()
    lg.debug("\tCreated attconverter.h/cpp".format(module.lower()))

def parse_includes(file_dir, includes_dir):
    lg.debug("Parsing includes")

    # get the files in the includes directory
    includes = [f for f in os.listdir(includes_dir) if not f.startswith(".") and f.endswith(".inc")]
    # currently unused, see below comment in __copy_codefile
    # copies = [f for f in os.listdir(includes_dir) if f.endswith(".copy")]

    for dp,dn,fn in os.walk(file_dir):
        for f in fn:
            if f.startswith("."):
                continue
            methods, inc = __process_include(f, includes, includes_dir)
            if methods:
                __parse_codefile(methods, inc, dp, f)

def __process_include(fname, includes, includes_dir):
    name,ext = os.path.splitext(fname)
    new_methods, includes_block = None, None
    if "{0}.inc".format(fname) in includes:
        lg.debug("\tProcessing include for {0}".format(fname))
        f = open(os.path.join(includes_dir, "{0}.inc".format(fname)), 'r')
        includefile = f.read()
        f.close()
        new_methods, includes_block = __parse_includefile(includefile)
        return (new_methods, includes_block)
    else:
        return (None, None)

def __parse_includefile(contents):
    # parse the include file for our methods.
    ret = {}
    inc = []
    reg = re.compile(r"/\* <(?P<elementName>[^>]+)> \*/(.+?)/\* </(?P=elementName)> \*/", re.MULTILINE|re.DOTALL)
    ret = dict(re.findall(reg, contents))

    # grab the include for the includes...
    reginc = re.compile(r"/\* #include_block \*/(.+?)/\* #include_block \*/", re.MULTILINE|re.DOTALL)
    inc = re.findall(reginc, contents)
    return (ret, inc)

def __parse_codefile(methods, includes, directory, codefile):
    f = open(os.path.join(directory, codefile), 'r')
    contents = f.readlines()
    f.close()
    regmatch = re.compile(r"/\* include <(?P<elementName>[^>]+)> \*/")
    incmatch = re.compile(r"/\* #include_block \*/")
    for i,line in enumerate(contents):
        imatch = re.match(incmatch, line)
        if imatch:
            if includes:
                contents[i] = includes[0]

        match = re.match(regmatch, line)
        if match:
            if match.group("elementName") in methods.keys():
                contents[i] = methods[match.group("elementName")].lstrip("\n")
    
    f = open(os.path.join(directory, codefile), 'w')
    f.writelines(contents)
    f.close()
    
    
def __copy_codefile(directory, codefile):  
    # att.h, att_defs.h and att.cpp are required.
    # These are the only files to be edited by hand.
    # For now they are in the Verovio codebase because this makes it easier to edit the files.
    # eventually, we might want to have them in the libmei include dir and use this function to
    # copy them in the output directory
    lg.debug("Todo")

