import fileinput
import re
from os import walk

def remove_module_imports(base_file):
	remove_marker = 'from dtsnmp.'
	with fileinput.input(base_file, inplace=True, backup='.bak') as file:
		for line in file:
			if not line.startswith(remove_marker):
				print(line, end='')

def add_modules_to_base(module_path, base_file):
	exclude_list = ['__init__.py']
	skip_line_markers = ('from .', 'import logging', 'logger = logging')

	# Create tuple of all required module files
	in_files = []
	for (dirpath, dirnames, filenames) in walk(module_path):
	    in_files.extend(filenames)
	    break
	for exclude in exclude_list:
		try:
		    in_files.remove(exclude)
		except ValueError:
		    pass
	in_files = tuple(module_path + f for f in in_files)

	with open(base_file, 'a+', newline='') as fout:
		with fileinput.input(files=in_files) as fin:
			for line in fin:
				if not line.startswith(skip_line_markers):
					fout.write(line)

if __name__ == '__main__':
	base_file = 'replace.py'
	module_path = './dtsnmp/'
	remove_module_imports(base_file)
	add_modules_to_base(module_path, base_file)
