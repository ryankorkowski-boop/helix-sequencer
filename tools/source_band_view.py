"""Helix solid-mesh view including dimensional, source-bound V3 drummer."""
import numpy as np
from PIL import Image

from tools.render_band_upgrade import GLView
from tools.render_intricate_band_samplers import SAMPLER_VERTEX,SAMPLER_FRAGMENT
from models.expressive_band_face import lip_ring_mesh


class SourceBandView(GLView):
    def __init__(self,scene,drummer,width,height,camera):
        custom=scene.custom;scene.custom=[]
        fragment=SAMPLER_FRAGMENT.replace('(0.20+energy)*(.26+.74*wave)','energy*(.26+.74*wave)')
        try:super().__init__(scene,width,height,SAMPLER_VERTEX.replace('activity[128]','activity[280]'),fragment)
        finally:scene.custom=custom
        self.camera=camera;self.drummer=drummer
        self.groups.append(self.make_vao(lip_ring_mesh(),[o for o in scene.instances if o['kind']=='lip_ring']))
        vertices=[];normals=[];colors=[];slots=[]
        for item in custom:
            mesh=item['mesh'];ids=mesh.faces.ravel();points=mesh.vertices[ids]
            vertices.append(points);normals.append(mesh.vertex_normals[ids])
            colors.append(np.tile(item['color'],(len(ids),1)))
            if item['name'].startswith(('bass','upright_bass','guitar','electric_guitar','piano','keyboard','lead','harmony')):
                channels=np.full(len(ids),item['slot'])
            else:
                # Existing stage geometry receives distinct musical duties by
                # position. Its moving light patterns require source activity.
                channels=np.where(points[:,0]<-.8,64,np.where(points[:,0]>.8,65,66))
                channels=np.where(points[:,1]>3.5,np.where(points[:,0]<0,67,68),channels)
                channels=np.where(points[:,1]<.15,np.where(points[:,0]<0,69,70),channels)
            slots.append(channels[:,None])
        for part in drummer.meshes:
            mesh=part['mesh'];ids=mesh.faces.ravel()
            vertices.append(mesh.vertices[ids]);normals.append(mesh.vertex_normals[ids])
            colors.append(mesh.visual.vertex_colors[ids,:3]/255)
            slots.append(np.full((len(ids),1),part['slot']))
        data=np.c_[np.vstack(vertices),np.vstack(normals),np.vstack(colors),np.vstack(slots)].astype('f4')
        vbo=self.ctx.buffer(data.tobytes())
        identity=self.ctx.buffer(np.r_[np.eye(4).T.ravel(),(1,1,1),-1].astype('f4').tobytes())
        self.source_vao=self.ctx.vertex_array(self.program,[
            (vbo,'3f 3f 3f 1f','in_position','in_normal','in_color','in_slot'),
            (identity,'4f 4f 4f 4f 3f 1f /i','m0','m1','m2','m3','instance_color','instance_slot')])

    def frame(self,levels,time=0):
        self.drummer.pose(time)
        vp,eye=self.camera(self.width,self.height,time)
        self.program['view_projection'].write(vp.T.astype('f4').tobytes())
        self.program['eye'].value=tuple(eye)
        self.program['song_time'].value=time
        self.fbo.use();self.draw(levels);self.source_vao.render()
        return Image.frombytes('RGB',(self.width,self.height),self.fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
