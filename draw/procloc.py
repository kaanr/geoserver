#!/usr/bin/env python
# coding: utf-8

import os
import re
from pyproj import Transformer
import pandas as pd
import mapnik
import datetime
import logging


def define_unique(dirName):
    """
        Return a dictionary of unique filenames in directory dirName
        with keys=filenames and values=file extensions.
    """

    files = {}
    for folderName, subfolders, filenames in os.walk(dirName):
        for i in filenames:
            if os.path.splitext(i)[1] in ['.ext1', '.ext2', '.ext3']:
                files.setdefault(os.path.splitext(i)[0], [])
                files[os.path.splitext(i)[0]].append(os.path.splitext(i)[1])
    logging.info('Inside this directory next files was founded: files = %s',
                 files)
    return files


def find_locationPart(txtFile):
    """
        Process .txt-file <txtFile> to define parts separated by blank line.
        Return a part of file as a list of lines with statistic of locations.
    """
    # To remember indices of all blank lines - in loc files
    # always 2 empty lines.
    # File's part with statistic of locations starts with second empty line.
    emptyLineList = []
    if len(txtFile) > 1:
        for lineNumber in range(len(txtFile)):
            if txtFile[lineNumber] == '\n':
                # To remember empty line's index number to list <emptyLineList>.
                emptyLineList.append(lineNumber + 1)
    else:
        return []

    # To return the rest of the file after second empty line.
    return emptyLineList


def parse_main_part(lines, dframe):
    """
        Excerpt geographic coordinates from lines of file's partition
        and other useful statistic information.
        Return a dataframe with that information.
    """

    dictF = {
        'dateTime': '',
        'param1': '',
        'operator': '',
        'param2': '',
        'param3': '',
        'address': ''
    }

    # To create complex regular expression:
    addr_regexp = re.compile(r"((?P<address>.*)\()?", re.VERBOSE)
    param1_regexp = re.compile(r"=((?P<param1>\d*))?")
    param2_cid_regexp = re.compile(
        r"=((?P<operator>\D*)(?P<param2>\d*)-(?P<param3>\w*))?", re.VERBOSE)

    # Looping over partition of file to excerpt useful information:
    for stroke in lines:
        # Excerpt data from lines by regular expression
        mo_addr = addr_regexp.search(stroke.split('\t')[-1])
        mo_param1 = param1_regexp.search(stroke.split('\t')[1])
        mo_param2_cid = param2_cid_regexp.search(stroke.split('\t')[2])

        # Next, fill the dictionary dictF.
        dictF['dateTime'] = stroke.split('\t')[0]
        dictF['param1'] = None if mo_param1.group(
            'param1') == None else mo_param1.group('param1')
        dictF['operator'] = None if mo_param2_cid.group(
            'operator') == None else mo_param2_cid.group('operator')
        dictF['param2'] = None if mo_param2_cid.group(
            'param2') == None else mo_param2_cid.group('param2')
        dictF['param3'] = None if mo_param2_cid.group(
            'param3') == None else mo_param2_cid.group('param3')
        dictF['address'] = '' if mo_addr.group(
            'address') == None else mo_addr.group('address')

        # To append this dictionary to dataframe dframe.
        dframe = dframe.append(dictF, ignore_index=True)
    return dframe


def extract_coord(lines, dframe):
    """
        Excerpt geographic coordinates from lines of files partition
        and other useful statistic information.
        Return a dataframe with that information.
    """

    dictF = {
        'countEvents': 0,
        'percentage': 0,
        'operator': '',
        'param2': '',
        'param3': '',
        'address': '',
        'lat': '',
        'latDD': 0,
        'lon': '',
        'lonDD': 0,
        'azimuth': ''
    }

    # To create complex regex:
    coordRegex = re.compile(
        r'''
        (?P<countEvents>^\d+)               # Count of events.
        \s+\(                               # Just space and open parenthesis.
        ((?P<percentage>\d+(\.\w*)?))?      # Percentage from total events.
        (%\))?                              # Percentage of total events.
        # LAC and CellID.
        (\s+-\s(?P<operator>\D)(?P<param2>\d*)-(?P<param3>\w*)\s*-)?
        (\s*(?P<address>.*)\()?             # Address's text description.
        ((?P<lat>\w*),)?                    # Latitude in DMS.
        (\s*(?P<lon>\w*),)?                 # Longitude.
        (\s+(?P<azimuth>\d*)\s+-)?          # Azimuth.
        ''', re.VERBOSE)

    # Looping over partition of file to excerpt useful information:
    for string in lines:
        mo = coordRegex.search(string)
        dictF['countEvents'] = float(
            0 if mo.group('countEvents') is None else mo.group('countEvents'))
        dictF['percentage'] = float(
            0 if mo.group('percentage') is None else mo.group('percentage'))
        dictF['operator'] = '' if mo.group('operator') is None else mo.group(
            'operator')
        dictF['param2'] = '' if mo.group('param2') is None else mo.group(
            'param2')
        dictF['param3'] = '' if mo.group('param3') is None else mo.group(
            'param3')
        dictF['address'] = '' if mo.group('address') is None else mo.group(
            'address')
        dictF['lat'] = '' if mo.group('lat') is None else mo.group('lat')
        dictF['latDD'] = 0 if dictF['lat'] == '' else dms2dd(dictF['lat'])
        dictF['lon'] = '' if mo.group('lon') is None else mo.group('lon')
        dictF['lonDD'] = 0 if dictF['lon'] == '' else dms2dd(dictF['lon'])
        dictF['azimuth'] = '' if mo.group('azimuth') is None else mo.group(
            'azimuth')
        # To append this dictionary to dataframe
        dframe = dframe.append(dictF, ignore_index=True)
    return dframe


def dms2dd(crd):
    """
       Convert map coordinate in DMS (degrees, minutes, seconds)
       to decimal degree.
    """
    if crd is None:
        return None
    #lat_deg, lat_min, lat_sec, lat_dir = re.split('[^\d]+', lat)
    # Split string by any non-digit symbol.
    crd_deg, crd_min, crd_sec, crd_dir = re.split('[^\d]+', crd)
    #lon_deg, lon_min, lon_sec, lon_dir = re.split('[^\d]+', lon)
    #print(f"Latitude in DMS: {lat_deg},{lat_min},{lat_sec}.")
    #print(f"Longitude in DMS: {lon_deg},{lon_min},{lon_sec}.")
    crd_dd = float(crd_deg) + float(crd_min) / 60 + float(crd_sec) / (60 * 60)
    #lat_dd = float(lat_deg) + float(lat_min)/60 + float(lat_sec)/(60*60)
    #lon_dd = float(lon_deg) + float(lon_min)/60 + float(lon_sec)/(60*60)
    #print(f"Latitude in DD: {lat_dd}.")
    #print(f"Longitude in DD: {lon_dd}.")
    #return lat_dd, lon_dd
    return crd_dd


def dd2WebCoord(lat, lon):
    """
        Convert point from geographic coordinate system (EPSG 4326) to
        projected coordinate system (EPSG 3857).
        Return lat, lon in meters.
    """

    transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
    x, y = transformer.transform(lat, lon)
    x = round(x, 2)
    y = round(y, 2)
    return (x, y)


def render_map(x, y, file, dir_output):
    """
        Render map box with marker in point(lat, lon)
    """
    mapnik_xml = "/home/osm/src/openstreetmap-carto/mapnik.xml"
    epsg_3857 = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 \
                 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs"

    # To define the boundaries of box
    box_bound = [x - 2000, y - 2000, x + 2000, y + 2000]

    # To create a map object
    m = mapnik.Map(1024, 1024)
    mapnik.load_map(m, mapnik_xml)

    # To create point style
    s = mapnik.Style()  # style object to hold rules
    r = mapnik.Rule()  # rule object to hold symbolizers

    # To create symbolizer
    point_sym = mapnik.MarkersSymbolizer()
    # point_sym.fill = mapnik.Color('red')
    # point_sym.allow_overlap = True
    # point_sym.width = mapnik.Expression("90")
    # point_sym.height = mapnik.Expression("90")
    # point_sym.opacity = .5
    # point_sym.strokewidth = mapnik.Expression("2")
    point_sym.file = 'static/img/marker-icon-2x-red.png'
    point_sym.allow_overlap = True

    r.symbols.append(point_sym)  # add the symbolizer to the rule object
    s.rules.append(r)  # add the rule to the styel object
    m.append_style('center', s)  # append style to map

    # To create datasource
    ds = mapnik.MemoryDatasource()
    f = mapnik.Feature(mapnik.Context(), 1)

    f.geometry = f.geometry.from_wkt("POINT({} {})".format(x, y))
    ds.add_feature(f)

    center_layer = mapnik.Layer('center_layer')
    center_layer.srs = epsg_3857
    center_layer.datasource = ds
    center_layer.styles.append('center')
    m.layers.append(center_layer)

    bbox = mapnik.Box2d(*box_bound)
    m.zoom_to_box(bbox)
    mapnik.render_to_file(m, os.path.join(dir_output,
                                          (file + '_2000' + '.png')))
    logging.info(f"\t\tRendered image to {file}_2000.png.")


def start(path):
    """
        Start function.
    """

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        filename=path + "/render.log")
    logging.info('Start process task!')

    dictOfLocParam = {
        'countEvents': [],
        'percentage': [],
        'operator': [],
        'param2': [],
        'param3': [],
        'address': [],
        'lat': [],
        'latDD': 0,
        'lon': [],
        'lonDD': 0,
        'azimuth': []
    }

    dictOfLoc_dateTime = {
        'dateTime': [],
        'param1': [],
        'operator': [],
        'param2': [],
        'param3': [],
        'address': []
    }

    # Content of report html-file.
    html_first_part = "<html><head><title>Анализ местоположений</title>"
    html_first_part += "<style>h1, h2, h3 {text-align: center}"
    html_first_part += "table, th, td {border: 1px solid black"
    html_first_part += "; border-collapse: collapse; border-spacing:8px}"
    html_first_part += "th {background-color:#3DBBDB;color:white}"
    html_first_part += "tr {text-align: center}"
    html_first_part += "img { border: 1px solid #ddd; /* Gray border */"
    html_first_part += "border-radius: 4px; /* Rounded border */"
    html_first_part += "padding: 5px; /* Some padding */"
    html_first_part += "width: 150px; /* Set a smal width */ }"
    html_first_part += "img:hover { "
    html_first_part += "box-shadow: 0 0 2px 1px rgba(0,140,186,0.5)"
    html_first_part += "; }"
    html_middle_part = "</style>" + "</head>" + "<body>"
    html_middle_part += "<h1>Анализ местоположений объекта.</h1>"
    html_middle_part += "<p>В таблице представлены 5 местоположений с наибольшим "
    html_middle_part += "количеством событий: </p>"
    html_end_part = "</body></html>"

    # To find all unique number in request
    # and save them in <dict_files>
    dict_files = define_unique(path)

    # To read the style.css file for inserting later in report html-file.
    with open('report_style.css') as f:
        styles = f.read()

    # To read the script.css file for inserting later in report html-file.
    with open('report_script.js') as f:
        script = f.read()

    # To process all files one by one.
    for file in dict_files:
        # To create two empty dataframe for each loc-file.
        df_loc = pd.DataFrame(dictOfLocParam)
        df_dt = pd.DataFrame(dictOfLoc_dateTime)

        # To choose loc-file.
        if 'loc' not in dict_files[file]:
            logging.info(
                f'Warning! There is no location file for this number - {file}.'
            )
            continue
        else:
            filename = os.path.join(path, (file + 'loc'))

        # To open loc-file.
        with open(filename, encoding='windows-1251') as f:
            # To read file and save content in <lines>.
            lines = f.readlines()

        # To find out all empty line indices in file.
        empty_lines_index = find_locationPart(lines)
        logging.info('********************************************')
        logging.info(
            f"\tStart to process file: {os.path.basename(filename) }.")
        logging.info(f"\t\tEmpty line indices: {empty_lines_index}")

        # To save second part of file with date and time.
        loc_dt_filepart = lines[1:empty_lines_index[0] - 1]

        # To save third part of file with location statistic:
        loc_stat_filepart = lines[empty_lines_index[1]:]

        # To process part of file with statistic of location:
        if loc_stat_filepart != [] and loc_dt_filepart != []:
            print('********************************************')
            print(filename)

            # To extract location data and save in dataframe.
            df_loc = extract_coord(loc_stat_filepart, df_loc)

            # To extract datetime data and save in dataframe.
            df_dt = parse_main_part(loc_dt_filepart, df_dt)
        else:
            logging.info('!!!!!!!!C A U T I O N!!!!!!!!!!!!')
            logging.info(f"ATTENTION: {filename}.")
            print('ATTENTION')

            # To escape this file and go to the next.
            continue

        # To group dataframe by column 'address' and sum by columns
        # 'countEvents' and 'percentage'.
        df_by_addr = df_loc.groupby(
            ['address', 'lat', 'latDD', 'lon',
             'lonDD'])[['countEvents', 'percentage']].sum().reset_index()

        # To define most frequent locations by sorting in descending
        # order and reset index.
        df_by_addr = df_by_addr.sort_values(
            'countEvents', ascending=False).reset_index(drop=True)

        # Html tags container for image and table.
        html_container = ""

        df_for_html = df_by_addr.iloc[:5, [0, 2, 4, 5, 6]].rename(
            columns={
                'address': 'Адрес',
                'latDD': 'Широта',
                'lonDD': 'Долгота',
                'countEvents': 'Кол-во событий тех.',
                'percentage': '%'
            })
        html_container += "<p>" + df_for_html.to_html() + "</p>"
        html_container += "<br><hr>"
        html_container += "<h3>Ниже представлены снимки карт указанных местоположений. "
        html_container += "Также представлена подробная информация"
        html_container += "(см. последние цифры ID).</h3>"

        # To select from df_loc all rows for first five max locations.
        for row in df_by_addr.iloc[:5, :].itertuples():
            if row[1] == 'No address':
                logging.info(
                    "There are no coordinates for this location so do \
                             not render the map.")
            else:
                # To choose only columns 3 and 5 (latDD and lonDD values).
                x, y = row[3:6:2]

                # To convert coordinates from EPSG4326 to EPSG3857.
                x, y = dd2WebCoord(x, y)

                # Then render map for this points (coordinates).
                render_map(x, y, file + '_' + str(row[0]), path)

                # Fill the html-content part of report file.
                html_container += f"<p>{row[0]} - {row[1]}"
                html_container += f" - {row[6]} событий. "
                html_container += f"<a href=\"javascript:PopUpShow('#chronology{row[0]}')\">"
                html_container += "Хронология по этому МП.</a></p>"
                html_container += f"<div class='b-popup' id='chronology{row[0]}'><div class='wrapper'>"
                html_container += "<div class='b-popup-content'>"
                html_container += f"<a href=\"javascript:PopUpHide('#chronology{row[0]}')\">Скрыть</a><br>"
                html_container += "<div class='popup_internal'>"
                html_container += f"{df_dt[df_dt['address'] == row[1]].reset_index(drop=True).to_html()}</div></div></div></div>"
                html_container += f"<a target='_blank' href=\"{file}_{row[0]}_2000.png\">"
                html_container += f"<img src=\"{file}_{row[0]}_2000.png\" alt=\"Location\"></a>"
                html_container += "<h4>Кол-во событий :</h4>"
                html_container += f"{df_loc[df_loc['address']==row[1]].reset_index(drop=True).to_html()}<br><hr width='50%'><br>"

        # Create a report html-file.
        with open(os.path.join(path, 'loc_analyze_' + file + '.html'),
                  'w') as f:
            f.write(html_first_part + styles + html_middle_part +
                    html_container + script + html_end_part)

        logging.info(f"\tFinish to process file {os.path.basename(filename)}.")
