import os
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime
from app.models.statement import Statement
from flask import abort, current_app, url_for, flash
from rapidfuzz import fuzz
from collections import defaultdict, Counter
import math

from app.utils.helper import load_json_file, save_json_file


class Extractor:
    def __init__(self, json_result):  
        self.json_result = json_result
  
    
    def _load_md(self):
        fileMD_Parameter_path = os.path.join(current_app.config['FILE_FOLDER'], 'MD_BankReportParameters.csv')
        if not os.path.exists(fileMD_Parameter_path):
            raise FileNotFoundError(f"File not found: {fileMD_Parameter_path}")
        masterParameter_df = pd.read_csv(fileMD_Parameter_path, delimiter=';')
        return masterParameter_df
    
        
    def _fuzzy_match(self, text, target_text, threshold=80):
        try:
            return fuzz.partial_ratio(self._normalize_text(text), self._normalize_text(target_text)) >= threshold
        except Exception as e:
            raise e
        
    
    def _normalize_text(self, text):
        try:
            return re.sub(r'\W+', '', str(text).lower())
        except Exception as e:
            print(f"Error: {e}")
            raise e


    def _normalize_master_data(self, master_df):
        try:
            master_df['OCR_Found_Bank_normalized'] = master_df['OCR_Found_Bank'].apply(self._normalize_text)
            for i in range(1, 9):
                master_df[f'OCR_Found_Type_{i:02d}_normalized'] = master_df[f'OCR_Found_Type_{i:02d}'].apply(self._normalize_text)
            return master_df
        except Exception as e:
            print(f"Error: {e}")
            raise e
    

    def _json_to_dataframe(self, data):
        try:
            rows = []
            for page in data["pages"]:
                page_idx = page["page_idx"]
                language = page.get("language", "Unknown")  
                for block in page["blocks"]:
                    block_geometry = json.dumps(block["geometry"]) 
                    for line in block["lines"]:
                        line_geometry = json.dumps(line["geometry"])
                        for word in line["words"]:
                            word_value = word["value"]
                            word_confidence = word["confidence"]
                            word_geometry = json.dumps(word["geometry"])
                            rows.append([
                                page_idx,
                                language,
                                block_geometry,
                                line_geometry,
                                word_value,
                                word_confidence,
                                word_geometry
                            ])
            
            df = pd.DataFrame(rows, columns=[
                "page_idx",
                "language",
                "block_geometry",
                "line_geometry",
                "word_value",
                "word_confidence",
                "word_geometry"
            ])
            
            return df
        except Exception as e:
            print(f"Error: {e}")
            raise e
 

    def _find_multiple_types(self, ocr_data, master_df, page_index):
        try:
            ocr_data_filtered = ocr_data[ocr_data['page_idx'] == page_index].copy()

            ocr_data_filtered['word_value_normalized'] = ocr_data_filtered['word_value'].apply(self._normalize_text)

            ocr_words_set = set(ocr_data_filtered['word_value_normalized'])
            
            best_match = None
            max_matches = 0
            
            for _, row in master_df.iterrows():
                bank_match = any(fuzz.ratio(row['OCR_Found_Bank_normalized'], word) > 80 for word in ocr_words_set)
                if not bank_match:
                    continue
                
                matches = 0
                for i in range(1, 9):
                    type_match = any(fuzz.ratio(row[f'OCR_Found_Type_{i:02d}_normalized'], word) > 80 for word in ocr_words_set)
                    if type_match:
                        matches += 1
                
                if matches >= 5 and matches > max_matches:
                    max_matches = matches
                    best_match = row
            
            if best_match is not None:
                column_name = {
                    'DC_Column': best_match['DC_Column'],
                    'Date_Trx_Column': best_match['Date_Trx_Column'],
                    'Date_Val_Column': best_match['Date_Val_Column'],
                    'Description_Column': best_match['Description_Column'],
                    'Reference_Column': best_match['Reference_Column'],
                    'Debit_Column': best_match['Debit_Column'],
                    'Credit_Column': best_match['Credit_Column'],
                    'Balance_Column': best_match['Balance_Column']
                }
                setting_parameters = {
                    'OD_Possible': best_match['OD_Possible'],
                    'OD_Location': best_match['OD_Location'],
                    'OD_Identifier': best_match['OD_Identifier'],
                    'DC_SingleColumn': best_match['DC_SingleColumn'],
                    'DC_Location': best_match['DC_Location'],
                    'DC_Identifier': best_match['DC_Identifier'],
                    'Summary_Page': best_match['Summary_Page'],
                    'Summary_Word': best_match['Summary_Word'],
                    'Column_Repeat': best_match['Column_Repeat']
                }
                column_threshold = {
                    'DC_Coord_Start': best_match['DC_Coord_Start'],
                    'DC_Coord_End': best_match['DC_Coord_End'],
                    'Date_Trx_Coord_Start': best_match['Date_Trx_Coord_Start'],
                    'Date_Trx_Coord_End': best_match['Date_Trx_Coord_End'],
                    'Date_Val_Coord_Start': best_match['Date_Val_Coord_Start'],
                    'Date_Val_Coord_End': best_match['Date_Val_Coord_End'],
                    'Description_Coord_Start': best_match['Description_Coord_Start'],
                    'Description_Coord_End': best_match['Description_Coord_End'],
                    'Reference_Coord_Start': best_match['Reference_Coord_Start'],
                    'Reference_Coord_End': best_match['Reference_Coord_End'],
                    'Debit_Coord_Start': best_match['Debit_Coord_Start'],
                    'Debit_Coord_End': best_match['Debit_Coord_End'],
                    'Credit_Coord_Start': best_match['Credit_Coord_Start'],
                    'Credit_Coord_End': best_match['Credit_Coord_End'],
                    'Balance_Coord_Start': best_match['Balance_Coord_Start'],
                    'Balance_Coord_End': best_match['Balance_Coord_End']
                }
                column_default = {
                    'DC_Coord_Default_Start': best_match['DC_Coord_Default_Start'],
                    'DC_Coord_Default_End': best_match['DC_Coord_Default_End'],
                    'Date_Trx_Coord_Default_Start': best_match['Date_Trx_Coord_Default_Start'],
                    'Date_Trx_Coord_Default_End': best_match['Date_Trx_Coord_Default_End'],
                    'Date_Val_Coord_Default_Start': best_match['Date_Val_Coord_Default_Start'],
                    'Date_Val_Coord_Default_End': best_match['Date_Val_Coord_Default_End'],
                    'Description_Coord_Default_Start': best_match['Description_Coord_Default_Start'],
                    'Description_Coord_Default_End': best_match['Description_Coord_Default_End'],
                    'Reference_Coord_Default_Start': best_match['Reference_Coord_Default_Start'],
                    'Reference_Coord_Default_End': best_match['Reference_Coord_Default_End'],
                    'Debit_Coord_Default_Start': best_match['Debit_Coord_Default_Start'],
                    'Debit_Coord_Default_End': best_match['Debit_Coord_Default_End'],
                    'Credit_Coord_Default_Start': best_match['Credit_Coord_Default_Start'],
                    'Credit_Coord_Default_End': best_match['Credit_Coord_Default_End'],
                    'Balance_Coord_Default_Start': best_match['Balance_Coord_Default_Start'],
                    'Balance_Coord_Default_End': best_match['Balance_Coord_Default_End'],
                    'YColumn_Coord_Default_Start': best_match['YColumn_Coord_Default_Start'],
                    'YColumn_Coord_Default_End': best_match['YColumn_Coord_Default_End']
                }
                return best_match['Bank'], best_match['Type'], column_name, setting_parameters, column_threshold, column_default
            
            return None, None, None, None, None, None
        except Exception as e:
            raise e
    

    def _check_and_return_all_pages(self, df_json, masterParameter_df):
        try:
            masterParameter_df = self._normalize_master_data(masterParameter_df)
            
            results = []

            unique_page_indices = df_json['page_idx'].unique()
            for page_index in unique_page_indices:
                bank_name, report_type, column_name, setting_parameters, column_threshold, column_default = self._find_multiple_types(df_json, masterParameter_df, page_index)
                
                if bank_name is not None:
                    results.append({
                        "page_index": page_index,                
                        "bank_name": bank_name,
                        "report_type": report_type,
                        "column_name": column_name,
                        "setting_parameters": setting_parameters,
                        "column_threshold": column_threshold,
                        "column_default": column_default
                    })

            bank_names = [param['bank_name'] for param in results]
            report_types = [param['report_type'] for param in results]
            if len(set(bank_names)) > 1 or len(set(report_types)) > 1:
                flash("Bank name or report type are different for some pages.", "warning")

            flash(f"Found {len(results)} pages with matching bank and report type.", "success")
            return results
        except Exception as e:
            raise e
        
    

    def _extract_coordinates_full(self, geometry):
        if pd.isna(geometry) or not isinstance(geometry, str):
            return None
        try:
            clean_str = geometry.translate({ord(i): None for i in '()[] '})
            coords = clean_str.split(',')
            if len(coords) != 4:
                raise ValueError("Coordinate string does not have exactly four values")
            coord_floats = [float(coord) for coord in coords]
            return ((coord_floats[0], coord_floats[1]), (coord_floats[2], coord_floats[3]))
        except Exception as e:
            raise e


    def _calculate_mode(self, values):
        if not values:
            return None
        try:
            value_counter = Counter(values)
            mode = value_counter.most_common(1)
            return mode[0][0] if mode else None
        except Exception as e:
            raise e
        
    def _calculate_and_print_statistics(self, filtered_df, parameters):
        try:
            # Initialize containers to accumulate results across all parameters
            all_global_y_end_q3 = {}
            all_global_keyword_coords = {}
            all_x_start_counter = Counter()
            all_x_end_counter = Counter()
            all_column_modes = {}
            
            all_y_starts = []
            all_y_ends = []

            threshold = 0.02  # Threshold for filtering coordinates within a certain range

            # Step 1: Gather all y_start and y_end coordinates for matching keywords
            # Redo -> should be calculating y start, y end per page idx
            for param in parameters:
                # Reverse the mapping of column names for easy lookup
                keywords = {value: key for key, value in param['column_name'].items()}

                for _, group in filtered_df.groupby('page_idx'):
                    # Iterate over each keyword to find matches in word_value
                    for value, key in keywords.items():
                        if pd.isna(value):
                            continue  # Skip if the keyword is NaN

                        # Filter coordinates matching the keyword
                        keyword_coords = group[group['word_value'].apply(lambda x: self._fuzzy_match(x, value))]['coordinates']
                        coords_list = keyword_coords.dropna().tolist()

                        # Collect y_start and y_end coordinates for matching keywords
                        y_start = [round(coord[0][1], 2) for coord in coords_list if coord]
                        y_end = [round(coord[1][1], 2) for coord in coords_list if coord]
                        all_y_starts.extend(y_start)
                        all_y_ends.extend(y_end)

            # Calculate the mode of y_start and y_end coordinates across all pages
            column_common_y_start = self._calculate_mode(all_y_starts)
            column_common_y_end = self._calculate_mode(all_y_ends)
            print(all_y_starts)
            print(column_common_y_start)

            # Step 2: Process each parameter to compute statistics
            for param in parameters:
                keywords = {value: key for key, value in param['column_name'].items()}
                global_y_end_q3 = {}
                global_keyword_coords = {key: {'x_start': [], 'x_end': [], 'y_start': [], 'y_end': []} for key in keywords.values()}

                for page, group in filtered_df.groupby('page_idx'):
                    coords_list = group['coordinates'].tolist()
                    if coords_list:
                        # Extract and round coordinates
                        x_start = [round(coord[0][0], 2) for coord in coords_list if coord]
                        x_end = [round(coord[1][0], 2) for coord in coords_list if coord]
                        y_start = [round(coord[0][1], 2) for coord in coords_list if coord]
                        y_end = [round(coord[1][1], 2) for coord in coords_list if coord]

                        # Calculate the 75th percentile of y_end coordinates
                        global_y_end_q3[page] = np.percentile(y_end, 75) if y_end else None

                        for value, key in keywords.items():
                            if pd.isna(value):
                                global_keyword_coords[key]['x_start'].append(None)
                                global_keyword_coords[key]['x_end'].append(None)
                                global_keyword_coords[key]['y_start'].append(None)
                                global_keyword_coords[key]['y_end'].append(None)
                            else:
                                # Filter coordinates matching the keyword
                                keyword_coords = group[group['word_value'].apply(lambda x: self._fuzzy_match(x, value))]['coordinates']
                                coords_list = keyword_coords.dropna().apply(
                                    lambda row: {
                                        'x_start': round(float(row[0][0]), 2),
                                        'y_start': round(float(row[0][1]), 2),
                                        'x_end': round(float(row[1][0]), 2),
                                        'y_end': round(float(row[1][1]), 2)
                                    }
                                ).tolist()

                                if coords_list:
                                    # Filter coordinates within the common y_start and y_end range
                                    filtered_coords = [
                                        coord for coord in coords_list
                                        if column_common_y_start - threshold <= coord['y_start'] <= column_common_y_start + threshold
                                        and column_common_y_end - threshold <= coord['y_end'] <= column_common_y_end + threshold
                                    ]
                                    global_keyword_coords[key]['x_start'].extend(coord['x_start'] for coord in filtered_coords)
                                    global_keyword_coords[key]['x_end'].extend(coord['x_end'] for coord in filtered_coords)
                                    global_keyword_coords[key]['y_start'].extend(coord['y_start'] for coord in filtered_coords)
                                    global_keyword_coords[key]['y_end'].extend(coord['y_end'] for coord in filtered_coords)

                # Calculate the mode of coordinates for each keyword
                column_modes = {}
                for key, coords in global_keyword_coords.items():
                    column_modes[f'{key}_x_start'] = self._calculate_mode([x for x in coords['x_start'] if x is not None])
                    column_modes[f'{key}_x_end'] = self._calculate_mode([x for x in coords['x_end'] if x is not None])
                    column_modes[f'{key}_y_start'] = self._calculate_mode([y for y in coords['y_start'] if y is not None])
                    column_modes[f'{key}_y_end'] = self._calculate_mode([y for y in coords['y_end'] if y is not None])

                # Step 3: Create mappings between x_start and x_end, and vice versa
                x_start_to_end = defaultdict(list)
                x_end_to_start = defaultdict(list)

                for _, group in filtered_df.groupby('page_idx'):
                    for coord in group['coordinates']:
                        if coord:
                            x_start, y_start = round(coord[0][0], 2), round(coord[0][1], 2)
                            x_end, y_end = round(coord[1][0], 2), round(coord[1][1], 2)
                            x_start_to_end[x_start].append(x_end)
                            x_end_to_start[x_end].append(x_start)

                # Count occurrences of x_start and x_end mappings
                x_start_counter = Counter(x_start_to_end)
                x_end_counter = Counter(x_end_to_start)

                # Step 4: Update global containers with the results from the current parameter
                all_global_y_end_q3.update(global_y_end_q3)
                for key, value in global_keyword_coords.items():
                    if key in all_global_keyword_coords:
                        for k, v in value.items():
                            all_global_keyword_coords[key][k].extend(v)
                    else:
                        all_global_keyword_coords[key] = value
                all_x_start_counter.update(x_start_counter)
                all_x_end_counter.update(x_end_counter)
                all_column_modes.update(column_modes)

            # Return the accumulated statistics
            return all_global_y_end_q3, all_global_keyword_coords, all_x_start_counter, all_x_end_counter, all_column_modes, column_common_y_start, column_common_y_end
        
        except Exception as e:
            # Raise any exception encountered during processing
            raise e



        
    
    
    def _get_parameters_for_page(self, page_index, parameters):
        for param in parameters:
            if param['page_index'] == page_index:
                return param
        return None
    

    def _adjust_coordinates(self, column_modes, page_idx, keyword, column_threshold, column_default):
        try:
            try:
                threshold_start_key = f'{keyword}_Coord_Start'
                threshold_end_key = f'{keyword}_Coord_End'
                default_start_key = f'{keyword}_Coord_Default_Start'
                default_end_key = f'{keyword}_Coord_Default_End'

                threshold_start = column_threshold.get(threshold_start_key, np.nan)
                threshold_end = column_threshold.get(threshold_end_key, np.nan)
                default_start = column_default.get(default_start_key, np.nan)
                default_end = column_default.get(default_end_key, np.nan)
                x_start_mode = column_modes.get(f'{keyword}_x_start', default_start)
                x_end_mode = column_modes.get(f'{keyword}_x_end', default_end)
                
                x_start = float(x_start_mode) + threshold_start if not np.isnan(threshold_start) else default_start
                x_end = float(x_end_mode) + threshold_end if not np.isnan(threshold_end) else default_end

            except (IndexError, ValueError, TypeError, KeyError):
                x_start = default_start
                x_end = default_end
            return x_start, x_end
        except Exception as e:
            raise e


    def _categorize_based_on_coordinates(self, coords, page_idx, column_modes, parameters, column_common_y_start, column_common_y_end):
        if not coords:
            return None

        x_start, y_start = coords[0]
        x_end, y_end = coords[1]

        param = self._get_parameters_for_page(page_idx, parameters)
        if not param:
            return "Other"

        column_threshold = param['column_threshold']
        column_default = param['column_default']

        y_threshold = column_common_y_end

        dc_x_start, dc_x_end = self._adjust_coordinates(column_modes, page_idx, "DC", column_threshold, column_default)
        trx_x_start, trx_x_end = self._adjust_coordinates(column_modes, page_idx, "Date_Trx", column_threshold, column_default)
        value_x_start, value_x_end = self._adjust_coordinates(column_modes, page_idx, "Date_Val", column_threshold, column_default)
        description_x_start, description_x_end = self._adjust_coordinates(column_modes, page_idx, "Description", column_threshold, column_default)
        reference_x_start, reference_x_end = self._adjust_coordinates(column_modes, page_idx, "Reference", column_threshold, column_default)
        debit_x_start, debit_x_end = self._adjust_coordinates(column_modes, page_idx, "Debit", column_threshold, column_default)
        credit_x_start, credit_x_end = self._adjust_coordinates(column_modes, page_idx, "Credit", column_threshold, column_default)
        saldo_x_start, saldo_x_end = self._adjust_coordinates(column_modes, page_idx, "Balance", column_threshold, column_default)

        if y_start >= y_threshold:
            if dc_x_start <= x_start and x_end <= dc_x_end:
                return "DC"
            elif trx_x_start <= x_start and x_end <= trx_x_end:
                return "Transaction Date"
            elif value_x_start <= x_start and x_end <= value_x_end:
                return "Value Date"
            elif description_x_start <= x_start and x_end <= description_x_end:
                return "Description"
            elif reference_x_start <= x_start and x_end <= reference_x_end:
                return "Reference"
            elif debit_x_start <= x_start and x_end <= debit_x_end:
                return "Debit"
            elif credit_x_start <= x_start and x_end <= credit_x_end:
                return "Credit"
            elif saldo_x_start <= x_start and x_end <= saldo_x_end:
                return "Saldo"
        return "Other"
    

    def _get_y_start(self, coords):
        try:
            result = self._extract_coordinates_full(coords)
            if result is not None:
                return result[0][1]
            return float('nan')
        except Exception as e:
            raise e
        

    def _get_x_start(self, coords):
        try:
            result = self._extract_coordinates_full(coords)
            if result is not None:
                return result[0][0]
            return float('nan')
        except Exception as e:
            raise e
    

    def _categorize_by_date_time(self, df, category='Transaction Date', y_start_threshold=0.005):
        try:
            df['y_start'] = df['word_geometry'].apply(self._get_y_start)
            df['x_start'] = df['word_geometry'].apply(self._get_x_start)

            filtered_df = df[df['category'] == category].copy()

            filtered_df.dropna(subset=['y_start'], inplace=True)

            if filtered_df.empty:
                print("No valid data to categorize. Returning original DataFrame.")
                return df

            filtered_df.sort_values(by=['page_idx', 'y_start'], inplace=True)

            current_row_count = 1
            current_page_idx = round(filtered_df.iloc[0]['page_idx'], 2)
            current_y_start = round(filtered_df.iloc[0]['y_start'], 2)
            row_counts = [current_row_count]

            for idx in range(1, len(filtered_df)):
                if filtered_df.iloc[idx]['page_idx'] != current_page_idx:
                    current_row_count = 1
                    current_page_idx = filtered_df.iloc[idx]['page_idx']
                elif filtered_df.iloc[idx]['y_start'] - current_y_start >= y_start_threshold:
                    current_row_count += 1

                current_y_start = filtered_df.iloc[idx]['y_start']
                row_counts.append(current_row_count)

            filtered_df['row_count'] = row_counts
            final_df = df.merge(filtered_df['row_count'], left_index=True, right_index=True, how='left')

            return final_df
        except Exception as e: 
            raise e


    def _propagate_row_count(self, df):
        try:
            dt_df = df[df['category'] == 'Transaction Date'].copy()
            dt_df.sort_values(by=['page_idx', 'y_start'], inplace=True)
            dt_df['next_y_start'] = dt_df.groupby('page_idx')['y_start'].shift(-1)
            for idx, row in df.iterrows():
                if row['category'] in ['Other', 'Transaction Date']:
                    continue
                boundaries = dt_df[dt_df['page_idx'] == row['page_idx']]
                for _, boundary in boundaries.iterrows():
                    if boundary['y_start'] <= row['y_start'] and (pd.isna(boundary['next_y_start']) or row['y_start'] < boundary['next_y_start']):
                        df.at[idx, 'row_count'] = boundary['row_count']
                        break  
            return df
        
        except Exception as e:
            raise e
    

    def _concatenate_words(self, group):
        return ' '.join(group['word_value'])

    def _concatenate_and_min(self, group):
        average_confidence = group['word_confidence'].min()
        return average_confidence
        
    
    def _get_df(self, df_flexcoord_04):
        try:
            df_flexcoord_04['y_start'] = round(df_flexcoord_04['y_start'], 2)
            df_flexcoord_04['x_start'] = round(df_flexcoord_04['x_start'], 2)
            df_flexcoord_05 = df_flexcoord_04.sort_values(by=['page_idx', 'row_count', 'y_start', 'x_start'])
            df_flexcoord_06 = df_flexcoord_05.groupby(['page_idx', 'row_count', 'category']).apply(self._concatenate_words).reset_index(name='concatenate_value')
            df_flexcoord_07 = df_flexcoord_05.groupby(['page_idx','row_count', 'category']).apply(self._concatenate_and_min).reset_index(name='min_confidence')
            df_combined = pd.merge(df_flexcoord_06, df_flexcoord_07, on=['page_idx', 'row_count', 'category'])
            return df_combined
        
        except Exception as e:
            raise e
        
    
    def _convert_to_iso_8601(self, date_string):
        date_formats = [
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y %H.%M.%S",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%b-%Y", 
            "%Y%m%d",
        ]
        try:  
            for date_format in date_formats:
                try:
                    datetime_obj = datetime.strptime(date_string, date_format)
                    return datetime_obj.strftime("%Y-%m-%dT%H:%M"), False
                except ValueError:
                    continue

            return date_string, False
        except Exception as e:
            raise e
    

    def _clean_and_check_double(self, value):
        try:
            cleaned_value = re.sub(r'[^\d.,]', '', value)
            cleaned_value = cleaned_value.replace(',', '.')

            if cleaned_value.count('.') > 1:
                parts = cleaned_value.rsplit('.', 1)
                integer_part = parts[0].replace('.', '')
                decimal_part = parts[1]
                cleaned_value = f"{integer_part}.{decimal_part}"
            
            if '.' in cleaned_value:
                integer_part, decimal_part = cleaned_value.split('.', 1)
                decimal_part = decimal_part.ljust(2, '0')[:2]
                cleaned_value = f"{integer_part}.{decimal_part}"
            else:
                cleaned_value += '.00'
                
            number = float(cleaned_value)

            return number, False

        except ValueError as e:
            print(f"Error: {e}")
            return 0.00, True
        
        
    def _convert_df_to_json(self, df_combined, tolerance=1e-2):
        try:
            output_json = []
            row_counter = 0
            prev_page_idx_row_count = (None, None)
            prev_balance = None  # To track the previous balance for the 'balance' check
            balance_faulty = False

            # Mapping for the JSON structure
            category_map = {
                'Transaction Date': 'datetime',
                'Value Date': 'valuedate',
                'Description': 'description',
                'Reference': 'reference',
                'Debit': 'debit',
                'Credit': 'credit',
                'Saldo': 'balance'
            }

            # Iterate over the DataFrame grouped by page_idx and row_count
            for (page_idx, row_count), group in df_combined.groupby(['page_idx', 'row_count']):
                if row_counter == 0 or (page_idx, row_count) != prev_page_idx_row_count:
                    row_counter += 1

                prev_page_idx_row_count = (page_idx, row_count)
                json_record = {"id": row_counter}
                debit_value = 0
                credit_value = 0

                for _, row in group.iterrows():
                    category_key = category_map.get(row['category'])
                    if category_key:
                        value = row['concatenate_value']
                        confidence = round(row['min_confidence'], 5)
                        faulty = False

                        if category_key in ['debit', 'credit', 'balance']:
                            value, faulty = self._clean_and_check_double(value)
                            if not faulty:
                                if category_key == 'debit':
                                    debit_value = value
                                elif category_key == 'credit':
                                    credit_value = value
                                elif category_key == 'balance':
                                    if prev_balance is None:
                                        faulty = False
                                    else:
                                        if isinstance(prev_balance, str):
                                            prev_balance, faulty = self._clean_and_check_double(prev_balance)
                                        if not faulty:
                                            expected_balance = prev_balance - debit_value + credit_value
                                            if not math.isclose(value, expected_balance, abs_tol=tolerance):
                                                faulty = False
                                            else:
                                                faulty = False
                                    balance_faulty = faulty

                        elif category_key in ['datetime', 'valuedate']:
                            value, faulty = self._convert_to_iso_8601(value)

                        elif category_key in ['description', 'reference']:
                            if not isinstance(value, str):
                                faulty = False

                        json_record[category_key] = {
                            "value": value,
                            "confidence": confidence,
                            "faulty": faulty
                        }

                # Check for missing keys and add dummy content - new code
                for key in category_map.values():
                    if key not in json_record:
                        json_record[key] = {
                            "value": "",
                            "confidence": 1,
                            "faulty": False
                        }

                if 'balance' in json_record and not balance_faulty:
                    prev_balance = json_record['balance']['value']
                else:
                    prev_balance = None

                output_json.append(json_record)

            transactions = {
                "transactions": output_json
            }
            return transactions
        
        except Exception as e:
            raise e

    def extract(self):
        try:
            df_json = self._json_to_dataframe(self.json_result)
            masterParameter_df = self._load_md()
            parameters = self._check_and_return_all_pages(df_json, masterParameter_df)
            df_flexcoord_01 = df_json.copy()
            df_flexcoord_01['coordinates'] = df_flexcoord_01['word_geometry'].apply(self._extract_coordinates_full)
            global_y_end_q3, global_keyword_coords, x_start_counter, x_end_counter, column_modes, column_common_y_start, column_common_y_end = self._calculate_and_print_statistics(df_flexcoord_01, parameters)
            df_flexcoord_02 = df_flexcoord_01.copy()
            df_flexcoord_02['category'] = df_flexcoord_02.apply(lambda row: self._categorize_based_on_coordinates(row['coordinates'], row['page_idx'], column_modes, parameters, column_common_y_start, column_common_y_end), axis=1)
            df_flexcoord_03 = self._categorize_by_date_time(df_flexcoord_02)
            df_flexcoord_04 = self._propagate_row_count(df_flexcoord_03)
            df_combined = self._get_df(df_flexcoord_04)
            output_json = self._convert_df_to_json(df_combined)

            return output_json



        except Exception as e:
            print(f"Error: {e}")
            flash("An error occurred during the extraction process.", "danger")
            return
            