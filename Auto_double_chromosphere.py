#!/usr/bin/env  python
# coding:utf8

import array
import random

def mp_sort():
    r_ran = [random.randint(1, 33) for _ in range(6)]  #随机生成6个1到33的数
    b_ran = [random.randint(1, 16) for _ in range(1)]
#    a_ran = b_ran + r_ran
    arr = array.array('i', r_ran)    #生成一个数组
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
            print("\nYour Lucky Number Is:\n")
            print(so1ist + b_ran)
        else:
            mp_sort()
    except Exception as e:
        print("Pleas Try Again!")
        print(e)


if __name__ == '__main__':
    mp_sort()


 #   print(arr.tolist() + r_ran)
 #   print(r_ran)
# print(arr.itemsize)
# print(arr.buffer_info())
# print(arr.count(1))
# print(arr.index(2))
