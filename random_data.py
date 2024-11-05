from random import randint
from collections import deque
from process import Process
from operation import random_operation

def data_gen(n: int=0, start: int=0, quantum: float=1.0):
    q = deque()

    for i in range(start, start+n):
        op, res = random_operation()
        p = Process(i, randint(4, 9), op, res, quantum, randint(5, 26))
        q.append(p)

    return q, i+1
