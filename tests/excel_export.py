import os 
from glob import glob
from pathlib import Path
import logging
import openpyxl
from argparse import ArgumentParser

config = {
    'base_url' : 'https://github.com/eu-digital-green-certificates/dcc-quality-assurance/blob/main/',
    'column_titles' : ['Issuing Country', 'Schema Version', 'Certificate Type', 'Validation Status', 'Code URL', 'Filename'],
    'column_value_ids' : ['country', 'version', 'type', None, 'url', 'file' ],
    'sheet' : 'Codes',
}

def main(args):
    workbook = _get_or_create_xlsx(args.filename, config['sheet'])

    workbook[config['sheet']].delete_rows(2, amount=1000)

    for directory in _get_country_directories():
        for match in _matching_files(directory):
            values = [ match.get(value_id) for value_id in config['column_value_ids']]
            values = [ value if value is not None else '' for value in values ]
            workbook[config['sheet']].append(values)

    workbook.save(args.filename)

def _get_or_create_xlsx(filename, sheet_to_use='Codes'):
    try: 
        wb = openpyxl.load_workbook(filename)
    except: 
        wb = openpyxl.Workbook()
        wb.active.title = sheet_to_use
        wb.active.append(config['column_titles'])

    if not sheet_to_use in wb.sheetnames:
        wb.create_sheet(sheet_to_use)
        wb[sheet_to_use].append(config['column_titles'])

    return wb

def _matching_files(directory):
    certificate_types = ['TEST','VAC','REC']
    
    for ctype in certificate_types:
        for match in glob(str(Path(directory,'*' , f'{ctype}*.png'))):
            version = match.split(os.sep)[-2]
            yield { 'type':ctype, 
                    'country':directory, 
                    'version':version, 
                    'url' : config['base_url']+match.replace(os.sep,'/'),
                    'file' : Path(match).name }

    for ctype in certificate_types:
        for match in glob(str(Path(directory, '*' ,'specialcases' , f'{ctype}*.png'))):
            version = match.split(os.sep)[-3]
            yield { 'type':f'{ctype} SpecialCase', 
                    'country':directory, 
                    'version':version, 
                    'url' : config['base_url']+match.replace(os.sep,'/'),
                    'file' : Path(match).name }


def _get_country_directories():
    # A country directory is any directory that has a name of exactly 2 letters
    return [ dirname for dirname in glob('??') if dirname.isalpha() ]


if __name__ == '__main__':
    try: 
        import coloredlogs
        coloredlogs.install()
    except:
        pass # If we don't have colored logs, it's not important

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    parser = ArgumentParser(description='Excel export ')
    parser.add_argument('filename', default='report.xlsx', help='Output file')
    args = parser.parse_args()
    main(args)