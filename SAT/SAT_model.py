from z3 import *
from itertools import combinations
import time

#Generic cardinality constraints
#IMPORTANTE: Provare altri encodings

def toBinary(num, length = None):
    num_bin = bin(num).split("b")[-1]
    if length:
        return "0"*(length - len(num_bin)) + num_bin
    return num_bin

def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one_np(bool_vars, name = ""):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]


#BITWISE ENCODING:
##def at_most_one(bool_vars, name):
##    constraints = []
##    n = len(bool_vars)
##    m = math.ceil(math.log2(n))
##    r = [Bool(f"r_{name}_{i}") for i in range(m)]
##    binaries = [toBinary(i, m) for i in range(n)]
##    for i in range(n):
##        for j in range(m):
##            phi = Not(r[j])
##            if binaries[i][j] == "1":
##                phi = r[j]
##            constraints.append(Or(Not(bool_vars[i]), phi))        
##    return And(constraints)


#HEULE ENCODING:
##def at_most_one(bool_vars, name):
##    if len(bool_vars) <= 4:
##        return And(at_most_one_np(bool_vars))
##    y = Bool(f"y_{name}")
##    return And(And(at_most_one_np(bool_vars[:3] + [y])), And(at_most_one_he(bool_vars[3:] + [Not(y)], name+"_")))

#SEQUENTIAL ENCODING:
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

def equal_vars(var1,var2):
    return And(Or(Not(var1),var2),Or(Not(var2),var1))

def lex_order(listvar1,listvar2):   
    constraints=[]
    n=len(listvar1)
    constraints.append(Or(listvar1[0],Not(listvar2[0]))) #first element of first list is ""<="" of first element of second list
    for i in range(1,n//4):     #il constraints "intero" è troppo grande, si può provare a giocare con questo range
        constraints.append(Or(Not(And([equal_vars(listvar1[j],listvar2[j]) for j in range(i)])), Or(listvar1[i],Not(listvar2[i]))))
    return And(constraints)
        

def exactly_one(bool_vars, name):
    return And(at_least_one(bool_vars), at_most_one(bool_vars, name))
####################################################################################################

#flatten list:
def flatten(l):
    return [item for sublist in l for item in sublist]
####################################################################################################


def sat_vlsi(width, nofrectangles, dimensions): #dimensions è una lista di coppie di coordinate [x,y]

    total_area = 0
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
    if total_area % width == 0:         #If total area is not divisible by width we round up
        min_height = max(total_area // width, max([dimensions[i][1] for i in range(nofrectangles)]))
    else:
        min_height = max(total_area // width + 1, max([dimensions[i][1] for i in range(nofrectangles)]))
    max_height = sum([i[1] for i in dimensions])            #stessi bound sull'altezza del modello CP

    #Variabile booleana Height[k] uguale a 1 se e solo se l'altezza della soluzione coincide Height[min_height+k].
    #Aggiungo il vincolo che esattamente una delle variabili è T, ma è ridondante: basterebbe che al massimo una lo sia.
    #(Non so quale delle alternative sia meglio per ora).
    #Height = [Bool(f'height_{i}') for i in range(min_height, max_height + 1)]  
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]   #max_height--->min_height
    #Voglio che X[k][j][i] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j
    
    s = Solver()

    #vincolo che esattamente una delle variabili-altezza sia T:
    #s.add(exactly_one(Height, f"height"))
    starting_time=time.time()
    print('generating model:')
    for k in range(nofrectangles):  #ogni rettangolo ha esattamente un'origine
        s.add(exactly_one(flatten(X[k]), f"origin_{k}"))



    #constraints no-overlap:
    for k in range(nofrectangles):
        for i in range(width - dimensions[k][0] + 1):
            for j in range(min_height - dimensions[k][1] + 1): ##max_height--->min_height
                for k1 in range(k+1, nofrectangles): #prima era range(nofrectangles), con if k != k1, ma così si tolgono un po' di implied constraints (modello è più piccolo)
                    #if k != k1:
                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], min_height - dimensions[k1][1] +1)):     #si dovrebbe capire graficamente #max_height--->min_height                                                                                         
                                s.add(Or(Not(X[k][j][i]), Not(X[k1][j1][i1])))
           # for w in range(dimensions[k]

    #horizontal symmetry breaking constraint:
    s.add(lex_order(flatten(flatten(X)), flatten(flatten(hperm(X,width,nofrectangles,dimensions)))))
    s.add(lex_order(flatten(flatten(X)), flatten(flatten(vperm(X,min_height,nofrectangles,dimensions)))))

    #possibili implied constraints:
           #1) in ogni i,j ci può essere al più un'origine di un rettangolo k
           #2) per ogni rettangolo k, Se X[k][j][i], allora i + dimensions[k][0] <= width
           #3) analogo per l'altezza
    end_time=time.time()
    print('Model generated in', end_time - starting_time, 'seconds')
    check_result = s.check()

    # If satisfiable
    if check_result == sat:
        m = s.model()

        # For convenience I also want the height to be returned
        # Setting it to 0 for now, but in the end it shall contain the
        # optimal height value
        height = min_height

        solutions = [X[k][j][i] for k in range(nofrectangles) for j in range(min_height - dimensions[k][1] + 1) for i in range(width - dimensions[k][0] + 1) if m.evaluate(X[k][j][i])] #max_height--->min_height
        return min_height, solutions, s.statistics()

    # If unsatisfiable
    return "unsat"

##width=8
##nofrectangles=4
##dimensions=[[3,3],[3,5],[5,3],[5,5]]
##min_height=8
##X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]

def hperm(A,width,nofrectangles,dimensions):
    return [[[A[k][j][width - i - dimensions[k][0]] for i in range(len(A[k][j]))] for j in range(len(A[k]))] for k in range(len(A))]

def vperm(A,min_height,nofrectangles,dimensions):
    return [[[A[k][min_height - j - dimensions[k][1]][i] for i in range(len(A[k][j]))] for j in range(len(A[k]))] for k in range(len(A))]
        








