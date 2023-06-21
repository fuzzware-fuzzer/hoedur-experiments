from functools import reduce
from pathlib import Path
from IPython import embed
from plotting import PlotStyle, PlotBackend, AltairPlotBackend, utc_timestamp_to_dt, PlotDataQuery, Selection, ChartStyle, ChartLayout
import pandas as pd
import altair as alt
import sys

from config import *


def plot_ablation_study(paper):
    EXPERIMENT = EXPERIMENTS['02-coverage-est-data-set']
    plot_data = PlotDataQuery(EXPERIMENT)
    selection = plot_data.experiment_selection()

    def filter_fn(selection: Selection) -> bool:
        target = selection.attrs()['TARGET']
        include_in_paper = EXPERIMENT['include_in_paper']

        if paper:
            return target in include_in_paper
        else:  # appendix
            return target not in include_in_paper

    selection = selection.filter(filter_fn)
    # print(selection.selections())

    pd.set_option('display.max_rows', 500)
    plot_builder = AltairPlotBackend(selection.selections())
    plot_builder = plot_builder.colorization_key('Fuzzers')
    plot_builder = plot_builder.chart_grouping_key('TARGET')

    def style_cb(group: str) -> PlotStyle:
        return PlotStyle(title=group, dots_every_n_minutes=120, y_lable='#Covered Basic Blocks', x_lable='Time (hh:mm)')

    plot_builder.set_selection_style_cb(style_cb)

    from plotting import color_selection_cb
    plot_builder.set_custom_color_cb(color_selection_cb)

    from plotting import name_resolver
    plot_builder.set_key_resolver_cb(name_resolver)

    charts = plot_builder.plot()
    chart = ChartLayout.cols_rows(charts, 4, 4)
    chart = ChartStyle.default_style(chart)

    args = sys.argv
    if len(args) != 2:
        print(f'Usage: {args[0]} <output-path>.(svg|png)')
        exit(1)

    out_path = args[1]
    chart.save(out_path)


# paper targets
plot_ablation_study(True)
