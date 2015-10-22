 # -- coding: utf-8 --

import os
import re
import codecs
import textwrap
import logging
import types
lg = logging.getLogger('schemaparser')
import pdb

import yaml

LANG_NAME="HTML"


def vrv_member_cc(name):
    cc = "".join([n[0].upper() + n[1:] for n in name.split(".")])
    return cc[0].lower() + cc[1:]
    
def vrv_member_cc_upper(name):
    return "".join([n[0].upper() + n[1:] for n in name.split(".")])

def vrv_load_config(includes_dir):
    """ Load the vrv attribute overrides into CONFIG."""
    global CONFIG
    
    if not includes_dir:
        0
        return
        
    config = os.path.join(includes_dir, "config.yml")
    if not os.path.isfile(config):
        return
    
    f = open(config, "r")
    CONFIG = yaml.load(f)
    f.close()
    
def vrv_get_att_config(module, att):
    lg.debug( module )
    if not module in CONFIG["modules"] or not att in CONFIG["modules"][module]["attributes"]:
        return None
    return CONFIG["modules"][module]["attributes"][att]
    
def vrv_get_type_config(type):
    if not type in CONFIG["defaults"]:
        return None
    return CONFIG["defaults"][type]

def vrv_translatetype(module, att):
    """ Get the type override for an attribute in module."""
    att_config = vrv_get_att_config(module, att)
    if att_config is None:
        return None, ""
        
    att = att_config["type"]
    return (att, "")
    
def vrv_translatedefault(type, module, att):
    """ Get the type default value."""
    # nothing in the defaults
    type_config = vrv_get_type_config(type)
    # nothing in the defaults
    if type_config is None or not "default" in type_config:
        return None

    att_config = vrv_get_att_config(module, att)
    # nothing in the module/att
    if att_config is None or "default" not in att_config:
        return type_config["default"]
       
    # return the module/att default 
    return att_config["default"]

def vrv_translateconverters(type, module, att):
    """ Get the type default converters."""
    default_converters = ["StrTo{0}".format(vrv_member_cc_upper(att)), "{0}ToStr".format(vrv_member_cc_upper(att))]
    type_config = vrv_get_type_config(type)
    # nothing in the defaults
    if type_config is None or not "converters" in type_config:
         return default_converters

    att_config = vrv_get_att_config(module, att)
    # nothing in the module/att
    if att_config is None or "converters" not in att_config:
        return type_config["converters"]
       
    # return the module/att default 
    return att_config["converters"]

def create(schema, outdir, includes_dir = ""):
    lg.debug("Begin Verovio C++ Output ... ")
    
    vrv_load_config(includes_dir)
    
    __create_att_classes(schema, outdir, includes_dir)
    
    lg.debug("Success!")

def __create_att_classes(schema, outdir, includes_dir):
    ###########################################################################
    # Header
    ###########################################################################
    lg.debug("Creating Doc.")
    enum = ""
    
    c = CONFIG["classes"]
    
    for cc in c:
        lg.debug("\tCreated atts_{0}.h".format(cc))
    
    for module, atgroup in sorted(schema.attribute_group_structure.iteritems()):
        fullout = ""
        classes = ""
        methods = ""
        
        if not atgroup:
            # continue if we don't have any attribute groups in this module
            continue
        
        for gp, atts in sorted(atgroup.iteritems()):
            if not atts:
                continue
            
            members = ""
            methods = ""
            for att in atts:
                if len(att.split("|")) > 1:
                    ns,att = att.split("|")
                
        #fullout = CLASSES_HEAD_TEMPLATE.format(**tplvars)
        fmh = open(os.path.join(outdir, "atts_{0}.h".format(module.lower())), 'w')
        fmh.write(fullout)
        fmh.close()
        lg.debug("\tCreated atts_{0}.h".format(module.lower()))
        
    ########################################################################### 
    # Classes enum
    ###########################################################################
    fmi = open(os.path.join(outdir, "att_classes.h".format(module.lower())), 'w')
    #fmi.write(LICENSE)
    #fmi.write(ENUM_GRP_START)
    #fmi.write(enum)
    #fmi.write(ENUM_GRP_END)
    fmi.close()
    lg.debug("\tCreated atts_{0}.cpp".format(module.lower()))
