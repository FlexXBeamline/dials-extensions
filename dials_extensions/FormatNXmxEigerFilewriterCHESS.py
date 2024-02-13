from __future__ import annotations

import re

import numpy as np
import h5py
import nxmx
from packaging import version

from scitbx.array_family import flex

from dxtbx.nexus import _dataset_as_flex, get_detector_module_slices
from dxtbx.format.FormatNXmxEigerFilewriter import FormatNXmxEigerFilewriter 
DATA_FILE_RE = re.compile(r"data_\d{6}")

print('LOADED CUSTOM DETECTOR FORMAT: FormatNXmxEigerFilewriterCHESS')

class FormatNXmxEigerFilewriterCHESS(FormatNXmxEigerFilewriter):
    _cached_file_handle = None

    @staticmethod
    def understand(image_file):
        with h5py.File(image_file) as handle:
            if "/entry/instrument/detector/detector_number" in handle:
                if (
                    handle["/entry/instrument/detector/detector_number"][()]
                    == b'E-32-0123'
                ):
                    return True
        return False

    def _get_nxmx(self, fh: h5py.File):
        nxmx_obj = nxmx.NXmx(fh)
        nxentry = nxmx_obj.entries[0]

        nxdetector = nxentry.instruments[0].detectors[0]
        if nxdetector.underload_value is None:
            nxdetector.underload_value = 0

        # older firmware versions had the detector dimensions inverted
        fw_version_string = (
            fh["/entry/instrument/detector/detectorSpecific/eiger_fw_version"][()]
            .decode()
            .replace("release-", "")
        )
        
        #print(f'detected Eiger firmware version: {fw_version_string}')
        if version.parse(fw_version_string) < version.parse("2022.1.2"):
            #print('swapping module size')
            for module in nxdetector.modules:
                module.data_size = module.data_size[::-1]
        return nxmx_obj
    
    def _goniometer(self):
        return self._goniometer_factory.known_axis((-1, 0, 0))
    
    # COPIED FROM PARENT CLASS
    def get_raw_data(self, index):
        nxmx_obj = self._get_nxmx(self._cached_file_handle)
        nxdata = nxmx_obj.entries[0].data[0]
        nxdetector = nxmx_obj.entries[0].instruments[0].detectors[0]

        # Prefer bit_depth_image over bit_depth_readout since the former
        # actually corresponds to the bit depth of the images as stored on
        # disk. See also:
        #   https://www.dectris.com/support/downloads/header-docs/nexus/
        bit_depth = self._bit_depth_image or self._bit_depth_readout
        raw_data = get_raw_data(nxdata, nxdetector, index, bit_depth)

        if bit_depth:
            # if 32 bit then it is a signed int, I think if 8, 16 then it is
            # unsigned with the highest two values assigned as masking values
            if bit_depth == 32:
                top = 2**31
            else:
                top = 2**bit_depth
            for data in raw_data:
                d1d = data.as_1d()
                d1d.set_selected(d1d == top - 1, -1)
                d1d.set_selected(d1d == top - 2, -2)
        return raw_data
    

def get_raw_data(
    nxdata: nxmx.NXdata,
    nxdetector: nxmx.NXdetector,
    index: int,
    bit_depth: int | None = None,
) -> tuple[flex.float | flex.double | flex.int, ...]:
    
    nimages = nxdetector._handle['detectorSpecific']['nimages'][()]
    ntrigger = nxdetector._handle['detectorSpecific']['ntrigger'][()]
    data_keys = [k for k in sorted(nxdata.keys()) if DATA_FILE_RE.match(k)]
    
    nimages_per_file = nxdata.get(data_keys[0]).shape[0]
    nfiles = len(data_keys)
    
    ind_array, ind_data = np.unravel_index(index, [nimages_per_file, nfiles], order='C')
    data = nxdata[data_keys[ind_data]]
    
    all_data = []
    sliced_outer = data[ind_array]
    
    # the following is the same as in parent class (necessary?)
    for module_slices in get_detector_module_slices(nxdetector):
        data_as_flex = _dataset_as_flex(
            sliced_outer, tuple(module_slices), bit_depth=bit_depth
        )
        all_data.append(data_as_flex)
    return tuple(all_data)
