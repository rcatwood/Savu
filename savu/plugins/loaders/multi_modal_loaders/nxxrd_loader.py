# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: tomography_loader
   :platform: Unix
   :synopsis: A class for loading tomography data using the standard loaders
   library.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""
import os.path as os
import logging
import h5py

from savu.core.utils import logmethod
from savu.plugins.loaders.base_multi_modal_loader import BaseMultiModalLoader
from savu.test import test_utils as tu
from savu.plugins.utils import register_plugin


@register_plugin
class NxxrdLoader(BaseMultiModalLoader):
    """
    A class to load tomography data from an NXxrd file

    :param calibration_path: path to the calibration file. Default: "test_data/data/LaB6_calibration_output.nxs"
    """

    def __init__(self):
        super(NxxrdLoader, self).__init__("NxxrdLoader")

    @logmethod
    def setup(self):
        data_str = '/instrument/detector/data'
        data_obj, xrd_entry = self.multi_modal_setup('NXxrd', data_str)
        mono_energy = data_obj.backing_file[
            xrd_entry.name + '/instrument/monochromator/energy']
        self.exp.meta_data.set_meta_data("mono_energy", mono_energy)
        self.set_motors(data_obj, xrd_entry, 'xrd')
        # hard coded for now, but we can change it to fram nx transformations
        # in future.
        data_obj.set_axis_labels('rotation_angle.degrees',
                                 'x.mm',
                                 'y.mm',
                                 'detector_x.mm',
                                 'detector_y.mm')

        rotation_angle = \
            data_obj.backing_file[xrd_entry.name + '/sample/theta']
        data_obj.meta_data.set_meta_data('rotation_angle', rotation_angle[...])
        #self.add_patterns_based_on_acquisition(data_obj, 'xrd')

        slicedir = tuple(range(len(data_obj.data.shape)-2))
        data_obj.add_pattern("DIFFRACTION", core_dir=(-2, -1),
                             slice_dir=slicedir)
        data_obj.add_pattern("SINOGRAM", core_dir=(0, 2),
                             slice_dir=(1, 3, 4))
        data_obj.add_pattern("PROJECTION", core_dir=(1, 2),
                             slice_dir=(0, 3, 4))

        calibration_path = self.parameters['calibration_path']
        if calibration_path.split('/')[0] == 'test_data':
            calibration_path = \
                os.realpath('.').split('savu')[0] + calibration_path

        calibrationfile = h5py.File(calibration_path, 'r')

        mData = data_obj.meta_data
        det_str = 'entry/instrument/detector'
        mData.set_meta_data("beam_center_x",
                            calibrationfile[det_str + '/beam_center_x'])
        mData.set_meta_data("beam_center_y",
                            calibrationfile[det_str + '/beam_center_y'])
        mData.set_meta_data("distance",
                            calibrationfile[det_str + '/distance'])
        mData.set_meta_data("incident_wavelength",
                            calibrationfile['/entry/calibration_sample/beam'
                                            '/incident_wavelength'])
        mData.set_meta_data("x_pixel_size",
                            calibrationfile[det_str + '/x_pixel_size'])
        mData.set_meta_data("detector_orientation",
                            calibrationfile[det_str + '/detector_orientation'])
