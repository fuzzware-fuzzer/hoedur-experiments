import altair as alt
import pandas as pd
import zstandard as zst
from altair_saver import save
#alt.data_transformers.enable('json', urlpath='./')
alt.data_transformers.enable('data_server')
alt.data_transformers.disable_max_rows()

from collections import defaultdict, deque
from email.policy import default
from functools import reduce
from optparse import Option
from pathlib import Path
import json
import re
import abc
import functools
import statistics
import math
from IPython import embed
import datetime
from tokenize import group
from typing import Any, Dict, List, Literal, Union, Tuple, Set, Optional, Callable
from enum import Enum
from numpy import median

from .query import Selection
from pandas import DataFrame

from config import FUZZER_SHAPE, FUZZER_NAME

class PlotBackend(Enum):
    ALTAIR = 'ALTAIR'
    MATPLOTLIB = 'MATPLOTLIB'

class PlotMetricType(Enum):
    COVERAGE_TRANSLATION_BLOCKS = 'COVERAGE_TRANSLATION_BLOCKS'

class PlotStyle():

    def __init__(self,
            title: str,
            line_chart: bool=True,
            dot_chart: bool=True,
            interval_area: bool=True,
            interval_size: float=0.66,
            dots_every_n_minutes: int=120,
            y_lable: str='#Covered Basic Blocks',
            x_lable: str='Time (hh:mm)',
            x_axis_domain_minutes: Tuple[int, int]=(0, 60*24),
            ) -> None:
        self.line_chart = line_chart
        self.dot_chart = dot_chart
        self.interval_area = interval_area
        self.interval_size = interval_size
        self.dots_every_n_minutes = dots_every_n_minutes
        self.x_lable = x_lable
        self.y_lable = y_lable
        self.x_axis_domain_minutes = x_axis_domain_minutes
        self.title = title

def utc_timestamp_to_dt(val: int) -> datetime.datetime:
    return datetime.datetime.utcfromtimestamp(val)

class ChartLayout():

    @staticmethod
    def cols_rows(charts: List[alt.Chart], num_cols: int, num_rows: int) -> alt.VConcatChart:
        assert num_rows > 0 and num_cols > 0
        charts: deque[alt.Chart] = deque(charts)

        rows = []
        for _ in range(0, num_rows):
            row = []
            for _ in range(0, num_cols):
                row.append((charts.popleft()))
                if len(charts) == 0:
                    break
            rows.append(row)
            if len(charts) == 0:
                break

        h_concat_charts = []
        for row in rows:
            chart = alt.HConcatChart()
            for e in row:
                chart |= e
            h_concat_charts.append(chart)

        v_concat_chart = alt.VConcatChart()
        for chart in h_concat_charts:
            v_concat_chart &= chart

        if len(charts):
            print('[!] Layout does not include all charts')

        return v_concat_chart

class ChartStyle():

    @staticmethod
    def default_style(chart: alt.Chart) -> alt.Chart:
        return chart.configure(font='cmr10').configure_axis(
            labelFontSize=18,
            titleFontSize=18,
        ).configure_title(
            fontSize=18,
        ).configure_legend(
            titleFontSize=20,
            labelFontSize=18,
            labelLimit=0,
        )

class AltairPlotBackend():

    def __init__(self, selections: List['Selection']) -> None:
        self._selections = selections
        self._data_frames: Dict[Selection, pd.DataFrame] = {}
        self._metric = PlotMetricType.COVERAGE_TRANSLATION_BLOCKS
        self._colorization_key: Optional[str] = None
        self._chart_grouping_key: Optional[str] = None
        self._selection_style_cb: Callable[[str], PlotStyle] = AltairPlotBackend._default_selection_style_cb
        self._key_resolver_cb: Callable[[str, str], str] = lambda _, v: v
        self._add_custom_layer_cb: Callable[[str, pd.DataFrame, alt.Color], Optional[alt.Chart]] = lambda _, __, ___: None
        self._custom_color_cb: Optional[Callable[[str], str]] = None

    def select_metric(self, metric: PlotMetricType) -> None:
        assert metric in [PlotMetricType.COVERAGE_TRANSLATION_BLOCKS]
        self._metric = metric

    def colorization_key(self, key: str) -> 'AltairPlotBackend':
        for selection in self._selections:
            if key not in selection.attrs():
                raise ValueError(f'Selection {selection} does not have an attribute {key}')
        self._colorization_key = key
        return self

    def chart_grouping_key(self, key: str) -> 'AltairPlotBackend':
        for selection in self._selections:
            if key not in selection.attrs():
                raise ValueError(f'Selection {selection} does not have an attribute {key}')
        self._chart_grouping_key = key
        return self

    def set_selection_style_cb(self, cb: Callable[[str], PlotStyle]) -> None:
        self._selection_style_cb = cb

    def set_key_resolver_cb(self, cb: Callable[[str, str], str]) -> None:
        self._key_resolver_cb = cb

    def set_custom_layer_cb(self, cb: Callable[[str, pd.DataFrame, alt.Color], Optional[alt.Chart]]) -> None:
        self._add_custom_layer_cb = cb

    def set_custom_color_cb(self, cb: Callable[[str], str]):
        self._custom_color_cb = cb

    def _transform_selections_to_raw_data(self) -> Dict['Selection', List[Dict[int, int]]]:
        """
        Populate `self._raw_data_x_y` with mapping from `Selection` to dict
        of x -> y mappings.
        """
        raw_data_x_y  = defaultdict(list)
        decompressor = zst.ZstdDecompressor()
        for selection in self._selections:
            selection_raw_data: Dict[int,int] = {}
            for f in selection.raw_data_files():
                decompressed = decompressor.decompress(f.read_bytes(), max_output_size=1024*1024*1024*10)
                if self._metric == PlotMetricType.COVERAGE_TRANSLATION_BLOCKS:
                    data = json.loads(decompressed)['coverage_translation_blocks']
                else:
                    raise NotImplementedError(f'Metric of type {self._metric} is not implemented yet')
                selection_raw_data = { e['x']: e['y'] for e in data }
                raw_data_x_y[selection].append(dict(list(sorted(selection_raw_data.items(), key=lambda e: e[0]))))
        return raw_data_x_y

    @staticmethod
    def _calculate_unique_x_value_sorted(raw_data_x_y: Dict['Selection', List[Dict[int, int]]]) -> List[int]:
        unique_x_value_sorted = set()
        for _, mappings_set in raw_data_x_y.items():
            for mappings in mappings_set:
                for x, _ in mappings.items():
                    unique_x_value_sorted.add(x)
        # TOOD: Make this configureable
        # We add every 60 seconds a data point, since a data point is needed in order
        # to draw, e.g., a dot (chart layer) at a specific location.
        unique_x_value_sorted |= {x for x in range(0, 24*3600, 60)}
        return list(sorted(unique_x_value_sorted))

    def _build_coverage_data_frame(self, selection: 'Selection', set_id: int, data: Dict[int,int], unique_x_value_sorted: List[int]) -> pd.DataFrame:
        frame: Dict[str, List[Union[int, str, float, datetime.datetime]]] = defaultdict(list)
        last = 0
        for minute in range(0, 24*60*1):
            measurements = set([last])
            for x in range(minute * 60, minute * 60 + 60):
                measurements.add(data.get(x, 0))
            y = max(measurements)
            last = y

            # copy selection attributes
            for k, v in selection.attrs().items():
                v = self._key_resolver_cb(k, v)
                frame[k].append(v)

            # The origin set of the data
            frame['set_id'].append(set_id)
            # The timestamp in minutes
            frame['min'].append(minute)
            # The timestamp as python datetime
            frame['x'].append(utc_timestamp_to_dt(minute*60))
            frame['y'].append(y)
        return pd.DataFrame(frame)



    @staticmethod
    def _default_selection_style_cb(category: str) -> PlotStyle:
        return PlotStyle(category)


    @staticmethod
    def _calculate_intervals(data: pd.DataFrame, interval_width: float=0.66) -> DataFrame:
        y_vals_grouped_by_min = data.groupby('min')['y'].apply(list)
        interval_elm_cnt =  math.floor(math.floor(len(y_vals_grouped_by_min[0]) * interval_width) / 2)

        interval_frame = defaultdict(list)
        index = []
        for min, y_vals in y_vals_grouped_by_min.items():
            elm_cnt = len(y_vals)
            assert elm_cnt > 2
            y_vals = sorted(y_vals)
            median_idx = elm_cnt // 2
            lower_bound: Any = y_vals[median_idx-interval_elm_cnt]
            upper_bound: Any = y_vals[median_idx+interval_elm_cnt]
            assert lower_bound is not None
            assert upper_bound is not None
            index.append(min)
            interval_frame['min'].append(min)
            interval_frame['interval_lower'].append(lower_bound)
            interval_frame['interval_upper'].append(upper_bound)
        ret = pd.DataFrame(interval_frame, index=index)
        return ret

    @functools.lru_cache()
    def _get_color_mapping(self, key: str) -> str:
        assert self._custom_color_cb is not None
        return self._custom_color_cb(key)

    @staticmethod
    def _name_to_shape(key: str) -> str:
        for (fuzzer_key, name) in FUZZER_NAME.items():
            if name == key:
                return FUZZER_SHAPE[fuzzer_key]

        raise ValueError(f'Unknown key for shape mapping: {key}')

    def _get_custom_shape_mapping(self, data: pd.DataFrame) -> tuple[list[Any], list[str]]:
        categories = list(data[self._colorization_key].unique())
        mappings = [AltairPlotBackend._name_to_shape(e) for e in categories]
        return categories, mappings

    def _get_custom_colorization(self, data: pd.DataFrame) -> Optional[tuple[list[Any], list[str]]]:
        if self._custom_color_cb is None:
            return None
        categories = list(data[self._colorization_key].unique())
        mappings = [self._get_color_mapping(e) for e in categories]
        return categories, mappings

    def plot(self) -> List[alt.LayerChart]:
        if self._colorization_key is None:
            raise ValueError(f'colorization_key() must be called first')
        if self._chart_grouping_key is None:
            raise ValueError(f'chart_grouping_key() must be called first')

        runs_raw_data_x_y: Dict[Selection, List[Dict[int, int]]] = self._transform_selections_to_raw_data()
        unique_x_value_sorted: List[int] = AltairPlotBackend._calculate_unique_x_value_sorted(runs_raw_data_x_y)

        # Convert raw values (x,y) for all runs for a specific selection to `DataFrame`s.
        selection_to_frame: Dict['Selection', pd.DataFrame] = {}
        for selection, raw_data_sets in runs_raw_data_x_y.items():
            frames = []
            for set_id, raw_data_set in enumerate(raw_data_sets):
                frame = self._build_coverage_data_frame(selection, set_id, raw_data_set, unique_x_value_sorted)
                frames.append(frame)
            selection_to_frame[selection] = pd.concat(frames)

        # Calculate intervals and merge them into our data frames.
        # This will add columns for the intervals to `selection_to_frame`.
        for selection, frame in selection_to_frame.items():
            intervals_frame = AltairPlotBackend._calculate_intervals(frame)
            selection_to_frame[selection] = frame.merge(intervals_frame, on='min')

        # Group the data based on a key that is set through `chart_grouping_key()`.
        # This key determines based on which attribute of a `Selection` distinct graphs
        # are plotted.
        grouped_selections: Dict[str, Dict[Selection, pd.DataFrame]] = defaultdict(lambda: defaultdict())
        for selection, frame in selection_to_frame.items():
            key = selection.attrs()[self._chart_grouping_key]
            grouped_selections[key][selection] = frame

        charts = []
        # For each group, create a graph and push it into `charts` list, which is returned at the end.
        for group_key, selection_to_frame in grouped_selections.items():
            frames = []

            # Discard the selection, and merge all frames (i.e., runs) into one big `merged_frame`.
            for _, frame in selection_to_frame.items():
                frames.append(frame)
            merged_frame = pd.concat(frames)

            # Apply custom colorization if desired.
            color_scale_kwargs: dict[Any, Any] = { }
            if category_to_color := self._get_custom_colorization(merged_frame):
                color_custom_scale = color_scale_kwargs.update(domain=category_to_color[0], range=category_to_color[1])
            color_custom_scale = alt.Scale(**color_scale_kwargs)

            # Apply custom shapes for data points if desired.
            # The color domain must be provided, in order to make sure that the shapes are colored according
            # to the colors set above.
            _shape_domain, shape_range = self._get_custom_shape_mapping(merged_frame)
            shape_custom_scale = alt.Scale(domain=color_custom_scale.domain, range=shape_range)

            # Get the style for the plot we are currently generating.
            style: PlotStyle = self._selection_style_cb(group_key)
            chart_title = style.title


            # (lower_bound, upper_bound)
            x_domain = style.x_axis_domain_minutes
            # Discard every row with a timestamp not in range of the domain we are interested in.
            merged_frame = merged_frame[merged_frame['x'] >= utc_timestamp_to_dt((x_domain[0]*60))]
            merged_frame = merged_frame[merged_frame['x'] <= utc_timestamp_to_dt((x_domain[1]*60))]

            # Make sure we have some padding (in y direction) between plot end and the plotted lines.
            max_interval_upper_value = merged_frame['interval_upper'].max()
            max_interval_upper_value += (max_interval_upper_value % 400)
            y_scale = alt.Scale(domain=[0, int(max_interval_upper_value)])

            # The layers (potentially multiple) this plot is build from.
            # A layer might be dots marking data points, or a line representing, e.g., the median.
            layers: List[Any] = []

            if style.dot_chart:
                # Mark some data points using some sort of marker (e.g., a square).
                dot_layer: alt.Chart = alt.Chart(merged_frame, title=chart_title).mark_point(filled=True, size=60).encode(
                    x=alt.X('x:T', axis=alt.Axis(format='%H:%M'), title=style.x_lable),
                    y=alt.Y('median(y)', title=style.y_lable),
                    shape=alt.Shape(f'{self._colorization_key}:N', legend=alt.Legend(orient='top'), scale=shape_custom_scale),
                    color=alt.Color(f'{self._colorization_key}:N', legend=alt.Legend(orient='top'), scale=color_custom_scale),
                ).transform_filter(alt.datum.min%style.dots_every_n_minutes == 0)
                layers.append(dot_layer)

            if style.line_chart:
                # Draw the median of the provided data.
                line_layer: alt.Chart = alt.Chart(merged_frame, title=chart_title).mark_line().encode(
                    x=alt.X('x:T', axis=alt.Axis(format='%H:%M'), title=style.x_lable),
                    y=alt.Y('median(y)', title=style.y_lable, scale=y_scale),
                    color=alt.Color(f'{self._colorization_key}:N', legend=None, scale=color_custom_scale),
                )
                layers.append(line_layer)

            if style.interval_area:
                # Draw the interval of the provided data.
                interval_layer: alt.Chart = alt.Chart(merged_frame, title=chart_title).mark_area(opacity=0.2).encode(
                    color=alt.Color(f'{self._colorization_key}:N', legend=None, scale=color_custom_scale),
                ).transform_window(
                    rollingy2='mean(interval_upper)',
                    rollingy='mean(interval_lower)',
                    frame=[-30, 30]
                ).encode(
                    x=alt.X('x:T', title=style.x_lable),
                    y=alt.Y('rollingy:Q', title=style.y_lable),
                    y2='rollingy2'
                )
                layers.append(interval_layer)

            # Allow the user to add custom layers in addition to the ones already generated above.
            color = color=alt.Color(f'{self._colorization_key}:N', scale=color_custom_scale)
            if custom_layer := self._add_custom_layer_cb(group_key, merged_frame, color):
                layers.append(custom_layer)

            chart = alt.layer(
                *layers,
            )

            charts.append(chart)

        return charts
