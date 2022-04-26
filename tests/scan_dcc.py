import zlib
import cbor2
import logging
from os import walk
from fnmatch import fnmatch
from pathlib import Path
from argparse import ArgumentParser
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode
from base45 import b45decode
from cose.messages import Sign1Message
from datetime import datetime
from hashlib import sha256
from base64 import b64encode

def main(args):
    if args.algorithm:
        with_all_dccs( print_algorithm, error_handler=_throw )
    if not args.validity_at is None:
        validation_clock = datetime.fromisoformat(args.validity_at)
        with_all_dccs( lambda f: validity_at(validation_clock, f), error_handler=_throw )
    if args.hash:
        with_all_dccs( print_hashes, error_handler=_display )

def with_all_dccs( function, error_handler=None, exclude="" ):
    ''' Walks through the current directory and all subdirectories and calls
        "function" for every png file that does not match the exclude filter. 
        If "error_handler" is not None, it is called with the exception that 
        occurs during handling.'''
    for base, dirs, files in walk('.'):
        for file in files: 
            if file.lower().endswith('.png'):
                fqfn = str(Path(base, file)) # fully qualified file name
                try: 
                    if not fnmatch( fqfn, exclude ):
                        function( fqfn )
                except Exception as error:
                    if not error_handler is None: 
                        error_handler( fqfn, error)


def load_dcc( file ):    
    '''Load QR code from image file and return Sign1Message and Payload
       Usage: s1msg, payload = load_dcc('my_dcc.png')
    '''
    s1msg, payload, rawdata = load_dcc_with_rawdata(file)
    return s1msg, payload

def load_dcc_with_rawdata( file ):
    '''Load QR code from image file and return Sign1Message, Payload and Raw Data
       Usage: s1msg, payload, raw_data = load_dcc('my_dcc.png')
    '''
    image = Image.open(file)
    qr_code = qr_decode(image)[0]
    qr_code_data =  qr_code.data.decode()
    assert qr_code_data.startswith('HC1:'), 'Magic number "HC1:" not found'
    logging.debug('Decoding/Decompressing Base45 data')
    decompressed = zlib.decompress(b45decode(qr_code_data[4:]))
    s1msg = Sign1Message.decode(decompressed)
    payload = cbor2.loads(s1msg.payload)
    return s1msg, payload, qr_code_data

def print_only( file ):
    print(file)

def _throw( file, error ):
    'Minimalistic error handler: Simply raise the exeption again'
    print('Error reading', file)
    raise error

def _display( file, error ):
    print('Error reading', file)


def get_hashes(file):
    def hashfunc( value ):
        'First 16 bytes only, base64-encoded'
        if isinstance( value, str ):
            value = value.encode('utf-8')
        return b64encode(sha256(value).digest()[:16]).decode('utf-8')


    s1msg, payload = load_dcc(file)
    country_code = payload[1]
    inner = payload[-260][1]
    uci = inner['v' if 'v' in inner.keys() else 't' if 't' in inner.keys() else 'r'][0]['ci']
    if get_algorithm(s1msg) == 'ES256':
        signature = s1msg.signature[:len(s1msg.signature)//2]
    else:
        signature = s1msg.signature
    
    return {
        'UCI' : hashfunc(uci),
        'COUNTRYCODEUCI' : hashfunc(country_code+uci),
        'SIGNATURE' : hashfunc(signature)
    }

def print_hashes(file):
    print(f'{file}\t{get_hashes(file)}')

def validity_at( validation_clock, file ):
    s1msg, payload = load_dcc(file)
    dcc_from = datetime.fromtimestamp(payload[6])
    dcc_until = datetime.fromtimestamp(payload[4])
    validity = 'VALID' if validation_clock >= dcc_from and validation_clock <= dcc_until else 'INVALID'
        
    print( '\t'.join([file, validity, validation_clock.isoformat()]))  


def get_algorithm( s1msg ):
    '''Print the algorithm of a DCC 
       ES256 = SHA256 with ECDSA
       PS256 = RSASSA-PSS using SHA-256
    '''
    for key,value in s1msg.phdr.items(): 
        _key = key.fullname
        if _key == 'ALG':
            return value.fullname
            

def print_algorithm( file ):
    s1msg, payload = load_dcc(file)
    print( '\t'.join([file, get_algorithm(s1msg)]))  

if __name__ == '__main__':
    parser = ArgumentParser(description='Scan all DCCs for something')
    parser.add_argument('--hash', action='store_true', help='Print hashes')
    parser.add_argument('--algorithm', action='store_true', help='Print algorithm')
    parser.add_argument('--validity-at', action='store', default=None, help='Check validity at ISO date')
    args = parser.parse_args()
    main(args)

