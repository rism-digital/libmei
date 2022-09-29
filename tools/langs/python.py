import logging
import re
from pathlib import Path

lg = logging.getLogger('schemaparser')

LANG_NAME = "Python"

MODULE_TEMPLATE = """
{license}

from pymei import MeiElement

{classes}
"""

MODULE_CLASS_TEMPLATE = """
class {className}_(MeiElement):
    def __init__(self):
        MeiElement.__init__(self, "{className}")
    # <{className}>
"""

LICENSE = """\"\"\"
    Copyright (c) 2011-2013 {authors}
    
    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:
    
    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
\"\"\""""

AUTHORS = "Andrew Hankinson, Alastair Porter, and Others"


def create(schema, outdir):
    lg.debug("Begin Python Output...")

    __create_python_classes(schema, outdir)
    __create_init(schema, outdir)

    lg.debug("Success!")


def __create_python_classes(schema, outdir):
    """Create Python Modules."""
    lg.debug("Creating Python Modules")

    for module, elements in sorted(schema.element_structure.items()):
        if not elements:
            continue
        class_output = ""
        module_output = ""

        for element, atgroups in sorted(elements.items()):
            methstr = {
                "className": element
            }
            class_output += MODULE_CLASS_TEMPLATE.format(**methstr)

        modstr = {
            "classes": class_output,
            "license": LICENSE.format(authors=AUTHORS),
        }
        module_output = MODULE_TEMPLATE.format(**modstr)

        fmi = Path(outdir, f"{module.lower()}.py")
        fmi.write_text(module_output)
        lg.debug(f"\tCreated {module.lower()}.py")


def __create_init(schema, outdir):
    """Create init file."""
    m = []
    a = []
    p = Path(outdir, "__init__.py")
    for module, elements in sorted(schema.element_structure.items()):
        a.append('"{0}"'.format(module.lower()))
        m.append(f"from pymei.Modules.{module.lower()} import *\n")
    init_string = "__all__ = [{0}]\n\n".format(", ".join(a)) + "".join(m)
    p.write_text(init_string)


def parse_includes(file_dir, includes_dir: str):
    """Parse includes."""
    lg.debug("Parsing includes")
    # get the files in the includes directory
    includes = [f for f in Path(includes_dir).iterdir()
                if not f.name.startswith(".")]

    for f in Path(file_dir).iterdir():
        if f.name.startswith("."):
            continue
        methods, inc = __process_include(f, includes, includes_dir)
        if methods:
            __parse_codefile(methods, inc, f.parent, f)


def __process_include(fname, includes, includes_dir: str):
    """Process the include file for our methods."""
    new_methods, includes_block = None, None
    if (fname + ".inc") in includes:
        lg.debug(f"\tProcessing include for {fname}")
        includefile = Path(includes_dir, {fname}).with_suffix(".inc").read_text()
        new_methods, includes_block = __parse_includefile(includefile)
        return (new_methods, includes_block)
    else:
        return (None, None)


def __parse_includefile(contents):
    """Parse the include file for our methods."""
    ret = {}
    inc = []
    reg = re.compile(
        r"# <(?P<elementName>[^>]+)>(.+?)# </(?P=elementName)>", re.MULTILINE | re.DOTALL)
    ret = dict(re.findall(reg, contents))

    # grab the include for the includes...
    reginc = re.compile(
        r"/\* #include_block \*/(.+?)/\* #include_block \*/", re.MULTILINE | re.DOTALL)
    inc = re.findall(reginc, contents)
    return (ret, inc)


def __parse_codefile(methods, includes, directory, codefile):
    f = Path(directory, codefile)
    contents = f.read_text()
    regmatch = re.compile(
        r"[\s]+# <(?P<elementName>[^>]+)>", re.MULTILINE | re.DOTALL)
    incmatch = re.compile(r"/\* #include_block \*/")
    for i, line in enumerate(contents):
        imatch = re.match(incmatch, line)
        if imatch:
            if includes:
                contents[i] = includes[0]

        match = re.match(regmatch, line)
        if match:
            if match.group("elementName") in list(methods.keys()):
                contents[i] = methods[match.group(
                    "elementName")].lstrip("\n") + "\n"

    f.write_text(contents)
