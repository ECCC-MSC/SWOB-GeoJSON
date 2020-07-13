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
    
    # extract the swob xml source name '\\' is a windows filepath
    # if this is implemented on another OS make sure to fix the filepath split
    swob_name_split = swob_file.split('\\')
    swob_name = swob_name_split[len(swob_name_split) - 1]
    
    # make sure the xml is parse-able
    try:
        xml_tree = et.parse(swob_file)
    except:
        print("Error in parsing file")
        error = 1

    if not error:
        general_info_tree = xml_tree.findall('.//om:Observation/om:metadata/dset:set/dset:general', namespaces)
        general_info_elements = list(general_info_tree[0].iter())
        properties = {}
        
        # extract swob dataset
        for element in general_info_elements:
            value_list = []
            if 'name' in element.attrib.keys():
                if element.tag.split('}')[1] == 'dataset':
                    properties[element.tag.split('}')[1]] = element.attrib['name'].replace('/', '-')
                
        # add swob source name to properties
        properties["swob"] = swob_name
        
        # extract ID related properties
        identification_tree = xml_tree.findall('.//om:Observation/om:metadata/dset:set/dset:identification-elements', namespaces)
        identification_elements = list(identification_tree[0].iter())
        
        for element in identification_elements:

            if 'name' in element.attrib.keys():
                name = element.attrib['name']
                value = element.attrib['value']
                
                # This is the list of ID properties we want for our geoJson
                # Feel free to add to it, make sure the property exists in the
                # identification section of the xml!
                if name == 'stn_nam':
                    properties[name] = value
                elif name == 'tc_id':
                    properties[name] = value
                elif name == 'msc_id':
                    properties[name] = value
                elif name == 'clim_id':
                    properties[name] = value
                elif name == 'stn_elev':
                    elevation = value
                elif name == 'lat':
                    latitude = value
                elif name == 'long':
                    longitude = value
                else:
                    pass
               
        # set up cords and time stamps
        swob_values['coordinates'] = [longitude, latitude, elevation]
        
        time_sample = list(xml_tree.findall('.//om:Observation/om:samplingTime/gml:TimeInstant/gml:timePosition', namespaces)[0].iter())[0]
        properties['obs_date_tm'] = time_sample.text
        
        time_result = list(xml_tree.findall('.//om:Observation/om:resultTime/gml:TimeInstant/gml:timePosition', namespaces)[0].iter())[0]
        properties['processed_date_tm'] = time_result.text
        
        # extract the result data from the swob
        result_tree = xml_tree.findall('.//om:Observation/om:result/dset:elements', namespaces)
        result_elements = list(result_tree[0].iter())
        
        last_element = ''
        for element in result_elements:
            nested = element.iter()
            for nest_elem in nested:
                result_val = []
                value = ''
                uom = ''
                if 'name' in nest_elem.attrib.keys():
                    name = nest_elem.attrib['name']
                    if 'value' in nest_elem.attrib.keys():
                        value = nest_elem.attrib['value']
                    if 'uom' in nest_elem.attrib.keys():
                        if nest_elem.attrib['uom'] != 'unitless':
                            uom = nest_elem.attrib['uom']
                        
                    # element can be 1 of 3 things:
                    #   1. a data piece
                    #   2. a qa summary
                    #   3. a data flag
                    if name != 'qa_summary' and name != 'data_flag':
                        properties[name] = value
                        if uom:
                            properties[name + '_uom'] = uom
                        last_element = name
                    elif name == 'qa_summary':
                        properties[last_element + '_qa'] = value
                    elif name == 'data_flag':
                        properties[last_element + '_data_flags'] = value
        
        swob_values['properties'] = properties
        
        return swob_values
        
"""
visualizes the extracted data from the SWOB xml file
param: swob_dict: swob in memory
"""
def visualizeDict(dic):
    for key in dic.keys():
            print(key)
            if isinstance(dic[key], dict):    
                for key2 in dic[key]:
                    print('    ' + str(key2) + ' ' + str(dic[key][key2]))
            else:
                print('    ' + str(dic[key]))
            print('')
        

"""
Produce GeoJSON from dict
:param swob_dict: swob in memory
:returns: geojson
"""
def swob2geojson(swob_dict):
    json_output = {}
    
    # verify dictionary contains the data we need to avoid error
    if 'properties' in swob_dict.keys() and 'coordinates' in swob_dict.keys():
        json_output['type'] = 'Feature'
        json_output["geometry"] = {"type": "Point", "coordinates": swob_dict['coordinates']}
        json_output["properties"] = swob_dict["properties"]
        return json_output
    else:
        print('Error, incorrectly formated dictionary passed into swob2geojson')
        return
    
#Testing
string = 'C:\\Users\\Robert\\Desktop\\swob2geojson\\2020-06-08-0000-CAAW-AUTO-minute-swob.xml'
swob_dict = parse_swob(string)

geoJson = swob2geojson(swob_dict)

visualizeDict(geoJson)
#print(geoJson)
