from z3 import *
from itertools import combinations
from functools import partial
import re
import time
from math import sqrt
from math import ceil

import util


VARIABLE_RE = re.compile(r'p[xy]_(\d+)_(\d+)')


##def at_least_one(bool_vars):
##    return Or(bool_vars)

#SEQUENTIAL ENCODING:
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
def equal_vars(var1,var2): #boolean variables are equal iff they are equivalent
    return And(Or(Not(var1),var2),Or(Not(var2),var1))

def identity(x):
    return x

def lex_order(listvar1,listvar2,name, func = identity):  #lex_order_CSE
    constraints=[]
    n = len(listvar1)
    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
    constraints.append(Or(Not(listvar2[0]),listvar1[0])) #lex_geq
    #constraints.append(Or(Not(listvar1[0]),listvar2[0]))   #lex_lesseq
    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
    for i in range(int(func(n)) - 2):
        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
    for i in range(int(func(n)) - 1):
        constraints.append(Or(Not(s[i]),(Or(Not(listvar2[i+1]),listvar1[i+1])))) #lex_geq
        #constraints.append(Or(Not(s[i]),(Or(Not(listvar1[i+1]),listvar2[i+1])))) #lex_lesseq
    return And(constraints)
##        
##
##def exactly_one(bool_vars, name):
##    return And(at_least_one(bool_vars), at_most_one(bool_vars, name))
####################################################################################################

#flatten list:
def flatten(l):
    return [item for sublist in l for item in sublist]
####################################################################################################


def sat_vlsi(width, nofrectangles, dimensions, min_height, timeout=300000): #dimensions è una lista di coppie di coordinate [x,y]
    
    s = Solver()

    PX=[[Bool(f'px_{k}_{i}') for i in range(width-dimensions[k][0] +1)] for k in range(nofrectangles)]      #The x coordinate of circuit k is <= i
    PY=[[Bool(f'py_{k}_{j}') for j in range(min_height-dimensions[k][1]+1)] for k in range(nofrectangles)]  #The y coordinate of circuit k is <= i 
    LR=[[Bool(f'lr_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]                #LR[k][k1] if k is at the left of k1
    UD=[[Bool(f'ud_{k}_{k1}') for k1 in range(nofrectangles)] for k in range(nofrectangles)]                #UD[k][k1] if k is under k1
      
    starting_time=time.time()
    print('generating solver:')

    for k in range(nofrectangles):  #Order encoding on the PX, PY variables
        for i in range(width-dimensions[k][0]):
            s.add(Or(Not(PX[k][i]),PX[k][i+1]))
        for j in range(min_height-dimensions[k][1]):
            s.add(Or(Not(PY[k][j]),PY[k][j+1]))

    for k in range(nofrectangles):  #each circuit must have an origin
        s.add(PX[k][width - dimensions[k][0]])
        s.add(PY[k][max(0,min_height - dimensions[k][1])])      #The max here is necessary because the index might be negative when not using the bounds of linear_optimization and
                                                                #binary_optimization


    for k in range(nofrectangles):  #no overlap: each circuit must be either to the left, to the right, below or above each other circuit
        for k1 in range(k+1, nofrectangles):
            s.add(Or(LR[k][k1],LR[k1][k],UD[k][k1],UD[k1][k]))

    for k in range(nofrectangles):  
        for k1 in range(k+1, nofrectangles):
            for i in range(-max(dimensions[k][0],dimensions[k1][0]), width-min(dimensions[k][0],dimensions[k1][0])): #if k is on the left of k1 and PX[k]>i, then PX[k1]>i+width(k)
                A=[]
                B=[]
                A.append(Not(LR[k][k1]))
                B.append(Not(LR[k1][k]))
                if i>=0:
                    if i <= width - dimensions[k][0]:   #This guarantees, in the case that i>width-w(k1), that the x coordinate of k is <= i
                        A.append(PX[k][i])              #if instead i is also <= width - w(k1), then the last condition is appended to 
                    if i <= width - dimensions[k1][0]:  #represent the condition of the last comment
                        B.append(PX[k1][i])
                if 0 <= i+dimensions[k][0] <= width - dimensions[k1][0]:                    
                    A.append(Not(PX[k1][i+dimensions[k][0]]))
                    
                if 0 <= i+dimensions[k1][0] <= width-dimensions[k][0]:
                    B.append(Not(PX[k][i+dimensions[k1][0]]))
                
                if len(A) > 1:      #This means that there isn't only the Not(LR) variable in A
                    s.add(Or(A))
                
                if len(B) > 1:      #Same as above
                    s.add(Or(B))
                    
            for j in range(-max(dimensions[k][1],dimensions[k1][1]), min_height - min(dimensions[k][1],dimensions[k1][1])):  #if k is under k1 and PX[k]>i, then PY[k1]>i+height(k)
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
                    C.append(Not(PY[k1][j+dimensions[k][1]]))
                    
                if 0 <= j+dimensions[k1][1] <= min_height - dimensions[k][1]:
                    D.append(Not(PY[k][j+dimensions[k1][1]]))

                #These are put in order to avoid imposing only Not(UD[k][k1]) or Not(UD[k1][k])
                if len(C) > 1:
                    s.add(Or(C))                
                if len(D) > 1:
                    s.add(Or(D))

            if dimensions[k][0] + dimensions[k1][0] > width:    #if the sum of widths (resp. heights) of circuits exceeds the max width (height),
                s.add(Not(LR[k][k1]))                           #then they can't be left or right (above or below) each other
                s.add(Not(LR[k1][k]))

            if dimensions[k][1] + dimensions[k1][1] > min_height:
                s.add(Not(UD[k][k1]))
                s.add(Not(UD[k1][k]))

    #instead of adding symmetry breaking for the model with rotations, we just constraint the biggest
    #circuit to be in the left-bottom part of the region of its possible positions. DO NOT USE WITH LEX_ORDER SYMMETRY-BREAKING


    #Maybe it is best to consider the smallest rectangle instead? There is more "information gain" I think

##    maxdimension=max(max(dimensions[k] for k in range(nofrectangles)))
##    indexmaxdimension=[k for k in range(nofrectangles) if maxdimension in dimensions[k]][0]
    mindimension=min(min(dimensions[k] for k in range(nofrectangles)))
    indexmindimension=[k for k in range(nofrectangles) if mindimension in dimensions[k]][0]
    
##    s.add(PX[indexmaxdimension][(width-dimensions[indexmaxdimension][0])//2])
##    s.add(PY[indexmaxdimension][(min_height - dimensions[indexmaxdimension][1])//2])
    s.add(PX[indexmindimension][(width-dimensions[indexmindimension][0])//2])
    s.add(PY[indexmindimension][(min_height - dimensions[indexmindimension][1])//2])

##    hsymm = []                  #Horizontal symmetry breaking
##    px=[]
##    for k in range(nofrectangles):      
##        hsymmcons=[Not(i) for i in PX[k][0:width-dimensions[k][0]]]
##        hsymmcons=hsymmcons[::-1]
##        hsymm+=hsymmcons
##        px+=PX[k][0:width-dimensions[k][0]]
##    s.add(lex_order(hsymm,px ,'hsymm'))
##
##    vsymm=[]                     #Vertical symmetry breaking
##    py=[]                      
##    for k in range(nofrectangles):
##        vsymmcons=[Not(i) for i in PY[k][0:min_height-dimensions[k][1]]]
##        vsymmcons=vsymmcons[::-1]
##        vsymm+=vsymmcons
##        py+=PY[k][0:min_height-dimensions[k][1]]
##    s.add(lex_order(vsymm,py,'vsymm'))

    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')

    #TIMEOUT:
    s.set('timeout', timeout)

    check_result = s.check()

    # If satisfiable
    if check_result == sat:

        m = s.model()
        solutions_x=[[PX[k][i] for i in range(width-dimensions[k][0] + 1) if m.evaluate(PX[k][i]) == True][0] for k in range(nofrectangles)]
        solutions_y=[[PY[k][i] for i in range(min_height - dimensions[k][1] + 1) if m.evaluate(PY[k][i]) == True][0] for k in range(nofrectangles)]

        return (min_height, adapt_solution(solutions_x, solutions_y),
                s.statistics(), end_time - starting_time)

    # If unsatisfiable
    print(s.statistics())
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


linear_optimization = partial(util.linear_optimization, sat_vlsi)


binary_optimization = partial(util.binary_optimization, sat_vlsi)
