# To run this code, need following packages
# pip install bokeh
# sudo pip install bokeh --upgrade
# python
#>>> import bokeh.sampledata
#>>> bokeh.sampledata.download()

from bokeh.io import show
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    ColorBar, LinearColorMapper, FixedTicker, NumeralTickFormatter, BasicTicker,
    Callback, Select, CustomJS,
    LabelSet, TapTool
)
from bokeh.models.layouts import VBox,HBox
from bokeh.palettes import Blues9 as palette
from bokeh.plotting import figure, gridplot
from bokeh.layouts import widgetbox

from bokeh.sampledata.us_states import data as states_map
#from bokeh.sampledata.unemployment import data as unemployment

import csv
import numpy as np
import requests


###############################################
#give the coordinates of the world via json url
#parmas:
#   @features: dicts of country name and polygon boundaries geo location
#              read from world-geo json url
#return:
#   ColumnDataSource object to plot
###############################################

def get_geo_world():
    url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
    r = requests.get(url)
    geo_json_data = r.json()
    features = geo_json_data['features']
    depth = lambda L: isinstance(L, list) and max(map(depth, L))+1
    xs = []
    ys = []
    names = []
    for feature in features:
        name = feature['properties']['name']
        coords = feature['geometry']['coordinates']
        nbdims = depth(coords)
        # one border
        if nbdims == 3:
            pts = np.array(coords[0], 'f')
            xs.append(pts[:, 0])
            ys.append(pts[:, 1])
            names.append(name)
        # several borders
        else:
            for shape in coords:
                pts = np.array(shape[0], 'f')
                xs.append(pts[:, 0])
                ys.append(pts[:, 1])
                names.append(name)
    source = ColumnDataSource(data=dict(x = xs, y = ys, name = names,))
    return source




###############################################
#give the count data of us each state according to selector
#params:
#   @occupation_set: a list of occupation id that user want, default as in each state add all count together
#return:
#   an dict of count data, contains key of 'State' and numeric number of occupation id
###############################################

def get_count_us_continent(occupations_set):#, add_all = None):
    filepath = "Count-allOccupations-Continent.csv"
    with open(filepath, "r") as csvfile:
        data = csv.reader(csvfile)
        headers = data.__next__()
        state_count_dict = {}
        state_count_dict[headers[0]] = []
        for i in range(1,len(headers)):
          headers[i] = int(headers[i])
          state_count_dict[headers[i]] = []
        for row in data:
            # the first item of each row is an instance of 'State', not an int
            state_count_dict[headers[0]].append(row[0])
            for h, v in zip(headers[1:], row[1:]):
                state_count_dict[h].append(int(v))

    state_count = np.zeros(len(state_count_dict['State']))
    #if not add_all:
    # add all occupations' count data together
    #    keys = [key for key in state_count_dict.keys() if key != 'State']
    #    for i in keys:
    #        state_count = [sum(x) for x in zip(state_count, state_count_dict[i])]
    #else:
    # add only required count data from occupations_set
    for i in occupations_set:
        state_count = [sum(x) for x in zip(state_count, state_count_dict[i])]

    return state_count




###############################################
#give the coordinates and count data of us states
#params:
#   @state_count_experience_selector_dict: dict of different count data on each state according to selection,
#                      here state are already sorted alphabetically in .csv file.
#   @state_count_careerarea_selector_dict: dict of count data on each state according to doubel selection
#   @state_map: sampledata from bokeh moduls, multipolygon of us map data
#return:
#   ColumnDataSource object to plot
###############################################

def get_source_geo_and_count_us_continent(state_count_experience_selector_dict, state_count_careerarea_selector_dict, states_map):
    states = {code: state for code, state in states_map.items()}
    states_sort_by_name = states.values()
    states_sort_by_name = sorted(states_sort_by_name, key = lambda x : x['name'])
    # sort states' geo by its name, it helps decide the order of count data. cause .csv data is already sorted by state name

    state_xs = [state["lons"] for state in states_sort_by_name]
    state_ys = [state["lats"] for state in states_sort_by_name]
    state_names = [state["name"] for state in states_sort_by_name]

    source = ColumnDataSource(data=dict(x = state_xs, y = state_ys,
        name = [name + ", United States" for name in state_names]))

    state_count_total = np.zeros(len(list(state_count_experience_selector_dict.values())[0]))
    for name, state_count in state_count_experience_selector_dict.items():
        state_count_total = [sum(x) for x in zip(state_count_total, state_count)]
        source.add(data = state_count, name = 'count'+name)
    source.add(data = state_count_total, name = 'count_all')
    source.add(data = state_count_total, name = 'count')

    for experience_selector_name, state_count_careerarea in state_count_careerarea_selector_dict.items():
        careerarea_selector_name_initial = 'count'+experience_selector_name
        for careerarea_name, state_count in state_count_careerarea.items():
            source.add(data = state_count, name = careerarea_selector_name_initial + careerarea_name)

    return source




###############################################
#gives a colormapping method and colorbar (not use it any more)
#params:
#   @palette: from bokeh library
#   @quantile_level: the amount of quantile levels that user want to plot the data
#   @data: data that needs to be plotted with different levels of quantile
#return:
#   ColorMapper object and list of int as ticker
###############################################
def color_map_ticker(palette, quantile_level, data):
    p = palette[:quantile_level - len(palette)]
    p.reverse()
    colormap = LinearColorMapper(palette=p, low=min(data), high=max(data))

    fixedticker = [min(data) + 1 + (max(data) - min(data) - 1) * i / quantile_level#, i/(quantile_level)*100)
        for i in range(0,quantile_level+1) ]

    #colormap, legendmap = [],[]
    #for c in state_count:
    #    index = 0
    #    while(c > quantile[index] and index < len(quantile)):
    #        index += 1
    #    colormap.append(palette[index-1])

    return colormap, fixedticker




###############################################
#gives info of every occupation id via .csv file
#return:
#   dicts: firststep, starterjob, occupationgroup, careerarea that maps to a set of occupation ids.
#   dicts: group_name maps group id to its name, careerarea_name maps careerarea id to its name
###############################################
def get_occupation_info():
    with open("Occupationid_firststep_group_careerarea.csv", "r") as csvfile:
        data = csv.reader(csvfile)
        #headers = data.__next__()
        next(data, None)
        occupations_firststep = {"False": [], "True": []}
        occupations_starterjob = {"False": [], "True": []}
        occupations_careerarea = {}
        occupations_occupationgroup = {}
        group_name = {}
        careerarea_name = {}
        for row in data:
            Id = int(row[0])
            if row[1] == 'FALSE':
                occupations_firststep["False"].append(Id)
            else:
                occupations_firststep["True"].append(Id)
            if row[2] == 'FALSE':
                occupations_starterjob["False"].append(Id)
            else:
                occupations_starterjob["True"].append(Id)
            group_id = int(row[3])
            group_name[group_id] = row[4]
            if group_id in occupations_occupationgroup.keys():
                occupations_occupationgroup[group_id].append(Id)
            else:
                occupations_occupationgroup[group_id] = []
                occupations_occupationgroup[group_id].append(Id)
            careerarea_id = int(row[5])
            careerarea_name[careerarea_id] = row[6]
            if careerarea_id in occupations_careerarea.keys():
                occupations_careerarea[careerarea_id].append(Id)
            else:
                occupations_careerarea[careerarea_id] = []
                occupations_careerarea[careerarea_id].append(Id)

    return (occupations_firststep,
            occupations_starterjob,
            occupations_occupationgroup,
            occupations_careerarea,
            group_name,
            careerarea_name)




###############################################
#give the coordinates and count data of us states
#params:
#   @sset_2_year, set_1_year, set_none: sets of occupation id from experience selection
#   @careerarea: career data maps area id to sets of occupation id
#   @careerarea_name: career data maps area name to its name
#return:
#   - dict of careerarea total count in all states according to 3 experience selectors (used for bar plot)
#   - dict of careerarea count in each state according to 3 experience selectors (used for career selector)
###############################################
def get_careerarea_count_selector(set_2_year, set_1_year, set_none, careerarea, careerarea_name):
    careerarea_count_total_2_year = {}
    careerarea_count_total_1_year = {}
    careerarea_count_total_none = {}

    careerarea_count_all = {}
    careerarea_count_2_year = {}
    careerarea_count_1_year = {}
    careerarea_count_none = {}

    for k,v in careerarea.items():
        temp_career_set_2_year = set(v)&set(set_2_year)
        temp_career_set_1_year = set(v)&set(set_1_year)
        temp_career_set_none = set(v)&set(set_none)

        temp_count_all = get_count_us_continent(v)
        temp_count_2_year = get_count_us_continent(temp_career_set_2_year)
        temp_count_1_year = get_count_us_continent(temp_career_set_1_year)
        temp_count_none = get_count_us_continent(temp_career_set_none)

        temp_sum_2_year = sum(temp_count_2_year)
        temp_sum_1_year = sum(temp_count_1_year)
        temp_sum_none = sum(temp_count_none)

        name = careerarea_name[k]

        careerarea_count_total_2_year[name] = temp_sum_2_year
        careerarea_count_total_1_year[name] = temp_sum_1_year
        careerarea_count_total_none[name] = temp_sum_none

        careerarea_count_all[name] = temp_count_all
        careerarea_count_2_year[name] = temp_count_2_year
        careerarea_count_1_year[name] = temp_count_1_year
        careerarea_count_none[name] = temp_count_none

    careerarea_count_total_dict = dict(
        _2_year = careerarea_count_total_2_year,
        _1_year = careerarea_count_total_1_year,
        _none = careerarea_count_total_none)

    state_count_careerarea_selector_dict = dict(
        _all_ = careerarea_count_all,
        _2_year_ = careerarea_count_2_year,
        _1_year_ = careerarea_count_1_year,
        _none_ = careerarea_count_none)

    return careerarea_count_total_dict, state_count_careerarea_selector_dict



###############################################
#give the coordinates and count data of us states
#params:
#   @careerarea_count_dict: dict of careerarea count according to 3 selectors
#return:
#   ColumnDataSource object to plot
###############################################
def get_source_careerarea_experience_count(careerarea_count_total_dict):
    experience_selector = ['count_all']
    experience_selector.extend(np.zeros(22))
    color = ['#6baed6'] * 23
    career_source = ColumnDataSource(data=dict(
        y = range(1,23+1),
        label_x = np.zeros(23),
        experience_selector = experience_selector,
        color = color,
        color2 = color,
        ))

    careerarea_count_all = {}
    for name, careerarea_count in careerarea_count_total_dict.items():
        x_temp = []
        tag_temp = []
        width_temp = []
        for k,v in sorted(careerarea_count.items(), key = lambda x: x[1]):
            x_temp.append(v/2)
            tag_temp.append(k)
            width_temp.append(v)
            if k in careerarea_count_all.keys():
                careerarea_count_all[k]+=v
            else:
                careerarea_count_all[k]=v

        career_source.add(data = width_temp, name = 'width'+name)
        career_source.add(data = x_temp, name = 'x'+name)
        career_source.add(data = tag_temp, name = 'tag'+name)

    width = sorted(careerarea_count_all.values())
    x = [v/2 for v in sorted(careerarea_count_all.values())]
    tag = [k for k,v in sorted(careerarea_count_all.items(), key = lambda x: x[1])]
    career_source.add(data = width, name = 'width')
    career_source.add(data = width, name = 'width_all')
    career_source.add(data = x, name = 'x')
    career_source.add(data = x, name = 'x_all')
    career_source.add(data = tag, name = 'tag')
    career_source.add(data = tag, name = 'tag_all')

    return career_source




###############################################
#print map with all countries in the world and give them a country name hovertool
###############################################
palette1 = ['#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
mp = figure(
    title="Job posting distribution over US",
    tools=TOOLS, toolbar_location="above",
    x_axis_location=None, y_axis_location=None,
    plot_width=1050, plot_height=680, x_range=(-160,-55), y_range=(7,75)
)
mp.grid.grid_line_color = None
mp.title.text_font_size = '20pt'

#print world map as background
mp1 = mp.patches(
    'x', 'y', source=get_geo_world(),
    fill_color="#F1EEF6", fill_alpha=0.7, line_width=0.5)

mp.add_tools(HoverTool(renderers=[mp1],
    point_policy = "follow_mouse",
    tooltips = {
        "Name": "@name",
        "(Lon, Lat)":
        "($x, $y)",}))


#print us states level map and coloring according to count data
#count_total = get_count_us_continent()
#source_total = get_source_geo_and_count_us_continent(dict(count_total = count_total), states_map)
#color_mapper, fixed_ticks = color_map_ticker(palette, 5, count_total)
#color_bar = ColorBar(color_mapper=color_mapper, ticker=FixedTicker(ticks = fixed_ticks),
#    formatter = NumeralTickFormatter(format="0.0"), label_standoff=14, border_line_color=None, location=(0,0))
#mp2 = mp.patches('x', 'y', source=source_total, fill_color={'field': 'count', 'transform': color_mapper},
#    fill_alpha=0.7, line_color="grey", line_width=0.5)
#mp.add_layout(color_bar, 'right')
#mp.add_tools(HoverTool(renderers=[mp2], point_policy = "follow_mouse", tooltips = {"Name": "@name", "Job posting amount": "@count",
#    "(Lon, Lat)": "($x, $y)",}))
#show(mp)

############################################
#get the new set of occupations according to selection
############################################

firststep, starterjob, occupationgroup, careerarea, group_name, careerarea_name = get_occupation_info()

#get the sets of occupations under different experience selectors
set_2_year = firststep['True']
set_1_year = set(firststep['False'])&set(starterjob['True'])
set_none = set(firststep['False'])&set(starterjob['False'])

#get the dicts of total count and count in each state of each career area under experience selectors
careerarea_count_total_dict, state_count_careerarea_selector_dict = get_careerarea_count_selector(
        set_2_year,
        set_1_year,
        set_none,
        careerarea,
        careerarea_name)


#print the career area count bar
career_source = get_source_careerarea_experience_count(careerarea_count_total_dict)

career_area_bar = figure(title="Select career areas",
    x_axis_location=None, y_axis_location = None,
    width=290, height=642, tools = "reset", toolbar_location="above", #y_range=career_source.data('name'),
    x_range = (0, max(career_source.data['width'])))
career_area_bar.grid.grid_line_color = None
career_area_bar.title.text_font_style = 'normal'

bar = career_area_bar.rect(
    x='x', y='y',
    width='width',
    height=0.4, color = 'color',
    source = career_source)

career_labels = LabelSet(
    x="label_x", y="y",
    text="tag",
    y_offset=5, x_offset = 2,
    text_font_size="8pt", text_color="#555555",
    source=career_source, text_align='left')

career_area_bar.add_layout(career_labels)

career_area_bar.add_tools(HoverTool(renderers=[bar],
    point_policy = "follow_mouse",
    tooltips = {
        "career area": "@tag",
        "total count": "@width"}))



############################################
#print the map that relates to two selectors
############################################

#get the count in each state of each experience selector
count_2_year = get_count_us_continent(set_2_year )
count_1_year = get_count_us_continent(set_1_year)
count_none = get_count_us_continent(set_none)

#make these count data into a dict
state_count_experience_selector_dict = dict(
    _none = count_none,
    _1_year = count_1_year,
    _2_year = count_2_year)

#get the source data based on experience selector and careerarea selector
source = get_source_geo_and_count_us_continent(
    state_count_experience_selector_dict,
    state_count_careerarea_selector_dict,
    states_map)


###
#here I have a bug that the color bar text of map cannot change according to selectors' changing.
#It is mainly because the argument of colobar model in bokeh does not support specific source data
#my way of solving this bug is to show the percent instead of specific numbers
###

#color_mapper, fixed_ticks = color_map_ticker(palette, 5, source.data['count'])

mp2 = mp.patches('x', 'y', source=source,
    fill_color={'field': 'count', 'transform': LinearColorMapper(palette=palette1)},
    fill_alpha=0.7, line_color="grey", line_width=0.5)

#color_bar = ColorBar(color_mapper=color_mapper, ticker=FixedTicker(ticks = fixed_ticks),
#    formatter = NumeralTickFormatter(format="0.0"), label_standoff=14, border_line_color=None, location=(0,0))
color_bar = ColorBar(
    color_mapper = LinearColorMapper(palette=palette1),
        #low = min(source.data['count']),
        #high = max(source.data['count'])),
    ticker=BasicTicker(),
    formatter = NumeralTickFormatter(format="0.0%"),
    label_standoff=14, border_line_color=None, location=(0,0))
#print(color_bar)

mp.add_layout(color_bar, 'right')

mp.add_tools(HoverTool(renderers=[mp2],
    point_policy = "follow_mouse",
    tooltips = {
        "Name": "@name",
        "Job posting amount": "@count",
        "(Lon, Lat)": "($x, $y)",}))



###############################################
#callbacks
###############################################
callback_experience = CustomJS(args=dict(
    source1 = source,
    source2 = career_source,
    color_bar = color_bar),
    code="""
        var f = cb_obj.get('value');
        var data1 = source1.get('data');
        var count = data1['count'];

        var mapper = color_bar.get('color_mapper');
        var mapper_low = mapper.get('low');
        var mapper_high = mapper.get('high');

        var data2 = source2.get('data');
        var width = data2['width'];
        var x = data2['x'];
        var tag = data2['tag'];
        var experience_selector = data2['experience_selector'][0]

        if (f == 'None') {
            for (i = 0; i < count.length; i++) {
                count[i] = data1['count_none'][i];
            }
            for (j = 0; j < width.length; j++){
                wjdth[i] = data2['width_none'][j];
                x[j] = data2['x_none'][j];
                tag[j] = data2['tag_none'][j];
            }
            experience_selector = "count_none"
        }else if (f == 'At least 1 year') {
            for (i = 0; i < count.length; i++) {
                count[i] = data1['count_1_year'][i];
            }
            for (j = 0; j < width.length; j++){
                width[j] = data2['width_1_year'][j];
                x[j] = data2['x_1_year'][j];
                tag[j] = data2['tag_1_year'][j];
            }
            experience_selector = "count_1_year"
        }else if (f == 'At least 2 year'){
            for (i = 0; i < count.length; i++) {
                count[i] = data1['count_2_year'][i];
            }
            for (j = 0; j < width.length; j++){
                width[j] = data2['width_2_year'][j];
                x[j] = data2['x_2_year'][j];
                tag[j] = data2['tag_2_year'][j];
            }
            experience_selector = "count_2_year"
        }else{
            for (i = 0; i < count.length; i++) {
                count[i] = data1['count_all'][i];
            }
            for (j = 0; j < width.length; j++){
                width[j] = data2['width_all'][j];
                x[j] = data2['x_all'][j];
                tag[j] = data2['tag_all'][j];
            }
            experience_selector = "count_all"
        }
        mapper_low = Math.min(count);
        mapper_high = Math.max(count);

        source1.trigger('change');
        source2.trgger('change');
        bar.trigger('change');
    """)


callback_career = CustomJS(args=dict(
    source1 = source,
    source2 = career_source),
    code="""
        var inds = cb_obj.get('selected')['1d'].indices;

        var data1 = source1.get('data');
        var count = data1['count'];

        var data2 = source2.get('data');
        var tag = data2['tag'];
        var experience_selector_name = data2['experience_selector'][0];
        var color = data2['color'];

        num = 0
        for (i = 0; i<color.length; i++){
            if(color[i] == "#08519c"){num += 1;}
        }

        for (i = 0; i < inds.length; i++) {
            careerarea_selector_name = experience_selector_name + "_"+ tag[inds[i]];
            if (color[inds[i]] == "#08519c"){
                color[inds[i]] = data2['color2'][inds[i]];
                for(j = 0; j < count.length; j++){
                    if (num == 0){
                        temp = data1[experience_selector_name][j];
                    }else{
                        temp = count[j];
                    }
                    temp = temp - data1[careerarea_selector_name][j];
                    if(temp <= 0){
                        count[j] = data1[experience_selector_name][j];
                    }else{
                        count[j] = temp
                    }
                }
            }
            else{
                color[inds[i]] = "#08519c";
                for(j = 0; j < count.length; j++){
                    if (num == 0){
                        temp = 0;
                    }else{
                        temp = count[j];
                    }
                    count[j] = temp + data1[careerarea_selector_name][j];
                }
            }
        }
        source1.trigger('change');
        source2.trigger('change');
    """)

######################################################
#Deploy widget, call back
######################################################
career_area_bar.add_tools(TapTool(renderers=[bar],
    callback = callback_career))

select_experience = Select(
    title="Select postings that require experience of:",
    value='All',
    options= ['All', 'None', 'At least 1 year', 'At least 2 year'],
    callback = callback_experience)

#Display data
multi_filter = VBox(widgetbox(select_experience), career_area_bar)
tot =  HBox(multi_filter, gridplot([[mp]]))


show(tot)
