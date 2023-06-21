from collections import defaultdict
from email.policy import default
from functools import reduce
from optparse import Option
from pathlib import Path
import json
import re
import abc
import statistics
import zstandard as zst
import math
from IPython import embed
import datetime
from tokenize import group
from typing import Any, Dict, List, Union, Tuple, Set, Optional, Callable, NoReturn
from enum import Enum
from numpy import median


# A selection of (possibly) multiple runs.
class Selection():
    next_id = 0

    def __init__(self, subtree: Dict[str, str]) -> None:
        self._attrs: Dict[str, str] = {}
        self._subtree = subtree
        self._raw_data_files: List[Path] = []
        self._id = Selection.next_id
        Selection.next_id += 1
        self._xyx_mappings: Optional[List[Dict[int, int]]] = None

    def id(self) -> int:
        return self._id

    def subtree(self) -> Dict[str, str]:
        return self._subtree

    def attrs(self) -> Dict[str, str]:
        return self._attrs

    def add_attr(self, key: str, val: str) -> None:
        assert self._attrs[key]
        self._attrs[key] = val

    def add_attrs(self, attrs: Dict[str, str]) -> None:
        self._attrs.update(attrs)

    def add_raw_data_file(self, path: Path) -> None:
        assert self._xyx_mappings is None
        self._raw_data_files.append(path)

    def add_raw_data_files(self, paths: List[Path]) -> None:
        assert self._xyx_mappings is None
        self._raw_data_files.extend(paths)

    def raw_data_files(self) -> List[Path]:
        return self._raw_data_files

    def _parse_raw_data(self) -> list[Dict[int, int]]:
        decompressor = zst.ZstdDecompressor()
        xy_mapping_sorted_all: List[Dict[int, int]] = []
        for f in self.raw_data_files():
            decompressed = decompressor.decompress(
                f.read_bytes(), max_output_size=1024*1024*1024*10)
            data = json.loads(decompressed)['coverage_translation_blocks']
            xy_mapping = {e['x']: e['y'] for e in data}
            xy_mapping_sorted = dict(
                list(sorted(xy_mapping.items(), key=lambda e: e[0])))  # type: ignore
            xy_mapping_sorted_all.append(xy_mapping_sorted)
        return xy_mapping_sorted_all

    def xy_mappings(self) -> List[Dict[int, int]]:
        if self._xyx_mappings is None:
            self._xyx_mappings = self._parse_raw_data()
        return self._xyx_mappings

    def __repr__(self) -> str:
        return f'Selection({self._attrs})'


class PlotDataQuery:

    def __init__(self, experiment: Dict[Any, Any]) -> None:
        self._experiment = experiment
        self._base_dir = experiment['path'] / 'results' / 'coverage'
        plot_data_manifest = self._base_dir / 'plots.json'
        self._plot_data_manifest = json.loads(plot_data_manifest.read_text())
        self._selections: List[Selection] = []

    def experiment_selection(self) -> 'PlotDataQuery':
        fuzzers = '|'.join(self._experiment['fuzzer'])
        targets = '|'.join(self._experiment['target'])
        selection = self.for_each(f'(?P<Fuzzers>{fuzzers})').for_each(f'(?P<TARGET>{targets})')
        selection = selection.select('.*')
        selection.expected_runs(self._experiment['runs'])
        return selection

    def selections(self) -> List[Selection]:
        return self._selections

    def for_each(self, selector: str) -> 'PlotDataQuery':
        if not self._selections:
            data = self._plot_data_manifest['data']
            for k, subtree in data.items():
                if matches := re.fullmatch(selector, k):
                    parent_selection = Selection(subtree)
                    parent_selection.add_attrs(matches.groupdict())
                    self._selections.append(parent_selection)
        else:
            new_selections = []
            for parent_selection in self._selections:
                subtree = parent_selection.subtree()
                for k, subsubtree in subtree.items():
                    if matches := re.fullmatch(selector, k):
                        selection = Selection(subsubtree)
                        selection.add_attrs(parent_selection.attrs())
                        selection.add_attrs(matches.groupdict())
                        new_selections.append(selection)
            self._selections = new_selections
        return self

    def expected_runs(self, val: int) -> 'PlotDataQuery':
        for selection in self.selections():
            if (actual_val := len(selection.raw_data_files())) != val:
                raise ValueError(
                    f'Selection {selection} contains {actual_val} runs instead of {val} runs.')
        return self

    def select(self, selector: str) -> 'PlotDataQuery':
        if not self._selections:
            raise NotImplementedError(
                'for_each() must be called at least once before selecting')

        for selection in self._selections:
            subtree = selection.subtree()
            for k, data_file in subtree.items():
                if matches := re.fullmatch(selector, k):
                    path = self.check_data_file_path(data_file)
                    selection.add_raw_data_file(path)
                    selection.add_attrs(matches.groupdict())

        return self

    def filter(self, fn: Callable[[Selection], bool]) -> 'PlotDataQuery':
        self._selections = [e for e in self._selections if fn(e)]
        return self

    def check_data_file_path(self, data_file: str) -> Path:
        def error(e: Exception) -> NoReturn:
            raise ValueError(
                'select() can only work on the last layer. You probably need to descend deeper using for_each()') from e

        if not data_file.endswith('.zst'):
            err = ValueError(
                f'Selected {data_file} as data file, which does not look like a zstd compressed file')
            error(err)

        data_file_path: Path = (self._base_dir / data_file).expanduser().resolve()
        if not data_file_path.exists():
            raise ValueError(
                f'Data {data_file} can not be found in the filesystem.')

        return data_file_path

    def __len__(self) -> int:
        return len(self._selections)
