# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 10, 2015

@author: jrm
"""
import logging
from declaracad.core.api import Plugin


class ConsolePlugin(Plugin):
    def start(self):
        """ Set the log level for IPython stuff to warn """
        for name in ['ipykernel.inprocess.ipkernel', 'traitlets',
                     'parso.python.diff', 'parso.cache']:
            log = logging.getLogger(name)
            log.setLevel(logging.WARNING)
