#--Start imports block
#System import
import os
from pprint import pprint
import typing as typ
from pathlib import Path as PathType
#Custom import
#--Finish imports block

#--Start global constant block
ignore_list = [
    '.gitkeep',
    './.cache',
    './.config',
    './.upm',
    './.replit',
    './.breakpoints',
    './.git',
    './venv',
    './replit.nix',
    './pyproject.toml',
    './poetry.lock',
    './__pycache__',
    '__pycache__',
    './flask_session',

    './var',
    './logs',
    './proxy_lists',
    './web_pages',
    'img',
]
#--Finish global constant block

#--Start decorator block
#--Finish decorator block

#--Start functional block

#Begin inside block
#End inside block
def get_all(in_dir: PathType) -> typ.List[PathType]:
    '''
    Gets list of directories and files from target directory.
    '''
    all = [
        os.path.join(in_dir, file_name)
        for file_name in os.listdir(in_dir)
    ]
    return all

def get_directories(in_dir: PathType='./') -> typ.List[PathType]:   
    '''
    Gets list of only diretories from target directory.
    ''' 
    all = get_all(in_dir)
    all_dirs = [
        file_name for file_name in all 
        if os.path.isdir(file_name)
    ]
    return all_dirs

def get_files(in_dir: PathType='.') -> typ.List[PathType]:
    '''
    Gets list of only files from target directory.
    '''
    all = get_all(in_dir)
    dir_files = [
        file_name for file_name in all 
        if os.path.isfile(file_name)
    ]
    return dir_files

def get_files_in_dirs(all_dirs: typ.List[PathType]) -> typ.List[PathType]:
    '''
    Gets all code files from target directodies.
    '''
    all_sub_files = list()

    for in_dir in all_dirs:
        print("\n*-- Sub directories in : %s" % in_dir)

        sub_dirs = get_directories(in_dir)
        sub_files = get_files(in_dir)

        sub_dirs = check_if_ignore(sub_dirs)
        sub_files = check_if_ignore(sub_files)

        print("* Edited sub directories: ")
        pprint(sub_dirs)
        print("* Edited sub files: ")
        pprint(sub_files)
        
        if sub_dirs:
            add_files = get_files_in_dirs(sub_dirs)
            sub_files.extend(add_files)

        all_sub_files.extend(sub_files)
    
    return all_sub_files

def is_ignore(path_name: PathType) -> bool:
    '''
    Cheks if file name in ignore list.
    '''
    name = path_name.split('/')[-1]
    if name in ignore_list:
        return True
    return False

def check_if_ignore(dirs_or_files: typ.List[PathType]) -> typ.List[PathType]:
    '''
    Checks if list of files in ignore list.
    '''
    return_list = list()

    for path_name in dirs_or_files:
        if not is_ignore(path_name):
            return_list.append(path_name)

    return return_list

def remove_ignores(list_of_paths: typ.List[PathType]) -> typ.List[PathType]:
    '''
    Removes files or dirs from list of paths if in ignore list.
    '''
    for ignore in ignore_list:
        if ignore in list_of_paths:
            list_of_paths.remove(ignore)
    
    return list_of_paths

def count_lines_in_file(path_name: PathType) -> int:
    '''
    Counts lines in target file.
    '''
    count_lines = len(open(path_name).readlines(  ))
    return count_lines

def count_lines_in_files(list_path_names: typ.List[PathType]) -> int:
    '''
    Count code lines in target list of files.
    '''
    all_count_lines = 0

    for path_name in list_path_names:
        count = count_lines_in_file(path_name)
        all_count_lines += count

    return all_count_lines

#--Finish functional block

#--Start main block
def main() -> typ.NoReturn:
    all_dirs = get_directories()
    all_files = get_files()

    all_dirs = remove_ignores(all_dirs)
    all_files = remove_ignores(all_files)

    add_files = get_files_in_dirs(all_dirs)
    all_files.extend(add_files)

    print("\n* All files: " % all_files)
    pprint(all_files)

    all_count_lines = count_lines_in_files(all_files)

    answer = "The Count Code Lines Is: " + str(all_count_lines)
    print("\n\n*------------------------------")
    print(answer)
    print("*------------------------------\n")

    return answer

if __name__ == '__main__':
    _ = main()
#--Finish main block