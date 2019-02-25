#!/usr/bin/env  python
# coding:utf8

import array
import random


def red_ball():
    r_ran = [random.randint(1, 35) for _ in range(6)]  #随机生成6个1到33的数
    arr = array.array('i', r_ran)  # 生成一个数组
    for i in range(len(arr)):         #外层循环控制次数
        for j in range(len(arr)-1):   #内层循环控制比较次数
            if arr[j] > arr[j+1]:
                tmp = arr[j]
                arr[j] = arr[j+1]    #如果前一个数大于后一个数则互换两个数数值
                arr[j+1] = tmp
    so1ist = arr.tolist()  #将数组转换成列表
    soset = set(so1ist)    #将列表转换成元组
    try:
        if len(so1ist) == len(soset):
            if len(so1ist) == len(soset):
                print("\nYour Lucky Number Is:\n")
                print('前区')
                for qq in so1ist:
                    print(' %s' % qq, end='')
        else:
            red_ball()
    except Exception as e:
        print("Pleas Try Again!")
        print(e)


def blue_ball():
    b_ran = [random.randint(1, 12) for _ in range(2)]
    brr = array.array('i', b_ran)  # 生成一个数组
    for k in range(len(brr)):  # 外层循环控制次数
        for l in range(len(brr) - 1):  # 内层循环控制比较次数
            if brr[l] > brr[l + 1]:
                tmp1 = brr[k]
                brr[l] = brr[l + 1]  # 如果前一个数大于后一个数则互换两个数数值
                brr[l + 1] = tmp1
    so1ist1 = brr.tolist()  # 将数组转换成列表pmpm
    soset1 = set(so1ist1)  # 将列表转换成元组
    try:
        if len(so1ist1) == len(soset1):
            if len(so1ist1) == len(soset1):
                print('\n后区')
                for hq in so1ist1:
                    print(' %s' % hq, end='')
        else:
            blue_ball()
    except Exception as e:
        print("Pleas Try Again!")
        print(e)


if __name__ == '__main__':
    red_ball()
    blue_ball()


 #   print(arr.tolist() + r_ran)
 #   print(r_ran)
# print(arr.itemsize)
# print(arr.buffer_info())
# print(arr.count(1))
# print(arr.index(2))
