# =================================================================
#
# Author: Thinesh Sornalingam <thinesh.sornalingam@canada.ca>,
#         Robert Westhaver <robert.westhaver.eccc@gccollaboration.ca>
#
# Copyright (c) 2020 Thinesh Sornalingam, Robert Westhaver
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import os
import sys
import logging
import xml.etree.ElementTree as et


LOGGER = logging.getLogger(__name__)


"""
Read swob at swob_path and return object 
:param swob_path: file path to SWOB XML
:returns: dictionary of SWOB
"""
def parse_swob(swob_file):
    namespaces = {'gml': 'http://www.opengis.net/gml', 
              'om': 'http://www.opengis.net/om/1.0', 
              'xlink': 'http://www.w3.org/1999/xlink',
              'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
              'dset': 'http://dms.ec.gc.ca/schema/point-observation/2.0'}
    
    swob_values = {}
    error = 0
    elevation = ''
    latitude = ''
    longitude = ''
    
    try:
        xml_tree = et.parse(swob_file)
    except:
        print("Error in parsing file")
        error = 1

    if not error:
        general_info_tree = xml_tree.findall('.//om:Observation/om:metadata/dset:set/dset:general', namespaces)
        general_info_elements = list(general_info_tree[0].iter())
        properties = {}
        
        for element in general_info_elements:
            value_list = []
            if 'name' in element.attrib.keys():
                for key in element.attrib.keys():
                    if key == 'name':
                        value_list.append(element.attrib[key].replace('/', '-'))
                    else:
                        value_list.append(element.attrib[key])
                if len(value_list) > 1:
                    properties[element.tag.split('}')[1]] = value_list
                else:
                    properties[element.tag.split('}')[1]] = value_list[0]
        
        swob_values['properties'] = properties
        
        identification_tree = xml_tree.findall('.//om:Observation/om:metadata/dset:set/dset:identification-elements', namespaces)
        identification_elements = list(identification_tree[0].iter())
        identifications = {}
        
        for element in identification_elements:
            value_list = []
            if 'name' in element.attrib.keys():
                for key in element.attrib.keys():
                    if key == 'name':
                        if element.attrib[key] == 'stn_elev':
                            elevation = element.attrib['value']
                        elif element.attrib[key] == 'lat':
                            latitude = element.attrib['value']
                        elif element.attrib[key] == 'long':
                            longitude = element.attrib['value']
                    else:
                        value_list.append(element.attrib[key])
                
                identifications[element.attrib['name']] = value_list
                
        swob_values['identification'] = identifications
        
        time_sample = list(xml_tree.findall('.//om:Observation/om:samplingTime/gml:TimeInstant/gml:timePosition', namespaces)[0].iter())[0]
        swob_values['sample-time'] = time_sample.text
        
        time_result = list(xml_tree.findall('.//om:Observation/om:resultTime/gml:TimeInstant/gml:timePosition', namespaces)[0].iter())[0]
        swob_values['result-time'] = time_result.text
        
        result_tree = xml_tree.findall('.//om:Observation/om:result/dset:elements', namespaces)
        result_elements = list(result_tree[0].iter())
        results = {}
        
        last_element = ''
        for element in result_elements:
            nested = element.iter()
            for nest_elem in nested:
                result_val = []
                if 'name' in nest_elem.attrib.keys():
                    for key in nest_elem.attrib.keys():
                        if key == 'name':
                            pass
                        else:
                            result_val.append(nest_elem.attrib[key])
                    results[nest_elem.attrib['name']] = result_val
                    last_element = nest_elem.attrib['name']
                else:
                    for key in nest_elem.attrib.keys():
                        result_val.append(nest_elem.attrib[key])
                    results[last_element + '_QA'] = result_val
        
        swob_values['results'] = results
        
        for key in swob_values.keys():
            print(key)
            if isinstance(swob_values[key], dict):    
                for key2 in swob_values[key]:
                    print('    ' + str(key2) + ' ' + str(swob_values[key][key2]))
            else:
                print('    ' + str(swob_values[key]))
            print('')
            
        
        
        

"""
Produce GeoJSON from dict
:param swob_dict: swob in memory
:returns: geojson
"""
def swob2geojson(swob_dict):
    pass
    

string = 'C:\\Users\\Robert\\Desktop\\swob2geojson\\2020-06-08-0000-CAAW-AUTO-minute-swob.xml'
parse_swob(string)
