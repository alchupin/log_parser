#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import gzip
import json
import os
import re
import sys
from statistics import median
from typing import Iterator

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config_format = """
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
"""
config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def find_last_log(path: str) -> str:
    """
    Возвращает последний файл (по дате в названии файла) в указанной директории
    :param path: путь к директории с лог-файлами, строка
    :return: имя файла, строка
    """
    if not os.path.exists(path):
        pass
    found_file = ''
    for file in os.listdir(path):
        match = (re.search(r'nginx-access-ui.log-[0-9]{8}', file))
        if match:
            match = str(match.group())
            if not found_file:
                found_file = file
            match_found = str(re.search(r'nginx-access-ui.log-[0-9]{8}', found_file).group())
            if datetime.datetime.strptime(match.split('-')[-1], '%Y%m%d') > datetime.datetime.strptime(match_found.split('-')[-1], '%Y%m%d'):
                found_file = file
    return found_file


def get_data(file: str) -> Iterator[tuple]:
    with gzip.open(file, 'rt') if file.endswith('.gz') else open(file) as f:
        for line in f:
            splited_line = line.split(' ')
            yield splited_line[7], float(splited_line[-1])


def form_statistic(*args):
    """
    В
    """
    urls = {}
    total_values = {
        'total_urls_appearance': 0,
        'total_request_time': 0}
    for data in args:
        for url, time in data:
            if url not in urls:
                urls[url] = {
                    'url_appearance_total': 1,
                    'url_request_time_total': time,
                    'url_request_time_list': [time],
                    'request_time_average': time
                }
            else:
                urls[url]['url_appearance_total'] += 1
                urls[url]['url_request_time_total'] += time
                urls[url]['url_request_time_list'].append(time)
            total_values['total_urls_appearance'] += 1
            total_values['total_request_time'] += time
    result_list = []

    for url in urls:
        urls[url]['request_time_avg'] = urls[url]['url_request_time_total'] / urls[url]['url_appearance_total']
        urls[url]['request_time_med'] = median(urls[url]['url_request_time_list'])
        urls[url]['request_time_max'] = max(urls[url]['url_request_time_list'])
        urls[url]['total_urls_appearance'] = total_values['total_urls_appearance']
        urls[url]['urls_appearance_proc'] = urls[url]['url_appearance_total'] / total_values['total_urls_appearance'] *100
        urls[url]['request_time_proc'] = urls[url]['url_request_time_total'] / total_values['total_request_time'] * 100

        url_dict = {
            'url': url,
            'count': urls[url]['url_appearance_total'],
            'count_proc': round(urls[url]['urls_appearance_proc'], 3),
            'time_avg': round(urls[url]['request_time_avg'], 3),
            'time_max': round(urls[url]['request_time_max'], 3),
            'time_med': round(urls[url]['request_time_med'], 3),
            'time_proc': round(urls[url]['request_time_proc'], 3),
            'time_sum': round(urls[url]['url_request_time_total'], 3)
        }
        result_list.append(url_dict)

    with open('report.html', 'r') as f_report:
        for line in f_report:
            with open('report-result.html', 'a') as f_mod:
                if '$table_json' in line:
                    line = line.replace('$table_json', json.dumps(result_list))
                f_mod.write(line)


def main():
    parser = argparse.ArgumentParser(description='Скрипт анализирует последний лог-файл')
    parser.add_argument("-c", "--config", action="store", help=f"полный путь до конфигурационного файла. Файл должен иметь следующий формат:{config_format}", default="/var/log/parse_log_config", required=False)
    args = parser.parse_args()
    path = args.config
    # if os.path.exists(path):

    print(find_last_log(path))

    if not find_last_log(path):
        print('Отсутствуют лог-файлы для обработки')
        sys.exit(0)
    else:
        print(find_last_log(path))
    # form_statistic(get_data((find_last_log(config['LOG_DIR']))))


if __name__ == "__main__":
    main()
