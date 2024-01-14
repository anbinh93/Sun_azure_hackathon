import os
import sys
import shutil
import traceback
import pandas as pd
sys.path.append(os.getcwd())


def create_temp_csv_file(headers: list, data: list, filename: str):
    try:
        shutil.rmtree('.temp/temp_queries', ignore_errors=True)
        os.makedirs('.temp', exist_ok=True)
        os.makedirs('.temp/temp_queries', exist_ok=True)

        df = pd.DataFrame(data, columns=headers)
        df.to_csv(f'.temp/temp_queries/{filename}', index=False)
        return f'.temp/temp_queries/{filename}'

    except Exception as e:
        print(traceback.format_exc())
        return None
