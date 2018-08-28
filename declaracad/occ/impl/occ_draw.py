"""
Created on Sep 30, 2016

@author: jrm
"""
from atom.api import Typed, Int, List, set_default
from enaml.application import timed_call

from ..draw import (
    ProxyPoint, ProxyVertex, ProxyLine, ProxyCircle, ProxyEllipse, 
    ProxyHyperbola, ProxyParabola, ProxyEdge, ProxyWire, 
    ProxySegment, ProxyArc, ProxyPolygon, ProxyBSpline, ProxyBezier
)
from .occ_shape import OccShape, OccDependentShape, coerce_axis

from OCC.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeVertex, BRepBuilderAPI_Transform, 
    BRepBuilderAPI_MakePolygon
)
from OCC.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
from OCC.gce import gce_MakeLin
from OCC.GC import GC_MakeSegment, GC_MakeArcOfCircle
from OCC.gp import gp_Pnt, gp_Lin, gp_Circ, gp_Elips, gp_Hypr, gp_Parab
from OCC.TopoDS import TopoDS_Vertex, topods
from OCC.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Geom import Geom_BezierCurve, Geom_BSplineCurve
from OCC.TColgp import TColgp_Array1OfPnt


class OccPoint(OccShape, ProxyPoint):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___pnt.html')

    #: A reference to the toolkit shape created by the proxy.
    shape = Typed(gp_Pnt)
    
    def create_shape(self):
        d = self.declaration
        # Not sure why but we need this
        # to force a sync of position and xyz
        print(d, self, d.position, d.x, d.y, d.z)
        self.shape = gp_Pnt(*d.position)
        
    def set_position(self, position):
        self.create_shape()


class OccVertex(OccShape, ProxyVertex):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_b_rep_builder_a_p_i___make_vertex.html')

    #: A reference to the toolkit shape created by the proxy.
    shape = Typed(TopoDS_Vertex)
    
    def create_shape(self):
        d = self.declaration
        v = BRepBuilderAPI_MakeVertex(gp_Pnt(d.x, d.y, d.z))
        self.shape = v.Vertex()
        
    def set_x(self, x):
        self.create_shape()
        
    def set_y(self, y):
        self.create_shape()    
        
    def set_z(self, z):
        self.create_shape()


class OccEdge(OccShape, ProxyEdge):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_b_rep_builder_a_p_i___make_edge.html')
    shape = Typed(BRepBuilderAPI_MakeEdge)
    
    def make_edge(self, *args):
        self.shape = BRepBuilderAPI_MakeEdge(*args)


class OccLine(OccEdge, ProxyLine):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___lin.html')

    def create_shape(self):
        d = self.declaration
        if len(d.points) == 2:
            shape = gce_MakeLin(gp_Pnt(*d.points[0]),
                                gp_Pnt(*d.points[1])).Value()
        else:
            shape = gp_Lin(coerce_axis(d.axis))
        self.make_edge(shape)
        
    def set_points(self, points):
        self.create_shape()
        

class OccSegment(OccLine, ProxySegment):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_g_c___make_segment.html')

    shape = List(BRepBuilderAPI_MakeEdge)
    
    def create_shape(self):
        d = self.declaration
        points = [gp_Pnt(*p) for p in d.points]
        if len(points) < 2:
            raise ValueError("A segment requires at least two points")
        edges = []
        for i in range(1, len(points)):
            segment = GC_MakeSegment(points[i-1], points[i]).Value()
            edges.append(BRepBuilderAPI_MakeEdge(segment))
        self.shape = edges


class OccArc(OccLine, ProxyArc):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_g_c___make_arc_of_circle.html')

    def create_shape(self):
        d = self.declaration
        points = [gp_Pnt(*p) for p in d.points]
        if d.radius:
            circle = gp_Circ(coerce_axis(d.axis), d.radius)
            sense = True
            if len(points) == 2:
                arc = GC_MakeArcOfCircle(circle, points[0], points[1],
                                         sense).Value()
                self.make_edge(arc)
            elif len(points) == 1:
                arc = GC_MakeArcOfCircle(circle, d.alpha1, points[0],
                                         sense).Value()
                self.make_edge(arc)
            else:
                arc = GC_MakeArcOfCircle(circle, d.alpha1, d.alpha2,
                                         sense).Value()
                self.make_edge(arc)
        elif len(points) == 3:
            if not points[0].IsEqual(points[2], d.tolerance):
                arc = GC_MakeArcOfCircle(points[0], points[1],
                                         points[2]).Value()
                self.make_edge(arc)
        else:
            raise ValueError("Could not create an Arc with the given children "
                             "and parameters. Must be given one of:\n\t"
                             "- three points\n\t"
                             "- radius and 2 points\n\t"
                             "- radius, alpha1 and one point\n\t"
                             "- raidus, alpha1 and alpha2")
                
    def set_radius(self, r):
        self.create_shape()
    
    def set_alpha1(self, a):
        self.create_shape()
    
    def set_alpha2(self, a):
        self.create_shape()


class OccCircle(OccEdge, ProxyCircle):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___circ.html')

    def create_shape(self):
        d = self.declaration
        self.make_edge(gp_Circ(coerce_axis(d.axis), d.radius))
        
    def set_radius(self, r):
        self.create_shape()


class OccEllipse(OccEdge, ProxyEllipse):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___elips.html')
    
    def create_shape(self):
        d = self.declaration
        self.make_edge(gp_Elips(coerce_axis(d.axis), d.major_radius,
                                d.minor_radius))
        
    def set_major_radius(self, r):
        self.create_shape()
        
    def set_minor_radius(self, r):
        self.create_shape()


class OccHyperbola(OccEdge, ProxyHyperbola):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___hypr.html')

    def create_shape(self):
        d = self.declaration
        self.make_edge(gp_Hypr(coerce_axis(d.axis), d.major_radius,
                               d.minor_radius))
        
    def set_major_radius(self, r):
        self.create_shape()
        
    def set_minor_radius(self, r):
        self.create_shape()


class OccParabola(OccEdge, ProxyParabola):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'classgp___parab.html')
    
    def create_shape(self):
        d = self.declaration
        self.make_edge(gp_Parab(coerce_axis(d.axis), d.focal_length))
        
    def set_focal_length(self, l):
        self.create_shape()


class OccPolygon(OccLine, ProxyPolygon):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_b_rep_builder_a_p_i___make_polygon.html')

    shape = Typed(BRepBuilderAPI_MakePolygon)
    
    def create_shape(self):
        d = self.declaration
        shape = BRepBuilderAPI_MakePolygon()
        for p in d.points:
            shape.Add(gp_Pnt(*p))
        if d.closed:
            shape.Close()
        self.shape = shape
        
    def set_closed(self, closed):
        self.create_shape()


class OccBSpline(OccLine, ProxyBSpline):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_geom___b_spline_curve.html')

    shape = Typed(Geom_BSplineCurve)
    
    def create_shape(self):
        d = self.declaration
        if not d.points:
            raise ValueError("Must have at least two points")
        # Poles and weights
        pts = TColgp_Array1OfPnt(1, len(d.points))
        set_value = pts.SetValue
        
        # TODO: Support weights
        for i, p in enumerate(d.points):
            set_value(i+1, gp_Pnt(*p))
        
        self.shape = GeomAPI_PointsToBSpline(pts).Curve().GetObject()
        
        
class OccBezier(OccLine, ProxyBezier):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_geom___bezier_curve.html')

    shape = Typed(Geom_BezierCurve)
    
    def create_shape(self):
        d = self.declaration
        pts = TColgp_Array1OfPnt(1, len(d.points))
        set_value = pts.SetValue
        
        # TODO: Support weights
        for i, p in enumerate(d.points):
            set_value(i+1, gp_Pnt(*p))
        self.shape = Geom_BezierCurve(pts)


class OccWire(OccShape, ProxyWire):
    #: Update the class reference
    reference = set_default('https://dev.opencascade.org/doc/refman/html/'
                            'class_b_rep_builder_a_p_i___make_wire.html')

    _update_count = Int(0)
    
    #: Make wire
    shape = Typed(BRepBuilderAPI_MakeWire)
    
    def create_shape(self):
        pass
    
    def init_layout(self):
        self.update_shape({})
        for child in self.children():
            self.child_added(child)
            
    def shape_to_wire(self, shape):
        
        if hasattr(shape, 'Wire'):
            return shape.Wire()
        elif hasattr(shape, 'Edge'):
            return shape.Edge()
        elif hasattr(shape, 'Shape'):  # Transforms
            return topods.Wire(shape.Shape())
        elif hasattr(shape, 'GetHandle'): # Curves
            return BRepBuilderAPI_MakeEdge(shape.GetHandle()).Edge()
        
        raise ValueError("Cannot build Wire from shape: {}".format(shape))
        
    def update_shape(self, change):
        d = self.declaration
        shape = BRepBuilderAPI_MakeWire()
        for c in self.children():
            convert = self.shape_to_wire
            if isinstance(c.shape, (list, tuple)):
                #: Assume it's a list of drawn objects...
                for item in c.shape:
                    shape.Add(convert(item))
            else:
                shape.Add(convert(c.shape))
                    
        assert shape.IsDone(), 'Edges must be connected'
        self.shape = shape
        
    def child_added(self, child):
        super(OccWire, self).child_added(child)
        child.observe('shape', self.update_shape)
        
    def child_removed(self, child):
        super(OccEdge, self).child_removed(child)
        child.unobserve('shape', self.update_shape)
        
