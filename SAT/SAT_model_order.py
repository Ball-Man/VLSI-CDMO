from z3 import *
from itertools import combinations
import time
from math import sqrt

import re
import sys
import glob
import json
import datetime
import os
import os.path as pt
import argparse

VARIABLE_RE = re.compile(r'p[xy]_(\d+)_(\d+)')


def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one_np(bool_vars, name = ""):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

#SEQUENTIAL ENCODING:
def at_most_one(bool_vars, name):
    if len(bool_vars)==1:
        return True
    constraints = []
    n = len(bool_vars)
    s = [Bool(f's_{name}_{i}') for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0]))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
        constraints.append(Or(Not(s[i-1]), s[i]))
    return And(constraints)

def equal_vars(var1,var2): #boolean variables are equal iff they are equivalent
    return And(Or(Not(var1),var2),Or(Not(var2),var1))

def lex_order(listvar1,listvar2,name, func = sqrt):  #lex_order_CSE
    constraints=[]
    n = len(listvar1)           #Anche qui si può provare a prendere f(n)<n per alleggerire il numero di constraints
    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
    constraints.append(Or(Not(listvar2[0]),listvar1[0])) #lex_geq
    #constraints.append(Or(Not(listvar1[0]),listvar2[0]))   #lex_lesseq
    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
    #for i in range(n-2):   #ordine lessicografico completo
    for i in range(int(func(n)) - 2):
        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
    #for i in range(n-1):   #ordine lessicografico completo
    for i in range(int(func(n)) - 1):
        constraints.append(Or(Not(s[i]),(Or(Not(listvar2[i+1]),listvar1[i+1])))) #lex_geq
        #constraints.append(Or(Not(s[i]),(Or(Not(listvar1[i+1]),listvar2[i+1])))) #lex_lesseq
    return And(constraints)
        

def exactly_one(bool_vars, name):
    return And(at_least_one(bool_vars), at_most_one(bool_vars, name))
####################################################################################################

#flatten list:
def flatten(l):
    return [item for sublist in l for item in sublist]

def hperm(A,width,dimensions): #symmetries
    return [[[A[k][j][width - i - dimensions[k][0]] for i in range(len(A[k][j]))] for j in range(len(A[k]))] for k in range(len(A))]

def vperm(A,min_height,dimensions):
    return [[[A[k][min_height - j - dimensions[k][1]][i] for i in range(len(A[k][j]))] for j in range(len(A[k]))] for k in range(len(A))]
####################################################################################################


def sat_vlsi(width, nofrectangles, dimensions): #dimensions è una lista di coppie di coordinate [x,y]
    
    s = Solver()
    
    total_area = 0
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
    if total_area % width == 0:         #If total area is not divisible by width we round up
        min_height = max(total_area // width, max([dimensions[i][1] for i in range(nofrectangles)]))
    else:
        min_height = max(total_area // width + 1, max([dimensions[i][1] for i in range(nofrectangles)]))

    # min_height = 90
    
    #X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]
    #Voglio che X[k][j][i] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j

    PX=[[Bool(f'px_{k}_{i}') for i in range(width-dimensions[k][0] +1)] for k in range(nofrectangles)]       #pos. of x_k is <= i
    PY=[[Bool(f'py_{k}_{j}') for j in range(min_height-dimensions[k][1]+1)] for k in range(nofrectangles)]
    LR=[[Bool(f'lr_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]
    UD=[[Bool(f'ud_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]
      
    starting_time=time.time()
    print('generating solver:')

    for k in range(nofrectangles):  #Order encoding
        for i in range(width-dimensions[k][0]):
            s.add(Or(Not(PX[k][i]),PX[k][i+1]))
        for j in range(min_height-dimensions[k][1]):
            s.add(Or(Not(PY[k][j]),PY[k][j+1]))

    for k in range(nofrectangles):  #ogni rettangolo ha un'origine
        s.add(PX[k][width - dimensions[k][0]])
        s.add(PY[k][min_height - dimensions[k][1]])

    for k in range(nofrectangles):  #no overlap
        for k1 in range(k+1, nofrectangles):
            s.add(Or(LR[k][k1],LR[k1][k],UD[k][k1],UD[k1][k]))

    for k in range(nofrectangles):
        for k1 in range(k+1, nofrectangles):
            for i in range(-max(dimensions[k][0],dimensions[k1][0]), width-min(dimensions[k][0],dimensions[k1][0])):
                A=[]
                B=[]
                A.append(Not(LR[k][k1]))
                B.append(Not(LR[k1][k]))
                if i>=0:
                    if i <= width - dimensions[k][0]:
                        A.append(PX[k][i])
                    if i <= width - dimensions[k1][0]:
                        B.append(PX[k1][i])
                if 0 <= i+dimensions[k][0] <= width - dimensions[k1][0]:
                    #print(i+dimensions[k][0])
                    A.append(Not(PX[k1][i+dimensions[k][0]]))                
                if 0 <= i+dimensions[k1][0] <= width-dimensions[k][0]:
                    B.append(Not(PX[k][i+dimensions[k1][0]]))
                #print('A is',A)
                if len(A) > 1:
                    s.add(Or(A))
                #print('B is', B)
                if len(B) > 1:
                    s.add(Or(B))
            for j in range(-max(dimensions[k][1],dimensions[k1][1]), min_height - min(dimensions[k][1],dimensions[k1][1])):
                C=[]
                D=[]
                C.append(Not(UD[k][k1]))
                D.append(Not(UD[k1][k]))
                if j >= 0:
                    if j <= min_height - dimensions[k][1]:
                        C.append(PY[k][j])
                    if j <= min_height - dimensions[k1][1]:
                        D.append(PY[k1][j])
                if 0 <= j+dimensions[k][1] <= min_height - dimensions[k1][1]:
                    #print(j+dimensions[k][1])
                    C.append(Not(PY[k1][j+dimensions[k][1]]))
                if 0 <= j+dimensions[k1][1] <= min_height - dimensions[k][1]:
                    D.append(Not(PY[k][j+dimensions[k1][1]]))
                #print('C is', C)
                if len(C) > 1:
                    s.add(Or(C))
                #print('D is',D)
                if len(D) > 1:
                    s.add(Or(D))
                
                    
##                for j in range(min_height-dimensions[k][1]):
##                    s.add(Or(Not(LR[k][k1]),PX[k][i],Not(PX[k1][min(i+dimensions[k][0], width-dimensions[k1][0])])))
##                    s.add(Or(Not(UD[k][k1]),PY[k][j],Not(PY[k1][min(j+dimensions[k][1], min_height - dimensions[k1][1])])))
##            for i in range(width-dimensions[k1][0]):
##                for j in range(min_height-dimensions[k1][1]):
##                    s.add(Or(Not(LR[k1][k]),PX[k1][i],Not(PX[k][min(i+dimensions[k1][0], width-dimensions[k][0])])))
##                    s.add(Or(Not(UD[k1][k]),PY[k1][j],Not(PY[k][min(j+dimensions[k1][1], min_height - dimensions[k][1])])))

    
                        
                
                    
    
    #constraints no-overlap:
##    for k in range(nofrectangles):
##        for i in range(width - dimensions[k][0] + 1):
##            for j in range(min_height - dimensions[k][1] + 1): 
##                for k1 in range(k+1, nofrectangles): #prima era range(nofrectangles), con if k != k1, ma così si tolgono un po' di implied constraints (modello è più piccolo)
##                    #if k != k1:
##                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
##                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], min_height - dimensions[k1][1] +1)):     #si dovrebbe capire graficamente                                                                                       
##                                s.add(Or(Not(X[k][j][i]), Not(X[k1][j1][i1])))

##    for k in range(nofrectangles-1):
##        for i in range(width - dimensions[k][0] + 1):
##            for j in range(min_height - dimensions[k][1] + 1):
##                for k1 in range(k+1, nofrectangles): #prima era range(nofrectangles), con if k != k1, ma così si tolgono un po' di implied constraints (modello è più piccolo)
##                    #if k != k1:
##                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
##                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], min_height - dimensions[k1][1] +1)):     #si dovrebbe capire graficamente                                                                                       
##                                s.add(Or(Not(X[k][j][i]), Not(X[k1][j1][i1])))

    #horizontal and vertical symmetry breaking constraint:
##    s.add(lex_order(flatten(flatten(X)), flatten(flatten(hperm(X,width,dimensions)))))
##    s.add(lex_order(flatten(flatten(X)), flatten(flatten(vperm(X,min_height,dimensions)))))
 #   s.add(lex_order(flatten(flatten(X)), flatten(flatten(hperm(X,width,dimensions))),'hsym'))
  #  s.add(lex_order(flatten(flatten(X)), flatten(flatten(vperm(X,min_height,dimensions))),'vsym'))

    #possibili implied constraints:
           #1) in ogni i,j ci può essere al più un'origine di un rettangolo k
           #2) per ogni rettangolo k, Se X[k][j][i], allora i + dimensions[k][0] <= width
           #3) analogo per l'altezza
    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')
    #print(s)

    #TIMEOUT:
    s.set('timeout', 300000)

    check_result = s.check()

    # If satisfiable
    if check_result == sat:
        
        m = s.model()

        solutions_x=[[PX[k][i] for i in range(width-dimensions[k][0]+1) if m.evaluate(PX[k][i])][0] for k in range(nofrectangles)]
        solutions_y=[[PY[k][i] for i in range(min_height - dimensions[k][1] +1) if m.evaluate(PY[k][i])][0] for k in range(nofrectangles)]

        return (min_height, adapt_solution(solutions_x, solutions_y),
                s.statistics(), end_time - starting_time)

    # If unsatisfiable
    return None


def adapt_solution(solutions_x, solutions_y) -> list[str]:
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


##def build_solutions(truex, truey):
##    outx=[]
##    outy=[]
##    for k in truex:
##        while i < nofrectangles:
##            if str(k)[3]
        
##    for k in truey:
##        outy.append(k[0])
##    coordk=[[outx[i],outy[i]] for i in range(len(outx))]
##    X=[f'x_{coordk[k][0]}_{coordk[k][1]}_{k}' for k in range(len(outx))]
        
    
    

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

        








