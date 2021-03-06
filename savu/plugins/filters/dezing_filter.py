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
# $Id: dezing_filter.py 467 2016-02-16 11:40:42Z kny48981 $


"""
.. module:: dezing_filter
   :platform: Unix
   :synopsis: A plugin to remove dezingers

.. moduleauthor:: Mark Basham <scientificsoftware@diamond.ac.uk>

"""
import logging
import numpy as np
import dezing

from savu.plugins.base_filter import BaseFilter
from savu.plugins.driver.cpu_plugin import CpuPlugin
from savu.plugins.utils import register_plugin


@register_plugin
class DezingFilter(BaseFilter, CpuPlugin):
    """
    A plugin for cleaning x-ray strikes based on statistical evaluation of \
    the near neighbourhood
    :param outlier_mu: Threshold for detecting outliers, greater is less \
    sensitive. Default: 10.0.
    :param kernel_size: Number of frames included in average. Default: 5.
    """

    def __init__(self):
        super(DezingFilter, self).__init__("DezingFilter")
        self.warnflag = 0
        self.errflag = 0

    def pre_process(self):
        (retval, self.warnflag, self.errflag) = \
            dezing.setup_size(self.data_size, self.parameters['outlier_mu'],
                              self.pad)

    def filter_frames(self, data):
        result = np.empty_like(data[0])
        logging.debug("Python: calling cython funciton dezing.run")
        (retval, self.warnflag, self.errflag) = dezing.run(data[0], result)
        return result

    def post_process(self):
        (retval, self.warnflag, self.errflag) = dezing.cleanup()

    def get_max_frames(self):
        """
        :returns:  an integer of the number of frames. Default 100
        """
        return 100

    def set_filter_padding(self, in_data, out_data):
        in_data = in_data[0]
        self.pad = (self.parameters['kernel_size'] - 1) / 2
        self.data_size = in_data.get_shape()
        in_data.padding = {'pad_multi_frames': self.pad}
        out_data[0].padding = {'pad_multi_frames': self.pad}

    def executive_summary(self):
        if self.errflag != 0:
            return(["ERRORS detected in dezing plugin, Check the detailed \
log messages."])
        if self.warnflag != 0:
            return(["WARNINGS detected in dezing plugin, Check the detailed \
log messages."])
        return "Nothing to Report"

# other examples
#        data.padding = {'pad_multi_frames':pad, 'pad_frame_edges':pad}
#        data.padding = {'pad_direction':[ddir, pad]}}
