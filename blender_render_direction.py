import bpy
import os
import math
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty
                       )
from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       UIList
                       )
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

import json

import mathutils
from bpy_extras.object_utils import world_to_camera_view



def get_camera_2d_origin():
    scene = bpy.context.scene

    # Getting resolution of the final render ( important to know where in pixel the point is )
    render = scene.render
    res_x = render.resolution_x
    res_y = render.resolution_y

    # Getting the current camera
    cam = bpy.context.scene.camera

    # The actual XYZ location of the origin
    coords = mathutils.Vector((0.0, 0.0, 0.0))

    # Voodoo magic blender can do to find the coordinate of the point, from camera XYZ 
    coords_2d = world_to_camera_view(scene, cam, coords) 

    origin_x = coords_2d.x * res_x
    origin_y = res_y - (coords_2d.y * res_y)

    return mathutils.Vector((round(origin_x), round(origin_y)))

class ModalTimerOperator(Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "render.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    
    updated = False
    end_early = False
    _timer = None
    
    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            print("do in timer")
            # change theme color, silly!
            #color = context.preferences.themes[0].view_3d.space.gradients.high_gradient
            #color.s = 1.0
            #color.h += 0.01

        return {'PASS_THROUGH'}
    
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)




class OT_OpenFilebrowser(Operator, ImportHelper):

    bl_idname = "filebrowser.render_path"
    bl_label = "Select render folder"
     
    filter_glob: StringProperty(
        default='*',
        options={'HIDDEN'}
    )
    
    some_boolean: BoolProperty(
        name='Do a thing',
        description='Do a thing with the file you\'ve selected'
    )

    def execute(self, context):
        """Do something with the selected file(s)."""

        filebase, extension = os.path.splitext(self.filepath)
        
        dirname, basename = os.path.split(self.filepath)
        
        print('Selected file:', self.filepath)
        print('filebase:', filebase)
        print('dirname:', dirname)
        print('basename:', basename)
        print('File extension:', extension)
        print('Some Boolean:', self.some_boolean)
        
        context.scene.render_prop.dirname = dirname
        
        return {'FINISHED'}

class ListItem(PropertyGroup): 
    """Group of properties representing an item in the list.""" 
    name: StringProperty( 
        name="Name", 
        description="A name for this item", 
        default="Untitled") 

    active: BoolProperty( 
        name="Active", 
        description="A name for this item", 
        default=False)
        
    random_prop: StringProperty( 
        name="Any other property you want", 
        description="", default="")



class MY_UL_List(UIList):
    """Actions UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        # We could write some code to decide which icon to use here...
        if item.active == True:
            custom_icon = 'CHECKBOX_HLT'
        else:
            custom_icon = 'CHECKBOX_DEHLT'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

        layout.enabled = item.active

    def draw(self, context):
        print("draw")

class RenderPropGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="name", default="Text")
    dirname: bpy.props.StringProperty(name="Output", default="/tmp/")
    value: bpy.props.IntProperty(name="value", default=5)
    frames: bpy.props.IntProperty(name="Frames (1/x)", default=4)

    my_list: bpy.props.CollectionProperty(type = ListItem)
        
    list_index: bpy.props.IntProperty(name = "Index for my_list", default = 0)


    directions: bpy.props.EnumProperty(name="Directions", description="How many object directions to render", items=[
        ('1','1', 'number of directions to render'),
        ('2','2','number of directions to render'),
        ('4','4','number of directions to render'),
        ('8','8','number of directions to render'),
        ('16','16','number of directions to render'),
        ('32','32','number of directions to render'),
        ])
    cardinal_names: bpy.props.BoolProperty(name="Generate cardinal direction names", description="If activated use E, NE, N, NW, W, SW, S, SE for <= 8 directions. Otherwise generate angle names.", default=True)
    facing_angle: bpy.props.IntProperty(name="Facing Angle", description="Left oriented rotation angle compared to a character looking to the north view (top of the screen).", default=0)
    

class LIST_OT_NewItem(Operator):
    """Add a new item to the list."""

    bl_idname = "my_list.new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        list = context.scene.my_list.add()

        return{'FINISHED'}



class LIST_OT_DeleteItem(Operator):
    """Delete the selected item from the list."""

    bl_idname = "my_list.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.my_list

    def execute(self, context):
        my_list = context.scene.my_list
        index = context.scene.list_index

        my_list.remove(index)
        context.scene.list_index = min(max(0, index - 1), len(my_list) - 1)

        return{'FINISHED'}



class LIST_OT_ActivateItem(Operator):
    """Activate the selected item from the list."""

    bl_idname = "my_list.activate_item"
    bl_label = "Activate an item"

    @classmethod
    def poll(cls, context):
        return context.scene.render_prop.my_list

    def execute(self, context):
        my_list = context.scene.render_prop.my_list
        index = context.scene.render_prop.list_index
        
        context.scene.render_prop.my_list[index].active = True

        return{'FINISHED'}
    

 
class LIST_OT_DeactivateItem(Operator):
    """Deactivate the selected item from the list."""

    bl_idname = "my_list.deactivate_item"
    bl_label = "Deactivate an item"

    @classmethod
    def poll(cls, context):
        return context.scene.render_prop.my_list

    def execute(self, context):
        my_list = context.scene.render_prop.my_list
        index = context.scene.render_prop.list_index
        
        context.scene.render_prop.my_list[index].active = False

        return{'FINISHED'}
    
class LIST_OT_UpdateList(Operator):
    """Clear all items of the list"""
    bl_idname = "my_list.update_list"
    bl_label = "Update List"
    bl_description = "Update all items of the list"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        print("execute")
        context.scene.render_prop.my_list.clear()
        for a in bpy.data.actions:
            print(a.name)
            item = context.scene.render_prop.my_list.add()
            item.name = a.name
        self.report({'INFO'}, "All items updated")

        return {'FINISHED'}

class RENDER_PT_panel_p(bpy.types.Panel):
    bl_idname = 'RENDER_PT_panel_p'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_label = 'Direction Renderer'

    def draw(self, context):
        scene = context.scene
        object = context.object
        
        self.layout.label(text="Settings to export rendered images:")
 
        row = self.layout.row()
        row.prop(context.scene.render_prop, "frames")
        
        row = self.layout.row()
        row.prop(context.scene.render_prop, "directions")
        
        row = self.layout.row()
        row.prop(context.scene.render_prop, "facing_angle")
        
        row = self.layout.row()
        row.prop(context.scene.render_prop, "cardinal_names")
                        
        split = self.layout.split(factor=0.92)
        
        col = split.column()
        col.template_list("MY_UL_List", "The_List", context.scene.render_prop,
                          "my_list", context.scene.render_prop, "list_index")

        col = split.column()
        col.operator('my_list.activate_item', text='', icon='CHECKBOX_HLT')
        col.operator('my_list.deactivate_item', text='', icon='CHECKBOX_DEHLT')
        col.operator('my_list.update_list', text='', icon='PREVIEW_RANGE')


        row = self.layout.row()

        split = self.layout.split(factor=0.92)

        col = split.column()
        col.prop(context.scene.render_prop, "dirname")
        
        col = split.column()
        col.operator(
            operator='filebrowser.render_path',
            icon='FILEBROWSER',
            text=''
        )
         
        
        # 'render.modal_timer_operator',
        # render operator call
        self.layout.operator(
            operator='object.render_operator',
            icon='RENDER_ANIMATION',
            text='Create direction images'
        )

        #for a in bpy.data.actions:
        #    print(a.name)
        #    item = context.scene.render_prop.my_list.add()
        #    item.name = a.name

     

    def register():
        bpy.types.Scene.render_prop = bpy.props.PointerProperty(type=RenderPropGroup)

        pass
        #bpy.types.Scene.my_list.clear()
        
        #item = bpy.types.Scene.render_prop.my_list.add()
        #item.name = "test"

        # populate the action animations list with items
        #for a in bpy.data.actions:
        #    item = bpy.context.scene.my_list.add()
        #    item.name = a.name

        


        #bpy.types.Scene.float_x = bpy.props.FloatProperty(default=4.5)
        #bpy.types.Scene.cube_x = bpy.props.IntProperty()
        
    def unregister():
        del bpy.types.Scene.render_prop
        #del bpy.types.Scene.my_list



class RenderOperator(bpy.types.Operator):
    bl_idname = "object.render_operator"
    bl_label = "Render Operator"

    def get_cardinal_name(self, angle):
        angle_name = "angle_error"
        
        if angle == 0:
            angle_name = "N"
        elif angle == 45:
            angle_name = "NW"
        elif angle == 90:
            angle_name = "W"
        elif angle == 135:
            angle_name = "SW"
        elif angle == 180:
            angle_name = "S"
        elif angle == 225:
            angle_name = "SE"
        elif angle == 270:
            angle_name = "E"
        elif angle == 315:
            angle_name = "NE"
        elif angle == 360: # not needed, but who knows...
            angle_name = "N"
            
        return angle_name

    def get_cardinal_angle(self, directions, direction_num) -> int:
        if direction_num > directions:
            return 0
        
        angle_slice = 360 / directions
        angle = round(direction_num * angle_slice)
               
        return angle

    def execute(self, context):
        print("Execute Render")
        
        #index = context.scene.list_index
        #name = context.scene.my_list[index].name
        #print(name)
        
        #for item in context.scene.my_list:
        #    print("name:" + item.name)
        
        # only to debug the render operation
        #return {'FINISHED'}

        render_path = context.scene.render_prop.dirname
        # path fixing
        render_path = os.path.abspath(render_path)
        if not os.path.exists(render_path):
            os.makedirs(render_path)
                            
        print("renderpath: " + render_path)

        # get list of selected objects
        selected_list = bpy.context.selected_objects

        # deselect all in scene
        bpy.ops.object.select_all(action='TOGGLE')
        
        # I left this in as in some of my models, I needed to translate the "root" object but
        # the animations were on the armature which I selected.
        # 
        #obRoot = bpy.context.scene.objects["root"]

        only_armatures = True
        for o in selected_list:
            if o.type != 'ARMATURE':
                only_armatures = False
        
        if only_armatures == False:
            self.report({'WARNING'}, "Please select only Armatures. (Current: %s)" % o.type)
            return {'FINISHED'}
        
        coord = get_camera_2d_origin()
        
        ortho_scale = bpy.context.scene.camera.data.ortho_scale
        cam_location = bpy.context.scene.camera.location
        cam_shift_x = bpy.context.scene.camera.data.shift_x
        cam_shift_y = bpy.context.scene.camera.data.shift_y
                    
        # calculate based on number of directions about which angle should be rotated each image
        directions = int(context.scene.render_prop.directions)
        
        blender_fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        
        img_width = bpy.context.scene.render.resolution_x
        img_height = bpy.context.scene.render.resolution_y
                    
        # loop all initial selected objects (which will likely just be one object.. I haven't tried setting up multiple yet)        
        for o in selected_list:
                        
            # select the object
            bpy.context.scene.objects[o.name].select_set(True)

            scn = bpy.context.scene

            # loop through the actions
            for item in context.scene.render_prop.my_list:
                # render only in the UIList activated actions
                if item.active == False:
                    continue
                
                #assign the action
                bpy.context.active_object.animation_data.action = bpy.data.actions.get(item.name)
                
                #dynamically set the last frame to render based on action
                scn.frame_end = int(bpy.context.active_object.animation_data.action.frame_range[1])
                                
                #create folder for animation
                action_folder = os.path.join(render_path, item.name)
                if not os.path.exists(action_folder):
                    os.makedirs(action_folder)
                
                #loop through all directions
                for direction_num in range(directions):
                    angle = self.get_cardinal_angle(directions, direction_num)
                    
                    if context.scene.render_prop.cardinal_names and directions <= 8:
                        angleDir = self.get_cardinal_name(angle)
                    else:
                        angleDir = str(angle)   
                     
                    #create folder for specific angle
                    animation_folder = os.path.join(action_folder, angleDir)
                    if not os.path.exists(animation_folder):
                        os.makedirs(animation_folder)
                    
                    #rotate the model for the new angle
                    bpy.context.active_object.rotation_mode = "XYZ"
                    bpy.context.active_object.rotation_euler[2] = math.radians(angle - context.scene.render_prop.facing_angle)
                    
                    # the below is for the use case where the root needed to be translated.
                    # obRoot.rotation_euler[2] = math.radians(angle)
                    
                    # loop through and render frames.  The UI sets how "often" it renders.
                    # Every frame is likely not needed.
                    json_frames = []
                    for i in range(scn.frame_start,scn.frame_end, context.scene.render_prop.frames):
                        scn.frame_current = i

                        json_frame = {}
                        render_filename = (str(item.name)
                                            + "_"
                                            + str(angle)
                                            + "_"
                                            + str(scn.frame_current).zfill(3)
                                            )
                        json_frame['name'] = render_filename
                        #json_frame['time'] = round(scn.frame_current / export_fps, 2)
                                                
                        scn.render.filepath = (
                                            animation_folder
                                            + "/"
                                            + render_filename
                                            )
                                            
                        bpy.ops.render.render( #{'dict': "override"},
                                              #'INVOKE_DEFAULT',  
                                              False,            # undo support
                                              animation=False, 
                                              write_still=True
                                             )
                        json_frames.append(json_frame)
                                             
                    json_dict = {
                      "fps": blender_fps / context.scene.render_prop.frames,
                      "origin": {
                           "x": int(coord.x),
                           "y": int(coord.y)
                      },
                      "camera": {
                          "ortho_scale": round(ortho_scale, 2),
                          "location": {
                            "x": round(cam_location[0], 2),
                            "y": round(cam_location[1], 2),
                            "z": round(cam_location[2], 2),
                          },
                          "shift": {
                            "x": round(cam_shift_x, 2),
                            "y": round(cam_shift_y, 2),
                          },
                      },
                      "animations": {
                            item.name: {
                                angleDir: json_frames
                            },                         
                        },
                    }

                    json_str = json.dumps(json_dict, indent=4)
                    
                    json_filename = os.path.join(animation_folder, "metadata.json")
                    print("json_filename: " + json_filename)

                    # write JSON file
                    with open(json_filename, 'w') as outfile:
                        outfile.write(json_str + '\n')
        
        # after rotation for export reset the z rotation back to zero 
        bpy.context.active_object.rotation_euler[2] = 0
                                                    
        return {'FINISHED'}

classes = [
    ListItem,
    MY_UL_List,
    RenderPropGroup,
    LIST_OT_NewItem,
    LIST_OT_DeleteItem,
    LIST_OT_ActivateItem,
    LIST_OT_DeactivateItem,
    LIST_OT_UpdateList,
    RENDER_PT_panel_p,
    RenderOperator,
    OT_OpenFilebrowser
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # progress bar
    #bpy.types.Text.progress_bar = bpy.props.IntProperty(
#                                subtype="PERCENTAGE",
#                                min=0,
#                                max=100
#                                )
    #bpy.types.Text.show_progress_bar = bpy.props.BoolProperty()
    #bpy.utils.register_class(ModalTimerOperator)
    #bpy.types.TEXT_HT_header.append(header_draw_func)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


    # progress bar
    #del bpy.types.Text.progress_bar
    #del bpy.types.Text.show_progress_bar
    #bpy.utils.unregister_class(ModalTimerOperator)
    #bpy.types.TEXT_HT_header.remove(header_draw_func)

if __name__ == "__main__":
    register()
