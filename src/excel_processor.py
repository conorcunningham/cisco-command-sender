import pandas as pd
from collections import namedtuple

Columns = namedtuple('column', 'hostname, version, ip')


class ExcelProcessor:

    def __init__(self, spreadsheet, username, password):
        self.spreadsheet = spreadsheet
        self.username = username
        self.password = password
        # self.sheet = sheet_name
        self.named_tuple = Columns
        self.data = self.read_sheet()

    def read_sheet(self):
        return pd.read_excel(self.spreadsheet)

    def run_sheet_read(self):
        hosts = []
        for index, row in self.data.iterrows():
            data: Columns = self.parse_case_sheet(self.named_tuple, row)
            if not self.is_row_sane(data):
                continue
            hosts.append(self.parse_hosts_for_netmiko(data.ip))
        return hosts

    def parse_hosts_for_netmiko(self, host, device_type='cisco_ios'):
        host = {
            'device_type': device_type,
            'host': host,
            'username': self.username,
            'password': self.password,
        }
        return host

    @staticmethod
    def is_row_sane(row):
        if row.hostname is None or row.ip is None:
            return False
        if '.ngbutikk.net' not in row.hostname:
            return False
        return True

    @staticmethod
    def clean_data(row):
        for key, value in row.items():
            if isinstance(value, str):
                value = value.strip()
            if pd.isna(value) or value == "" or value == "null":
                row[key] = None
        return row

    def parse_case_sheet(self, obj, row):
        return obj(**self.clean_data(row))
