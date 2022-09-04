import time
from itertools import combinations
from functools import partial

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

##def lex_order(listvar1,listvar2):   #Ordine lessicografico: listvar1<=listvar2
##    constraints=[]
##    n=len(listvar1)
##    constraints.append(Or(Not(listvar1[0]),listvar2[0])) #first element of first list is ""<="" of first element of second list
##    for i in range(1,10):     #il constraints "intero" è troppo grande, si può provare a giocare con questo range
##        #constraints.append(Or(Not(And([equal_vars(listvar1[j],listvar2[j]) for j in range(i)])), Or(listvar1[i],Not(listvar2[i]))))
##        #constraints.append(Implies(And([equal_vars(listvar1[k],listvar2[k]) for k in range(i)]),Implies(listvar1[i],listvar2[i])))
##        constraints.append(Or(Not(And([equal_vars(listvar1[k],listvar2[k]) for k in range(i)])),Or(Not(listvar1[i]),listvar2[i])))
##    return And(constraints)

def lex_order(listvar1,listvar2,name):  #lex_order_CSE
    constraints=[]
    n = len(listvar1)           #Anche qui si può provare a prendere f(n)<n per alleggerire il numero di constraints
    s = [Bool(f's_{name}_{i}') for i in range(n-1)]
    constraints.append(Or(Not(listvar2[0]),listvar1[0]))
    constraints.append(equal_vars(s[0],equal_vars(listvar1[0],listvar2[0])))
    for i in range(n//2-2):
        constraints.append(equal_vars(s[i+1], And(s[i], equal_vars(listvar1[i+1],listvar2[i+1]))))
    for i in range(n//2-1):
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
                
        
def sat_vlsi(width, nofrectangles, dimensions, max_height, timeout=300000): #dimensions è una lista di coppie di coordinate [x,y]

    s = Solver()

    total_area = 0
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
    if total_area % width == 0:         #If total area is not divisible by width we round up
        min_height = max(total_area // width, max(min(dimensions[i][0], dimensions[i][1]) for i in range(nofrectangles)))
    else:
        min_height = max(total_area // width + 1, max(min(dimensions[i][0], dimensions[i][1]) for i in range(nofrectangles)))
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]  #max_height--->min_height
    Xr = [[[Bool(f'x_{i}_{j}_{k+nofrectangles}') for i in range(width - dimensions[k][1] + 1)] for j in range(min_height - dimensions[k][0] + 1)] for k in range(nofrectangles)]
    #R=[Bool(f'Rotated_{k}') for k in range(nofrectangles)] #Per ogni rettangolo k, R[k] è True se e solo se k è ruotato

##    for k in range(nofrectangles):  #se il rettangolo è un quadrato non lo faccio ruotare
##        if dimensions[k][0] == dimensions[k][1]:
##            s.add(Not(R[k]))
    
    Xboth=X+Xr
    dimensionsboth = dimensions+[item[::-1] for item in dimensions] #dimensioni di tutti i rettangoli "base" e poi di tutti i rettangoli ruotati
    #Voglio che X[k][j][i] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j

    for k in range(nofrectangles):
        if dimensions[k][0] == dimensions[k][1]:
            for v in flatten(Xr[k]):
                s.add(Not(v))

    starting_time=time.time()
    print('generating solver:')
    
    for k in range(nofrectangles):  #ogni rettangolo ha esattamente un'origine
        #s.add(exactly_one(flatten(X[k]), f"origin_{k}"))
        s.add(at_least_one(flatten(X[k])+flatten(Xr[k])))  #per avere meno clauses posso mettere anche che ogni rettangolo ha almeno un'origine:
                                            #alla peggio puoi ottenere come soluzione un rettangolo con circuiti duplicati,
                                            #e quando costruisci fisicamente il chip scegli dove piazzare i circuiti in una qualsiasi delle posizioni restituite dalla soluzione
##    for k in range(nofrectangles):
##            for j in range(min_height-dimensions[k][1] +1):
##                for i in range(width - dimensions[k][0] +1):
##                    s.add(Or((Not(R[k]),Not(X[k][j][i]))))  #R[k] implica che il rettangolo k (non ruotato) non abbia un'origine
##
##    for k in range(nofrectangles):
##            for j in range(min_height-dimensions[k][0]+1):
##                for i in range(width-dimensions[k][1]+1):
##                    s.add(Or(R[k],Not(Xr[k][j][i])))        #Non R[k] implica che il rettangolo k (ruotato) non abbia un'origine

    #constraints no-overlap:
    for k in range(2*nofrectangles):
        for i in range(width - dimensionsboth[k][0] + 1):
            for j in range(min_height - dimensionsboth[k][1] + 1): ##max_height--->min_height
                for k1 in range(k+1, 2*nofrectangles): #prima era range(nofrectangles), con if k != k1, ma così si tolgono un po' di implied constraints (modello è più piccolo)
                    if k != k1 - 2*nofrectangles:
                        for i1 in range(max(i-dimensionsboth[k1][0]+1,0), min(i+dimensionsboth[k][0], width - dimensionsboth[k1][0] +1)):
                            for j1 in range(max(j-dimensionsboth[k1][1]+1,0), min(j+dimensionsboth[k][1], min_height - dimensionsboth[k1][1] +1)):     #si dovrebbe capire graficamente #max_height--->min_height
                                s.add(Implies(Xboth[k][j][i], Not(Xboth[k1][j1][i1])))

    #SYMMETRY-BREAKING CONSTRAINTS:
    #s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(hperm(Xboth,width,dimensionsboth)))))      #horizontal symmetry
    #s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(vperm(Xboth,min_height,dimensionsboth))))) #vertical symmetry
    s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(hperm(Xboth,width,dimensionsboth))),'hsym'))
    s.add(lex_order(flatten(flatten(Xboth)), flatten(flatten(vperm(Xboth,min_height,dimensionsboth))),'vsym'))

    #possibili implied constraints:
           #1) in ogni i,j ci può essere al più un'origine di un rettangolo k
           #2) per ogni rettangolo k, Se X[k][j][i], allora i + dimensions[k][0] <= width
           #3) analogo per l'altezza
                                
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
    return None


linear_optimization = partial(util.linear_optimization, sat_vlsi)


binary_optimization = partial(util.binary_optimization, sat_vlsi)
