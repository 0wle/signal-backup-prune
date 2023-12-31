import argparse
import os
import re
from pathlib import Path

path_to_backups = ""


class InvalidPath(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidPattern(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def filter_files(filename):
    is_file = os.path.isfile(os.path.join(path_to_backups, filename))
    is_backup = re.compile("(^).+\\.backup$").match(filename)
    return is_file and is_backup


def get_path_to_backups(path_arg):
    path = Path(path_arg).resolve()
    if not os.path.isdir(path):
        raise InvalidPath("Path is not a directory")
    elif len(os.listdir(path)) == 0:
        raise InvalidPath("Directory is empty!")
    else:
        global path_to_backups
        path_to_backups = path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", action="store", help="the path to the signal backups directory", metavar="Path")
    parser.add_argument("pattern", action="store",
                        help="amount of yearly, monthly and daily backups to keep, use '-' if using flags",
                        metavar="YY-MM-DD | -")
    parser.add_argument("-y", "--yearly", action="store", type=int, required=False, dest="yearly")
    parser.add_argument("-m", "--monthly", action="store", type=int, required=False, dest="monthly")
    parser.add_argument("-d", "--daily", action="store", type=int, required=False, dest="daily")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")

    args = parser.parse_args()
    try:
        # Check if the pattern is either valid YY-MM-DD format or -
        if not re.compile("(^([0-9]+)(-)([0-9]+)(-)([0-9]+)$)|(^-$)").match(args.pattern):
            raise InvalidPattern("Invalid pattern specified!")
        if args.pattern == "-" and not args.yearly and not args.monthly and not args.daily:
            raise InvalidPattern("When using '-', the yearly, monthly and daily flags have to specified")
        get_path_to_backups(path_arg=args.path)

        backup_directory = os.listdir(path_to_backups)
        backup_files = list(filter(lambda file: filter_files(file), backup_directory))

        if len(backup_files) == 0:
            raise InvalidPath("No backup files found")
        if args.dry_run:
            zipped = list(zip(backup_files, range(len(backup_files))))
            # poc on how to output files
            print(' '.join(['\n' + x[0] if (x[1] % 4 == 0) else '\t' + x[0] for x in zipped]))

    except InvalidPath as path_error:
        print("Specified path exception: ", path_error.value)
        exit(-1)
    except InvalidPattern as pattern_error:
        print("Specified pattern error: ", pattern_error.value)
        exit(-1)
