# coding : utf-8
#
# nclr_versioning/__init__.py
#

bl_info = {
	"name" : "nclr versioning",
	"author" : "LNSEAB",
	"version" : ( 0, 1 ),
	"blender" : ( 2, 78, 0 ),
	"location" : "Versioning",
	"category" : "System"
}

import sys
import bpy
from . import lang
from . import git
from bpy.app.handlers import persistent

def update_history(context) :
	if not git.is_initialized( context ) :
		return

	log = git.log( context )
	context.scene.nclr_versioning.history.clear()
	for elem in log :
		entry = context.scene.nclr_versioning.history.add()
		entry.message = elem[0]
		entry.date = elem[1]
		entry.hash = elem[2]
		entry.name = "{} {} {}".format( entry.message, entry.date, entry.hash )

def git_root_path(context, path) :
	return bpy.path.relpath( path, context.scene.nclr_versioning.work_dir ).lstrip( "/" )

class HistoryEntry(bpy.types.PropertyGroup) :
	message = bpy.props.StringProperty()
	date = bpy.props.StringProperty()
	hash = bpy.props.StringProperty()

class VersioningContext(bpy.types.PropertyGroup) :
	work_dir = bpy.props.StringProperty()
	history = bpy.props.CollectionProperty( type = HistoryEntry )
	history_index = bpy.props.IntProperty()

class Init(bpy.types.Operator) :
	bl_idname = "nclr_versioning.init"
	bl_label = "Initialize"

	def execute(self, context) :
		return { "FINISHED" }

class CommitMessageDialog(bpy.types.Operator) :
	bl_idname = "object.nclr_versioning_commit_message_dialog"
	bl_label = "Input commit message"

	message = bpy.props.StringProperty( name = "Message" )

	def invoke(self, context, event) :
		return context.window_manager.invoke_props_dialog( self )

	def execute(self, context) :
		if self.message == "" :
			self.report( { "ERROR" }, bpy.app.translations.pgettext( "no message" ) )
			return { "CANCELLED" }
		git.add( context, [git_root_path( context, bpy.data.filepath )] )
		git.commit( context, self.message )
		update_history( context )
		return { "FINISHED" }

class Commit(bpy.types.Operator) :
	bl_idname = "nclr_versioning.commit"
	bl_label = "Commit"

	def execute(self, context) :
		bpy.ops.object.nclr_versioning_commit_message_dialog( "INVOKE_DEFAULT" )
		return { "FINISHED" }

class CommitAmendMessageDialog(bpy.types.Operator) :
	bl_idname = "object.nclr_versioning_commit_amend_message_dialog"
	bl_label = "Input commit message"

	message = bpy.props.StringProperty( name = "Message" )

	def invoke(self, context, event) :
		return context.window_manager.invoke_props_dialog( self )

	def execute(self, context) :
		if self.message == "" :
			self.report( { "ERROR" }, bpy.app.translations.pgettext( "no message" ) )
			return { "CANCELLED" }
		git.commit_amend( context, self.message )
		update_history( context )
		return { "FINISHED" }

class CommitAmend(bpy.types.Operator) :
	bl_idname = "nclr_versioning.commit_amend"
	bl_label = "Amend"

	def execute(self, context) :
		bpy.ops.object.nclr_versioning_commit_amend_message_dialog( "INVOKE_DEFAULT" )
		return { "FINISHED" }

class OutputAsFile(bpy.types.Operator) :
	bl_idname = "nclr_versioning.output_as_file"
	bl_label = "Output as File"

	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	check_existing = bpy.props.BoolProperty( default = True, options = { "HIDDEN" } )

	def invoke(self, context, event) :
		context.window_manager.fileselect_add( self )
		return { "RUNNING_MODAL" }

	def execute(self, context) :
		index = context.scene.nclr_versioning.history_index
		hash = context.scene.nclr_versioning.history[index].hash
		fp = open( self.filepath, "wb" )
		fp.write( git.cat_file( context, hash, git_root_path( context, bpy.data.filepath ) ).stdout )
		fp.close()
		return { "FINISHED" }

class VersioningPanel(bpy.types.Panel) :
	bl_idname = "OBJECT_PT_nclr_versioning_panel"
	bl_label = "Versioning"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "Versioning"

	@classmethod
	def poll(cls, context) :
		return ( context.object is not None )

	def draw(self, context) :
		self.layout.label( "History" )
		self.layout.template_list( 
			"UI_UL_list", "history_list", 
			context.scene.nclr_versioning, "history",
			context.scene.nclr_versioning, "history_index",
			rows = 5
		)
		self.layout.operator( Commit.bl_idname )
		self.layout.operator( CommitAmend.bl_idname )
		self.layout.separator()
		self.layout.operator( OutputAsFile.bl_idname )

class VersioningPreferences(bpy.types.AddonPreferences) :
	bl_idname = __package__

	execute_path = bpy.props.StringProperty( name = "Git Execute Path", subtype = "FILE_PATH" )

	def draw(self, context) :
		self.layout.prop( self, "execute_path" )

@persistent
def file_handler(dummy) :
	cur_dir = bpy.path.abspath( "//" )
	bpy.context.scene.nclr_versioning.work_dir = cur_dir
	update_history( bpy.context )

def register() :
	bpy.utils.register_module( __name__ )
	bpy.types.Scene.nclr_versioning = bpy.props.PointerProperty( type = VersioningContext )
	bpy.app.handlers.load_post.append( file_handler )
	bpy.app.handlers.save_post.append( file_handler )
	bpy.app.translations.register( __name__, lang.tranlation_dict )

def unregister() :
	bpy.app.translations.unregister( __name__ )
	bpy.app.handlers.load_post.remove( file_handler )
	bpy.app.handlers.save_post.remove( file_handler )
	del bpy.types.Scene.nclr_versioning
	bpy.utils.register_module( __name__ )

if __name__ == "__main__" :
	register()