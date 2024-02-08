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
    dry_run = False
    formatted = True
    quiet = False

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("path", action="store", help="the path to the signal backups directory", metavar="Path")
        parser.add_argument("pattern", action="store",
                            help="amount of yearly, monthly and daily backups to keep, use '-' if using flags",
                            metavar="YY-MM-DD | -")
        parser.add_argument("-y", "--yearly", action="store", type=int, required=False, dest="yearly")
        parser.add_argument("-m", "--monthly", action="store", type=int, required=False, dest="monthly")
        parser.add_argument("-d", "--daily", action="store", type=int, required=False, dest="daily")
        parser.add_argument("--dry-run", help="execute a dry run", action="store_true", dest="dry_run")
        parser.add_argument("-u", "--not-formatted", action="store_false",
                            help="quiet output except list of files without format", required=False, dest="formatted")
        parser.add_argument("-q", "--quiet", action="store_true", help="quiet operation", dest="quiet")

        args = parser.parse_args()
        self.__get_increments(args=args)

        self.dry_run = args.dry_run
        self.formatted = args.formatted
        self.quiet = args.quiet
        self.path_to_backups = DirectoryHelper.get_path(args.path)

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
        for i in range(1, len(sorted_list)):
            if not daily_files_counter == daily and int(current[15:17]) != int(sorted_list[i][15:17]):
                current = sorted_list[i]
                daily_files_counter += 1
                continue
            elif not monthly_files_counter == monthly and int(current[12:14]) != int(sorted_list[i][12:14]):
                current = sorted_list[i]
                monthly_files_counter += 1
                continue
            elif not yearly_files_counter == yearly and int(current[7:11]) != int(sorted_list[i][7:11]):
                current = sorted_list[i]
                yearly_files_counter += 1
                continue
            else:
                files_to_delete.append(current)
                current = sorted_list[i]

        return files_to_delete

    @staticmethod
    def delete(path_to_dir, files):
        [os.remove(os.path.join(path_to_dir, file)) for file in files]

    @staticmethod
    def get_path(path_arg):
        path = Path(path_arg).resolve()
        if not os.path.isdir(path):
            raise InvalidPath("Path is not a directory")
        elif len(os.listdir(path)) == 0:
            raise InvalidPath("Directory is empty!")
        else:
            return path


class FileList(list):
    formatted = True

    def __init__(self, iterable, formatted):
        super().__init__(iterable)
        self.formatted = formatted

    def __repr__(self):
        if self.formatted:
            print(' '.join(['\n' + x[0] if (x[1] % 4 == 0) else '\t' + x[0] for x in self]))
            return ' '.join(['\n' + x[0] if (x[1] % 4 == 0) else '\t' + x[0] for x in self])
        else:
            return '\n'.join(map(lambda x: x[0], self))


if __name__ == '__main__':
    try:
        args_handler = ArgsHandler()
        backup_files = DirectoryHelper.get_backup_files(args_handler.path_to_backups)
        initial_size = DirectoryHelper.get_size(args_handler.path_to_backups, backup_files)
        files_to_be_deleted = DirectoryHelper.filter_files_for_deletion(
            yearly=args_handler.yearly,
            monthly=args_handler.monthly,
            daily=args_handler.daily,
            file_list=backup_files
        )
        size_after = initial_size - DirectoryHelper.get_size(args_handler.path_to_backups, files_to_be_deleted)
        if args_handler.dry_run:
            if not args_handler.quiet:
                print("Files that would be deleted:  ")
            files_for_deletion = FileList(zip(files_to_be_deleted,
                                              range(len(files_to_be_deleted))), args_handler.formatted)
            print(files_for_deletion)
        else:
            DirectoryHelper.delete(args_handler.path_to_backups, files_to_be_deleted)
        if not args_handler.quiet:
            print("Size before deletion: " + str(initial_size / 1024 ** 3) + "GB \t" + "Size after deletion: " + str(
                size_after / 1024 ** 3) + "GB")
            print("Files total: " + str(len(files_to_be_deleted)))

    except InvalidPath as path_error:
        print("Specified path exception: ", path_error.value)
        exit(-1)
    except InvalidPattern as pattern_error:
        print("Specified pattern error: ", pattern_error.value)
        exit(-1)
