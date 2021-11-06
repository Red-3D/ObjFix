import bpy

bl_info = {
    "name": "ObjFix",
    "author": "Falco Badermann <falcobadermann@gmail.com>",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "category": "Object",
    "Location": "View3D > Object > ObjFix",
    "description": "Fix common issues of the obj importer",
    "doc_url": "https://github.com/Red-3D/ObjFix",
    "category": "Import-Export"
}

# class definition
class OBJECT_OT_objfix(bpy.types.Operator):
    """fix common issues of the obj importer"""
    bl_label = "ObjFix"
    bl_idname = "object.objfix"
    bl_description = "Fix common issues of the obj importer"
    bl_options = {'REGISTER', 'UNDO'}

    fix_materialColors: bpy.props.BoolProperty (
        name = "texture color",
        description = "colorize texture with material color",
        default = True
    )

    fix_mesh: bpy.props.BoolProperty (
        name = "un-triangulate",
        description = "merge by distance and optimize flat surfaces",
        default = True
    )

    fix_shading: bpy.props.BoolProperty (
        name = "shading",
        description = "misc shading fixes",
        default = True
    )

    # deactivate the operator when there isnt anything it could act upon
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.selected_objects

    # operator definition
    def execute(self, context):

        for obj in context.selected_objects:

            if obj.type != 'MESH': continue

            if self.fix_materialColors:

                for mat in obj.material_slots:

                    mat = mat.material.node_tree

                    if mat.nodes.get('Mix') or not mat.nodes.get('Image Texture'):
                        break

                    # get references to other nodes
                    texture = mat.nodes.get('Image Texture')
                    bsdf = mat.nodes.get('Principled BSDF')
                    out = mat.nodes.get('Material Output')

                    # add and configure the mixrgb node
                    mix = mat.nodes.new(type='ShaderNodeMixRGB')
                    mix.blend_type = 'MULTIPLY'
                    mix.inputs[2].default_value = bsdf.inputs[0].default_value
                    mix.inputs[0].default_value = 1

                    # relink the shader
                    mat.links.clear()
                    mat.links.new(texture.outputs[0], mix.inputs[1])
                    mat.links.new(mix.outputs[0], bsdf.inputs[0])
                    mat.links.new(bsdf.outputs[0], out.inputs[0])

                    # imrove shader readability
                    bsdf.location.y = out.location.y
                    bsdf.location.x = out.location.x - (bsdf.width + 20)

                    mix.location.y = bsdf.location.y
                    mix.location.x = bsdf.location.x - (mix.width + 20)

                    texture.location.y = mix.location.y
                    texture.location.x = mix.location.x - (texture.width + 20)

            if self.fix_mesh:

                # to quads
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold = 0.0001)
                bpy.ops.mesh.dissolve_limited(angle_limit = 0.017)
                bpy.ops.object.mode_set(mode='OBJECT')

            if self.fix_shading:

                # fix shading
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
                bpy.ops.object.shade_smooth()
                bpy.context.object.data.use_auto_smooth = True
                bpy.context.object.data.auto_smooth_angle = 0.523599

        return {'FINISHED'}


def objfix_draw(self, context):
    self.layout.operator("object.objfix", icon = "GHOST_ENABLED")

def register():
    bpy.utils.register_class(OBJECT_OT_objfix)
    bpy.types.VIEW3D_MT_object.append(objfix_draw)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_objfix)
    bpy.types.VIEW3D_MT_object.remove(objfix_draw)

if __name__ == '__main__':
    register()
