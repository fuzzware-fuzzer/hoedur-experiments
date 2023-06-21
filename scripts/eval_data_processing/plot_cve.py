from functools import reduce
from pathlib import Path
from IPython import embed
from plotting import PlotStyle, PlotBackend, AltairPlotBackend, utc_timestamp_to_dt, PlotDataQuery, Selection, ChartStyle, ChartLayout
import pandas as pd
import copy
import sys
import altair as alt
import base64

from config import *

EXPERIMENT_NAME = '01-bug-finding-ability'
EXPERIMENT = EXPERIMENTS[EXPERIMENT_NAME]
plot_data = PlotDataQuery(EXPERIMENT)
selection = plot_data.experiment_selection()

pd.set_option('display.max_rows', 500)
plot_builder = AltairPlotBackend(selection.selections())

# Create for each TARGET one plot. The key is defined in `PlotDataQuery.experiment_selection()`.
plot_builder = plot_builder.chart_grouping_key('TARGET')

# In each plot, colorize the lines according to the key `Fuzzers`.
# The key is defined in `PlotDataQuery.experiment_selection()`.
plot_builder = plot_builder.colorization_key('Fuzzers')

def encode_image(image_path: str) -> str:
    import base64, io
    from PIL import Image

    image = Image.open(image_path)
    output = io.BytesIO()
    image.save(output, format='PNG')
    encoded_string = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()
    return encoded_string

def custom_layer(group_name: str, data: pd.DataFrame, color: alt.Color):
    import cve_timing_data

    def load_timings_in_minutes(fuzzer: str):
        timings = {}

        for (target, bugs) in EXPERIMENT['timings']['fuzzware-cve'].items():
            for bug in bugs:
                values = cve_timing_data.load_data(EXPERIMENT_NAME, fuzzer, target, bug)
                timings[bug] = [e//60 for e in values if e is not None]

        return timings

    fuzzware_timings_ts_in_m = load_timings_in_minutes('fuzzware')
    hoedure_timings_ts_in_m = load_timings_in_minutes('hoedur')
    hoedure_single_timings_ts_in_m = load_timings_in_minutes('hoedur-single-stream')

    data['marker_fw_img'] = None
    data['marker_ho_img'] = None
    data['marker_hosi_img'] = None

    layers = []
    for k, v in fuzzware_timings_ts_in_m.items():
        if group_name.endswith(k):
            data.loc[data['min'].isin(list(v)), 'marker_fw_img'] = encode_image('input/explosion-icon-fw.png')
            layer = alt.Chart(data).mark_image(
                width=25,
                height=25
            ).encode(
                x='x:T',
                y='median(y)',
                url='marker_fw_img',
                color=color
            ) \
            .transform_filter(alt.FieldOneOfPredicate(field='min', oneOf=list(v))) \
            .transform_filter(alt.datum.Fuzzers == 'Fuzzware')
            layers.append(layer)

    for k, v in hoedure_timings_ts_in_m.items():
        if group_name.endswith(k):
            data.loc[data['min'].isin(list(v)), 'marker_ho_img'] = encode_image('input/explosion-icon-ho.png')
            layer = alt.Chart(data).mark_image(
                width=27,
                height=27,
            ).encode(
                x='x:T',
                y='median(y)',
                url='marker_ho_img',
                color=color
            ).transform_filter(alt.FieldOneOfPredicate(field='min', oneOf=list(v))) \
            .transform_filter(alt.datum.Fuzzers == 'Hoedur')
            layers.append(layer)

    for k, v in hoedure_single_timings_ts_in_m.items():
        if group_name.endswith(k):
            data.loc[data['min'].isin(list(v)), 'marker_hosi_img'] = encode_image('input/explosion-icon-hosi.png')
            layer = alt.Chart(data).mark_image(
                width=27,
                height=27,
            ).encode(
                x='x:T',
                y='median(y)',
                url='marker_hosi_img',
                color=color
            ).transform_filter(alt.FieldOneOfPredicate(field='min', oneOf=list(v))) \
            .transform_filter(alt.datum.Fuzzers == 'Single-Stream-Hoedur')
            layers.append(layer)
    return alt.layer(*layers)

plot_builder.set_custom_layer_cb(custom_layer)

from plotting import color_selection_cb
plot_builder.set_custom_color_cb(color_selection_cb)

def selection_style(category: str) -> PlotStyle:
    # Get only the CVE-.... part of the category
    title = category.split('/')[-1]
    return PlotStyle(title, dots_every_n_minutes=120, x_lable='Time (hh:mm)', y_lable='#Covered Basic Blocks', x_axis_domain_minutes=(0, 24*60))
plot_builder.set_selection_style_cb(selection_style)

from plotting import name_resolver
plot_builder.set_key_resolver_cb(name_resolver)

charts = plot_builder.plot()
chart = ChartLayout.cols_rows(charts, 4, 3)
chart = ChartStyle.default_style(chart)

args = sys.argv
if len(args) != 2:
    print(f'Usage: {args[0]} <output-path>.(svg|png)')
    exit(1)

out_path = args[1]
chart.save(out_path)
