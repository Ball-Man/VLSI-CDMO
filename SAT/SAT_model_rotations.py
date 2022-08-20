from z3 import *
from itertools import combinations
import time

#Generic cardinality constraints
#IMPORTANTE: Provare altri encodings (questi sono i "sequential" encoding, O(n) clauses
#Per ora sto provando a verificare la satisfiability con la min_height, idealmente Height dovrebbe essere una variabile

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

def lex_order(listvar1,listvar2):   #Ordine lessicografico "al contrario": listvar1>=listvar2 
    constraints=[]
    n=len(listvar1)
    constraints.append(Implies(listvar2[0],listvar1[0])) #first element of first list is ""<="" of first element of second list
    for i in range(1,100):     #il constraints "intero" è troppo grande, si può provare a giocare con questo range
        #constraints.append(Or(Not(And([equal_vars(listvar1[j],listvar2[j]) for j in range(i)])), Or(listvar1[i],Not(listvar2[i]))))
        constraints.append(Implies(And([equal_vars(listvar1[k],listvar2[k]) for k in range(i)]),Implies(listvar2[i],listvar1[i])))
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

def apply_rotations(width, nofrectangles, dimensions):
    s=Solver()
    Rotated = [Bool(f'rotated_{k}') for k in range(nofrectangles)]
    for k in range(nofrectangles):  #square rectangles and rectangles with height greater than the max width won't be rotated
        if dimensions[k][0] == dimensions[k][1] or dimensions[k][1] > width:
            s.add(Not(Rotated[k]))
    while(True):  
        check_result = s.check()
        if check_result == sat:
            m=s.model()
            actual_dimensions=[]
            for k in range(nofrectangles):
                if m.evaluate(Rotated[k]) == True:
                    actual_dimensions.append(dimensions[k][::-1])
                else:
                    actual_dimensions.append(dimensions[k])
            a= sat_vlsi(width, nofrectangles, actual_dimensions)
            if a != None:
                return a
            formulas=[]
            for k in range(nofrectangles):
                if m.evaluate(Rotated[k]) == True:
                    formulas.append(Rotated[k])
                else:
                    formulas.append(Not(Rotated[k]))
            formula = And(formulas)
            s.add(Not(formula))
    return "unsat"
                
        
def sat_vlsi(width, nofrectangles, dimensions): #dimensions è una lista di coppie di coordinate [x,y]

    s = Solver()

    total_area = 0
    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
    if total_area % width == 0:         #If total area is not divisible by width we round up
        min_height = max(total_area // width, max([dimensions[i][1] for i in range(nofrectangles)]))
    else:
        min_height = max(total_area // width + 1, max([dimensions[i][1] for i in range(nofrectangles)]))

    #Variabile booleana Height[k] uguale a 1 se e solo se l'altezza della soluzione coincide Height[min_height+k].
    #Aggiungo il vincolo che esattamente una delle variabili è T, ma è ridondante: basterebbe che al massimo una lo sia.
    #(Non so quale delle alternative sia meglio per ora).
    #Height = [Bool(f'height_{i}') for i in range(min_height, max_height + 1)]
    
    #max_x_pos = [width - dimensions[k][0] for k in range(nofrectangles)]
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(min_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]   #max_height--->min_height
    #Voglio che X[k][j][i] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j
    

    #vincolo che esattamente una delle variabili-altezza sia T:
    #s.add(exactly_one(Height, f"height"))

    starting_time=time.time()
    print('generating solver:')
    
    for k in range(nofrectangles):  #ogni rettangolo ha esattamente un'origine
        #s.add(exactly_one(flatten(X[k]), f"origin_{k}"))
        s.add(at_least_one(flatten(X[k])))  #per avere meno clauses posso mettere anche che ogni rettangolo ha almeno un'origine:
                                            #alla peggio puoi ottenere come soluzione un rettangolo con circuiti duplicati,
                                            #e quando costruisci fisicamente il chip scegli dove piazzare i circuiti in una qualsiasi delle posizioni restituite dalla soluzione


    #constraints no-overlap:
    for k in range(nofrectangles):
        for i in range(width - dimensions[k][0] + 1):
            for j in range(min_height - dimensions[k][1] + 1): ##max_height--->min_height
                for k1 in range(k+1, nofrectangles): #prima era range(nofrectangles), con if k != k1, ma così si tolgono un po' di implied constraints (modello è più piccolo)
                    #if k != k1:
                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], min_height - dimensions[k1][1] +1)):     #si dovrebbe capire graficamente #max_height--->min_height                                                                                         
                                s.add(Implies(X[k][j][i], Not(X[k1][j1][i1])))

    #horizontal symmetry breaking constraint:
    #s.add(lex_order(flatten(flatten(X)), flatten(flatten(hperm(X,width,dimensions)))))
    #s.add(lex_order(flatten(flatten(X)), flatten(flatten(vperm(X,min_height,dimensions)))))

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
        solutions = [X[k][j][i] for k in range(nofrectangles) for j in range(min_height - dimensions[k][1] + 1) for i in range(width - dimensions[k][0] + 1) if m.evaluate(X[k][j][i])] #max_height--->min_height
        return min_height, solutions, s.statistics()

    # If unsatisfiable
    return None



