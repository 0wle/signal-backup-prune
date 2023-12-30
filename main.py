import argparse
import os
import re

path_to_backups = ""


class InvalidPath(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def filter_files(filename):
    is_file = os.path.isfile(os.path.join(path_to_backups, filename))
    is_backup = re.compile(".*\.backup$").fullmatch(filename)
    return is_file and is_backup


def get_path_to_backups(path_arg):
    path = os.path.abspath(path_arg)
    if not os.path.isdir(path):
        raise InvalidPath("Path is not a directory")
    elif len(os.listdir(path)) == 0:
        raise InvalidPath("Directory is empty!")
    else:
        global path_to_backups
        path_to_backups = path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", action='store')
    args = parser.parse_args()
    try:
        get_path_to_backups(path_arg=args.path)

        backup_directory = os.listdir(path_to_backups)
        backup_files = list(filter(lambda file: filter_files(file), backup_directory))
        print(backup_files)
        if len(backup_files) == 0:
            raise InvalidPath("No backup files found")

    except InvalidPath as path_error:
        print("Specified path exception: ", path_error.value)
        exit(-1)
