# ---license-start
# eu-digital-green-certificates / dgc-testdata
# ---
# Copyright (C) 2021 T-Systems International GmbH and all other contributors
# ---
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ---license-end

import os 
import re
import cbor2
import base64

from zlib import decompress
from base45 import b45decode
from cose.messages import Sign1Message
from cose.headers import Algorithm, KID
from datetime import date, datetime, timezone
from PIL.Image import NONE, open as image_open
from pyzbar.pyzbar import decode as qrcode_decode


# Constants
TIMESTAMP_ISO8601_EXTENDED = "%Y-%m-%dT%H:%M:%S.%fZ"

class DccQrCode():
    "Represents a DCC QR code based on a file"

    def __init__(self, path):
        def datetime_to_string(decoder, value):
            'replace datetime objects with a string representation when loading the CBOR'
            return {k: v.astimezone(timezone.utc).strftime(TIMESTAMP_ISO8601_EXTENDED) \
                    if isinstance(v, (date, datetime)) else v for k, v in value.items()}

        self.file_path = path
        image = image_open( path )
        self.qr_code_data = qrcode_decode(image)[0].data.decode()
        if not self.qr_code_data.startswith('HC1:'):
            raise ValueError('Encoded data does not begin with magic number "HC1:"')
        self.decompressed = decompress(b45decode(self.qr_code_data[4:]))
        try:
            self.sign1Message = Sign1Message.decode(self.decompressed)
        except AttributeError: 
            self.sign1Message = Sign1Message.decode(b'\xD2'+self.decompressed)
            print('Warning: Untagged COSE message.')
        self.payload = cbor2.loads(self.sign1Message.payload, object_hook=datetime_to_string)
        self._path_country = None
    
    def get_key_id_base64(self):     
        "returns the key ID of the COSE message"   
        if KID in self.sign1Message.phdr:
            kid = self.sign1Message.phdr[KID]
        else:
            kid = self.sign1Message.uhdr[KID]

        return base64.b64encode(kid).decode("ascii")        

    def get_path_schema_version(self): 
        """Returns the schema version that is encoded in the path (exactly 3 digits separated by dots)
           or None if no match is found."""
        _previous = None
        for subdir_name in self.file_path.split(os.sep):
            if re.match("^\\d\\.\\d\\.\\d$", subdir_name):
                self._path_country = _previous
                return subdir_name
            _previous = subdir_name
        return None # --> No path schema version

    def get_path_country(self): 
        """Returns the country code that is encoded in the path right before the schema version"""
        if self._path_country is None: 
            self.get_path_schema_version()
        return self._path_country

    def get_file_name(self):
        return self.file_path.split(os.sep)[-1]