LibMEI
------

**Remark:** this repository is no longer used for Verovio developments. The code has been refactored and moved to the Verovio [repository](https://github.com/rism-digital/verovio). 


[![Build Status](https://travis-ci.org/DDMAL/libmei.png?branch=master)](https://travis-ci.org/DDMAL/libmei)

LibMEI is a C++ library for reading and writing [MEI](http://music-encoding.org) files

It is developed by the [Distributed Digital Music Archives and Libraries Lab](http://ddmal.music.mcgill.ca/)
at the Schulich School of Music at McGill University, Montréal, Canada

This is a modified version that is used for generating C++ code for [Verovio](http://www.verovio.org). The main differences with LibMEI are:

1. it generates only attribute classes (Mixin in LibMEI),
2. each attribute has a C++ type deduced from the MEI schema or given in a separted configuration file,
3. it uses the MEI page-based customization not included in the MEI 2013 v2.1.0 (see [MEI](http://www.music-encoding.org)).


License
-------
LibMEI is released under the MIT license.

Compilation & Usage
-------------------

There is a modified CPP script ```tools/lang/cplusplus_vrv.py``` that can be activated with the ```-l vrv``` language option.

Additional C++ includes are in the ```tools/includes/vrv``` directory. The code will be generated into a ./libmei sub-directory at organized in Verovio.

A compiled version of the 2013 schema with the latest page-based customization is available in ```mei/xxxx-xx-xx/mei-page-based.xml.odd```.

To generate the code, simply

    python3 tools/parseschema2.py -l vrv -o path_to_verovio_directory -i tools/includes/vrv mei/2013-11-05/mei-page-based.xml.odd
    
Remark: you will need the `lxml` and `pyyaml` packages to be installed for this to run.
