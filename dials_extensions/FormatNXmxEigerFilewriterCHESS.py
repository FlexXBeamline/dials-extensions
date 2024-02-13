from __future__ import annotations

import re

import numpy as np
import h5py
import nxmx
from packaging import version

from scitbx.array_family import flex

from dxtbx.nexus import _dataset_as_flex, get_detector_module_slices
import dxtbx.format.FormatNXmxEigerFilewriter # WARNING... GOING TO MONKEY PATCH dxtbx.format.FormatNXmxEigerFilewriter.get_raw_data 

DATA_FILE_RE = re.compile(r"data_\d{6}")

print('LOADED MODULE: FormatNXmxEigerFilewriterCHESS')

class FormatNXmxEigerFilewriterCHESS(dxtbx.format.FormatNXmxEigerFilewriter.FormatNXmxEigerFilewriter):
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
    

def get_raw_data_faster(
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

# WARNING, MONKEY PATCH HERE!
dxtbx.format.FormatNXmxEigerFilewriter.get_raw_data = get_raw_data_faster