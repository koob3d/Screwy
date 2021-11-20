bl_info = {
    "name": "New Screw",
    "author": "Paul Booker",
    "version": (1, 0),
    "blender": (2, 93, 5),
    "location": "View3D > Add > Mesh > New Screw",
    "description": "Adds a new Mesh Screw",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
}

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty, BoolProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from math import pi, sin, cos, copysign


def add_screw(self, context):

    num_turns = self.num_turns
    hel_rad = self.helix_radius
    hel_segs = self.helix_segments
    stretch = self.stretch
    end_taper = self.end_taper
    taper_turns = self.taper_turns
    win_rad = self.winding_radius
    win_segs = self.winding_segments
    height = self.winding_height
    power = 2 / self.winding_profile
    ngon_caps = self.ngon_caps
    tri_caps = self.tri_caps
    inner_faces = self.inner_faces
    smooth_faces = self.smooth_faces
    screw = self.screw

    sink = []
    cosk = []
    # precalculate inner loop values of semi-circular profile (just for reference)
    # for k in range(win_segs + 1):
    #     ang = k * pi / win_segs
    #     sink.append(sin(ang) * win_rad * height)
    #     cosk.append(cos(ang) * win_rad)

    # precalculate inner loop values of versatile profile
    for k in range(win_segs + 1):
        ang = k * pi / win_segs
        csk = cos(ang)
        sink.append(win_rad * (sin(ang) ** power) * height)
        cosk.append(win_rad * (abs(csk) ** power) * copysign(1, csk))

    # taper option, still seeking better taper profile
    taper_turns *= hel_segs
    min_taper = (1 - end_taper) / taper_turns
    last_seg = num_turns * hel_segs

    # define vertices
    verts = []
    faces = []
    h_angle = 2 * pi / hel_segs
    win_diam = 2 * win_rad

    for i in range(num_turns + 1):
        for j in range(hel_segs):
            seg = i * hel_segs + j
            if 0 <= seg <= taper_turns:
                if seg == 0:
                    taper = end_taper
                else:
                    taper = seg * min_taper + end_taper
            elif (last_seg - taper_turns) <= seg <= last_seg:
                if seg == last_seg:
                    taper = end_taper
                else:
                    taper = (last_seg - seg) * min_taper + end_taper
            else:
                taper = 1.0

            z_stretch = stretch * seg / hel_segs * 0.5
            vx_cos = cos(h_angle * j)
            vy_sin = sin(h_angle * j)
            vz_tns = (i * win_diam) + (j * win_diam / hel_segs) + z_stretch

            for k in range(win_segs + 1):
                radius = sink[k] + hel_rad * taper
                vx = vx_cos * radius
                vy = vy_sin * radius
                vz = vz_tns - cosk[k]

                verts.append((vx, vy, vz))

            # The first k-loop of num_turns+1 defines the final vertices
            if i == num_turns:
                break

    # re-centre z
    z_offset = (vz - win_rad) / 2
    verts = [(v[0], v[1], v[2]-z_offset) for v in verts]

    # define faces
    for i in range(num_turns):

        i_turns = i * hel_segs * (win_segs + 1)

        for j in range(hel_segs):

            j_segs = (win_segs + 1) * j
            jj_segs = (win_segs + 1) * (j+1)

            for k in range(win_segs):

                fa = i_turns + j_segs + k + 1
                fb = i_turns + j_segs + k
                fc = i_turns + jj_segs + k
                fd = i_turns + jj_segs + k + 1
                if k == 0:
                    fe = fb
                    ff = fc
                faces.append([fa, fb, fc, fd])

            if inner_faces is True:
                faces.append([fe, fa, fd, ff])

    if ngon_caps is True:
        verts_len = len(verts)
        cap_start = [i for i in range(win_segs+1)]
        cap_end = [i for i in range(verts_len-1, verts_len-win_segs-2, -1)]
        faces.extend([cap_start, cap_end])

    if tri_caps is True:
        v_1st = verts[0]
        v_end = verts[-1]
        cap_vert1 = (v_1st[0], v_1st[1]-win_rad/3, v_1st[2]+win_rad)
        cap_vert2 = (v_end[0], v_end[1]+win_rad/3, v_end[2]-win_rad)
        verts.extend([cap_vert1, cap_vert2])

        verts_len = len(verts)

        # cap1
        pt = verts_len - 2
        for v in range(win_segs):
            faces.append([pt, v, v+1])
        if inner_faces is True:
            faces.append([pt, win_segs, 0])

        # cap2
        pt = verts_len - 1
        v_frst = verts_len - win_segs - 3
        v_last = verts_len - 3
        for v in range(v_frst, v_last):
            faces.append([pt, v+1, v])
        if inner_faces is True:
            faces.append([pt, v_frst, v_last])

    mesh = bpy.data.meshes.new(name="Screw")
    mesh.from_pydata(verts, [], faces)

    object_data_add(context, mesh, operator=self)

    # mode dependent
    mode = bpy.context.mode
    if mode == 'OBJECT':
        if smooth_faces is True:
            bpy.ops.object.shade_smooth()
        if screw is True:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.mode_set(mode='OBJECT')
    if mode == 'EDIT':
        if smooth_faces is True:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
            bpy.ops.object.mode_set(mode='EDIT')
        if screw is True:
            bpy.ops.mesh.remove_doubles()


class OBJECT_OT_add_screw(Operator, AddObjectHelper):
    """Create a new Screw Object"""
    bl_idname = "mesh.add_screw"
    bl_label = "Add Screw Object"
    bl_options = {'REGISTER', 'UNDO'}

    num_turns: IntProperty(
        name="Number of turns",
        description="Number of turns",
        min=1, max=2000,
        default=3)
    helix_radius: FloatProperty(
        name="Helix Radius",
        description="Helix Radius",
        min=0.001, max=100.0,
        default=1.0)
    helix_segments: IntProperty(
        name="Helix Segments",
        description="Helix Segments",
        min=3, max=100,
        default=32)
    inner_faces: BoolProperty(
        name="Inside Faces",
        description="Inside Faces",
        default=False)
    smooth_faces: BoolProperty(
        name="Smooth Faces",
        description="Smooth Faces",
        default=True)
    screw: BoolProperty(
        name="Screw",
        description="Screw",
        default=False)
    stretch: FloatProperty(
        name="Stretch",
        description="Stretch",
        min=0, max=10,
        default=0)
    end_taper: FloatProperty(
        name="End Taper",
        description="End Taper",
        min=0, max=10,
        default=1.0)
    taper_turns: FloatProperty(
        name="Taper Turns",
        description="Taper Turns",
        min=0.01, max=20.0,
        default=0.01) # avoid div by zero
    ngon_caps: BoolProperty(
        name="Ngon caps",
        description="Ngon caps",
        default=False)
    tri_caps: BoolProperty(
        name="Triangle caps",
        description="Triangle caps",
        default=False)
    winding_radius: FloatProperty(
        name="Winding Radius",
        description="Winding Radius",
        min=0.001, max=10.0,
        default=0.3)
    winding_segments: IntProperty(
        name="Winding Segments",
        description="Winding Segments",
        min=1, max=12,
        default=7)
    winding_height: FloatProperty(
        name="Winding Height",
        description="Winding Height",
        min=-5.0, max=5.0,
        default=1.0)
    winding_profile: FloatProperty(
        name="Winding Profile",
        description="Winding Profile",
        min=0.01, max=10,
        default=2)

    def execute(self, context):

        add_screw(self, context)

        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_screw.bl_idname,
        text="Screw",
        icon='PLUGIN')


# This allows you to right click on a button and link to documentation
#def add_object_manual_map():
#    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
#    url_manual_mapping = (
#        ("bpy.ops.mesh.add_screw", "scene_layout/object/types.html"),
#    )
#    return url_manual_prefix, url_manual_mapping


def register():
    bpy.utils.register_class(OBJECT_OT_add_screw)
#    bpy.utils.register_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_screw)
#    bpy.utils.unregister_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
