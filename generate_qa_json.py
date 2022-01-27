#!/bin/env python3.9

import base64
import json
import os
from PIL import Image
from pyzbar.pyzbar import decode
import zlib
from base45 import b45decode
from cbor2 import loads
from cose.messages import Sign1Message


# Files starting with these prefixes will be skipped
EXCLUDED_PREFIXES = ('.', '_', '@')

# Only files with these extensions will be processed
ALLOWED_EXT = ['.PNG']


def read_file(file: str) -> str:
    """
    Reads the given file and returns the contents as a base64 string

    @param file: Path to a file
    @return: base64 string containing the file bytes
    """
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def read_qr(file: str) -> str:
    """
    Scans the barcode and returns the contents as a string

    @param file: Path to the QR file
    @return: Barcode string
    """
    barcode = decode(Image.open(file))[0]
    return barcode.data.decode("utf-8")


def read_dcc_payload(hcert):
    base45 = hcert[4:]
    compressed_bytes = b45decode(base45)
    cose_bytes = zlib.decompress(compressed_bytes)
    cose_message = Sign1Message.decode(cose_bytes)
    cbor_message = loads(cose_message.payload)
    return cbor_message[-260][1]


def relative_path_unc(root_dir: str, full_path: str) -> str:
    """
    Converts a full path to a relative path and normalizes to unix notation.

    @param root_dir: Root directory using OS-specific notation
    @param full_path: Full path to file using OS-specific notation
    @return: Path to file relative to *root_dir* using unix/posix notation
    """
    if root_dir == ".":
        return full_path.replace("\\", "/")[2:]
    else:
        return full_path[:](root_dir, "").replace("\\", "/")[1:]


def process(source_dir: str) -> str:
    """
    Creates a JSON containing all of the QRs in the repository in b64 form and as hcert string form.

    @param source_dir: Directory containing the QR codes
    @return: Results encoded as an JSON string
    """
    result = list()
    for dir_path, dir_names, filenames in os.walk(source_dir):
        dir_names[:] = [dir_name for dir_name in dir_names if not dir_name.startswith(EXCLUDED_PREFIXES)]
        for filename in filenames:
            if os.path.splitext(filename)[1].upper() in ALLOWED_EXT:
                source_file = os.path.join(dir_path, filename)
                hcert = read_qr(source_file)
                result.append({
                    "path": relative_path_unc(source_dir, source_file),
                    "data": read_file(source_file),
                    "hcert": hcert,
                    "dcc": read_dcc_payload(hcert)
                })
    return json.dumps(result)


print(process("."))
