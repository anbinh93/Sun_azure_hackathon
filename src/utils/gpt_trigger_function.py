def build_filter_query(**kwargs):
    """
    This function will build the filter query for SQLite.

    Returns:
    The select query for SQLite. Must have all the columns in the schema.
    """

    range_value = {}

    query = 'SELECT * FROM laptop_detail_update\nWHERE 1=1\n'

    for key, value in kwargs.items():
        if key == 'content':
            continue
        if value is None:
            continue
        if isinstance(value, list):
            if key == 'disk_type':
                condition = f"AND lower({key}) LIKE '%{value}%'\n"
                query += condition
            elif key == 'cpu' or key == 'screen_resolution':
                condition = 'AND ('
                for v in value:
                    or_condition = f"lower({key}) LIKE '%{v}%' OR "
                    condition += or_condition
                # Remove the last OR
                condition = condition[:-3] + ')\n'
                query += condition
            else:
                condition = f'{key} IN ('
                if isinstance(value[0], str):
                    for v in value:
                        condition += f"'{v}',"
                else:  # float or int
                    for v in value:
                        condition += f"{v},"

                # Remove the last comma and add a closing bracket
                condition = condition[:-1] + ')'
                query += 'AND ' + condition + '\n'
        elif isinstance(value, str):
            condition = f"AND {key} = '{value}'\n"
            query += condition
        elif isinstance(value, int) or isinstance(value, float):
            if 'start' in key or 'end' in key:
                real_key = key.replace('start_', '').replace('end_', '')

                if real_key not in range_value:
                    range_value[real_key] = {}

                if 'start' in key:
                    range_value[real_key]['start'] = value
                else:
                    range_value[real_key]['end'] = value
            else:
                condition = f'AND {key} = {value}\n'
                query += condition

    # Add range value
    for key, val_range in range_value.items():
        start_val = val_range.get('start', None)
        end_val = val_range.get('end', None)

        if start_val and end_val:
            condition = f'AND {key} BETWEEN {start_val} AND {end_val}\n'
        elif start_val is None:
            condition = f'AND {key} <= {end_val}\n'
        elif end_val is None:
            condition = f'AND {key} >= {start_val}\n'
        else:
            continue

        query += condition

    return query
