# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Switch Objects based on Distance",
    "category": "3d View",
    "author": "lucasvinbr (lucasvinbr@gmail.com)",
    "version": "0.1",
    "location": "Scene Properties > Switch Objects Based On Distance",
    "description": "Toggles display of one object from a list based on the objects' distance from the viewer (viewer to first valid object in list)",
}

import bpy

from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty,
                       EnumProperty)

from bpy.types import (Operator,
                       Panel,
                       Menu,
                       PropertyGroup,
                       Scene,
                       UIList)
                       
from bpy.app.handlers import persistent


def switchDistantObjects(region3d, objsList):
    dist = None
    foundDisplayableObj = False
    for i, objListEntry in enumerate(objsList):
        if objListEntry.target_obj is None:
            continue
        
        if dist is None:
            dist = (region3d.view_matrix.translation - objListEntry.target_obj.matrix_world.translation).magnitude
        
        if not foundDisplayableObj:
            foundDisplayableObj = dist < objListEntry.max_dist
            objListEntry.target_obj.hide = not foundDisplayableObj
        else:
            objListEntry.target_obj.hide = True


class ObjByDistPanel(bpy.types.Panel):
    """Creates a Panel in the Scene properties window"""
    bl_label = "Switch Objects on Distance"
    bl_idname = "SCENE_PT_objects_on_dist"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        
        curScene = context.scene
        
        row = layout.row()
        row.prop(curScene, "objByDistEnabled")
        
        row = layout.row()
        row.label(text="Objects List:")
        
        row = layout.row()
        row.template_list("objByDistListItems", "", curScene, "objByDistList", curScene, "objByDistListIndex", rows=4)

        col = row.column(align=True)
        col.operator("objByDist.list_action", icon='ZOOMIN', text="").action = 'ADD'
        col.operator("objByDist.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.separator()
        col.operator("objByDist.list_action", icon='TRIA_UP', text="").action = 'UP'
        col.operator("objByDist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'
        

class DistBasedShowableEntry(PropertyGroup):
    max_dist = FloatProperty(name="Max Distance", description="The maximum distance (viewer to first object in list) at which this object will be shown. At greater distances, the next object in the list will be shown")
    target_obj = PointerProperty(type=bpy.types.Object, name="Target Object", description="Object affected by this rule")
    entry_id = IntProperty()

class objByDistListItems(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(0.9)
        split.prop(item, "target_obj", text="")
        split = layout.split(0.9)
        split.prop(item, "max_dist")

    def invoke(self, context, event):
        pass   

class objByDistListOps(Operator):
    """Move items up and down, add and remove"""
    bl_idname = "objbydist.list_action"
    bl_label = "Replacer List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action = bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def invoke(self, context, event):
        curScene = context.scene
        idx = curScene.objByDistListIndex

        try:
            item = curScene.objByDistList[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(curScene.objByDistList) - 1:
                item_next = curScene.objByDistList[idx+1].name
                curScene.objByDistList.move(idx, idx+1)
                curScene.objByDistListIndex += 1
                

            elif self.action == 'UP' and idx >= 1:
                item_prev = curScene.objByDistList[idx-1].name
                curScene.objByDistList.move(idx, idx-1)
                curScene.objByDistListIndex -= 1
                

            elif self.action == 'REMOVE':
                curScene.objByDistListIndex -= 1
                curScene.objByDistList.remove(idx)

        if self.action == 'ADD':
            item = curScene.objByDistList.add()
            item.entry_id = len(curScene.objByDistList) - 1
            if item.entry_id > 0:
                item.max_dist = curScene.objByDistList[item.entry_id - 1].max_dist * 2
                item.target_obj = curScene.objByDistList[item.entry_id - 1].target_obj
                
            curScene.objByDistListIndex = len(curScene.objByDistList)-1


        return {"FINISHED"}



#--------------
#REGISTER\UNREGISTER
#--------------

classes = (
    objByDistListItems,
    objByDistListOps,
    DistBasedShowableEntry,
    ObjByDistPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    
    Scene.objByDistEnabled = BoolProperty(default=False, name="Enable", description="Enables or disables the plugin's effects")
    
    
    Scene.objByDistList = CollectionProperty(type=DistBasedShowableEntry)
    Scene.objByDistListIndex = IntProperty()


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del Scene.objByDistEnabled
    del Scene.objByDistList
    del Scene.objByDistListIndex


@persistent
def check_switchObjByDist(scn):
    if scn.objByDistEnabled:
        for winMan in bpy.data.window_managers:
            for win in winMan.windows:
                for area in win.screen.areas:
                    if area.type == "VIEW_3D":
                        switchDistantObjects(area.spaces.active.region_3d, scn.objByDistList)




bpy.app.handlers.scene_update_post.append(check_switchObjByDist)

if __name__ == "__main__":
    register()
 
