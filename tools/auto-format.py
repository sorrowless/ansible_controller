import os
import io
import sys
import ruamel.yaml

from glob import glob


def get_files_pathes():
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    path = path[:path.rfind('/')]

    vars_files = glob(path + "/group_vars/**/*.yml", recursive=True) + \
        glob(path + "/host_vars/**/*.yml", recursive=True) + \
        glob(path + "/host_vars/.DEPRECATED/**/*.yml", recursive=True) + \
        glob(path + "/host_vars/.examples/**/*.yml", recursive=True)

    vault_files = glob(path + "/**/*vault.yml", recursive=True)
    vars_files = set(vars_files) - set(vault_files)
    vars_files = list(vars_files)

    return vars_files


def get_file_content(file: str) -> list:
    lines = []
    with open(file) as content:
        for line in content:
            lines.append(line)
    return lines


def format_trailing_spaces(file_content: list) -> list:
    result = []
    for line in file_content:
        result.append(line.rstrip())
    return result


def format_white_space_in_end(file_content: list) -> list:
    result = file_content
    i = len(result) - 1
    while i > 0:
        if result[i] != "":
            break
        del result[i]
        i -= 1
    result.append("")
    return result


# Reload and redump yaml file can fix bunch of lint problems
def yaml_reload_redump(file_content: list) -> list:
    file_content = "\n".join(file_content)

    yaml = ruamel.yaml.YAML()
    yaml.allow_duplicate_keys = True
    yaml.preserve_quotes = True
    yaml.width = 1000
    file_content = yaml.load(file_content)
    buf = io.BytesIO()
    yaml.dump(file_content, buf)
    file_content = buf.getvalue().decode("utf-8")

    result = ["---"] + file_content.split("\n")
    return result
    

def format_comments(file_content: list) -> list:
    result = []
    leading_whitespaces = 0
    line_index = 0
    while line_index < len(file_content):
        if file_content[line_index].lstrip()[:1] == "#":

            for under_line in file_content[line_index:]:
                if len(under_line.replace(' ', '')) != 0 and under_line.lstrip()[:1] != "#":
                    leading_whitespaces = len(under_line) - len(under_line.lstrip())
                    break
            file_content[line_index] = ' ' * leading_whitespaces + file_content[line_index].lstrip()

        if "#" in file_content[line_index]:
            line = file_content[line_index]
            comment_index = line.rfind("#") +1
            line = line[:comment_index] + ' ' + line[comment_index:].lstrip()
            file_content[line_index] = line

        result.append(file_content[line_index])
        line_index += 1
    return result


def format_empty_lines(file_content: list) -> list:
    result = []
    count_empty_lines = 0
    for line in file_content:
        if line.replace(" ", "") == "":
            count_empty_lines += 1
        else:
            count_empty_lines = 0
        
        if count_empty_lines <= 2:
            result.append(line)
    
    return result


def rewrite_file(file: str, file_content: list) -> None:
    file_content = "\n".join(file_content)
    with open(file, "w") as f:
        f.write(file_content)


def format_controller():
    vars_files = get_files_pathes()
    for file in vars_files:
        content = get_file_content(file)
        content = format_trailing_spaces(content)
        content = yaml_reload_redump(content)
        content = format_white_space_in_end(content)
        content = format_comments(content)
        content = format_empty_lines(content)
        rewrite_file(file, content)

        # break

format_controller()
