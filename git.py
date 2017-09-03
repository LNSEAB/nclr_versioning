# coding : utf-8
#
# nclr_versioning/
#

import subprocess
import os
import re

def __execute_path(context):
	addon_prefs = context.user_preferences.addons[__package__].preferences
	if addon_prefs.execute_path and addon_prefs.execute_path != "" :
		return addon_prefs
	return "git"

def __get_work_dir(context) :
	return context.scene.nclr_versioning.work_dir

def __command(context, cmd, args = []) :
	assert isinstance( args, list )
	work_dir = __get_work_dir( context ) 
	if work_dir != "" and os.getcwd() != work_dir :
		os.chdir( work_dir )
	return subprocess.run( [__execute_path( context ), cmd] + args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT )

def is_initialized(context) :
	return os.path.isdir( __get_work_dir( context ) + ".git" )

def init(context) :
	return __command( context, "init" )

def status(context, files) :
	assert isinstance( files, list )
	lines = __command( context, "status", ["--short"] + files ).stdout.decode( "utf-8" ).split( "\n" )
	items = []
	for i in range( 0, len( lines ) - 1 ) :
		items.append( ( ines[i][3:].rstrip(), lines[i][:2] ) )
	return items

def log(context) :
	lines = __command( context, "log", [r'--pretty=format:"%s" "%cd" %H'] ).stdout.decode( "utf-8" ).split( "\n" )
	items = []
	r = re.compile( "^\"(.+)\" \"(.+)\" ([0-9A-Za-z]+)" )
	for s in lines :
		m = r.match( s )
		if m :
			items.append( m.groups() )
	return items

def add(context, files) :
	assert isinstance( files, list )
	return __command( context, "add", files )

def commit(context, msg) :
	return __command( context, "commit", ["-m", msg] )

def commit_amend(context, msg) :
	return __command( context, "commit", ["--amend", "-m", msg] )

def cat_file(context, hash, file) :
	return __command( context, "cat-file", ["-p", hash + ":" + file] )