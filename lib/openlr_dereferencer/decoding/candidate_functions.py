"Contains functions for candidate searching and map matching"

from itertools import product
# from logging import debug
from ....src.QgsOpenlrLog import log
from typing import Optional, Iterable, List, Tuple
from openlr import FRC, LocationReferencePoint
from ..maps import shortest_path, MapReader, Line
from ..maps.a_star import LRPathNotFoundError
from ..observer import DecoderObserver
from .candidate import Candidate
from .scoring import score_lrp_candidate, angle_difference
from .error import LRDecodeError
from .path_math import coords, project, compute_bearing
from .routes import Route
from .configuration import Config


def make_candidates(
        lrp: LocationReferencePoint,
        line: Line,
        config: Config,
        is_last_lrp: bool
) -> Iterable[Candidate]:
    "Yields zero or more LRP candidates based on the given line"
    point_on_line = project(line, coords(lrp))
    # debug(f"{point_on_line}")
    reloff = point_on_line.relative_offset

    # Snap to the relevant end of the line
    # debug(f"not {is_last_lrp} and {point_on_line.distance_from_start()} and {point_on_line.distance_to_end()} <= {config.candidate_threshold}")
    if not is_last_lrp and point_on_line.distance_from_start() <= config.candidate_threshold:
        reloff = 0.0
    if is_last_lrp and point_on_line.distance_to_end() <= config.candidate_threshold:
        reloff = 1.0
    # Drop candidate if there is no partial line left
    # debug(f"{is_last_lrp}---{reloff}----not {is_last_lrp}----{reloff}")
    if is_last_lrp and reloff <= 0.0 or not is_last_lrp and reloff >= 1.0:
        return
    if is_last_lrp:
        reloff = 1
    else:
        reloff =0
    candidate = Candidate(line, reloff)
    # debug(f"test--{reloff}---{candidate}")
    bearing = compute_bearing(lrp, candidate, is_last_lrp, config.bear_dist)
    bear_diff = angle_difference(bearing, lrp.bear)
    if abs(bear_diff) > config.max_bear_deviation:
        #log.debug(f"Not considering {candidate} because the bearing difference is {bear_diff} °. bear: {bearing}. lrp bear: {lrp.bear}")
        # debug(f"bear: {bearing}. lrp bear: {lrp.bear}")
        return
    # print(candidate)
    candidate.score = score_lrp_candidate(lrp, candidate, config, is_last_lrp)
    # print(candidate.score)
    # print('candidate',str(dir(candidate)))
    if candidate.score >= config.min_score:
        yield candidate


def nominate_candidates(
        lrp: LocationReferencePoint, reader: MapReader, config: Config, is_last_lrp: bool
) -> Iterable[Candidate]:
    "Yields candidate lines for the LRP along with their score."
    #if is_last_lrp:
        #log.debug("last point, {}".format('-' * 40))
    #else:
        #log.debug("start point, {}".format('-' * 40))
    #log.debug(f"Finding candidates for LRP {lrp} at {coords(lrp)} in radius {config.search_radius}")
    for line in reader.find_lines_close_to(coords(lrp), config.search_radius):
        yield from make_candidates(lrp, line, config, is_last_lrp)


def get_candidate_route(start: Candidate, dest: Candidate, lfrc: FRC, maxlen: float) -> Optional[Route]:
    """Returns the shortest path between two LRP candidates, excluding partial lines.

    If it is longer than `maxlen`, it is treated as if no path exists.

    Args:
        map_reader:
            A reader for the map on which the path is searched
        start:
            The starting point.
        dest:
            The ending point.
        lfrc:
            "lowest frc". Line objects from map_reader with an FRC lower than lfrc will be ignored.
        maxlen:
            Pathfinding will be canceled after exceeding a length of maxlen.

    Returns:
        If a matching shortest path is found, it is returned as a list of Line objects.
        The returned path excludes the lines the candidate points are on.
        If there is no matching path found, None is returned.
    """
    #log.debug("route, {}".format('-' * 40))
    #log.debug(f"Try to find path between {start, dest}")
    if start.line.line_id == dest.line.line_id:
        return Route(start, [], dest)
    #log.debug(f"Finding path between nodes {start.line.end_node.node_id, dest.line.start_node.node_id}")
    linefilter = lambda line: line.frc <= lfrc
    try:
        path = shortest_path(start.line.end_node, dest.line.start_node, linefilter, maxlen=maxlen)
        #log.debug(f"Returning {path}")
        return Route(start, path, dest)
    except LRPathNotFoundError:
        #log.debug(f"No path found between these nodes")
        return None


def match_tail(
        current: LocationReferencePoint,
        candidates: List[Candidate],
        tail: List[LocationReferencePoint],
        reader: MapReader,
        config: Config,
        observer: Optional[DecoderObserver]
) -> List[Route]:
    """Searches for the rest of the line location.

    Every element of `candidates` is routed to every candidate for `tail[0]` (best scores first).
    Actually not _every_ element, just as many as it needs until some path matches the DNP.

    Args:
        current:
            The LRP with which this part of the line location reference starts.
        candidates:
            The Candidates for the current LRP
        tail:
            The LRPs following the current.

            Contains at least one LRP, as any route has two ends.
        reader:
            The map reader on which we are operating. Needed for nominating next candidates.
        config:
            The wanted behaviour, as configuration options
        observer:
            The optional decoder observer, which emits events and calls back.

    Returns:
        If any candidate pair matches, the function calls itself for the rest of `tail` and
        returns the resulting list of routes.

    Raises:
        LRDecodeError:
            If no candidate pair matches or a recursive call can not resolve a route.
    """
    last_lrp = len(tail) == 1
    # The accepted distance to next point. This helps to save computations and filter bad paths
    minlen = (1 - config.max_dnp_deviation) * current.dnp - config.tolerated_dnp_dev
    maxlen = (1 + config.max_dnp_deviation) * current.dnp + config.tolerated_dnp_dev
    lfrc = config.tolerated_lfrc[current.lfrcnp]

    # Generate all pairs of candidates for the first two lrps
    next_lrp = tail[0]
    # print('end'+'-'*20)
    next_candidates = nominate_candidates(next_lrp, reader, config, last_lrp)
    # print([candidate.score for candidate in next_candidates])
    next_candidates = list(next_candidates)
    # print('next',next_candidates)
    if observer is not None:
        observer.on_candidates_found(next_lrp, next_candidates)

    pairs = list(product(candidates, next_candidates))
    # print('pairs',pairs)
    # Sort by line scores
    scores = [(pair[0].line.line_id,pair[0].score,pair[-1].line.line_id,pair[-1].score) for pair in pairs]
    pairs.sort(key=lambda pair: (pair[0].score + pair[1].score), reverse=True)
    # print('pairs.score', scores)
    # For every pair of candidates, search for a path matching our requirements
    for (c_from, c_to) in pairs:
        # print('ss',(c_from, c_to))
        route = handleCandidatePair((current, next_lrp), (c_from, c_to), observer, lfrc, minlen, maxlen)

        if route is None:
            continue
        if last_lrp:
            # print('route',[route])
            return [route],scores
        try:
            # print('-'*20)
            # print('s1',[route])
            # print('s2',match_tail(next_lrp, [c_to], tail[1:], reader, config, observer))
            # print('-' * 20)

            new_route = match_tail(next_lrp, [c_to], tail[1:], reader, config, observer)

            if isinstance(new_route,tuple):
                _route = new_route[0]
                _scores = new_route[1]
                if len(_route)>0:
                    return [route]+_route,scores+_scores
                else:
                    return [route],scores

        except LRDecodeError:
            #log.debug("Recursive call to resolve remaining path had no success")
            continue

    if observer is not None:
        observer.on_matching_fail(current, next_lrp, candidates, next_candidates)
        # print('========================================')
        # print(observer.on_matching_fail(current, next_lrp, candidates, next_candidates))
    # raise LRDecodeError("Decoding was unsuccessful: No candidates left or available.")
    print(LRDecodeError("Decoding was unsuccessful: No candidates left or available."))
    return None,None

def handleCandidatePair(
        lrps: Tuple[LocationReferencePoint, LocationReferencePoint],
        candidates: Tuple[Candidate, Candidate],
        observer: Optional[DecoderObserver],
        lowest_frc: FRC,
        minlen: float,
        maxlen: float,
    ) -> Optional[Route]:
    """
    Try to find an adequate route between two LRP candidates.

    Args:
        lrps:
            The two LRPs
        candidates:
            The two candidates
        observer:
            An optional decoder observer
        lowest_frc:
            The lowest acceptable FRC for a line to be considered part of the route
        minlen:
            The lowest acceptable route length in meters
        maxlen:
            The highest acceptable route length in meters

    Returns:
        If a route can not be found or has no acceptable length, None is returned.
        Else, this function returns the found route.
    """
    current, next_lrp = lrps
    source, dest = candidates
    route = get_candidate_route(source, dest, lowest_frc, maxlen)

    if not route:
        #log.debug("No path for candidate found")
        if observer is not None:
            observer.on_route_fail(current, next_lrp, source, dest)
        return None

    length = route.length()

    if observer is not None:
        observer.on_route_success(current, next_lrp, source, dest, route)

    #log.debug(f"DNP should be {current.dnp} m, is {length} m.")
    # If the path does not match DNP, continue with the next candidate pair
    if length < minlen or length > maxlen:
        #log.debug("Shortest path deviation from DNP is too large")
        return None

    #log.debug(f"Taking route {route}.")
    print("Taking route...."+str(route))
    return route
