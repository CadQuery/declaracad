"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import logging
import traceback
from enaml.image import Image
from enaml.icon import Icon, IconImage
from enaml.application import timed_call
from twisted.protocols.basic import LineReceiver

try:
    import ujson as json
except ImportError:
    import json

# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
log = logging.getLogger("declaracad")


def clip(s, n=1000):
    """ Shorten the name of a large value when logging"""
    v = str(s)
    if len(v) > n:
        v[:n]+"..."
    return v

# -----------------------------------------------------------------------------
# Icon and Image helpers
# -----------------------------------------------------------------------------
#: Cache for icons
_IMAGE_CACHE = {}


def icon_path(name):
    """ Load an icon from the res/icons folder using the name 
    without the .png
    
    """
    path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(path, 'res', 'icons', '%s.png' % name)


def load_image(name):
    """ Get and cache an enaml Image for the given icon name.
    
    """
    path = icon_path(name)
    global _IMAGE_CACHE
    if path not in _IMAGE_CACHE:
        with open(path, 'rb') as f:
            data = f.read()
        _IMAGE_CACHE[path] = Image(data=data)
    return _IMAGE_CACHE[path]


def load_icon(name):
    img = load_image(name)
    icg = IconImage(image=img)
    return Icon(images=[icg])


def menu_icon(name):
    """ Icons don't look good on Linux/osx menu's """
    if sys.platform == 'win32':
        return load_icon(name)
    return None


class JSONRRCProtocol(LineReceiver):
    def send_message(self, message):
        response = {'jsonrpc': '2.0'}
        response.update(message)
        self.transport.write(json.dumps(response).encode()+b'\r\n')
        
    def lineReceived(self, line):
        """ Process stdin as json-rpc request """
        response = {}
        try:
            request = json.loads(line)
        except Exception as e:
            self.send_message({"id": None,
                               'error': {'code': -32700,
                                         'message': 'Parse error'}})
            return
        
        request_id = request.get('id')
        method = request.get('method')
        if method is None:
            self.send_message({"id": request_id,
                               'error': {'code': -32600,
                                         'message': "Invalid request"}})
            return
        
        handler = getattr(self, 'handle_{}'.format(method), None)
        if handler is None:
            self.send_message({"id": request_id,
                               'error': {'code': -32601,
                                         'message': "Method not found"}})
            return
        
        try:
            params = request.get('params', [])
            if isinstance(params, dict):
                result = handler(**params)
            else:
                result = handler(*params)
        except Exception as e:
            self.send_message({"id": request_id,
                               'error': {'code': -32601,
                                         'message': traceback.format_exc()}})
        
        if request_id is not None:
            self.send_message({'id': request_id, 'result': result})
