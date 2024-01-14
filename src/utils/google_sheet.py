import os
import sys
sys.path.append(os.getcwd())  # NOQA

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    secret_file = os.path.join('config/secret_key.json')
except:
    print('Please put your secret_key.json file in the config folder')

creds = ServiceAccountCredentials.from_json_keyfile_name(
    filename=secret_file, scopes=scopes)

files = gspread.authorize(creds)


def read_data() -> pd.DataFrame:
    """
    Read the data from the spreadsheet 'reservation' and return a pandas DataFrame

    Sample data:
    | STT | Họ và Tên | Số điện thoại | Môn học đề xuất mở thêm (Dự kiến) | Mã môn học | Lí do mở thêm | 
    | ---- | ----- | -------- | ---- | ---- | ---------------- | ----- | ------- |

    Returns:
        pd.DataFrame: A pandas DataFrame
    """
    # Open the workbook
    workbook = files.open('Lịch hẹn khách hàng An Phát')

    # Get all sheets
    sheet = workbook.sheet1

    # Using pandas to read the data
    data = pd.DataFrame(sheet.get_all_records())

    return data


def update_data(data: dict):
    """
    Update the data to the spreadsheet 'reservation'

    Args:
        data (dict): A dictionary of data to update

        Example:
        {
            'STT': '1',
            'Họ và Tên': 'Nguyễn Văn A',
            'Số điện thoại': '0123456789',
            'Môn học đề xuất mở thêm (Dự kiến)': 'Giải tích', 
            'Mã môn học': 'MI1001', 
            'Lí do mở thêm': 'Đi chơi'
        }
    """
    # Open the workbook
    workbook = files.open('Đăng ký xin mở thêm lớp')

    # Get all sheets
    sheet = workbook.sheet1

    # Update the data
    sheet.append_row(list(data.values()))

    # Call the sheet to sort the data by the column 'date' in asc order except the first row
    sheet.sort((1, 'asc'), range='A2:G100000')


if __name__ == '__main__':
    print(read_data())

    # Sample data
    data = {
        'ID': '1',
        'Họ và Tên': 'Nguyễn Văn A',
        'Số điện thoại': '0123456789',
        'Môn học đề xuất mở thêm (Dự kiến)': 'Giải tích',
        'Mã môn học': 'MI1001',
        'Lí do mở thêm': 'Đi chơi'
    }

    update_data(data)
