import fileinput
from os import walk

"""
Helper script to bundle the local dtsnmp module into the main plugin code
Prevents it from being wiped during oneagent_build_plugin
Usage: python prepare_build.py
"""

def remove_module_imports(base_file):
	remove_marker = 'from dtsnmp.'
	with fileinput.input(base_file, inplace=True, backup='.bak') as file:
		for line in file:
			if not line.startswith(remove_marker):
				print(line, end='')

def add_modules_to_base(module_path, base_file):
	exclude_list = ['__init__.py', 'cisco_process_mib.py']
	skip_line_markers = ('from .', 'import logging', 'logger = logging')

	# Get the list of all required module py files
	in_files = []
	for (dirpath, dirnames, filenames) in walk(module_path):
	    in_files.extend(filenames)
	    break
	for exclude in exclude_list:
		try:
		    in_files.remove(exclude)
		except ValueError:
		    pass
	in_files = [module_path + f for f in in_files]

	module_boundary_marker = '\n#####\n#LOCAL DTSNMP MODULE\n####\n'
	# append each module file to the main custom_plugin file
	with open(base_file, 'a+', newline='') as fout:
		fout.write(module_boundary_marker)
		for in_file in in_files:
			with open(in_file, 'r') as fin:
				for line in fin:
					if not line.startswith(skip_line_markers):
						fout.write(line)
				# Add newlines between file cats
				fout.write('\n\n')
			
if __name__ == '__main__':
	base_file = 'custom_snmp_base_plugin_remote.py'
	module_path = './dtsnmp/'
	remove_module_imports(base_file)
	add_modules_to_base(module_path, base_file)
