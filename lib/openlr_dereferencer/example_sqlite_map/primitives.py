"Contains the Node and the Line class of the example format"

from itertools import chain
from typing import Iterable
from openlr import Coordinates, FRC, FOW
from shapely.geometry import LineString
from ..maps import Line as AbstractLine, Node as AbstractNode
from ...dbconn import cursor

# https://epsg.io/4326
SRID = 4326
TAB_NODE = 'data_nodes_openlr'
TAB_ROAD = 'data_lines_openlr'
SCHEMA = 'public'


class Line(AbstractLine):
    "Line object implementation for the example format"
    def __init__(self, map_reader, line_id: int):
        if not isinstance(line_id, int):
            raise ExampleMapError(f"Line id '{line_id}' has confusing type {type(line_id)}")
        self.map_reader = map_reader
        self.line_id_internal = line_id

    def __repr__(self):
        return f"Line with id={self.line_id} of length {self.length}"

    @property
    def line_id(self) -> int:
        "Returns the line id"
        return self.line_id_internal

    @property
    def start_node(self) -> "Node":
        "Returns the node from which this line comes from"
        stmt = "SELECT startnode FROM {2}.{0} WHERE line_id = {1};".format(
            TAB_ROAD, self.line_id, SCHEMA)
        (point_id,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return self.map_reader.get_node(point_id)

    @property
    def end_node(self) -> "Node":
        "Returns the node to which this line goes"
        stmt = "SELECT endnode FROM {2}.{0} WHERE line_id = {1};".format(
            TAB_ROAD, self.line_id, SCHEMA)
        (point_id,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return self.map_reader.get_node(point_id)

    @property
    def fow(self) -> FOW:
        "Returns the form of way for this line"
        stmt = "SELECT fow FROM {2}.{0} WHERE line_id = {1};".format(
            TAB_ROAD, self.line_id, SCHEMA)
        (fow,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return FOW(fow)

    @property
    def frc(self) -> FRC:
        "Returns the functional road class for this line"
        stmt = "SELECT frc FROM {2}.{0} WHERE line_id = {1};".format(
            TAB_ROAD, self.line_id, SCHEMA)
        (frc,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return FRC(frc)

    @property
    def geometry(self) -> LineString:
        "Returns the line geometry"
        points = [self.point_n(index + 1) for index in range(self.num_points())]
        return LineString(points)

    def distance_to(self, coord) -> float:
        "Returns the distance of this line to `coord` in meters"
        stmt = """SELECT Distance(Makepoint({3}, {4}), t2.geom)
        FROM {2}.{1} t1, {2}.{0} t2 WHERE t2.line_id = {5};
        """.format(TAB_ROAD, TAB_NODE, SCHEMA, coord.lon, coord.lat, self.line_id)
        (dist,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        # Details about a bug in mod_spatialite:
        # https://gis.stackexchange.com/questions/359993/spatialite-distance-returns-null-when-geometries-touch
        if dist is None:
            return 0.0
        return dist

    def num_points(self) -> int:
        "Returns how many points the path geometry contains"
        # stmt = "SELECT NumPoints(path) FROM lines WHERE lines.rowid = ?"
        stmt = """SELECT ST_NumPoints(geom) FROM {2}.{1} WHERE line_id = {0};
        """.format(self.line_id, TAB_ROAD, SCHEMA)
        (count,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return count

    def point_n(self, index) -> Coordinates:
        "Returns the `n` th point in the path geometry, starting at 0"
        stmt = """SELECT st_X(st_PointN(geom, {0})), st_Y(st_PointN(geom, {0}))
        FROM {3}.{2} WHERE line_id = {1};""".format(index, self.line_id, TAB_ROAD, SCHEMA)
        (lon, lat) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        if lon is None or lat is None:
            raise Exception(f"line {self.line_id} has no point {index}!")
        return Coordinates(lon, lat)

    def near_nodes(self, distance):
        "Yields every point within a certain distance, in meters."
        stmt = """SELECT node_id FROM {2}.{0} t1, {2}.{1} t2 WHERE line_id = {3}
        AND Distance(t1.geom, t2.geom) <= {4};""".format(TAB_NODE, TAB_ROAD, SCHEMA, self.line_id, distance)
        for (point_id,) in cursor(self.map_reader.connection, stmt, ret=True):
            yield self.map_reader.get_node(point_id)

    @property
    def length(self) -> float:
        "Length of line in meters"
        stmt = "SELECT ST_Length(geom, True) FROM {2}.{1} WHERE line_id ={0};".format(
            self.line_id, TAB_ROAD, SCHEMA)
        (result,) = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return result


class Node(AbstractNode):
    "Node class implementation for example_sqlite_map"

    def __init__(self, map_reader, node_id: int):
        if not isinstance(node_id, int):
            raise ExampleMapError(f"Node id '{id}' has confusing type {type(node_id)}")
        self.map_reader = map_reader
        self.node_id_internal = node_id

    @property
    def node_id(self):
        return self.node_id_internal

    @property
    def coordinates(self) -> Coordinates:
        stmt = "SELECT st_X(geom), st_Y(geom) FROM {2}.{0} WHERE node_id = {1};".format(
            TAB_NODE, self.node_id, SCHEMA)
        geo = cursor(self.map_reader.connection, stmt, ret=True)[0]
        return Coordinates(lon=geo[0], lat=geo[1])

    def outgoing_lines(self) -> Iterable[Line]:
        stmt = "SELECT line_id FROM {2}.{0} WHERE startnode ={1};".format(
            TAB_ROAD, self.node_id, SCHEMA)
        for (line_id,) in cursor(self.map_reader.connection, stmt, ret=True):
            yield Line(self.map_reader, line_id)

    def incoming_lines(self) -> Iterable[Line]:
        stmt = "SELECT line_id FROM {1}.{0} WHERE endnode = {2};".format(TAB_ROAD, SCHEMA, self.node_id)
        for (line_id,) in cursor(self.map_reader.connection, stmt, ret=True):
            yield Line(self.map_reader, line_id)

    def connected_lines(self) -> Iterable[Line]:
        return chain(self.incoming_lines(), self.outgoing_lines())


class ExampleMapError(Exception):
    "Some error reading the DB"
