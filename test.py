from src.utils.csv_builder import create_temp_csv_file


# Now convert the query result to a csv file
headers = ["Semester",
           "School/Institute Code",
           "Class Code",
           "Accompanying class code",
           "Subject Code",
           "Subject Name in Vietnamese",
           "Subject Name in English",
           "Number of credit",
           "Weekday",
           "Time",
           "Start Period",
           "End Period",
           "Session",
           "Week",
           "Phòng",
           "Need Experiment Class",
           "Current signed-up student",
           "Maximum number of student",
           "Status",
           "Class type",
           "Faculty Type"]

filename = 'current_query.csv'

ad = [(20222, 'KSPKT', 142873, 142873.0, 'ED2030', 'Thiết kế dạy học', 'Instructional Design', 3, 5.0, '0920-1145', 4.0, 6.0, 'Sáng', '25-32,34-42', 'TC-212', 'TN',
       50.0, 80, 'Mở ĐK', 'LT+BT', 'CT CHUẨN'), (20222, 'KSPKT', 731696, 731696.0, 'ED2030', 'Thiết kế dạy học', 'Instructional Design', 3, 5.0, '1300-1500', 1300.0, 1500.0, 'Chiều', '36-41', 'D3-5-303', None, 18.0, 18, 'Mở ĐK', 'TN', 'CT CHUẨN'), (20222, 'KSPKT', 731697, 731697.0, 'ED2030', 'Thiết kế dạy học', 'Instructional Design', 3, 5.0, '1500-1700', 1500.0, 1700.0, 'Chiều', '36-41', 'D3-5-303', None, 14.0, 15, 'Mở ĐK', 'TN', 'CT CHUẨN'), (20222, 'KSPKT', 731698, 731698.0, 'ED2030', 'Thiết kế dạy học', 'Instructional Design', 3, 4.0, '1300-1500', 1300.0, 1500.0, 'Chiều', '36-41', 'D3-5-303', None, 6.0, 15, 'Mở ĐK', 'TN', 'CT CHUẨN'),
      (20222, 'KSPKT', 731699, 731699.0, 'ED2030', 'Thiết kế dạy học', 'Instructional Design', 3, 4.0, '1500-1700', 1500.0, 1700.0, 'Chiều', '36-41', 'D3-5-303', None, 11.0, 18, 'Mở ĐK', 'TN', 'CT CHUẨN')]

csv_path = create_temp_csv_file(headers, ad, filename)
