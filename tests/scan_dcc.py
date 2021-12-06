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

def main(args):
    if args.algorithm:
        with_all_dccs( print_algorithm, error_handler=_throw, exclude='venv*' )

        
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
                        function(fqfn )
                except Exception as error:
                    if not error_handler is None: 
                        error_handler( fqfn, error)



def load_dcc( file ):
    '''Load QR code from image file and return Sign1Message and Payload
       Usage: s1msg, payload = load_dcc('my_dcc.png')
    '''
    image = Image.open(file)
    qr_code = qr_decode(image)[0]
    qr_code_data =  qr_code.data.decode()
    assert qr_code_data.startswith('HC1:'), 'Magic number "HC1:" not found'
    logging.debug('Decoding/Decompressing Base45 data')
    decompressed = zlib.decompress(b45decode(qr_code_data[4:]))
    s1msg = Sign1Message.decode(decompressed)
    #    print(cbor2.loads(decompressed))
    #    print(f'Unprotected Header: {cose_data.uhdr}')
    #    print(f'Protected Header: {cose_data.phdr}')
    #    print(f'KID = {get_kid_b64(cose_data)}')
    payload = cbor2.loads(s1msg.payload)
    return s1msg, payload

def print_only( file ):
    print(file)

def _throw( file, error ):
    'Minimalistic error handler: Simply raise the exeption again'
    print('Error reading', file)
    raise error

def print_algorithm( file ):
    '''Print the algorithm of a DCC 
       ES256 = SHA256 with ECDSA
       PS256 = RSASSA-PSS using SHA-256
    '''
    s1msg, payload = load_dcc(file)
    for key,value in s1msg.phdr.items(): 
        _key = key.fullname
        if _key == 'ALG':
            _value = value.fullname
            print( '\t'.join([file, _value]))  



if __name__ == '__main__':
    parser = ArgumentParser(description='Scan all DCCs for something')
    parser.add_argument('--algorithm', action='store_true', help='Print algorithm')
    args = parser.parse_args()
    main(args)

