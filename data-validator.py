"""
Validate JSON file as described in Syniti software engineer questions.
See https://github.com/Syniti/software-engineer-questions
Validation implemented in the class DataValidator.
"""

import json
import unittest

class NoIDError(KeyError):
    """Raise if malformed record does not have an ID."""

class DataValidator():
    """
    Validate a JSON file containing a name, address, and ZIP code.
    """
    def __init__(self):
        """
        self.bad_records: set of ids of invalid records
        self.records_seen: dictionary of processed records (key/hash: string of data except id, value: record id)
        """
        self.bad_records = set()
        self.records_seen = {}

    def remove_id(self, record):
        """
        Return a record with all fields except the ID.
        """
        d = {}
        for k in record.keys():
            if k != "id":
                d[k] = record[k]
        return d

    def have_seen(self, record):
        """
        Determines if a duplicate record has already been processed.
        Comparison made on the basis of all keys except 'id'. If record is
        unique, add it to self.record_seen.
        """
        record_string = str( self.remove_id(record) )
        if record_string in self.records_seen:
            return True

        self.records_seen[record_string] = record['id']
        return False

    def is_null_missing_blank(self, record, key):
        """
        Determines if a key in a record is missing, is None, or is blank.
        """
        if key not in record.keys():
            return True
        if record[key] is None:
            return True
        if len(record[key]) == 0:
            return True

        return False

    def valid_zip_code(self, zip_code):
        """
        Determines if a ZIP code is valid.
        Accepted formats: 00000, 00000-0000, 000000000 (no hyphen)
        (note that ZIP is expected as a string in the source data)
        """
        if zip_code.isnumeric() and ( len(zip_code) == 5 or len(zip_code) == 9):
            return True
        if '-' in zip_code:
            a = zip_code.split('-')
            if len(a) == 2:
                if a[0].isnumeric() and len(a[0]) == 5 and a[1].isnumeric() and len(a[1]) == 4:
                    return True
        return False

    def add_to_bad_records(self, record):
        """
        Add a record ID to self.bad_records.
        """
        self.bad_records.add(record['id'])

    def add_duplicate_to_bad_records(self, record):
        """
        Add a previously-seen duplicate of a record to self.bad_records
        """
        record_string = str( self.remove_id(record) )
        if record_string in self.records_seen:
            self.bad_records.add( self.records_seen[record_string] )

    def record_is_valid(self, record):
        """
        Determine if a single record is valid.
        Each record is a dictionary of key-value pairs.
        """
        if 'id' not in record.keys():
            raise NoIDError
        if self.is_null_missing_blank(record, 'name'):
            return False
        if self.is_null_missing_blank(record, 'address'):
            return False
        if self.is_null_missing_blank(record, 'zip'):
            return False
        if not self.valid_zip_code(record['zip']):
            return False
        return True

    def validate_file(self, file_path):
        """
        For a JSON-encoded file at file_path, determine which records are invalid.
        The ID of invalid records will be added to the self.bad_records list.
        """
        with open(file_path) as f:
            data = json.load(f)
            for d in data:
                if self.have_seen(d):
                    self.add_to_bad_records(d)
                    self.add_duplicate_to_bad_records(d)
                elif not self.record_is_valid(d): # if duplicate, doesn't matter if otherwise valid
                    self.add_to_bad_records(d)

    def print_invalid_records(self):
        """
        Print the IDs of invalid records.
        """
        for a in self.bad_records:
            print(a)

class TestValidator(unittest.TestCase):
    """
    Test the main methods of DataValidator.
    (Command-line: `python3 -m unittest data-validator.py`)
    """
    def setUp(self):
        self.validator = DataValidator()

    def test_null_missing_blank(self):
        self.assertFalse(self.validator.is_null_missing_blank({'name': 'David Schlachter'}, "name"))
        self.assertTrue(self.validator.is_null_missing_blank({'key': 'value'}, "name"))
        self.assertTrue(self.validator.is_null_missing_blank({'name': ''}, "name"))
        self.assertTrue(self.validator.is_null_missing_blank({'name': None}, "name"))

    def test_zip_code(self):
        self.assertTrue(self.validator.valid_zip_code("00000"))
        self.assertTrue(self.validator.valid_zip_code("00000-0000"))
        self.assertTrue(self.validator.valid_zip_code("000000000"))
        self.assertFalse(self.validator.valid_zip_code(""))
        self.assertFalse(self.validator.valid_zip_code("0a000"))
        self.assertFalse(self.validator.valid_zip_code("00"))
        self.assertFalse(self.validator.valid_zip_code("0000000000000000"))
        self.assertFalse(self.validator.valid_zip_code("qwertyuio"))

    def test_have_seen(self):
        self.assertFalse(self.validator.have_seen({'a':'0', 'b':'1', 'c':'2', 'id':'3'}))
        self.assertTrue(self.validator.have_seen({'a':'0', 'b':'1', 'c':'2', 'id':'3'})) # identical record
        self.assertTrue(self.validator.have_seen({'a':'0', 'b':'1', 'c':'2', 'id':'4'})) # different ID
        self.assertFalse(self.validator.have_seen({'a':'0', 'b':'1', 'c':'2', 'd':'4', 'id':'5'})) # extra property
        self.assertFalse(self.validator.have_seen({'a':'0', 'b':'1', 'id':'6'})) # missing property
        self.assertFalse(self.validator.have_seen({'a':0, 'b':1, 'c': 2, 'id':'7'})) # 0 != '0'
        self.assertFalse(self.validator.have_seen({'a':  None,  'b':1, 'c': 2, 'id':'8'}))
        self.assertFalse(self.validator.have_seen({'a': 'None', 'b':1, 'c': 2, 'id':'9'})) # None != 'None'

    def test_add_to_bad_records(self):
        self.validator.add_to_bad_records({'a':'0', 'id':'1'})
        self.assertTrue('1' in self.validator.bad_records)

    def test_duplicate_records(self):
        """
        Test the program specifications for duplicates:

        > Write a program that will read in the data and mark any records:
        >    1. That are a duplicate of another record
        > ...
        > Each record has an ID but that should only be used to identify a
        > record, not for validity or duplication testing (eg, two records
        > may be identical but have different IDs).
        """
        ids = ['7152', '9913', '2467', '1192', '9222']
        test_data = [
            {'name':'0', 'address':'1',  'zip':'00000', 'id': ids[0]},
            {'name':'0', 'address':'1',  'zip':'00000', 'id': ids[1]},
            {'name':'2', 'address':'3',  'zip':'00004', 'id': ids[2]},
            {'name':'0', 'address':None, 'zip':'00000', 'id': ids[3]},
            {'name':'0', 'address':None, 'zip':'00000', 'id': ids[4]}
            ]
        test_file = '/tmp/test-file.json' # test is *nix only, sorry!
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        self.validator.validate_file(test_file)
        self.assertTrue(ids[0] in self.validator.bad_records)
        self.assertTrue(ids[1] in self.validator.bad_records)
        self.assertFalse(ids[2] in self.validator.bad_records)
        self.assertTrue(ids[3] in self.validator.bad_records)
        self.assertTrue(ids[4] in self.validator.bad_records)

    def test_record_is_valid(self):
        """
        Test the specification for a valid record:
        >    2. name field is null, missing, or blank
        >    3. address field is null, missing, or blank
        >    4. zip is null, missing, or an invalid U.S. zipcode
        """
        a = {'name': 'David Schlachter', 'address': 'Montreal, QC', 'zip': '00000', 'id':'0'}
        self.assertTrue(self.validator.record_is_valid(a))
        # null, missing, blank fields
        for key in ['name', 'address', 'zip']:
            for value in ['', None]:
                b = a
                b[key] = value
                self.assertFalse(self.validator.record_is_valid(b))
            b = a
            del b[key]
            self.assertFalse(self.validator.record_is_valid(b))
        with self.assertRaises(NoIDError):
            self.validator.record_is_valid({'a':'0'})

if __name__ == "__main__":
    validator = DataValidator()
    validator.validate_file("data.json")
    validator.print_invalid_records()
