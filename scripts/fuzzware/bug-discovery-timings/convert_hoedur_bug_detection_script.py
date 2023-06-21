#!/usr/bin/env python3

""" Utility which converts a hoedur hook-bugs.rn bug detection
hook script to a Fuzzware-compatible equivalent hook_bugs_fuzzware.py

This util takes away the manual translation process, which is time-consuming
and prone to errors.

Note that this script bases largely on text pattern replacements. Thus,
not all code constructs may be supported. To see which type of *.rn code
structures are supported, refer to the existing hook-bugs.rn scripts.
"""

import argparse
import re
import os

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("hoedur_script", help="Hoedur bug detection script path.")
    parser.add_argument("out_fuzzware_script", help="Output converted Fuzzware bug detection hook.")
    parser.add_argument("-f", "--force", default=False, action="store_true", help="Reference output file name of Fuzzware bug detection hooks to compare to.")
    return parser


NUM_SPACES_PER_TAB = 4

PREAMBLE_CODE = """
from fuzzware_harness import globs
from unicorn import UcError

def add_bug(name):
    print(f"Heureka! {name}", flush=True)

"""

def replace_reg_read(source_string):
    def convert_reg_read(match_obj):
        reg_name = match_obj.group(1)
        return f"globs.uc.regs.{reg_name.lower()}"

    # Reading registers
    regex_reg_read = re.compile('register::read\("([^"]+)"\)\?')
    # Replace occurrences
    return re.sub(regex_reg_read, convert_reg_read, source_string)

def replace_func_defs(source_string):
    def convert_func_definition(match_obj):
        fn_name = match_obj.group(1)
        fn_args = match_obj.group(2)
        body = ""

        # Handle bb hooks by assigning args to globals
        if fn_name.startswith("on_"):
            # hook naming convention: remove arguments
            for arg_name in fn_args.split(","):
                arg_name = arg_name.rstrip().lstrip()
                if not arg_name:
                    continue
                body+="\n"+(NUM_SPACES_PER_TAB*" ")
                if arg_name in ("pc", "_"):
                    body += "pc = uc.regs.pc"
                else:
                    body += f"global {arg_name}"
            fn_args = "uc"

        return f"def {fn_name} ({fn_args}):{body}"

    fun_def_regex = re.compile('fn *([^\()]+) *\(([^\)]*)\) *{')
    return re.sub(fun_def_regex, convert_func_definition, source_string)

def replace_if_statements(source_string):
    def convert_if_statement(match_obj):
        operator = match_obj.group(1).rstrip()
        cond_statement = match_obj.group(2).rstrip()
        return f"{operator} {cond_statement}:"

    regex = re.compile('(if|while) ([^{]+){')
    return re.sub(regex, convert_if_statement, source_string)

def replace_for_loops(source_string):
    def convert_for_loop(match_obj):
        varnames = match_obj.group(1)
        iterable = match_obj.group(2)
        return f"for {varnames} in {iterable}:"

    regex = re.compile('for\s+([^{]+)\s+in\s+([^{]+)\s+{')
    return re.sub(regex, convert_for_loop, source_string)

def replace_symbol_resolves(source_string):
    def convert(match_obj):
        symbol_name = match_obj.group(1)
        postfix = match_obj.group(2)
        return f"globs.uc.symbols['{symbol_name}']{postfix}"

    regex = re.compile('symbolizer::resolve\("([^"]+)"\)\??(.*)')

    return re.sub(regex, convert, source_string)

def replace_format_macros(source_string):
    def convert(match_obj):
        macro_name = match_obj.group(1)
        format_string = match_obj.group(2)
        arguments = match_obj.group(3)
        if "log::" in macro_name:
            return f"print({format_string}.format({arguments})"
        else:
            return f"{format_string}.format({arguments}"

    regex = re.compile('(format!|log::[a-z]+!)\(("[^"]+"),([^\)]+\))')

    return re.sub(regex, convert, source_string)

def replace_mem_reads(source_string):
    def convert(match_obj):
        indentation = match_obj.group(1)
        line = match_obj.group(2)
        
        res = f"{indentation}try:\n{indentation}{NUM_SPACES_PER_TAB*' '}{line}\n{indentation}except UcError:\n{indentation}{NUM_SPACES_PER_TAB*' '}return None"
        print(f"MATCH Result: {res}")
        return res

    regex = re.compile('( *)(.*memory::read_u[0-9]{1,2}\([^\)]+\)\?.*)')

    return re.sub(regex, convert, source_string)

def replace_unwrap_or(source_string):
    def convert(match_obj):
        indentation = match_obj.group(1)
        varname = match_obj.group(2)
        expression = match_obj.group(3)
        alternative = match_obj.group(4)
        res = f"{indentation}try:\n{indentation}{NUM_SPACES_PER_TAB*' '}{varname} = {expression}\n{indentation}except UcError:\n{indentation}{NUM_SPACES_PER_TAB*' '}{varname} = {alternative}"
        return res

    regex = re.compile('( *)([^\s]*) = (.*)\.unwrap_or\(([^\)])\);')

    return re.sub(regex, convert, source_string)

def globalize_structs(source_string):
    struct_names = []
    """
    1. Auto-generate python classes from struct definitions
    2. Auto-generate global variables based on struct variables which are created in the main function
    """
    # Generate Python class definitions
    def convert_struct_definition(match_obj):
        struct_name = match_obj.group(1).rstrip()
        struct_names.append(struct_name)
        struct_member_names = match_obj.group(2).split(",")
        res = f"class {struct_name}:\n"
        res += (NUM_SPACES_PER_TAB*" ")+ "def __init__(self"
        for i in range(len(struct_member_names)):
            struct_member_names[i] = struct_member_names[i].rstrip().lstrip()

        # Constructor prototype
        for i, memb_name in enumerate(struct_member_names):
            res += f", {memb_name}=None"
        res += "):"

        # Constructor body
        for memb_name in struct_member_names:
            res += "\n" + (2*NUM_SPACES_PER_TAB*" ")
            res += f"self.{memb_name} = {memb_name}"
        res += "\n"

        return res

    regex = re.compile('struct +([^\{]+) *\{([^\}^\n]+)\}')

    source_string = re.sub(regex, convert_struct_definition, source_string)

    # Generate global class objects from main-local struct instantiations
    # Find main body
    main_start = source_string.index("pub fn main(api)")
    main_end = source_string.index("\n}", main_start)
    old_main_body = source_string[main_start : main_end+2]
    
    bb_hook_rego_regex = re.compile(".*api.on_basic_block\s*\(\s*Some\s*\(\s*([^,]+)\)\s*,.*( on_[^\(]+)\(.*")
    bb_hook_sym_resolve_regex = re.compile('symbolizer::resolve\("([^"]+)"\)\??([^\)]*)')

    new_main_body = ""
    for line in old_main_body.split("\n"):
        new_main_body += "#" + line + "\n"

        if "let " in line:
            new_main_body += line.replace("let ", "").replace("{", "(").replace("}", ")").replace(":", "=").lstrip() + "\n"
            continue

        m = bb_hook_rego_regex.match(line)
        if m:
            print(f"match: {m}\nfor line {line}")
            hook_location = m.group(1).lstrip().rstrip()

            # Skip unbounded hooks
            if hook_location == "None":
                continue

            hook_name = m.group(2).lstrip().rstrip()
            print(f"Hook location: {hook_location}")
            print(f"Hook name    : {hook_name}")

            # Replace symbol resolution
            hook_location = re.sub(bb_hook_sym_resolve_regex, lambda m: f'{m.group(1)}{m.group(2)}'.replace(" ", ""), hook_location)

            hook_config_line = f"# {hook_location} {hook_name}"
            print(f"Hook config line: {hook_config_line}")
            source_string = hook_config_line+"\n"+source_string

    source_string = source_string.replace(old_main_body, new_main_body)

    return source_string


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    source_path, out_path = args.hoedur_script, args.out_fuzzware_script

    if not os.path.exists(source_path):
        print(f"[ERROR] source file '{source_path}' does not exist")
        exit(1)
    if (not args.force) and os.path.exists(out_path):
        print(f"[ERROR] destination file '{out_path}' already exists (use --force to override anyways)")
        exit(2)

    with open(source_path, "r") as f:
        source_string = f.read()

    source_string = "\n" + PREAMBLE_CODE + source_string

    replacement_hooks = [
        globalize_structs,
        replace_reg_read,
        replace_func_defs,
        replace_if_statements,
        replace_for_loops,
        replace_symbol_resolves,
        replace_format_macros,
        replace_unwrap_or,
        replace_mem_reads,
    ]
    for replacement_hook in replacement_hooks:
        source_string = replacement_hook(source_string)

    replacements = [
        ("memory::read_u32", "globs.uc.mem.u32"),
        ("memory::read_u16", "globs.uc.mem.u16"),
        ("memory::read_u8", "globs.uc.mem.u8"),
        ("input::add_bug", "add_bug"),
        ("?;", ""),
        (";", ""),
        ("let ", ""),
        ("https://", "LINK_GUARD"),
        ("//", "#"),
        ("LINK_GUARD", "https://"),
        ("const ", ""),
        ("} else if", "elif"),
        ("} else", "else"),
        ("else {", "else:"),
        ("else if", "elif"),
        ("||\n", "or \\\n"),
        ("||", "or"),
        ("&&\n", "and \\\n"),
        ("&&", "and"),
        (")?", ")"),
        (" !=", "GUARD_!=_GUARD"),
        (" !", " not "),
        ("GUARD_!=_GUARD", " !="),
        (".push(", ".append("),
        ("false", "False"),
        ("true", "True"),
        ("api.on_prepare_run", "#api.on_prepare_run"),
        ("\n"+(0 * NUM_SPACES_PER_TAB * " ") + "}", ""),
        ("\n"+(1 * NUM_SPACES_PER_TAB * " ") + "}", ""),
        ("\n"+(2 * NUM_SPACES_PER_TAB * " ") + "}", ""),
        ("\n"+(3 * NUM_SPACES_PER_TAB * " ") + "}", ""),
        ("\n"+(4 * NUM_SPACES_PER_TAB * " ") + "}", ""),
    ]

    for rn_tok, replacement_tok in replacements:
        source_string = source_string.replace(rn_tok, replacement_tok)

    with open(out_path, "w") as f:
        f.write(source_string)
