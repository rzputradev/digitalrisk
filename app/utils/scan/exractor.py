from datetime import datetime
from flask import abort, current_app, url_for, flash
from copy import deepcopy

class Extractor:
    def __init__(self, json_data):  
        self.json_data = json_data
        self.expected_headers = [
            {"Posting", "Date", "Effective", "Branch", "Journal", "Transaction", "Description", "Amount", "DB/CR", "Balance"},
            {"Tgl", "Transaksi", "No.", "Dokumen", "Uraian", "Tipe", "Mutasi", "Saldo"},
            {"TIME", "REMARK", "DEBET", "CREDIT", "TELLER", "ID"},
            {"Tanggal", "Keterangan", "Debit", "Kredit", "Saldo", "SEQ"},
            {"Posting", "Date", "Remark", "Reference", "No", "Debit", "Credit", "Balance"},
            {"Date", "Val.Date", "Description", "Reference", "No.", "Debet", "Credit", "Balance"},
            {"Date", "Time", "Value", "Description", "Reference", "No.", "Debit", "Credit", "Saldo"},
        ]
        self.statement_settings = [
            {
                "id": 0,
                "report_type": ["BNI", "ACCOUNT", "STATEMENT"],
                "lower_limit": [
                    ["Ending", "Balance"]
                ]
            },
            {
                "id": 1,
                "report_type": ["Histori", "Transaksi"],
                "lower_limit": [
                    ["Apabila", "terdapat", "perbedaan", "dengan", "catatan"],
                    ["Saldo", "Awal"]
                ]
            },
            {
                "id": 2,
                "report_type": ["BANK", "RAKYAT", "INDONESIA", "Account", "Statement"],
                "lower_limit": [
                    ["OPENING", "CLOSING", "BALANCE"]
                ]
            },
            {
                "id": 3,
                "report_type": ["BANK", "BRI", "LAPORAN", "TRANSAKSI"],
                "lower_limit": [
                    ["Saldo", "Awal", "Total", "Debit"]
                ]
            },
            {
                "id": 4,
                "report_type": ["mandiri", "Laporan", "Rekening", "Koran"],
                "lower_limit": [
                    ["No", "of", "Debit"]
                ]
            },
            {
                "id": 5,
                "report_type": ["mandiri", "rekening", "koran"],
                "lower_limit": [
                    ["Mutasi", "Kredit"]
                ]
            },
            {
                "id": 6,
                "report_type": ["mandiri", "TRANSACTION", "INQUIRY"],
                "lower_limit": [
                    ["Total", "Transaction"]
                ]
            }

        ]
        self.normalize = []
        self.template = {
                            "id": 0,
                            "datetime": {
                                "value": "",
                                "confidence": 0.0,
                            },
                            "valuedate": {
                                "value": "",
                                "confidence": 0.0,
                            },
                            "description": {
                                "value": "",
                                "confidence": 0.0,
                            },
                            "debit": {
                                "value": 0.0,
                                "confidence": 0.0,
                            },
                            "credit": {
                                "value": 0.0,
                                "confidence": 0.0,
                            },
                            "balance": {
                                "value": 0.0,
                                "confidence": 1.0,
                            },
                            "calculated_balance": {
                                "value": 0.0,
                            },
                            "balance_check": {
                                "value": False
                            },
                            "classification": {
                                "value": "",
                            },
                        }

    def find_table_header(self, json_data, page_idx):
        blocks = json_data["pages"][page_idx]["blocks"]
        
        found_words = {}
        
        for block in blocks:
            for line in block.get("lines", []):
                for word in line.get("words", []):
                    value = word["value"]
                    found_words[value] = found_words.get(value, []) + [word["geometry"]]
        
        for header in self.expected_headers:
            matched_count = sum(1 for word in header if word in found_words)
            if matched_count >= len(header) * 0.8: 
                matched_geometries = {word: found_words[word] for word in header if word in found_words}
                return matched_geometries
        
        return None

    def find_header_coordinate(self, matched_geometries, y_tolerance=0.01):
        rows = {}
        
        for word, geometries in matched_geometries.items():
            for geometry in geometries:
                y_coord = geometry[0][1]
                matched_row = None
                for existing_y in rows.keys():
                    if abs(existing_y - y_coord) < y_tolerance:
                        matched_row = existing_y
                        break
                
                if matched_row is None:
                    rows[y_coord] = []
                else:
                    y_coord = matched_row
                    
                rows[y_coord].append({
                    'word': word,
                    'geometry': geometry
                })
        
        header_row = max(rows.items(), key=lambda x: len(x[1]))
        
        header_row_sorted = sorted(header_row[1], key=lambda x: x['geometry'][0][0])
        words_in_order = [item['word'] for item in header_row_sorted]
        geometries = [item['geometry'][0][1] for item in header_row_sorted]
        highest_geometry = max(geometries)
        lowest_geometry = min(geometries)
        
        return {
            'highest_geometry': highest_geometry,
            'lowest_geometry': lowest_geometry,
            'words': words_in_order, #show words for debugging
            'geometries': geometries #show geometries for debugging
        }

    def split_json_data(self, json_data, lowest_geometry, highest_geometry, page_idx):
        above_header = []
        below_header = []

        blocks = json_data["pages"][page_idx]["blocks"]
        
        for block in blocks:
            for line in block.get("lines", []):
                for word in line.get("words", []):
                        word_y_coord = word['geometry'][0][1]
                        word_x_coord = word['geometry'][0][0]
                        
                        if word_y_coord < lowest_geometry:
                            above_header.append({
                                'value': word['value'],
                                'y_coord': word_y_coord,
                                'x_coord': word_x_coord
                            })
                        elif word_y_coord > highest_geometry:
                            below_header.append({
                                'value': word['value'],
                                'confidence': word['confidence'],
                                'geometry': word['geometry'],
                            })

        return above_header, below_header
    
    def get_statement_id(self, above_header):
        values = {item['value'] for item in above_header}
        
        statement_id = None
        lower_limit = None

        for setting in self.statement_settings:
            match_statement_count = sum(1 for value in setting["report_type"] if value in values)
            if match_statement_count == len(setting["report_type"]):
                statement_id = setting["id"]
                lower_limit = setting["lower_limit"]

        if statement_id:
            return statement_id, lower_limit
        else:
            return None, None

    def get_table_content(self, below_header, limits, tolerance=0.01):
        results = []
        table_content = []

        for limit in limits:
            matched_items = [item for item in below_header if item['value'] in limit]
            grouped_items = {}
            
            for item in matched_items:
                rounded_y = round(item['geometry'][0][1] / tolerance) * tolerance
                
                if rounded_y not in grouped_items:
                    grouped_items[rounded_y] = []
                grouped_items[rounded_y].append(item)

            for y_coord, items in grouped_items.items():
                matched_values = {item['value'] for item in items}
                if all(value in matched_values for value in limit):
                    results.append(items)

        if results:
            limit_coordinate = [item for sublist in results for item in sublist]
            min_coordinate = min(limit_coordinate, key=lambda item: item['geometry'][0][1])['geometry'][0][1]

            for words in below_header:
                if words["geometry"][0][1] < (min_coordinate - 0.01):
                    table_content.append(words)

            return table_content
        else:
            return below_header
        
    
    #---extractor methhod---
    def get_date_balance(self, normalized_data, target_page, balance_align, tolerance=0.01):

        x_date = float('inf')
        x_balance = float('-inf')
        dates = []
        balances = []

        for page in normalized_data:
            if page['page_id'] == target_page and 'words' in page:
                page_data = page['words']

                for word in page['words']:
                    x_date_coordinate = word['geometry'][0][0]
                    x_balance_coordinate = word['geometry'][balance_align][0]

                    if x_date_coordinate < x_date:
                        x_date = x_date_coordinate

                    if x_balance_coordinate > x_balance:
                        x_balance = x_balance_coordinate

                for word in page['words']:
                    x_date_coordinate = word['geometry'][0][0]
                    y_date_coordinate = word['geometry'][0][1]
                    x_balance_coordinate = word['geometry'][balance_align][0]
                    y_balance_coordinate = word['geometry'][0][1]

                    if abs(x_date_coordinate - x_date) <= tolerance:
                        dates.append((word['value'], word['confidence'], y_date_coordinate))

                    if abs(x_balance_coordinate - x_balance) <= tolerance:
                        balances.append((word['value'], word['confidence'], y_balance_coordinate))

        if len(balances) > len(dates):
            smallest_balance = min(balances, key=lambda x: x[2])
            balances.remove(smallest_balance)

        return dates, balances, page_data

    def group_rows(self, date, balance, page_data):
        distances = []
        rows = []
        filtered_date_balance_rows = []    
        for i in range(len(date)):
            distance = abs(date[i][2] - balance[i][2])
            max_y = max(date[i][2], balance[i][2])
            min_y = min(date[i][2], balance[i][2])
            distances.append((distance, max_y, min_y))

        for i in range(len(distances)):
            if i + 1 < len(distances):
                next_y_coord = distances[i + 1][2]
            else:
                next_y_coord = distances[i][2] + 0.02
            row_data = []
            for word in page_data:
                item_y_coord = word['geometry'][0][1]
                if item_y_coord < (next_y_coord - 0.001) and (item_y_coord + distances[i][0] + 0.001) >= distances[i][1]:
                    row_data.append(word)

            rows.append({'row_data': row_data})


        date_set = set(date)
        balance_set = set(balance)
        
        for row in rows:
            filtered_row = {
                'row_data': []
            }
            for item in row['row_data']:
                value = item['value']
                confidence = item['confidence']
                geometry_y = item['geometry'][0][1]

                if (value, confidence, geometry_y,) not in date_set and (value, confidence, geometry_y) not in balance_set:
                    filtered_row['row_data'].append(item)
            
            if filtered_row['row_data']:
                filtered_date_balance_rows.append(filtered_row)

                
        return filtered_date_balance_rows
    
    #---statement_id = bni-digics
    def get_debit_credit(self, filtered_date_balance_rows):
        mutation = []
        type = []
        debits = []
        credits = []
        debits_credits = []
        no_document = []

        filtered_mutation = []
        filtered_type = []
        filtered_no_doc = []

        #get mutation
        for row in filtered_date_balance_rows:
            mutation_coordinate = max(row['row_data'], key=lambda x: x['geometry'][1][0])
            mutation.append(mutation_coordinate)

        mutation_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in mutation}

        for entry in filtered_date_balance_rows:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in mutation_set 
            ]
            if filtered_row_data: 
                filtered_mutation.append({'row_data': filtered_row_data})
        #get type
        for row in filtered_mutation:
            type_coordinate = max(row['row_data'], key=lambda x: x['geometry'][1][0])
            type.append(type_coordinate)

        type_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in type}

        for entry in filtered_mutation:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in type_set 
            ]
            if filtered_row_data: 
                filtered_type.append({'row_data': filtered_row_data})

        if len(type) != len(mutation):
            raise ValueError("The lengths of type_data and mutation_data must be the same.")
        
        #get debits and credits from combined type and mutation
        for t, m in zip(type, mutation):
            debits_credits.append({
                'value': [[t['value']], [m['value']]],
                'confidence': max(t['confidence'], m['confidence'])
            })

        debits = [(0.0, 1)] * len(debits_credits)
        credits = [(0.0, 1)] * len(debits_credits)

        for index, item in enumerate(debits_credits):
            value_type = item['value'][0][0]  
            value_amount = item['value'][1][0]  
            confidence = item['confidence']  

            if value_type == 'D':
                debits[index] = (value_amount, confidence)
            elif value_type == 'K':
                credits[index] = (value_amount, confidence)
            else:
                debits[index] = (0.0, 0)
                credits[index] = (0.0, 0)
        
        #clear number of document
        for row in filtered_type:
            no_doc_coordinate = min(row['row_data'], key= lambda x: x['geometry'][0][0])
            no_document.append(no_doc_coordinate)

        no_doc_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in no_document}

        for entry in filtered_type:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in no_doc_set 
            ]
            if filtered_row_data: 
                filtered_no_doc.append({'row_data': filtered_row_data})

        return debits, credits, filtered_no_doc

    #---statement_id = bri-statement_transaction---

    def get_datetime_userId(self, filtered_data, dates):

        userId_collumn = []
        time_collum = []
        times = []
        tolerance = 0.02

        for row in filtered_data:
            max_x_coordinate = max(row['row_data'], key=lambda x: x['geometry'][0][0])
            min_x_coordinate = min(row['row_data'], key=lambda x: x['geometry'][0][0])

            userId_collumn.append(max_x_coordinate)                
            time_collum.append(min_x_coordinate)
            times.append((min_x_coordinate['value'], min_x_coordinate['confidence']))

        highest_userId = max(item['geometry'][0][0] for item in userId_collumn)
        userId = [item for item in userId_collumn if abs(item['geometry'][0][0] - highest_userId) <= tolerance]

        date_times = [
            (f"{date} {time}", min(date_conf, time_conf))
            for (date, date_conf, _), (time, time_conf) in zip(dates, times)
        ]

        userId_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in userId}
        times_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in time_collum}

        filtered_time_userId = []

        for entry in filtered_data:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in userId_set and (item['value'], tuple(map(tuple, item['geometry']))) not in times_set 
            ]
            if filtered_row_data: 
                filtered_time_userId.append({'row_data': filtered_row_data})
        return date_times, filtered_time_userId

    def get_balance_credit_debit(self, filtered_time_userId):

        balances = []
        balance_collumn = []
        filtered_balance = []
        
        credits = []
        credit_collumn = []
        filtered_credit = []

        debits = []
        debit_collumn = []
        filtered_debit = []


        for row in filtered_time_userId:
            max_x_coordinate = max(row['row_data'], key=lambda x: x['geometry'][1][0])
            balances.append((max_x_coordinate['value'], max_x_coordinate['confidence']))
            balance_collumn.append(max_x_coordinate)
        
        balance_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in balance_collumn}

        for entry in filtered_time_userId:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in balance_set 
            ]
            if filtered_row_data: 
                filtered_balance.append({'row_data': filtered_row_data})

        for row in filtered_balance:
            credit_coordinate = max(row['row_data'], key=lambda x: x['geometry'][1][0])
            credits.append((credit_coordinate['value'], credit_coordinate['confidence']))
            credit_collumn.append(credit_coordinate)

        credit_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in credit_collumn}

        for entry in filtered_balance:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in credit_set 
            ]
            if filtered_row_data: 
                filtered_credit.append({'row_data': filtered_row_data})
            
        for row in filtered_credit:
            debit_coordinate = max(row['row_data'], key=lambda x: x['geometry'][1][0])
            debits.append((debit_coordinate['value'], debit_coordinate['confidence']))
            debit_collumn.append(debit_coordinate)
        
        debit_set = {(item['value'], tuple(map(tuple, item['geometry']))) for item in debit_collumn}

        for entry in filtered_credit:
            filtered_row_data = [
                item for item in entry['row_data']
                if (item['value'], tuple(map(tuple, item['geometry']))) not in debit_set 
            ]
            if filtered_row_data: 
                filtered_debit.append({'row_data': filtered_row_data})

        return balances, credits, debits, filtered_debit
    
    #---statement_id = Mandiri-account_statement---
    def valid_date_format(self, date_string):
        try:
            datetime.strptime(date_string, '%d/%m')
            return True
        except ValueError:
            return False
        
    def number_format(self, input_str):
        if all(char.isdigit() or char in ",." for char in input_str):
            return True
        else:
            return False

    def get_valdate_credit(self, filtered_data, tolerance=0.02):
        x_start = float('inf')
        x_end = float('-inf')
        valdate = []
        debit_credit = []
        credits = []
        debits = []

        for row in filtered_data:
            
            for item in row['row_data']:
                left_x_coordinate = item['geometry'][0][0]
                right_x_coordinate = item['geometry'][1][0]

                if left_x_coordinate < x_start:
                    x_start = left_x_coordinate

                if right_x_coordinate > x_end:
                    x_end = right_x_coordinate

        for row in filtered_data:
            row_credits = []
            row_data_to_remove = []
            for item in row['row_data']:
                left_x_coordinate = item['geometry'][0][0]
                right_x_coordinate = item['geometry'][1][0]

                if abs(left_x_coordinate - x_start) <= tolerance:
                    if self.valid_date_format(item['value']) :
                        valdate.append((item['value'], item['confidence']))
                        row_data_to_remove.append(item)

                if abs(right_x_coordinate - x_end) <= tolerance:
                    if self.number_format(item['value']) or len(item['value']) <= 1:
                        row_credits.append((item['value'], item['confidence']))
                        row_data_to_remove.append(item)
                    
            for data in row_data_to_remove:
                row['row_data'].remove(data)
                    
            debit_credit.append(row_credits)
            
        if debit_credit != [[]]:
            for row in debit_credit:
                if len(row) > 1 or any(item[0] == "D" for item in row):
                    debits.append(row[0])
                    credits.append((0,1))
                else:
                    credits.append(row[0])
                    debits.append((0,1))

        return valdate, debits, credits, filtered_data

    #---mandiri-transaction_inquery---
    def get_datetime_credit(self, filtered_data, dates, tolerance=0.01):
        x_start = float('inf')
        x_end = float('-inf')
        times = []
        credits = []

        for row in filtered_data:
            credit_added = False
            row_data_to_remove = []

            for item in row['row_data']:
                left_x_coordinate = item['geometry'][0][0]
                right_x_coordinate = item['geometry'][1][0]

                if left_x_coordinate < x_start:
                    x_start = left_x_coordinate

                if right_x_coordinate > x_end:
                    x_end = right_x_coordinate
            
            for item in row['row_data']:
                left_x_coordinate = item['geometry'][0][0]
                right_x_coordinate = item['geometry'][1][0]

                if abs(left_x_coordinate - x_start) <= tolerance:
                    times.append((item['value'], item['confidence']))
                    row_data_to_remove.append(item)

                if abs(right_x_coordinate - x_end) <= tolerance and not credit_added:
                    credits.append((item['value'], item['confidence']))
                    credit_added = True

                if abs(right_x_coordinate - x_end) <= tolerance:
                    row_data_to_remove.append(item)

            for data in row_data_to_remove:
                row['row_data'].remove(data)

        date_times = [
            (f"{date} {time}", min(date_conf, time_conf))
            for (date, date_conf, _), (time, time_conf) in zip(dates, times)
        ]
                    
        return date_times, credits, filtered_data

    def get_valuedate_debit(self, filtered_data, tolerance=0.01):
        x_start = float('inf')
        x_end = float('-inf')
        valuedates = []
        debits = []

        for row in filtered_data:
            row_data_to_remove = []
            
            for item in row['row_data']:
                x_coordinate = item['geometry'][1][0]

                if x_coordinate < x_start:
                    x_start = x_coordinate

                if x_coordinate > x_end:
                    x_end = x_coordinate
                    
            for item in row['row_data']:
                x_coordinate = item['geometry'][1][0]

                if abs(x_coordinate - x_start) <= tolerance:
                    valuedates.append((item['value'], item['confidence']))
                    row_data_to_remove.append(item)

                if abs(x_coordinate - x_end) <= tolerance:
                    debits.append((item['value'], item['confidence']))
                    row_data_to_remove.append(item)
            
            for data in row_data_to_remove:
                row['row_data'].remove(data)
        

        return valuedates, debits, filtered_data
    
    def get_description(self, filtered_data):
        descriptions = []
        for row in filtered_data:
            if not row['row_data']:
                # Handle empty `row_data` case
                descriptions.append((" ", 0))  # Replace with a suitable default value
            else:
                description = ' '.join(entry['value'] for entry in row['row_data'])
                confidence = min(entry['confidence'] for entry in row['row_data'])
                descriptions.append((description, confidence))
        return descriptions
    
    def clean_float_string(self, value):
        if len(value) > 2 and (value[-3] == '.' or value[-3] == ','):
            value = value[:-3]

        value = value.replace(',', '')
        value = value.replace('.', '')

        return int(value)

    def make_transaction(self, template,  date_times, valuedates, descriptions, debits, credits, balances):
        transactions = []
        transaction_id = 0

        for page_id, dt_list in date_times.items():
            for i, (dt, dt_conf) in enumerate(dt_list):

                credit_val, credit_conf = (0.0, 0.0)
                balance_val, balance_conf = (0.0, 0.0)
                valuedate_val, valuedate_conf = ("", 0.0)
                debit_val, debit_conf = (0.0, 0.0)
                description_val, description_conf = ("", 0.0)

                try:
                    if page_id in credits and i < len(credits[page_id]):
                        credit_val, credit_conf = credits[page_id][i]
                    
                    if page_id in balances and i < len(balances[page_id]):
                        balance_val, balance_conf = balances[page_id][i][:2]

                    if page_id in valuedates and i < len(valuedates[page_id]):
                        valuedate_val, valuedate_conf = valuedates[page_id][i]

                    if page_id in debits and i < len(debits[page_id]):
                        debit_val, debit_conf = debits[page_id][i]

                    if page_id in descriptions and i < len(descriptions[page_id]):
                        description_val, description_conf = descriptions[page_id][i]

                except IndexError:
                    continue 

                transaction = deepcopy(template)
                transaction["id"] = transaction_id
                transaction["datetime"]["value"] = dt
                transaction["datetime"]["confidence"] = dt_conf
                transaction["valuedate"]["value"] = valuedate_val 
                transaction["valuedate"]["confidence"] = valuedate_conf if valuedate_conf else 1
                transaction["description"]["value"] = description_val
                transaction["description"]["confidence"] = description_conf
                transaction["debit"]["value"] = self.clean_float_string(debit_val) if debit_val else 0.0
                transaction["debit"]["confidence"] = debit_conf if debit_conf else 1
                transaction["credit"]["value"] = self.clean_float_string(credit_val) if credit_val else 0.0
                transaction["credit"]["confidence"] = credit_conf if credit_conf else 1
                transaction["balance"]["value"] = self.clean_float_string(balance_val) if balance_val else 0.0
                transaction["balance"]["confidence"] = balance_conf if balance_conf else 0.0

                transactions.append(transaction)
                transaction_id += 1 

        return transactions
    
    def extract(self):
        table_headers, header_coordinates, above_headers, below_headers, table_contents = {}, {}, {}, {}, {}

        date_times, valuedates, descriptions, debits, credits, balances, seqs = {}, {}, {}, {}, {}, {}, {}
        dates = {}
        pages_data, filtered_date_balance_rows, filtered_datetime_credit_rows, filtered_valuedate_debit_row, filtered_valdate_credit_rows = {}, {}, {}, {}, {}
        filtered_date_seqs, filtered_times_userIds, filtered_debits, filtered_no_docs = {}, {}, {}, {}
        try:
            #---start normalize---
            for page in self.json_data["pages"]:
                page_idx = page["page_idx"]
                words_without_header = []

                table_header = self.find_table_header(self.json_data, page_idx)
                table_headers[page_idx] = table_header

                if table_headers[0] is not None and table_header is not None:
                    header_coordinate = self.find_header_coordinate(table_headers[page_idx])
                    header_coordinates[page_idx] = header_coordinate

                    above_header, below_header = self.split_json_data(self.json_data, header_coordinates[page_idx]['lowest_geometry'], header_coordinates[page_idx]['highest_geometry'], page_idx)
                    above_headers[page_idx], below_headers[page_idx] = above_header, below_header

                    if above_headers[0] != []:
                            statement_id, lower_limit = self.get_statement_id(above_headers[0])
                    elif above_header[0] == []:
                        print("Account Statement is unknown")
                        break

                    if statement_id:
                        table_content = self.get_table_content(below_headers[page_idx], lower_limit)
                        table_contents[page_idx] = table_content
                    else:
                        print("Account Statement is unknown")
                        break

                elif table_headers[0] is not None and table_header is None:
                    for block in page.get("blocks", []):
                        for line in block.get("lines", []):
                            for word in line.get("words", []):
                                words_without_header.append({
                                    'value': word['value'],
                                    'confidence': word['confidence'],
                                    'geometry': word['geometry'],
                                })

                    below_headers[page_idx] = words_without_header
                    table_content = self.get_table_content(below_headers[page_idx], lower_limit)
                    table_contents[page_idx] = table_content
                else:
                    print("Input is invald!")
                    break
                page_data = {
                    "page_id": page_idx,
                    "statement_id": statement_id,
                    "words": []
                }
                page_data["words"].extend(table_contents[page_idx])
                self.normalize.append(page_data)
            
            #---start extractor---
            for page in self.normalize:
                page_id = page.get("page_id")

                if page.get("statement_id") == 1 :
                    date, balance, page_data = self.get_date_balance(self.normalize, page_id, 1)
                    dates[page_id], balances[page_id], pages_data[page_id] = date, balance, page_data

                    filtered_date_balance_row = self.group_rows(dates[page_id], balances[page_id], pages_data[page_id])
                    filtered_date_balance_rows[page_id] = filtered_date_balance_row        
                    #modify dates tuples
                    date_times = {}
                    for key, value in dates.items():
                        date_times[key] = [(item[0], item[1]) for item in value]

                    debit, credit, filtered_doc  = self.get_debit_credit(filtered_date_balance_rows[page_id])
                    debits[page_id], credits[page_id], filtered_no_docs[page_id] = debit, credit, filtered_doc

                    descriptions[page_id] = self.get_description(filtered_no_docs[page_id])
                
                elif page.get("statement_id") == 3 :
                    date, seq, page_data = self.get_date_balance(self.normalize, page_id, 0)
                    dates[page_id], seqs[page_id], pages_data[page_id] = date, seq, page_data

                    filtered_date_seq = self.group_rows(dates[page_id], seqs[page_id], pages_data[page_id])
                    filtered_date_seqs[page_id] = filtered_date_seq

                    date_time, filtered_time_userId = self.get_datetime_userId(filtered_date_seqs[page_id], dates[page_id])
                    date_times[page_id], filtered_times_userIds[page_id] = date_time, filtered_time_userId    
                    
                    balance, credit, debit, filtered_debit = self.get_balance_credit_debit(filtered_times_userIds[page_id])
                    balances[page_id], credits[page_id], debits[page_id], filtered_debits[page_id] = balance, credit, debit, filtered_debit

                    descriptions[page_id] = self.get_description(filtered_debits[page_id])
                elif page.get("statement_id") == 5:
                    date, balance, page_data = self.get_date_balance(self.normalize, page_id, 1)
                    dates[page_id], balances[page_id], pages_data[page_id] = date, balance, page_data

                    #modify dates tuples
                    date_times = {}
                    for key, value in dates.items():
                        date_times[key] = [(item[0], item[1]) for item in value]
                                          
                    filtered_date_balance_row = self.group_rows(dates[page_id], balances[page_id], pages_data[page_id])
                    filtered_date_balance_rows[page_id] = filtered_date_balance_row

                    valdate, debit, credit, filtered_valdate_credit_row = self.get_valdate_credit(filtered_date_balance_rows[page_id])
                    valuedates[page_id], debits[page_id], credits[page_id], filtered_valdate_credit_rows[page_id] = valdate, debit, credit, filtered_valdate_credit_row
                    descriptions[page_id] = self.get_description(filtered_valdate_credit_rows[page_id])
                elif page.get("statement_id") == 6 and len(page.get("words", [])) >= 6:
                    date, balance, page_data = self.get_date_balance(self.normalize, page_id, 0)
                    dates[page_id], balances[page_id], pages_data[page_id] = date, balance, page_data

                    filtered_date_balance_row = self.group_rows(dates[page_id], balances[page_id], pages_data[page_id])
                    filtered_date_balance_rows[page_id] = filtered_date_balance_row

                    datetime, credit, filtered_datetime_credit_row = self.get_datetime_credit(filtered_date_balance_rows[page_id], date)
                    date_times[page_id], credits[page_id], filtered_datetime_credit_rows[page_id] = datetime, credit, filtered_datetime_credit_row

                    valuedate, debit, filtered_row = self.get_valuedate_debit(filtered_datetime_credit_rows[page_id])
                    valuedates[page_id], debits[page_id], filtered_valuedate_debit_row[page_id] = valuedate, debit, filtered_row

                    descriptions[page_id] = self.get_description(filtered_valuedate_debit_row[page_id])

            transactions = self.make_transaction(self.template, date_times, valuedates, descriptions, debits, credits, balances)
            transaction_result = {"transactions": transactions}
            return transaction_result
        except Exception as e:
            print(f"Error: {e}")
            flash("An error occurred during the extraction process.", "danger")
            return
            