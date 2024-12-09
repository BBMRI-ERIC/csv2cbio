import os
import re
from importlib import import_module
import random

import pandas as pd
import numpy as np
from ._singletons import FunctionDefinitionFile, AbsPath

abspath = AbsPath().path


def get_template_file_by_name(name):
    return f"{abspath}study_templates/{name}"


def get_defined_source_csv_headers(config):
    return [item["source_id"] if "source_id" in item else item["id"] for item in config["columns"] if
            not "value" in item]


def get_defined_target_csv_headers(config):
    return [item["id"].upper() for item in config["columns"] if not "value" in item]


def get_defined_constant_csv_headers(config):
    return [item["id"].upper() for item in config["columns"] if "value" in item]


def read_opt(name, source, require=True, default=None, assert_type=None):
    value = None
    if require:
        try:
            value = source[name]
        except Exception as e:
            raise ValueError(f"Field {name} is required in {source}!") from e
    value = source.get(name, None)  # do not use default here, we will test type
    if assert_type is not None and value is not None and not isinstance(value, assert_type):
        raise ValueError(f"Field {name} must be an instance of {assert_type}!")
    if default is not None and value is None:
        return default
    return value


# Proxy stub class for csv reader if we have array of rows already in memory
class CsvReaderStub:
    def __init__(self, data):
        if len(data) > 0 and not isinstance(data[0], list):
            raise ValueError("Invalid data: table must be 2D array!")
        self.data = data
        self.current_idx = -1

    def __getitem__(self, index):
        try:
            return self.data[index]
        except IndexError as e:
            print('Exception: Index={0} len={1}'.format(index, len(self)))
            raise StopIteration

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        self.current_idx = -1
        return self

    def __next__(self):
        self.current_idx += 1
        if self.current_idx == len(self.data):
            raise StopIteration
        else:
            return self.data[self.current_idx]


class CbioCSVWriter:
    def __init__(self):
        self.input_delimiter = '\t'
        self.input = None
        self.config = None
        self.guard_columns = []
        self.required_value_map = {}
        self.fn_module = None

    def with_required_columns(self, *columns):
        self.guard_columns.extend(columns)
        return self

    def with_input(self, inputs, options):
        """Read input CSV data: either a file, or a list of rows, where each row is a list of items (~table, 2D list)

        Args:
            inputs (_type_): input: table, string or file
            options (str, optional): ignored if input is table, default '\t'.

        Returns: self for builder pattern
        """
        self.input_delimiter = options["delimiter"]
        self.input_prefix = options['source_prefix']
        if isinstance(inputs, list):
            columns = inputs.pop(0)
            self.input = pd.DataFrame(inputs, columns=columns)
            return self

        if isinstance(inputs, str):
            inputs = f"{self.input_prefix}{inputs}"
            if not os.path.isfile(inputs):
                raise ValueError(f"Input file {self.input_prefix}{inputs} does not exist!")
        self.input = pd.read_csv(inputs, delimiter=self.input_delimiter)
        return self

    def with_allowed_values_set(self, key, values):
        self.required_value_map[key.upper()] = values
        return self

    def prepare_headers(self, config):
        if not isinstance(self.input, pd.DataFrame):
            raise SyntaxError("with_input must be called first!")
        self.config = config
        self.source_columns_out = get_defined_target_csv_headers(config)
        self.source_columns_in = get_defined_source_csv_headers(config)
        self.constant_columns = get_defined_constant_csv_headers(config)

        cols = config["columns"]
        self.cols_map = {cols[i]["id"].upper(): cols[i] for i in range(len(cols))}
        self.required_colmns = [*self.source_columns_out, *self.constant_columns]

        self._filter_input()
        # todo: consider flexible order by definition order
        if self._option("join_last", require=False):
            self._group_input()
            self._create_columns()
            self._join_input()
        else:
            self._join_input()
            self._group_input()
            self._create_columns()
        return self.required_colmns

    def _option(self, name, source=None, require=True, default=None, assert_type=None):
        return read_opt(name, source=self.config if source is None else source, require=require,
                        default=default, assert_type=assert_type)
        
    def _create_columns(self):
        create = self._option("create", require=False, assert_type=list)
        if create:
            for new_col in create:
                function = new_col.get("function", None)
                column_name = new_col.get("new_column", None)
                columns = new_col.get("source_ids", None)

                if function is not None and column_name is not None and type(columns) == list:
                    fn = self._read_func(function["name"])
                    if fn is not None:
                        args = {**function}
                        del args["name"]
                        self.input[column_name] = self.input.apply(lambda row: fn([row[col] for col in columns], **args), axis=1)
                    else:
                        print(f"WARN: invalid function {function['name']} does not exist!")
                else:
                    print(f"WARN: function, column_name and columns keys for creation are reguired, ignoring {new_column}...")

    def _join_input(self):
        joins = self._option("join", require=False, assert_type=list)
        if joins:
            for join in joins:
                file = self._option("file", source=join, assert_type=str)
                other_input = pd.read_csv(f"{self.input_prefix}{file}", delimiter=self.input_delimiter)
                self.input = self.input.merge(
                    other_input,
                    how=self._option("how", source=join, require=False, assert_type=str, default="inner"),
                    left_on=self._option("left_on", source=join),
                    right_on=self._option("right_on", source=join),
                    suffixes=(
                        self._option("lsuffix", source=join, require=False),
                        self._option("rsuffix", source=join, require=False)
                    )
                )

    def _filter_input(self):
        filters = self._option("filter", require=False, assert_type=list)
        if filters:
            for filter in filters:
                rule = self._option("one_of", source=filter, require=False, assert_type=list)
                if rule:
                    column = self._option("source_id", source=filter, assert_type=str)
                    self.input = self.input.loc[self.input[column].isin(rule)]
                    continue
                rule = self._option("regex", source=filter, require=False, assert_type=str)
                if rule:
                    column = self._option("source_id", source=filter, assert_type=str)
                    self.input = self.input.loc[
                        self.input[column].apply(lambda x: bool(re.search(rule, x) if isinstance(x, str) else None))]
                    continue
                rule = self._option("operator", source=filter, require=False, assert_type=dict)
                if rule:
                    column = self._option("source_id", source=filter, assert_type=str)
                    command = self._option("command", source=rule, assert_type=str)
                    arg = self._option("arg", source=rule)
                    command = self._option(command, source={
                        ">": lambda y: y > arg,
                        ">=": lambda y: y >= arg,
                        "<": lambda y: y < arg,
                        "<=": lambda y: y <= arg,
                        "==": lambda y: y == arg,
                        "!=": lambda y: y != arg
                    })
                    # todo add support for arbitrary function
                    self.input = self.input.loc[self.input[column].apply(command)]
                    continue
                rule = self._option("function", source=filter, require=False, assert_type=dict)
                if (rule):
                    cols = self._option("source_id", source=filter, require=False, assert_type=str)
                    if cols is None:
                        cols = self._option("source_ids", source=filter, require=False, assert_type=list)
                    if cols is None:
                         raise Exception("Filter: source_id or source_ids ust be defined as a filter argument!")
                     
                    fn = self._read_func(rule.get("name"))
                    if fn is None:
                        raise Exception("Filter: function.name must be a valid function name!")
                    else:
                        args = {**rule}
                        del args["name"]
                        self.input = self.input.loc[self.input[cols].apply(fn, axis=1)]
                    continue
                

    def _group_input(self):
        config = self.config
        group_rules = config.get("group", None)
        if group_rules is not None:
            aggregates = self._option("aggregate", source=group_rules, require=False)
            rules = {}
            has_rules = False
            if aggregates:
                selections = {item["id"]: item for item in aggregates}
                selection_keys = selections.keys()

                for key in selection_keys:
                    has_rules = True
                    sel = selections[key]
                    out_key = self._option("source_id", source=sel, require=False, default=key)

                    function = sel.get("function", None)
                    if function is not None:
                        fn = self._read_func(function["name"])
                        if fn is None:
                            rules[key] = pd.NamedAgg(column=out_key, aggfunc="min")
                        else:
                            args = {**function}
                            del args["name"]
                            rules[key] = pd.NamedAgg(column=out_key, aggfunc=lambda x: fn(x, **args))
                        continue

                    value = self._option("value", source=sel, require=False)
                    if value is not None:
                        rules[key] = pd.NamedAgg(column=out_key, aggfunc=lambda x: value)
            groups = self._option("by", source=group_rules)
            if has_rules:
                self.input = self.input.groupby(groups, as_index=False).agg(**rules)
            else:
                self.input = self.input[groups].drop_duplicates().reset_index(drop=True)

    def _write_type(self, value):
        value = value.upper()
        if value not in ["STRING", "NUMBER", "BOOLEAN"]:
            raise f"Invalid patient column type: {value}!"
        return value

    def _require_init(self):
        if not self.config:
            raise SyntaxError("prepare_headers must be called first!")
        if not isinstance(self.input, pd.DataFrame):
            raise SyntaxError("with_input must be called first!")

    def write_comment_ids(self, output):
        self._require_init()
        print("#", end='', file=output)
        try:
            print(*[item["name"] for item in self.config["columns"]], sep='\t', file=output)
        except KeyError as e:
            raise ValueError(f"Could not find 'name' property for {get_caller(2)} entries: missing key? check your study YAML!")

    def write_comment_descriptions(self, output):
        self._require_init()
        print("#", end='', file=output)
        try:
            print(*[item["description"] for item in self.config["columns"]], sep='\t', file=output)
        except KeyError as e:
            raise ValueError(f"Could not find 'description' property for {get_caller(2)} entries: missing key? check your study YAML!!")

    def write_comment_data_types(self, output):
        self._require_init()
        print("#", end='', file=output)
        try:
            print(*[self._write_type(item["data_type"]) for item in self.config["columns"]], sep='\t', file=output)
        except KeyError as e:
            raise ValueError(f"Could not find 'data_type' property for {get_caller(2)} entries: missing key? check your study YAML!!")

    def write_comment_priority(self, output):
        self._require_init()
        print("#", end='', file=output)
        print(*[item.get("priority", "1") for item in self.config["columns"]], sep='\t', file=output)

    def write_header(self, output):
        self._require_init()
        print(*self.required_colmns, sep='\t', file=output)

    def _test_value(self, key, value):
        test = self.required_value_map.get(key, None)
        if test is not None and value not in test:
            raise ValueError(f"Value {value} is not allowed for column {key}!")

    def _get_constant(self, item):
        value = item["value"]
        # TODO DITCHED
        # template = item.get("template", None)
        # if isinstance(template, dict):
        #     # todo find data
        #     value = value.format(**template)
        return value

    def _read_func(self, fnpath):
        """
        Retrieves function either from a module path, or a global function name (e.g. max)
        """
        try:
            path = fnpath.rsplit(".", maxsplit=1)
            if len(path) > 1:
                m = import_module(path[0])
                return getattr(m, path[1])
            if self.fn_module is None:
                definition_path = FunctionDefinitionFile(None).path
                if definition_path is None:
                    return None
                import importlib
                spec = importlib.util.spec_from_file_location("cbio.functions", definition_path)
                self.fn_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.fn_module)
            return getattr(self.fn_module, path[0]) if len(path) > 0 else None
        except Exception as e:
            raise ValueError(f"Invalid function provided: {fnpath.rsplit('.', maxsplit=1)}") from e
        
    def _get_value(self, spec, value, na_value=""):
        """
        Executes function retrieved by a function spec block:
        function:
            name: name
            ... custom args ...
        """
        function = self._option("function", source=spec, require=False, assert_type=dict)
        fn = self._read_func(function["name"]) if function is not None else None

        if fn is not None:
            args = {**function}
            del args["name"]
            value = fn(value, **args)

        if pd.isna(value):
            return na_value
        
        conversion = self._option("convert", source=spec, require=False, assert_type=str)
        if conversion:
            try:
                value = self._convert_value(value, conversion)
            except Exception as e:
                print("WARNING: failed to convert value", value, "to type", conversion, "using '", na_value ,"' value.")
                return na_value
        return value

    def _convert_value(self, value, to_type):
        type_map = {
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'datetime': pd.to_datetime
        }
        if to_type in type_map:
            try:
                return type_map[to_type](value)
            except ValueError:
                raise ValueError(f"Could not convert '{value}' to {to_type}!")
        raise ValueError(f"Unsupported type: {to_type}")

    def write_data(self, output):
        self._require_init()
        header = list(self.input.columns)

        header_diff = set(self.source_columns_in) - set(header)
        assert len(header_diff) == 0, f"Column IDs MUST MATCH to the CSV header! \n\
        Is there typo in the header name, or does the clinical file contain header row? \n\
        Do you define a group strategy that redefines the column names (id: <new_name>, source_id: <original>)? \n\
        Could not find these columns: {header_diff} \n\
        Existing columns: {header}"

        self.input = self.input.replace({None: np.nan})

        for col in self.guard_columns:
            require_header(self.required_colmns, col, 2)

        constant_values = [self._get_constant(item) for item in self.config["columns"] if "value" in item]

        for index, row in self.input.iterrows():
            values = []
            for i in range(len(self.source_columns_in)):
                value = row[self.source_columns_in[i]]
                out_key = self.source_columns_out[i]
                self._test_value(out_key, value)
                values.append(self._get_value(self.cols_map[out_key], value))

            for key, value in zip(self.constant_columns, constant_values):
                self._test_value(key, value)
                values.append(self._get_value(self.cols_map[key], value))
            print(*values, sep='\t', file=output)


def require_header(llist, name, caller_depth=1):
    if not name in llist:
        # Parse problem name from the caller script name: sample.py --> Sample
        raise ValueError(f"{get_caller(caller_depth + 1)} columns MUST include {name} column ID!")


def get_caller(caller_depth=1):
    import inspect
    import pathlib
    frame = inspect.stack()[caller_depth]
    return pathlib.Path(frame.filename).stem.capitalize()


def read_safe_file(inp):
    if os.path.isfile(inp):
        with open(inp, 'r') as inp:
            content = inp.read()
        return content
    raise Exception(f"Clinical data file does not exist! {inp}")


def _get_key(key):
    if ":" in key:
        return key.split(":")[0]
    return key


def _get_value_or_default(key, data):
    if ":" in key:
        key = key.split(":")
        try:
            return data[key[0]]
        except KeyError:
            return key[1]
    return read_opt(key, data)


def write_meta_file(inp, outp, data, fields=None):
    content = read_safe_file(inp)
    fields = fields if fields is not None else data.keys()
    with open(outp, 'w') as output:
        output.write(content.format(**{
            _get_key(key): _get_value_or_default(key, data) for key in fields
        }))


def pick_color(value=None):
    colors = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond',
              'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral',
              'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray',
              'darkgreen', 'darkgrey', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid',
              'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey',
              'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue',
              'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod',
              'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki',
              'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan',
              'lightgoldenrodyellow', 'lightgray', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon',
              'lightseagreen',
              'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen',
              'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple',
              'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred',
              'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive',
              'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
              'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red',
              'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna',
              'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow', 'springgreen', 'steelblue', 'tan',
              'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow',
              'yellowgreen']
    if isinstance(value, str):
        value = value.lower()
        if not value in colors:
            raise ValueError(f"Color {value} not a valid color: use one of: {colors}.")
        return value
    if isinstance(value, int):
        try:
            return colors[value]
        except IndexError as e:
            raise ValueError(f"Color {value} not a valid color index: use between 0 and {len(colors) - 1}.") from e
    # else random color
    return colors[random.randrange(len(colors))]
