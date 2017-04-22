# -*- coding: utf8 -*-

"""
Converts a dictionary into an XML string - does not preserve atomic types other than string.
It could use some refactoring to avoid code repetition, but it would take some time and thinking.

It can convert report objects of varying structures.
"""


# >>> compatibility with Python 3
from __future__ import print_function, unicode_literals
import sys
if sys.version_info < (3,):  # pragma: no cover
    integer_types = (int, long,)
    from itertools import imap
    from builtins import range as range3  # requires package future in Python2 (unfortunate, but there's no better way)
else:  # pragma: no cover
    integer_types = (int,)
    imap = map
    range3 = range
    unicode = str
# I use the names imap and range3 to make it explicit for Python2 programmers and avoid confusion
# <<< compatibility with Python 3

import codecs # for utf-8 file writing
from xml.sax.saxutils import escape as xml_escape
from collections import Iterable  # to test data types for lists
import logging
from xml.dom.minidom import parseString


LOG = logging.getLogger("reportGenXML")


def set_debug(debug=True, filename='reportGenXML.log'):
    if debug:
        import datetime
        print('Debug mode is on. Events are logged at: %s' % (filename))
        logging.basicConfig(filename=filename, level=logging.INFO)
        LOG.info('\nLogging session starts: %s' % (
            str(datetime.datetime.today()))
        )
    else:
        logging.basicConfig(level=logging.WARNING)
        print('Debug mode is off.')
        
def xml_escape_aux(s):
    """ auxiliary escape function - returns the object back if it's not a string """
    if type(s) in (str, unicode):
        return xml_escape(s)
    else: return s

def sanitize_xml_kv_pair(key, attr):
    """best-effort fix of XML k-v pairs if invalid, just passes them through otherwise"""
    LOG.info('Inside sanitize_xml_kv_pair(). Testing key "%s" with attr "%s"' % (
        unicode(key), unicode(attr))
    )
    key = xml_escape_aux(key)
    attr = xml_escape_aux(attr)
    
    # pass through if key is already valid
    if key_is_valid_xml(key):
        return key, attr

    key = repr(key) # try Python's repr conversion
    if key_is_valid_xml(key):
        return key, attr
        
    # try replacing spaces with underscores
    key = key.replace(' ', '_')
    if key_is_valid_xml(key):
        return key, attr
        
    # last resort is moving it to a named attribute
    attr['key'] = key
    key = 'key'
    return key, attr
        

def make_attrstring(attr):
    """Returns an attribute string in the form key="val" """
    attrstring = ' '.join(['%s="%s"' % (k, v) for k, v in attr.items()])
    return '%s%s' % (' ' if attrstring != '' else '', attrstring)


def key_is_valid_xml(key):
    """Checks that a key is a valid XML name"""
    LOG.info('Inside key_is_valid_xml(). Testing "%s"' % (unicode(key)))
    test_xml = '<?xml version="1.0" encoding="UTF-8" ?><%s>foo</%s>' % (key, key)
    try:
        parseString(test_xml)
        return True
    except Exception:  # exceptions are lacking in minidom
        return False


def XML_NULL_element(key):
    """None values are considered NULL elements in XML, which are empty like <this></this> or like <this/> 
    I chose the latter """
    LOG.info('XML_NULL_element(): key="%s"' % (unicode(key)))
    return '<%s/>' % (key,)


def convert_dispatch(obj, parent='root'):
    """dispatches obj to its corresponding function"""
    
    LOG.info('convert_dispatch() - type: "%s", obj="%s"' % (type(obj).__name__, unicode(obj)))
    
    key = "item"
    
    if type(obj) == bool:  # it's important that this is done first, so the it's picked up by the string converter
        obj = repr(obj)

    if type(obj) in (str, unicode):
        return convert_atom(key, obj)        
            
    if obj is None:
        return XML_NULL_element(key)
        
    if isinstance(obj, dict):
        return convert_dict(obj, parent)
        
    if isinstance(obj, Iterable):
        return convert_list(obj, parent)
        
    raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))


def convert_atom(key, val, attr={}):
    """Converts a string into an XML element"""
    LOG.info('convert_atom() - key="%s", val="%s", type(val): "%s"' % (
        unicode(key), unicode(val), type(val).__name__)
    )

    key, attr = sanitize_xml_kv_pair(key, attr)

    attrstring = make_attrstring(attr)
    return '<%s%s>%s</%s>' % ( key, attrstring, xml_escape_aux(val), key )


def convert_dict(obj, parent):
    """Converts a dict - dispatches recursively"""
    LOG.info('convert_dict(): obj type is: "%s", obj="%s"' % (
        type(obj).__name__, unicode(obj))
    )
    output = []
        
    for key, val in obj.items():
        LOG.info('Loop convert_dict(): key="%s", val="%s", type(val)="%s"' % ( unicode(key), unicode(val), type(val).__name__))

        attr = {}

        key, attr = sanitize_xml_kv_pair(key, attr)

        if type(val) == bool:  # it's important that this is done first, so the it's picked up by the string converter
            val = repr(val)

        elif type(val) in (str, unicode):
            output.append(convert_atom(key, val, attr))

        elif isinstance(val, dict):
            output.append('<%s%s>%s</%s>' % ( key, make_attrstring(attr), convert_dict(val, key), key) )

        elif isinstance(val, Iterable):
            output.append('<%s%s>%s</%s>' % ( key, make_attrstring(attr), convert_list(val, key), key) )

        elif val is None:
            output.append(XML_NULL_element(key))

        else:
            raise TypeError('Unsupported type: %s (%s)' % ( val, type(val).__name__) )

    return ''.join(output)


def convert_list(items, parent):
    """Converts a list - dispatches recursively"""
    LOG.info('Inside convert_list()')
    output = []

    key = "item"

    for i, val in enumerate(items):
        LOG.info('Looping convert_list() items: val="%s", key="%s", type="%s"' % (
            unicode(val), key, type(val).__name__)
        )
        attr = {}  # see convert_dic()
        
        if type(val) == bool: # it's important that this is done first, so the it's picked up by the string converter
            val = repr(val)
            
        elif type(val) in (str, unicode):
            output.append(convert_atom(key, val, attr))
            
        elif isinstance(val, dict):
            output.append('<%s>%s</%s>' % ( key, convert_dict(val, parent), key,) )

        elif isinstance(val, Iterable):
            output.append('<%s %s>%s</%s>' % ( key, make_attrstring(attr), convert_list(val, key), key,) )
                
        elif val is None:
            output.append(XML_NULL_element(key))
            
        else:
            raise TypeError('Unsupported data type: %s (%s)' % ( val, type(val).__name__) )
    return ''.join(output)

# Entry points ----- ----- ----- ----- -----


def generateXMLFile(reportObject, outPath):
    " basic conversion of a Python object into an XML string - returns True on success"
    LOG.info('entry point generateXMLFile')
    try:
        f = codecs.open(outPath, encoding='utf-8', mode='wb')

        f.write('<?xml version="1.0" encoding="UTF-8" ?>')
        f.write('<root>%s</root>' % (convert_dispatch(reportObject, parent="root"),))

        f.close()
    except IOError as e:
        LOG.error("I/O error({0}): {1} -- path: {2}".format(e.errno, e.strerror, outPath))
        return False
    
    return True


def generateXMLString(reportObject):
    " basic conversion of a Python object into an XML string - returns the string"
    LOG.info('entry point generateXMLString')

    output = list()
    output.append('<?xml version="1.0" encoding="UTF-8" ?>')
    output.append('<root>%s</root>' % (convert_dispatch(reportObject, parent="root"),))

    return u''.join(output).encode('utf-8')

#  Sanity tests ----- ----- ----- ----- -----

if __name__ == '__main__':
    """ sanity tests """
    import json

    rep1 = json.loads('{"organization":"Dunder Mifflin","reported_at":"2015-04-21","created_at":"2015-04-22",' +
                      '"inventory":[{"name":"paper","price":"2.00"},{"name":"stapler","price":"5.00"},{"name":' +
                      '"printer","price":"125.00"},{"name":"ink","price":"3000.00"}]}')
    
    rep2 = json.loads('{"organization":"Skynet Papercorp","reported_at":"2015-04-22","created_at":"2015-04-23",' +
                      '"inventory":[{"name":"paper","price":"4.00"}]}')

    rep3 = json.loads('{"organization":"Skynet Papercorp","reported_at":"2015-04-22","created_at":"2015-04-23",' +
                      '"inventory":[{"name":"paper","price":"4.00"}]}')
    
    for i in range3(151):
        rep3["inventory"].append({"name": "name_%s" %i, "price": "%s.00" %i}) # create a very large inventory
        
    rep4 = json.loads('{"organization":"Skynet Papercorp","reported_at":"2015-04-22","created_at":"2015-04-23",' +
                      '"inventory":[{"name":"paper","price":"4.00"}, {"internal": [{"name":"paper","price":"2.00"},' +
                      '{"name":"stapler","price":"5.00"},{"name":"printer","price":"125.00"},{"deeper":' +
                      '{"organization":"Skynet Papercorp","reported_at":"2015-04-22","created_at":"2015-04-23",' +
                      '"inventory":[{"name":"paper","price":"4.00"}]}},{"name":"ink","price":"3000.00"}]}]}')

    rep5 = json.loads('{"attribute":"eye color","value":"yellow","notes":"some notes here",' +
                      '"list":[{"left":"eye","right":"eye"}]}')
    # checked with pro.jsonlint.com to verify the test is not being fed malformed structures

    generateXMLFile(rep1, "tests/report_1.xml")
    generateXMLFile(rep2, "tests/report_2.xml")
    generateXMLFile(rep3, "tests/report_3.xml")  # large inventory
    generateXMLFile(rep4, "tests/report_4.xml")  # nested structure
    generateXMLFile(rep5, "tests/report_5.xml")

    print(generateXMLString(rep3))

    for i in (rep1, rep2, rep3, rep4, rep5,):
        print(json.dumps(i))
