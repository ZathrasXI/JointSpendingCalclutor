import unittest
from unittest.mock import patch
from wow import *
import os
import csv

class TestData():
    FOLDER_NAME = 'test_data'
    with patch('builtins.input', return_value=FOLDER_NAME):
        DIRECTORY = find_folder()
    
    with patch("builtins.input", return_value="Jan Sophie"):
        NAMES = get_names()

    SPREADSHEET_NAME = "totals"
    with patch("builtins.input", return_value=SPREADSHEET_NAME):
        TOTALS_SPREADSHEET, HEADER = create_totals_file(DIRECTORY)

    STATEMENTS = get_statements(DIRECTORY, TOTALS_SPREADSHEET)
    HEADER = ["person_owed"] + NAMES

    def create_empty_totals_spreadsheet(self):
        with open(self.DIRECTORY + self.TOTALS_SPREADSHEET, "w") as t:
            clear_spreadsheet = csv.DictWriter(t, self.HEADER)
            clear_spreadsheet.writeheader()


    def remove_totals_spreadsheet(self):
        os.remove(self.DIRECTORY + self.TOTALS_SPREADSHEET)


class TestGetDetails(unittest.TestCase, TestData):
    
    def test_which_folder_are_the_statements_in(self):
        assert os.path.isdir(self.DIRECTORY) is True
        assert self.DIRECTORY[-1] == '/'


    def test_add_trailing_space(self):
        folder_name = add_trailing_slash_if_needed(self.FOLDER_NAME)
        assert folder_name[-1] == '/'


    def test_folder_contains_correct_statements(self):
        statement_1 = 'jans_statement.csv'
        statement_2 = 'sophies_statement.csv'
        statement_3 = 'jans_coop_bank_statement.csv'
        assert statement_1 in self.STATEMENTS
        assert statement_2 in self.STATEMENTS
        assert statement_3 not in self.STATEMENTS
        

    def test_create_totals_file(self):
        with patch("builtins.input", return_value="totals"):
            spreadsheet, header = create_totals_file(self.DIRECTORY)
        assert spreadsheet == self.SPREADSHEET_NAME + ".csv"
        assert header == ['person_owed']
        assert os.path.isfile(self.DIRECTORY + self.TOTALS_SPREADSHEET) is True
        with open(self.DIRECTORY + self.TOTALS_SPREADSHEET) as totals:
            reader = csv.DictReader(totals)
            file_header = reader.fieldnames
            assert header == file_header

        self.remove_totals_spreadsheet()


    def test_whose_statement_is_this(self):
        with patch("builtins.input", return_value="Sophie"):
            person = whose_statement(self.STATEMENTS[0])
        assert person == "Sophie"
        assert person != "Michael"
    

class TestReadStatement(unittest.TestCase, TestData):
    #TODO test for skipping a transaction in a statement

    def test_one_person_pays_for_all_transactions(self):
        case = {   
                "statement_owner": self.NAMES[1],
                "return_value": "Jan",
                "expected": {
                    "person_owed":"Sophie",
                    "Jan":90.0
                }
            }
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(self.STATEMENTS[0], case['statement_owner'], self.DIRECTORY)
        assert case['expected'] == owed_from_statement


    def test_2_people_go_halves_on_all_transactions(self):
        case = {
                "statement_owner": self.NAMES[1],
                "return_value": "Jan James",
                "expected": {
                    "person_owed": "Sophie",
                    "Jan": 45.0,
                    "James": 45.0
                }
            }
        
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(self.STATEMENTS[0], case['statement_owner'], self.DIRECTORY)
        assert case['expected'] == owed_from_statement


    def test_3_people_split_cost(self):
        case = {   
                "statement_owner": self.NAMES[0],
                "return_value": "Sophie Jane Sven",
                "expected": {
                    "person_owed": "Jan",
                    "Sophie": 30.0,
                    "Jane": 30.0,
                    "Sven": 30.0
                }
            }
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(self.STATEMENTS[0], case['statement_owner'], self.DIRECTORY)
        assert case['expected'] == owed_from_statement


class TestMergeTotalsSpreadsheetWithOwedFromStatement(unittest.TestCase, TestData):

    def test_can_merge_empty_totals_with_totals_from_statement(self):
        self.create_empty_totals_spreadsheet()
        case = {
                "statement_owner": self.NAMES[1],
                "return_value": "Jan",
                "statement":self.STATEMENTS[0],
                "totals_spreadsheet": self.TOTALS_SPREADSHEET,
                "expected": {
                    "person_owed": "Sophie",
                    "Jan": 90.0,
                }
            }
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(case['statement'], case['statement_owner'], self.DIRECTORY)
        updated_totals, header = merge_owed_from_statement_with_totals(self.DIRECTORY, everyone_who_owes_from_this_statement, case['statement_owner'], case['totals_spreadsheet'], owed_from_statement)
        assert case['expected'] == updated_totals[0]

    def test_can_update_prepopulated_totals_statement_one_person_paid_for_everything(self):
        case = {
                "statement_owner": self.NAMES[1],
                "return_value": "Jan",
                "statement": self.STATEMENTS[0],
                "totals_spreadsheet": "../prefilled_totals.csv",
                "expected": [
                    {
                        "person_owed": "Sophie",
                        "Jan": 190.0,
                        "Sophie": 0.0
                    },
                    {
                        "person_owed": "Jan",
                        "Jan": 0.0,
                        "Sophie":10.0
                    }
                ]
            }
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(case['statement'], case['statement_owner'], self.DIRECTORY)
    
        updated_totals, header = merge_owed_from_statement_with_totals(self.DIRECTORY, everyone_who_owes_from_this_statement,case['statement_owner'], case['totals_spreadsheet'], owed_from_statement)
        assert case['expected'][0] in updated_totals
        assert case['expected'][1] in updated_totals
        assert len(updated_totals) == 2

class TestWriteTotalsSpreadsheet(unittest.TestCase, TestData):

    def test_can_write_to_totals_spreadsheet(self):
        case = {
                "statement_owner": self.NAMES[1],
                "return_value": "Jan",
                "statement": self.STATEMENTS[0],
                "totals_spreadsheet": "../prefilled_totals.csv",
                "expected": [
                    {
                        'person_owed': 'person_owed', 
                        'Jan': 'Jan', 
                        'Sophie': 'Sophie'
                    },
                    {
                        "person_owed": "Sophie",
                        "Jan": "190.0",
                        "Sophie": "0.0"
                    },
                    {
                        "person_owed": "Jan",
                        "Jan": "0.0",
                        "Sophie":"10.0"
                    }
                ]
            }
        with patch("builtins.input", return_value=case['return_value']):
            owed_from_statement, everyone_who_owes_from_this_statement = read_statement(case['statement'], case['statement_owner'], self.DIRECTORY)
    
        updated_totals, header = merge_owed_from_statement_with_totals(self.DIRECTORY, everyone_who_owes_from_this_statement,case['statement_owner'], case['totals_spreadsheet'], owed_from_statement)        
        write_to_totals_spreadsheet(self.DIRECTORY, self.NAMES, self.TOTALS_SPREADSHEET, updated_totals)

        with open(self.DIRECTORY + self.TOTALS_SPREADSHEET, "r") as t:
            reader = csv.DictReader(t, fieldnames=header)
            print("FIELDNAMES", reader.fieldnames)
            list_of_rows = list(reader)
            assert case['expected'] == list_of_rows

        self.remove_totals_spreadsheet()
