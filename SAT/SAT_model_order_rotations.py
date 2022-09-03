from z3 import *
from itertools import combinations
import time
from math import sqrt
from math import ceil

import re
import sys
import glob
import json
import datetime
import os
import os.path as pt
import argparse

VARIABLE_RE = re.compile(r'p[xy]_(\d+)_(\d+)')


##def at_least_one(bool_vars):
##    return Or(bool_vars)
##
###SEQUENTIAL ENCODING:
##def at_most_one(bool_vars, name):
##    if len(bool_vars)==1:
##        return True
##    constraints = []
##    n = len(bool_vars)
##    s = [Bool(f's_{name}_{i}') for i in range(n - 1)]
##    constraints.append(Or(Not(bool_vars[0]), s[0]))
##    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
##    for i in range(1, n - 1):
##        constraints.append(Or(Not(bool_vars[i]), s[i]))
##        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
##        constraints.append(Or(Not(s[i-1]), s[i]))
##    return And(constraints)
##
##def equal_vars(var1,var2): #boolean variables are equal iff they are equivalent
##    return And(Or(Not(var1),var2),Or(Not(var2),var1))
##
##def lex_order(listvar1,listvar2,name, func = sqrt):  #lex_order_CSE
##    constraints=[]
##    n = len(listvar1)
##    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
##    constraints.append(Or(Not(listvar2[0]),listvar1[0])) #lex_geq
##    #constraints.append(Or(Not(listvar1[0]),listvar2[0]))   #lex_lesseq
##    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
##    for i in range(int(func(n)) - 2):
##        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
##    for i in range(int(func(n)) - 1):
##        constraints.append(Or(Not(s[i]),(Or(Not(listvar2[i+1]),listvar1[i+1])))) #lex_geq
##        #constraints.append(Or(Not(s[i]),(Or(Not(listvar1[i+1]),listvar2[i+1])))) #lex_lesseq
##    return And(constraints)
##        
##
##def exactly_one(bool_vars, name):
##    return And(at_least_one(bool_vars), at_most_one(bool_vars, name))
####################################################################################################

#flatten list:
##def flatten(l):
##    return [item for sublist in l for item in sublist]
####################################################################################################


def sat_vlsi(width, nofrectangles, dimensions, min_height): #dimensions è una lista di coppie di coordinate [x,y]
    
    s = Solver()

    PX=[[Bool(f'px_{k}_{i}') for i in range(width-min(dimensions[k])+1)] for k in range(nofrectangles)]      #The x coordinate of circuit k is <= i
    PY=[[Bool(f'py_{k}_{j}') for j in range(min_height-min(dimensions[k])+1)] for k in range(nofrectangles)]  #The y coordinate of circuit k is <= i 
    LR=[[Bool(f'lr_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]                #LR[k][k1] if k is at the left of k1
    UD=[[Bool(f'ud_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]                #UD[k][k1] if k is under k1
    R=[Bool(f'r_{k}') for k in range(nofrectangles)]                                                        #R[k] iff k is rotated
      
    starting_time=time.time()
    print('generating solver:')

    for k in range(nofrectangles):  #Order encoding on the PX, PY variables
        for i in range(width-min(dimensions[k])): 
            s.add(Or(Not(PX[k][i]),PX[k][i+1]))
        for j in range(min_height-min(dimensions[k])):
            s.add(Or(Not(PY[k][j]),PY[k][j+1]))

    for k in range(nofrectangles):  #each circuit must have an origin that makes it remain inside the outer rectangle
        s.add(Or(R[k],PX[k][width - dimensions[k][0]]))           #if k is not rotated, its origin has x coordinate <= W-w(k)
        s.add(Or(Not(R[k]), PX[k][width-dimensions[k][1]]))         #if k is rotated, its origin has  coordinate <= W-h(k)
        s.add(Or(R[k],PY[k][max(0, min_height - dimensions[k][1])]))        #Same for the y coordinate. The max is needed to avoid acessing PY[k] with negative indices (this may happen if
        s.add(Or(Not(R[k]),PY[k][max(0,min_height - dimensions[k][0])]))    #the height 

    for k in range(nofrectangles):  #no overlap: each circuit must be either to the left, to the right, below or above each other circuit
        for k1 in range(k+1, nofrectangles):
            s.add(Or(LR[k][k1],LR[k1][k],UD[k][k1],UD[k1][k]))

    for k in range(nofrectangles):  #Square circuits shall not be rotated
        if dimensions[k][0] == dimensions[k][1]:
            s.add(Not(R[k]))

    for k in range(nofrectangles):  
        for k1 in range(k+1, nofrectangles):
            for i in range(-max(dimensions[k]+dimensions[k1]), width-min(dimensions[k]+dimensions[k1])): #if k is on the left of k1 and PX[k]>i, then PX[k1]>i+width(k)
                A=[]
                AR=[]
                B=[]    
                BR=[]
                A.append(Not(LR[k][k1]))
                A.append(R[k])
                AR.append(Not(LR[k][k1]))
                AR.append(Not(R[k]))
                B.append(Not(LR[k1][k]))
                B.append(R[k1])
                BR.append(Not(LR[k1][k]))
                BR.append(Not(R[k1]))
                if i>=0:
                    if i <= width - min(dimensions[k]):
                        A.append(PX[k][i])
                        AR.append(PX[k][i])
                    if i <= width - min(dimensions[k1]):
                        B.append(PX[k1][i])
                        BR.append(PX[k1][i])
                        
                if 0 <= i+dimensions[k][0] <= width - min(dimensions[k1]):                    
                    A.append(Not(PX[k1][i+dimensions[k][0]]))
                if 0 <= i+dimensions[k][1] <= width - min(dimensions[k1]):
                    AR.append(Not(PX[k1][i+dimensions[k][1]]))
                    
                if 0 <= i+dimensions[k1][0] <= width- min(dimensions[k]):
                    B.append(Not(PX[k][i+dimensions[k1][0]]))
                if 0 <= i+dimensions[k1][1] <= width - min(dimensions[k]):
                    BR.append(Not(PX[k][i+dimensions[k1][1]]))
                
                if len(A) > 2:      #This means that there aren't only Not(LR) and R (or Not(R)) variables in A, AR, B, and BR.
                    s.add(Or(A))
                if len(AR) > 2:
                    s.add(Or(AR))                
                if len(B) > 2:
                    s.add(Or(B))
                if len(BR) > 2:
                    s.add(Or(BR))
                    
            for j in range(-max(dimensions[k]+dimensions[k1]), min_height - min(dimensions[k]+dimensions[k1])):  #if k is under k1 and PX[k]>i, then PY[k1]>i+height(k)
                C=[]
                CR=[]
                D=[]    
                DR=[]
                C.append(Not(UD[k][k1]))
                C.append(R[k])
                CR.append(Not(UD[k][k1]))
                CR.append(Not(R[k]))
                D.append(Not(UD[k1][k]))
                D.append(R[k1])
                DR.append(Not(UD[k1][k]))
                DR.append(Not(R[k1]))
                if j >= 0:
                    if j <= min_height - min(dimensions[k]):
                        C.append(PY[k][j])
                        CR.append(PY[k][j])
                    if j <= min_height - min(dimensions[k1]):
                        D.append(PY[k1][j])
                        DR.append(PY[k1][j])
                        
                if 0 <= j+dimensions[k][1] <= min_height - min(dimensions[k1]): #The same as above, for the vertical direction
                    C.append(Not(PY[k1][j+dimensions[k][1]]))                    
                if 0 <= j+dimensions[k][0] <= min_height - min(dimensions[k1]):
                    CR.append(Not(PY[k1][j+dimensions[k][0]]))
                    
                if 0 <= j+dimensions[k1][1] <= min_height - min(dimensions[k]):
                    D.append(Not(PY[k][j+dimensions[k1][1]]))
                if 0 <= j+dimensions[k1][0] <= min_height - min(dimensions[k]):
                    DR.append(Not(PY[k][j+dimensions[k1][0]]))

                #These are put in order to avoid imposing only Not(UD[k][k1]) and Not(UD[k1][k])
                if len(C) > 2:      #This means that there aren't only Not(LR) and R (or Not(R)) variables in A, AR, B, and BR.
                    s.add(Or(C))
                if len(CR) > 2:
                    s.add(Or(CR))                
                if len(D) > 2:
                    s.add(Or(D))
                if len(DR) > 2:
                    s.add(Or(DR))
                
                    
    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')

    #TIMEOUT:
    s.set('timeout', 300000)

    check_result = s.check()

    # If satisfiable
    if check_result == sat:
        
        m = s.model()

        solutions_x=[[PX[k][i] for i in range(width-min(dimensions[k])+1) if m.evaluate(PX[k][i]) == True][0] for k in range(nofrectangles)]
        solutions_y=[[PY[k][i] for i in range(min_height - min(dimensions[k]) +1) if m.evaluate(PY[k][i]) == True][0] for k in range(nofrectangles)]
        #print(m)
        return (min_height, adapt_solution(solutions_x, solutions_y, R),
                s.statistics(), end_time - starting_time)

    # If unsatisfiable
    return None


def adapt_solution(solutions_x, solutions_y, R) -> list[str]:
    """Map solutions in a format viable for the exec all script."""
    new_solutions = []
    for sx, sy in zip(map(str, solutions_x), map(str, solutions_y)):
        # SHOULD always match
        kx, x = VARIABLE_RE.match(sx).groups()
        ky, y = VARIABLE_RE.match(sy).groups()

        if kx != ky:
            raise Exception('Rectangle mismatch, contact me (mistri)')

        new_solutions.append(f'x_{x}_{y}_{kx}')

    return new_solutions



def linear_optimization(width, nofrectangles, dimensions, max_height):
    
    total_area = 0
    
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
        
    min_height = max(ceil(total_area / width), max([min(dimensions[i]) for i in range(nofrectangles)]))        #If total area is not divisible by width we round up

    while True:
        print('Trying height =', min_height)
        testsol=sat_vlsi(width, nofrectangles, dimensions, min_height)
        print(testsol[2])
        if testsol != None:
            return testsol
        min_height += 1


def binary_optimization(width, nofrectangles, dimensions, max_height):
    
    total_area = 0
    
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
        
    min_height = max(ceil(total_area / width), max([min(dimensions[i]) for i in range(nofrectangles)]))
    #max_height = sum([dimensions[k][1] for k in range(nofrectangles)])

    if min_height == max_height:
        return sat_vlsi(width,nofrectangles, dimensions, min_height)

    while min_height != max_height:
        print('Trying height =', (min_height + max_height) // 2)
        testsol = sat_vlsi(width,nofrectangles, dimensions, (min_height + max_height) // 2)
        #print(A[2])
        if testsol == None:
            min_height = ((min_height + max_height) // 2) + 1
        else:
            testsol1 = testsol   #testsol1 keeps track of the last correct solution so it can be returned without recomputing sat_vlsi if in the last iteration A == None
            max_height = (min_height + max_height) // 2

    return testsol1


    
        
    


        
    
    

#FOR TESTING PURPOSE:
#Questa è l'istanza 30
#width=37
#nofrectangles=27
#dimensions=[[3,3],[3,4],[3,5],[3,6],[3,7],[3,8],[3,9],[3,11],[3,12],[3,13],[3,14],[3,17],[3,18],[3,21],[4,3],[4,4],[4,5],[4,6],[4,10],[4,22],[4,24],[5,3],[5,4],[5,6],[5,10],[5,14],[12,37]]
##X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]

# DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')

# with open(sorted(
#             glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')))[-1]) as fin:
#     instance_data = json.load(fin)

#     sat_vlsi(instance_data['width'], instance_data['n'],
#                                    instance_data['circuits'])
width = 8
nofrectangles=4
dimensions=[[3,3],[5,3],[3,5],[5,5]]
        
print(sat_vlsi(width, nofrectangles,dimensions, 8))







