#! /usr/bin/env python
# encoding: utf-8
# Yinon Ehrlich, 2008, 2009

"""
Should be serve as common tester for all cc derivativers, currently:
msvc, g++, sunc++, gcc & suncc.
"""

import os, sys, shutil, tempfile
import common_test

# allow importing from wafadmin dir.
sys.path.append(os.path.abspath(os.path.pardir))
from Constants import *

# The following string is a wscript for tests.
# Note the embedded strings that changed by self._test_dic: set_env, tool, objname, build_type
wscript_contents = """
blddir = 'build'
srcdir = '.'

def configure(conf):
	%(set_env)s
	conf.check_tool('%(tool)s')

def build(bld):
	bld.new_task_gen(features=%(features)s, source='%(source)s', target='hello')

def set_options(opt):
	opt.tool_options('%(tool)s')
"""

cpp_program_code = """
#include <iostream>
int main()
{
	std::cout << "hi";
	return 0;
}
"""

c_program_code = """
#include <stdio.h>
int main()
{
	printf("hi");
	return 0;
}
"""

lib_code = """
int getIt()
{
	return 2;
}
"""

class CcRootTester(common_test.CommonTester):

	# utilities functions:
	
	def _populate_dictionary(self, features, source, code, set_env='pass'):
		"""
		standard template for functions below - single (write) access point to dictionary. 
		"""
		self._test_dic['features'] = features
		self._test_dic['source'] = source
		self._test_dic['code'] = code
		self._test_dic['set_env'] = set_env
		self._write_files()
		
	def _setup_cpp_program(self):
		self._populate_dictionary(['cxx', 'cprogram'], 'main.cpp', cpp_program_code)
		
	def _setup_c_program(self):
		self._populate_dictionary(['cc', 'cprogram'], 'main.c', c_program_code)
		
	def _setup_cpp_share_lib(self):
		self._populate_dictionary(['cxx', 'cshlib'], 'lib.cpp', lib_code)
	
	def _setup_cpp_static_lib(self):
		self._populate_dictionary(['cxx', 'cstaticlib'], 'lib.cpp', lib_code)
	
	def _setup_c_share_lib(self):
		self._populate_dictionary(['cc', 'cshlib'], 'lib.c', lib_code)
	
	def _setup_c_static_lib(self):
		self._populate_dictionary(['cc', 'cstaticlib'], 'lib.c', lib_code)

	def _setup_cpp_objects(self):
		self._populate_dictionary(['cxx'], 'mere.cpp', lib_code)
		
	def _setup_c_objects(self):
		self._populate_dictionary(['cc'], 'mere.c', lib_code)

	def _setup_cpp_program_with_env(self, env_line):
		self._populate_dictionary(['cxx', 'cprogram'], 'main.cpp', cpp_program_code, env_line)

	def _setup_c_program_with_env(self, env_line):
		self._populate_dictionary(['cc', 'cprogram'], 'main.c', cpp_program_code, env_line)

	def _write_source(self):
		self._write_file(self._test_dic['source'], self._test_dic['code'])

	def _write_files(self):
		self._write_wscript(wscript_contents % self._test_dic)
		self._write_source()

	def __init__(self, methodName):
		common_test.CommonTester.__init__(self, methodName)

	def setUp(self):

		# populate specific tool's dictionary
		self._test_dic = {}
		try:
			self._test_dic['tool'] = self.tool_name
			self._test_dic['objname'] = self.object_name
		except AttributeError:
			print "Testers that inherited ccroot have to define 'self.tool_name' and 'self.object_name'"
			sys.exit(1)

		# define & create temporary testing directories
		self._test_dir_root = tempfile.mkdtemp("", ".waf-testing_")
		self._srcdir = self._test_dir_root
		self._blddir = os.path.join( self._test_dir_root, "build" )
		self._wscript_file_path = os.path.join(self._test_dir_root, WSCRIPT_FILE)
		os.chdir(self._test_dir_root)

	def test_default_flags_patterns(self):
		# white box test: makes sure that correct flags/pattersn are defined
		self._validate_flags_patterns(sys.platform)

	def test_deceived_platform_flags_patterns(self):
		# white box test: makes sure that correct flags/pattersn are defined
		# for other platform
		global sys
		deceived_platform = self._get_other_platform()

		# be ware, evil in its best ! :)
		try:
			sys.platform = deceived_platform
			self._validate_flags_patterns(deceived_platform)
		finally:
			sys=reload(sys)

	def test_another_platform_flags_patterns(self):
		# white box test: makes sure that correct flags/pattersn are defined
		# for other platform given as parameter
		self._validate_flags_patterns(self._get_other_platform(), set_target=True)

	def _get_other_platform(self):
		if sys.platform == 'linux2':
			return 'win32'
		return 'linux2'

	def _validate_flags_patterns(self, dest_os, set_target=False):
		# TODO: extend the tests for other platforms...
		wscript_contents = """
blddir = 'build'
srcdir = '.'

def configure(conf):
	conf.check_tool('%(tool)s')"""
		self._write_wscript(wscript_contents % self._test_dic)
		conf = self._setup_configure()
		env = conf.env
		if set_target:
			env['DEST_OS'] = dest_os
		conf.sub_config([''])

		self.assert_(env['staticlib_PATTERN'] == 'lib%s.a', 'incorrect staticlib pattern')
		self.assert_(env['staticlib_LINKFLAGS'] == ['-Wl,-Bstatic'], 'incorrect staticlib_LINKFLAGS')
		if self.tool_name == 'gcc':
			self.assert_(env['shlib_CCFLAGS'] == ['-fPIC', '-DPIC'], 'incorrect shlib CCFLAGS')
		else:
			self.assert_(env['shlib_CXXFLAGS'] == ['-fPIC', '-DPIC'], 'incorrect shlib CXXFLAGS was %s' % env['shlib_CXXFLAGS'])

		if dest_os in ('win32', 'cygwin'):
			self.assert_(env['program_PATTERN'] == '%s.exe', 'incorrect program pattern, was "%s", dest_os = %s' % (env['program_PATTERN'], dest_os))
			self.assert_(env['shlib_PATTERN'] == '%s.dll', 'incorrect shlib pattern')
		elif dest_os == 'linux2': # TODO potential problem here: ccroot.py's DEST_OS is supposed to be 'linux'
			self.assert_(env['program_PATTERN'] == '%s', 'incorrect program pattern')
			self.assert_(env['shlib_PATTERN'] == 'lib%s.so', 'incorrect shlib pattern')

			self.assert_(env['shlib_LINKFLAGS'] == ['-shared'], 'incorrect staticlib_LINKFLAGS')
		else:
			raise NotImplementedError('tests for %s were not implemented yet...' % dest_os)

	def tearDown(self):
		'''tearDown - deletes the directories and files created by the tests ran '''
		os.chdir(self._waf_root_dir)

		if os.path.isdir(self._test_dir_root):
			shutil.rmtree(self._test_dir_root)
