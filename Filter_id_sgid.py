#!/usr/bin/env  python
# coding:utf8

import re

"""
A = '0<id<5119'
B = '5120<id<10239'
C = '10240<id<12031'
D = '12032<id<20479'
E = '20480<id<25599'
F = '25600<id<30719'
G = '30720<id<40959'
H = '40960<id<65536'
"""

def read_file(filename):
    """
    读取原始文件并通过正则匹配数据
    :param filename:
    :return:
    """
    with open(filename) as fo1:
        for lines in fo1.readlines():
            if lines:
                #rec_list.append(lines)
                id_A = re.findall(re_A_id, lines)
                sgid_A = re.findall(re_A_sgid, lines)
                if sgid_A:
                    sgid = int(sgid_A[0])
                    print(sgid)
                    if sgid<0 or sgid>5119:
                        with open('A_illegal_conf.xml', 'a+') as f0:
                            f0.write(lines)
                            print(lines)
                    elif 0<=sgid<=5119:
                        with open('A_legal_conf.xml', 'a+') as f0:
                            f0.write(lines)
                            print(lines)
                    else:
                        with open('A_legal_conf.xml', 'a+') as f0:
                            f0.write(lines)
                            print(lines)
                elif id_A:
                    id = int(id_A[0])
                    print(id)
                    if id<0 or id>5119:
                        with open('A_illegal_conf.xml', 'a+') as f1:
                            f1.write(lines)
                            print(lines)
                    else:
                        with open('A_legal_conf.xml', 'a+') as f1:
                            f1.write(lines)
                            print(lines)
                else:
                    with open('A_legal_conf.xml', 'a+') as f2:
                        f2.write(lines)
                        print(lines)


if __name__ == '__main__':
    rec_list = []  # 用于记录每次读取信息的列表
    re_A_id = r'.*id="(\d{1,5})".*'  # 匹配id号的正则
    re_A_sgid = r'servicegroupId="(\d{1,5})"'  # 匹配sgid的正则
    filepath = r'E:\jianshu_spider\DNP\A_transport.conf.xml'  # 目标文件
    fn = filepath
    read_file(fn)
