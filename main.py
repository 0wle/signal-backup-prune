import argparse
import os
import re
from pathlib import Path


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


class ArgsHandler:
    path_to_backups = None
    yearly = None
    monthly = None
    daily = None
    verbose = False
    dry_run = False

    def __init__(self):
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
        self.__get_path_to_backups(path_arg=args.path)
        self.__get_increments(args=args)

        self.dry_run = args.dry_run
        self.verbose = args.verbose

    def __get_path_to_backups(self, path_arg):
        path = Path(path_arg).resolve()
        if not os.path.isdir(path):
            raise InvalidPath("Path is not a directory")
        elif len(os.listdir(path)) == 0:
            raise InvalidPath("Directory is empty!")
        else:
            self.path_to_backups = path

    def __get_increments(self, args):
        # Check if the pattern is either valid YY-MM-DD format or -
        if not re.compile("(^([0-9]+)(-)([0-9]+)(-)([0-9]+)$)|(^-$)").match(args.pattern):
            raise InvalidPattern("Invalid pattern format!")
        elif args.pattern == "-":
            if not args.yearly and not args.monthly and not args.daily:
                raise InvalidPattern("When using '-', the yearly, monthly and daily flags have to specified!")
            else:
                self.yearly = args.yearly
                self.monthly = args.monthly
                self.daily = args.daily
        else:
            path_args = args.pattern.split("-")
            self.yearly = int(path_args[0])
            self.monthly = int(path_args[1])
            self.daily = int(path_args[2])


class DirectoryHelper:

    @staticmethod
    def get_backup_files(path_to_backups):
        backup_directory = os.listdir(path_to_backups)
        files = list(filter(
            lambda file: DirectoryHelper.__filter_files(path_to_backups=path_to_backups, file=file), backup_directory
        ))
        if len(files) == 0:
            raise InvalidPath("No backup files found")
        else:
            return files

    @staticmethod
    def __filter_files(path_to_backups, file):
        is_file = os.path.isfile(os.path.join(path_to_backups, file))
        is_backup = re.compile("(^).+\\.backup$").match(file)
        return is_file and is_backup

    @staticmethod
    def get_size(path_to_backup, files):
        return sum([os.stat(os.path.join(path_to_backup, x)).st_size for x in files])

    @staticmethod
    def filter_files_for_deletion(yearly, monthly, daily, file_list):
        file_list.sort()
        sorted_list = list(reversed(file_list))
        current = sorted_list[0]
        daily_files_counter = 0
        monthly_files_counter = 0
        yearly_files_counter = 0
        files_to_delete = []
        print(sorted_list)
        for i in range(1, len(sorted_list)):
            if daily_files_counter < daily:
                if int(current[15:17]) != int(sorted_list[i][15:17]):
                    current = sorted_list[i]
                    daily_files_counter += 1
                    continue
                else:
                    files_to_delete.append(current)
                    current = sorted_list[i]
                    continue
            elif monthly_files_counter < monthly:
                if int(current[12:14]) != int(sorted_list[i][12:14]):
                    current = sorted_list[i]
                    monthly_files_counter += 1
                    continue
                else:
                    files_to_delete.append(current)
                    current = sorted_list[i]
                    continue
            elif yearly_files_counter < yearly:
                if int(current[7:11]) != int(sorted_list[i][7:11]):
                    current = sorted_list[i]
                    yearly_files_counter += 1
                    continue
                else:
                    files_to_delete.append(current)
                    current = sorted_list[i]
                    continue
            else:
                files_to_delete.append(current)
                current = sorted_list[i]

        return files_to_delete


if __name__ == '__main__':
    try:
        args_handler = ArgsHandler()
        backup_files = DirectoryHelper.get_backup_files(args_handler.path_to_backups)
        # OutputHandler.print_init(args_handler)
        initial_size = DirectoryHelper.get_size(args_handler.path_to_backups, backup_files)
        files_to_be_deleted = DirectoryHelper.filter_files_for_deletion(
            yearly=args_handler.yearly,
            monthly=args_handler.monthly,
            daily=args_handler.daily,
            file_list=backup_files
        )
        #  TODO: clean this up by introducing an output helper
        if args_handler.dry_run:
            size_after = initial_size - DirectoryHelper.get_size(args_handler.path_to_backups, files_to_be_deleted)
            print("Files that would be deleted:  ")
            zipped = list(zip(files_to_be_deleted, range(len(files_to_be_deleted))))
            print(' '.join(['\n' + x[0] if (x[1] % 4 == 0) else '\t' + x[0] for x in zipped]))
            print("Size before deletion: " + str(initial_size / 1024 ** 3) + "GB \t" + "Size after deletion: " + str(
                size_after / 1024 ** 3) + "GB")

    except InvalidPath as path_error:
        print("Specified path exception: ", path_error.value)
        exit(-1)
    except InvalidPattern as pattern_error:
        print("Specified pattern error: ", pattern_error.value)
        exit(-1)
