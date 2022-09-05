import time
from itertools import combinations
from functools import partial
from math import sqrt

from z3 import *
import util


def at_least_one(bool_vars):
    return Or(bool_vars)


def at_most_one(bool_vars, name):
    constraints = []
    n = len(bool_vars)
    s = [Bool(f"s_{name}_{i}") for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0]))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
        constraints.append(Or(Not(s[i-1]), s[i]))
    return And(constraints)


def equal_vars(var1,var2): #boolean variables are equal iff they are equivalent
    return And(Or(Not(var1),var2),Or(Not(var2),var1))

def lex_order(listvar1,listvar2,name):  #lex_order_CSE
    constraints=[]
    n = len(listvar1)          
    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
    constraints.append(Or(Not(listvar2[0]),listvar1[0]))
    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
    for i in range(int(sqrt(n))-2):
        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
    for i in range(int(sqrt(n))-1):
        constraints.append(Or(Not(s[i]),(Or(Not(listvar2[i+1]),listvar1[i+1]))))
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
                
        
def sat_vlsi(width, nofrectangles, dimensions, min_height, timeout=300000): #dimensions è una lista di coppie di coordinate [x,y]

    s = Solver()
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]  #max_height--->min_height
    Xr = [[[Bool(f'x_{i}_{j}_{k+nofrectangles}') for i in range(width - dimensions[k][1] + 1)] for j in range(min_height - dimensions[k][0] + 1)] for k in range(nofrectangles)]
    
    Xboth=X+Xr
    dimensionsboth = dimensions+[item[::-1] for item in dimensions] #doubled the array of the dimensions

    for k in range(nofrectangles):              #square circuits shall not be rotated
        if dimensions[k][0] == dimensions[k][1]:
            for v in flatten(Xr[k]):
                s.add(Not(v))

    starting_time=time.time()
    print('generating solver:')
    
    for k in range(nofrectangles):  #each circuit has at least an origin
        #s.add(exactly_one(flatten(X[k]), f"origin_{k}"))
        s.add(at_least_one(flatten(X[k])+flatten(Xr[k])))  #See the reports, we chose at_least_one for practical reasons
        

    #constraints no-overlap:
    for k in range(2*nofrectangles):
        for i in range(width - dimensionsboth[k][0] + 1):
            for j in range(min_height - dimensionsboth[k][1] + 1): ##max_height--->min_height
                for k1 in range(k+1, 2*nofrectangles):
                    if k != k1 - 2*nofrectangles:
                        for i1 in range(max(i-dimensionsboth[k1][0]+1,0), min(i+dimensionsboth[k][0], width - dimensionsboth[k1][0] +1)):
                            for j1 in range(max(j-dimensionsboth[k1][1]+1,0), min(j+dimensionsboth[k][1], min_height - dimensionsboth[k1][1] +1)):     #Consult the report for the no_overlap constraint
                                s.add(Implies(Xboth[k][j][i], Not(Xboth[k1][j1][i1])))

    #SYMMETRY-BREAKING CONSTRAINTS:
    s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(hperm(Xboth,width,dimensionsboth))),'hsym'))       #horizontal symmetry
    s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(vperm(Xboth,min_height,dimensionsboth))),'vsym'))  #vertical symmetry
                                
    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')

    s.set('timeout', timeout)

    check_result = s.check()

    # If satisfiable
    if check_result == sat:
        m = s.model()
        solutionsa = [Xboth[k][j][i] for k in range(nofrectangles) for j in range(min_height - dimensionsboth[k][1] + 1) for i in range(width - dimensionsboth[k][0] + 1) if m.evaluate(Xboth[k][j][i])] #max_height--->min_height
        solutionsb = [Xboth[k][j][i] for k in range(nofrectangles, 2*nofrectangles) for j in range(min_height - dimensionsboth[k][1] + 1) for i in range(width - dimensionsboth[k][0] + 1) if m.evaluate(Xboth[k][j][i])]

        solutions = solutionsa+solutionsb
        print(solutions)
        return min_height, solutions, s.statistics(), end_time - starting_time

    # If unsatisfiable
    return None, None, s.statistics(), end_time - starting_time


linear_optimization = partial(util.linear_optimization, sat_vlsi)


binary_optimization = partial(util.binary_optimization, sat_vlsi)
