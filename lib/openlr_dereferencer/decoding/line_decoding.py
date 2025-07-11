"Contains the decoding logic for line location"

from typing import List, Optional
from openlr import LineLocationReference, LocationReferencePoint
from ..maps import MapReader
from ..observer import DecoderObserver
from .candidate_functions import nominate_candidates, match_tail
from .line_location import build_line_location, LineLocation
from .routes import Route
from .configuration import Config


def dereference_path(
        lrps: List[LocationReferencePoint],
        reader: MapReader,
        config: Config,
        observer: Optional[DecoderObserver]
) -> List[Route]:
    "Decode the location reference path, without considering any offsets"
    first_lrp = lrps[0]
    # print('*'*20)
    first_candidates = list(nominate_candidates(first_lrp, reader, config, False))
    # print('*' * 20)
    if observer is not None:
        observer.on_candidates_found(first_lrp, first_candidates)

    linelocationpath,scores = match_tail(first_lrp, first_candidates, lrps[1:], reader, config, observer)
    # print(linelocationpath)
    return linelocationpath,scores


def decode_line(reference: LineLocationReference, reader: MapReader, config: Config,
                observer: Optional[DecoderObserver]) -> LineLocation:
    """Decodes an openLR line location reference

    Candidates are searched in a radius of `radius` meters around an LRP."""
    parts,scores = dereference_path(reference.points, reader, config, observer)
    return build_line_location(parts, reference),scores
