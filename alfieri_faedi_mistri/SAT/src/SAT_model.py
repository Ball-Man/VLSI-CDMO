from z3 import *
from itertools import combinations
from functools import partial
import time
from math import sqrt
from math import ceil

import util


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

def equal_vars(var1,var2):  #boolean variables are equal iff they are equivalent
    return And(Or(Not(var1),var2),Or(Not(var2),var1))

##def lex_order(listvar1,listvar2):   #Lexicographic order (NAIVE ENCODING)
##    constraints=[]
##    n=len(listvar1)
##    constraints.append(Or(Not(listvar1[0]),listvar2[0])) #first element of first list is ""<="" of first element of second list
##    for i in range(1,n):     #The "whole" constraint is too large, we can adapt this range
##        #constraints.append(Or(Not(And([equal_vars(listvar1[j],listvar2[j]) for j in range(i)])), Or(listvar1[i],Not(listvar2[i]))))
##        #constraints.append(Implies(And([equal_vars(listvar1[k],listvar2[k]) for k in range(i)]),Implies(listvar1[i],listvar2[i])))
##        constraints.append(Or(Not(And([equal_vars(listvar1[k],listvar2[k]) for k in range(i)])),Or(Not(listvar1[i]),listvar2[i])))
##    return And(constraints)

def lex_order(listvar1,listvar2,name, func = math.sqrt):  #lex_order_CSE
    constraints=[]
    n = len(listvar1)
    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
    constraints.append(Or(Not(listvar2[0]),listvar1[0])) #lex_geq
    #constraints.append(Or(Not(listvar1[0]),listvar2[0]))   #lex_lesseq
    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
    #for i in range(n-2):   #complete lexicographic order
    for i in range(int(func(n)) - 2):   
        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
    #for i in range(n-1):   #complete lexicographic order
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


def sat_vlsi(width, nofrectangles, dimensions, min_height, timeout=300000): #dimensions è una lista di coppie di coordinate [x,y]

    s = Solver()
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]
    #X[k][j][i] == 1 if and only if the origin of circuit k has coordinates i,j

    starting_time=time.time()
    print('generating solver:')
    
    for k in range(nofrectangles):  #Each circuit has an origin
        #s.add(exactly_one(flatten(X[k]), f"origin_{k}"))
        s.add(at_least_one(flatten(X[k])))  #In order to obtain a smaller number of clauses we impose at_least_one instead of exactly_one, see the report
                        
    #constraints no-overlap:
    for k in range(nofrectangles-1):
        for i in range(width - dimensions[k][0] + 1):
            for j in range(min_height - dimensions[k][1] + 1):
                for k1 in range(k+1, nofrectangles): 
                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], min_height - dimensions[k1][1] +1)):     #See the report                                                                                     
                                s.add(Or(Not(X[k][j][i]), Not(X[k1][j1][i1])))

    #horizontal and vertical symmetry breaking constraint:
    s.add(lex_order(flatten(flatten(X)), flatten(flatten(hperm(X,width,dimensions))),'hsym'))
    s.add(lex_order(flatten(flatten(X)), flatten(flatten(vperm(X,min_height,dimensions))),'vsym'))

    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')

    #TIMEOUT:
    s.set('timeout', timeout)

    check_result = s.check()

    # If satisfiable
    if check_result == sat:
        m = s.model()
        solutions = [X[k][j][i] for k in range(nofrectangles) for j in range(min_height - dimensions[k][1] + 1) for i in range(width - dimensions[k][0] + 1) if m.evaluate(X[k][j][i])] #max_height--->min_height
        print(solutions)
        return min_height, solutions, s.statistics(), end_time - starting_time

    # If unsatisfiable
    return None, None, s.statistics(), end_time - starting_time


linear_optimization = partial(util.linear_optimization, sat_vlsi)


binary_optimization = partial(util.binary_optimization, sat_vlsi)
