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
.. module:: nxtomo_loader
   :platform: Unix
   :synopsis: A class for loading standard tomography data

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""

import h5py
import logging

from savu.data.data_structures.data_add_ons import TomoRaw
from savu.plugins.base_loader import BaseLoader

from savu.plugins.utils import register_plugin


@register_plugin
class NxtomoLoader(BaseLoader):
    """
    A class to load tomography data from a Nexus file
    :param data_path: Path to the data. Default: 'entry1/tomo_entry/data/data'.
    :param dark: Optional path to the dark field data file and nxs \
        entry. Default: [None, None].
    :param flat: Optional Path to the flat field data file and path to data \
        in nxs file. Default: [None, None].
    """

    def __init__(self, name='NxtomoLoader'):
        super(NxtomoLoader, self).__init__(name)

    def setup(self):
        exp = self.exp
        data_obj = exp.create_data_object('in_data', 'tomo')

        # from nexus file determine rotation angle
        rot = 0
        detY = 1
        detX = 2
        data_obj.set_axis_labels('rotation_angle.degrees',
                                 'detector_y.pixel',
                                 'detector_x.pixel')

        data_obj.add_pattern('PROJECTION', core_dir=(detX, detY),
                             slice_dir=(rot,))
        data_obj.add_pattern('SINOGRAM', core_dir=(detX, rot),
                             slice_dir=(detY,))

        objInfo = data_obj.meta_data
        expInfo = exp.meta_data

        data_obj.backing_file = \
            h5py.File(expInfo.get_meta_data("data_file"), 'r')

        logging.debug("Opening file '%s' '%s'", 'tomo_entry',
                      data_obj.backing_file.filename)

        data_obj.data = data_obj.backing_file[self.parameters['data_path']]

        self.__set_dark_and_flat(data_obj)

        rotation_angle = \
            data_obj.backing_file['entry1/tomo_entry/data/rotation_angle']
        objInfo.set_meta_data("rotation_angle", rotation_angle
                              [(objInfo.get_meta_data("image_key")) == 0, ...])

        try:
            control = data_obj.backing_file['entry1/tomo_entry/control/data']
            objInfo.set_meta_data("control", control[...])
        except:
            logging.warn("No Control information available")

        data_obj.set_shape(data_obj.data.shape)
        self.set_data_reduction_params(data_obj)

    def __set_dark_and_flat(self, data_obj):
        if self.parameters['dark'][0] and self.parameters['flat'][0]:
            mData = data_obj.meta_data
            dfile, dentry = self.parameters['dark']
            ffile, fentry = self.parameters['flat']
            mData.set_meta_data('dark', h5py.File(dfile, 'r')[dentry][...])
            mData.set_meta_data('flat', h5py.File(dfile, 'r')[dentry][...])
        else:
            try:
                image_key = data_obj.backing_file[
                    'entry1/tomo_entry/instrument/detector/''image_key']
                TomoRaw(data_obj)
                data_obj.get_tomo_raw().set_image_key(image_key[...])
            except:
                pass
