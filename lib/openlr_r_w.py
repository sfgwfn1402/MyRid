
import math
import decimal
import base64
import binascii
import numbers
from collections import OrderedDict
import pdb

sgn = lambda x: math.copysign(1, x)


def j_round(float_num):
    """java like rounding for complying with the OpenLR java: 2.5 -> 3"""
    num = decimal.Decimal(float_num).to_integral_value(rounding=decimal.ROUND_HALF_UP)
    return int(num)


def deg_to_int(deg, resolution=24):
    val = sgn(deg) * 0.5 + float(deg * (1 << resolution)) / 360.0
    return j_round(val)


def int_to_deg(val, resolution=24):
    return ((val - sgn(val) * 0.5) * 360) / (1 << resolution)


def bytes_to_int(b, signed=True):
    """converts big endian bytes to signed/unsigned int"""
    resolution = len(b) * 8

    hex_b = binascii.hexlify(b)
    val = int(hex_b, 16)
    if signed and b[0] >> 7:
        val -= 1 << resolution
    return val


def int_to_bytes(val, size=3, signed=True):
    """positive/negative int values to big endian"""
    if not isinstance(val, numbers.Integral):
        raise ValueError("%s is not integer" % val)
    max_range = 1 << 8 * size
    if signed:
        if val >= (max_range / 2) or val < -(max_range / 2):
            raise ValueError(
                "%s bytes signed int requires %s <= number <= %s but number = %s"
                % (size, -(max_range // 2), (max_range // 2) - 1, val)
            )
    else:
        if val < 0 or val >= max_range:
            raise ValueError(
                "%s byte(s) unsigned int requires 0 <= number <= %s but number = %s"
                % (size, max_range - 1, val)
            )
    if val < 0:
        val += max_range
    arr = []
    for _ in range(size):
        val, reminder = divmod(val, 256)
        arr.append(reminder)
    return bytearray(reversed(arr))


class Points_Info():
    
    def __init__(self) -> None:
        self.properties = OrderedDict({
            "lon": 0,
            "lat": 0,
            "frc": 0,
            "fow": 0,
            "lfnp": 7,
            "bear": 0.01,
            "dnp": 0,
            "seq": 1
            })


class Get_Openlr2Info():
    """input 2 points openlr code, convert to dict.
    key_list 
    ["version", "location_type", "points":[("lon", "lat"， “frc",
    "fow", "lfnp", "bear", "first_dnp")], "poff_bs", "noff_bs",
    "poff", "noff"]
    """

    def __init__(self, res):
        self.openlr_byte = base64.b64decode(res)

        self.dct_info = OrderedDict()
        self.base_dnp = 58.6
        self.base_bear = 11.25
        self.off = 256.0
        self.micro_deg_factor = 100000.0
        self.points = (len(self.openlr_byte)-16)//7
        self.rela_lon = 0
        self.rela_lat = 0

    def _get_bit(self, i):
        return format(self.openlr_byte[i], 'b').zfill(8)

    def _get_version(self):
        ver = self._get_bit(0)
        self.dct_info["location_type"] = int(ver[1:5], 2)
        self.dct_info["version"] = int(ver[5:], 2)

    def _get_coord(self, point, local=1):
        point.properties["lon"]  = int_to_deg(bytes_to_int(self.openlr_byte[local:local+3]))
        point.properties["lat"]  = int_to_deg(bytes_to_int(self.openlr_byte[local+3:local+6]))
        self.rela_lon, self.rela_lat = point.properties["lon"], point.properties["lat"]
        return point

    def _get_frc_fow(self, point, local=7):
        ver = self._get_bit(local)
        point.properties["frc"] = int(ver[2:5], 2)
        point.properties["fow"] = int(ver[5:], 2)
        return point

    def _get_lfrc_bear(self, point, local=8):
        ver = self._get_bit(local)
        point.properties["lfnp"] = int(ver[:3], 2)
        point.properties["bear"] = (int(ver[3:], 2)+0.5)*self.base_bear
        return point

    def _get_dnp(self, point, local=9):
        ver = self._get_bit(local)
        point.properties["dnp"] = int((int(ver[0:8], 2)+0.5)*self.base_dnp)
        return point

    def _get_rela_coord(self, point, local=10):
        lon_int = bytes_to_int(self.openlr_byte[local:local+2])
        point.properties["lon"] = self.rela_lon + lon_int/self.micro_deg_factor
        self.rela_lon = point.properties["lon"]

        lat_int = bytes_to_int(self.openlr_byte[local+2:local+4])
        point.properties["lat"] = self.rela_lat + lat_int/self.micro_deg_factor
        self.rela_lat = point.properties["lat"]

        return point

    def _get_end_bear(self, point, local=15):
        ver = self._get_bit(local)
        point.properties["bear"] = (int(ver[3:], 2)+0.5)*self.base_bear
        return point

    def _get_off_bs(self, local=15):
        ver = self._get_bit(local)
        self.dct_info["poff_bs"] = int(ver[1], 2)
        self.dct_info["noff_bs"] = int(ver[2], 2)

    def _get_off(self, local=16):
        if self.dct_info["poff_bs"] == 1:
            self.dct_info["poff"] = (bytes_to_int(self.openlr_byte[local:local+1], signed=False)+0.5)/self.off
        else:
            self.dct_info["poff"] = 0

        if self.dct_info["noff_bs"] == 1:
            self.dct_info["noff"] = (bytes_to_int(self.openlr_byte[local+1:], signed=False)+0.5)/self.off
        else:
            self.dct_info["noff"] = 0

    def _get_start_point(self):
        point = Points_Info()
        point = self._get_coord(point, 1)
        point = self._get_frc_fow(point, 7)
        point = self._get_lfrc_bear(point, 8)
        point = self._get_dnp(point, 9)
        point.properties["seq"] = 1
        return point.properties

    def _get_location_point(self, seq):
        point = Points_Info()
        step = seq*7+9
        point = self._get_rela_coord(point, step+1)
        point = self._get_frc_fow(point, step+5)
        point = self._get_lfrc_bear(point, step+6)
        point = self._get_dnp(point, step+7)
        point.properties["seq"] = seq+2
        return point.properties

    def _get_end_point(self, step):
        point = Points_Info()
        point = self._get_rela_coord(point, step+1)
        point = self._get_frc_fow(point, step+5)
        point = self._get_end_bear(point, step+6)
        point.properties["seq"] = self.points+2
        return point.properties

    def get_info(self):
        self._get_version()

        lst = []
        lst.append(self._get_start_point())

        for ii in range(self.points):
            lst.append(self._get_location_point(ii))

        lst.append(self._get_end_point(self.points*7+9))
        self.dct_info["points"] = lst

        self._get_off_bs(self.points*7+15)
        self._get_off(self.points*7+16)

        return self.dct_info


class Get_Info2Openlr():
    """input dict, convert to 2 points openlr code.
    key_list 
    ["location_type", "version", "points":[("lon", "lat", frc", "fow", "lfnp",
    "bear", "dnp", "seq")], "poff_bs", "noff_bs", "poff", "noff"]
    """

    def __init__(self, dct_info):
        self.dct_info = dct_info
        self.openlr_byte = b''
        self.base_dnp = 58.6
        self.base_bear = 11.25
        self.off = 256.0
        self.micro_deg_factor = 100000.0
        self.rela_lon = 0
        self.rela_lat = 0

        lst_key = ["location_type", "version", "points", "poff_bs", "noff_bs",
        "poff", "noff"]

        for k in lst_key:
            if k not in self.dct_info.keys():
                raise ValueError("lost key {}".format(k))

    def _get_base(self):
        location_type = self.dct_info['location_type'] & 0b1111
        version = self.dct_info['version'] & 0b111
        base_int = version + (location_type << 3)
        self.openlr_byte += int_to_bytes(base_int, size=1, signed=False)

    def _get_coord(self, point):
        self.rela_lon = point["lon"]
        lon = deg_to_int(point["lon"])
        self.openlr_byte += int_to_bytes(lon, size=3)

        self.rela_lat = point["lat"]
        lat = deg_to_int(point["lat"])
        self.openlr_byte += int_to_bytes(lat, size=3)

    def _get_rela_attr(self, point):
        frc = point["frc"]
        fow = point["fow"]
        attr_frc_fow = fow + (frc << 3)
        self.openlr_byte += int_to_bytes(attr_frc_fow, size=1, signed=False)

        lfnp = point["lfnp"]
        bear = (point["bear"] - self.base_bear / 2) / self.base_bear
        bear = j_round(bear)

        attr_bear = int(bear) + (lfnp << 5)
        self.openlr_byte += int_to_bytes(attr_bear, size=1, signed=False)

        attr_dnp = point["dnp"]
        interval = j_round(float(attr_dnp) / self.base_dnp - 0.5)
        self.openlr_byte += int_to_bytes(int(interval), size=1, signed=False)

    def _get_rela_coord(self, point):
        lon_rel = j_round(self.micro_deg_factor * (point["lon"] - self.rela_lon))
        self.openlr_byte += int_to_bytes(lon_rel, size=2)
        self.rela_lon = point["lon"]

        lat_rel = j_round(self.micro_deg_factor * (point["lat"] - self.rela_lat))
        self.openlr_byte += int_to_bytes(lat_rel, size=2)
        self.rela_lat = point["lat"]

    def _get_end_attr(self, point):
        frc = point["frc"]
        fow = point["fow"]
        attr_frc_fow = fow + (frc << 3)
        self.openlr_byte += int_to_bytes(attr_frc_fow, size=1, signed=False)

    def _get_offbs_bear(self, point):
        poff_bs = 0
        if self.dct_info["poff"] > 0:
            poff_bs = 1

        noff_bs = 0
        if self.dct_info["noff"] > 0:
            noff_bs = 1

        bear = (point["bear"] - self.base_bear / 2) / self.base_bear
        bear = j_round(bear)
        attr_bear = int(bear) + (noff_bs << 5) + (poff_bs << 6)
        self.openlr_byte += int_to_bytes(attr_bear, size=1, signed=False)

    def _get_off_attr(self):
        poff = 0
        if self.dct_info["poff"] > 0:
            poff = j_round(float(self.dct_info["poff"]) * 256 - 0.5)
        self.openlr_byte += int_to_bytes(poff, size=1, signed=False)

        noff = 0
        if self.dct_info["noff"] > 0:
            noff = j_round(float(self.dct_info["noff"]) * 256 - 0.5)
        self.openlr_byte += int_to_bytes(noff, size=1, signed=False)

    def _get_start_point(self, point):
        self._get_coord(point)
        self._get_rela_attr(point)

    def _get_location_point(self, point):
        self._get_rela_coord(point)
        self._get_rela_attr(point)

    def _get_end_point(self, point):
        self._get_rela_coord(point)
        self._get_end_attr(point)

    def openlr_info(self):
        self._get_base()

        self._get_start_point(self.dct_info["points"][0])

        for point in self.dct_info["points"][1:-1]:
            self._get_location_point(point)

        self._get_end_point(self.dct_info["points"][-1])

        self._get_offbs_bear(self.dct_info["points"][-1])
        self._get_off_attr()

        openlr = base64.b64encode(self.openlr_byte)
        return str(openlr, encoding = "utf-8")
