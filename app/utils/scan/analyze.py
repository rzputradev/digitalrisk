import json
from datetime import datetime
from dateutil import parser

class Analyze:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            print(f"Error: The file {self.file_path} was not found.")
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from the file.")

    def parse_date(self, date_str):
        date_str = date_str.replace('.', ':')  
        try:
            return parser.parse(date_str).date()  
        except ValueError:
            raise ValueError(f"Date format for '{date_str}' is not recognized.")

    def check_balance_validity(self):
        previous_balance = None

        for transaction in self.data['transactions']:
            current_balance = transaction['balance']['value']
            debit = transaction['debit']['value']
            credit = transaction['credit']['value']

            if previous_balance is None:
                calculated_balance = current_balance
            else:
                calculated_balance = previous_balance + credit - debit

            is_valid = (calculated_balance == current_balance)
            transaction['calculated_balance'] = {'value': calculated_balance}
            transaction['balance_check'] = {'value': is_valid}
            previous_balance = current_balance

    def exclude_transactions(self):
        transactions = self.data['transactions']

        # Group transactions by date
        transactions_by_date = {}
        for transaction in transactions:
            date_str = transaction['datetime']['value']  
            date = self.parse_date(date_str)  
            if date not in transactions_by_date:
                transactions_by_date[date] = []
            transactions_by_date[date].append(transaction)

        # Categorize transactions
        for date, trans in transactions_by_date.items():
            debit_values = {}
            credit_values = {}

            for transaction in trans:
                debit = transaction['debit']['value']  
                credit = transaction['credit']['value']  
                transaction_id = transaction['id']

                if debit != 0:
                    debit_values[transaction_id] = debit
                if credit != 0:
                    credit_values[transaction_id] = credit

            for transaction in trans:
                transaction_id = transaction['id']
                debit = transaction['debit']['value']  
                credit = transaction['credit']['value']  

                # Check if the transaction should be included or excluded
                include = True
                if debit != 0 and debit in credit_values.values():
                    include = False
                if credit != 0 and credit in debit_values.values():
                    include = False

                transaction['classification'] = {
                    "value": "" if include else "Exclude"
                }

    def get_weekend_transactions(self):
        weekend_transactions = []
        for transaction in self.data['transactions']:
            datetime_str = transaction['datetime']['value']
            try:
                date_obj = self.parse_date(datetime_str)
                day_name = date_obj.strftime("%A")
                if day_name in ["Saturday", "Sunday"]:
                    weekend_transactions.append(transaction)
            except ValueError as e:
                print(e)
        return weekend_transactions

    def fraud_transactions(self, threshold=100000000, rtgs_threshold=500000000):
        weekend_transactions = self.get_weekend_transactions()  # No arguments passed
        for transaction in self.data['transactions']:
            debit_value = transaction.get('debit', {}).get('value', 0)
            credit_value = transaction.get('credit', {}).get('value', 0)

            # Check if the transaction is a weekend transaction
            if transaction in weekend_transactions:
                if debit_value >= threshold or credit_value >= threshold:
                    if 'rtgs' in transaction.get('description', {}).get('value', '').lower():
                        if debit_value >= rtgs_threshold or credit_value >= rtgs_threshold:
                            transaction['classification'] = {"value": "Fraud"}
                    else:
                        transaction['classification'] = {"value": "Fraud"}

    def include_transaction(self):
        for transaction in self.data['transactions']:
            if transaction['classification']['value'] == "":
                transaction['classification']['value'] = "Include"

    def add_status(self):
        self.data['status'] = {
            "analyze": True,
        }

    def save_data(self):
        try:
            with open(self.file_path, 'w') as file:
                json.dump(self.data, file, indent=4)
        except IOError:
            print(f"Error: Failed to write to the file {self.file_path}.")

    def process_transactions(self):
        self.load_data()
        if self.data is not None:
            try:
                self.check_balance_validity()
                self.exclude_transactions()
                self.fraud_transactions()
                self.include_transaction()
                self.add_status()
                self.save_data()
            except ValueError as e:
                print(f"Error in date parsing: {e}")
                raise
            except Exception as e:
                print(f"An error occurred during processing: {e}")
                raise 
        else:
            print("Error: No data to process.")