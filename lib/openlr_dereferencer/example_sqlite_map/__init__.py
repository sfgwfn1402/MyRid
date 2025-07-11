"""The example map format described in `map_format.md`, conforming to
the interface in openlr_dereferencer.maps"""

import os
# import sqlite3
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool
from typing import Sequence, Tuple, Iterable
from openlr import Coordinates
from .primitives import Line, Node, ExampleMapError, SRID
from ..maps import MapReader, wgs84
from ...dbconn import db_conn, cursor

TAB_NODE = 'data_nodes_openlr'  # guf
TAB_ROAD = 'data_lines_openlr'  # guf

class ExampleMapReader(MapReader):
    """
    This is a reader for the example map format described in `map_format.md`.
    Create an instance with: `ExampleMapReader('example.sqlite')`.
    """
    def __init__(self, map_db_file: str, schema: str):
        dct_dbinfo = map_db_file
        user = dct_dbinfo['user']
        pw = dct_dbinfo['pw']
        host = dct_dbinfo['host']
        port = dct_dbinfo['port']
        db = dct_dbinfo['db']
        self.schema = schema
        self.connection = db_conn(host, port, user, pw, db)

        # engine = create_engine(
        #     'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(
        #         user, pw, host, port, db),
        #     echo=False,
        #     # pool_recycle=3600,
        #     client_encoding='utf8',
        #     poolclass=NullPool)
        #
        # DB_Session = sessionmaker(bind=engine)
        # self.connection = DB_Session()

    def get_line(self, line_id: int) -> Line:
        return Line(self, line_id)

    def get_lines(self) -> Iterable[Line]:
        stmt = "SELECT line_id FROM {1}.{0};".format(TAB_ROAD, self.schema)
        for (line_id,) in cursor(self.connection, stmt, ret=True):
            yield Line(self, line_id)

    def get_linecount(self) -> int:
        stmt = "SELECT COUNT(1) FROM {1}.{0};".format(TAB_ROAD, self.schema)
        (count,) = cursor(self.connection, stmt, ret=True)[0]
        return count

    def get_node(self, node_id: int) -> Node:
        return Node(self, node_id)

    def get_nodes(self) -> Iterable[Node]:
        stmt = "SELECT node_id FROM {1}.{0};".format(TAB_NODE, self.schema)
        for (node_id,) in cursor(self.connection, stmt, ret=True):
            yield Node(self, node_id)

    def get_nodecount(self) -> int:
        stmt = "SELECT COUNT(1) FROM {1}.{0};".format(TAB_NODE, self.schema)
        (count,) = cursor(self.connection, stmt, ret=True)[0]
        return count

    def find_nodes_close_to(self, coord: Coordinates, dist: float) -> Iterable[Node]:
        """Finds all nodes in a given radius, given in meters
        Yields every node within this distance to `coord`."""
        lon, lat = coord.lon, coord.lat
        stmt = """SELECT nodes_id FROM {1}.{0} WHERE Distance(MakePoint({2}, {3}),coord,1)< {3};
        """.format(TAB_NODE, self.schema, lon, lat, dist)
        for (node_id,) in cursor(self.connection, stmt, ret=True):
            yield Node(self, node_id)

    def find_lines_close_to(self, coord: Coordinates, dist: float) -> Iterable[Line]:
        "Yields all lines within `dist` meters around `coord`"
        lon, lat = coord.lon, coord.lat
        stmt = """SELECT line_id FROM {5}.{4} WHERE st_dwithin(ST_SetSRID(ST_Point(
        {0}, {1}), {2}), geom, {3}, True);""".format(lon, lat, SRID, dist,
                                                     TAB_ROAD, self.schema)

        for (line_id,) in cursor(self.connection, stmt, ret=True):
            yield Line(self, line_id)
