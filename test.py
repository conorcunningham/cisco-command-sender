from src.excel_processor import ExcelProcessor

excel = ExcelProcessor("data_files/Switchfinder_poc.xlsx")
hosts = excel.run_sheet_read()

print(hosts)
