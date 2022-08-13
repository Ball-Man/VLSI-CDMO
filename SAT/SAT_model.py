from z3 import *
from itertools import combinations

#Generic cardinality constraints
#IMPORTANTE: Provare altri encodings (questi sono i "sequential" encoding, O(n) clauses

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
    min_height = max(total_area // width, max([(dimensions[i])[1] for i in range(nofrectangles)]))
    max_height = sum([i[0] for i in dimensions])            #stessi bound sull'altezza del modello CP

    #Variabile booleana Height[k] uguale a 1 se e solo se l'altezza della soluzione coincide Height[min_height+k].
    #Aggiungo il vincolo che esattamente una delle variabili è T, ma è ridondante: basterebbe che al massimo una lo sia.
    #(Non so quale delle alternative sia meglio per ora).
    Height = [Bool(f'height_{i}') for i in range(min_height, max_height + 1)]
    
    #max_x_pos = [width - dimensions[k][0] for k in range(nofrectangles)]
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width - dimensions[k][0] + 1)] for j in range(max_height - dimensions[k][1] + 1)] for k in range(nofrectangles)]
    #Voglio che X[k][j][i] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j
    
    s = Solver()

    #vincolo che esattamente una delle variabili-altezza sia T:
    s.add(exactly_one(Height, f"height"))

    for k in range(nofrectangles):  #ogni rettangolo ha esattamente un'origine
        s.add(exactly_one(flatten(X[k]), f"origin_{k}"))



    #constraints no-overlap:
    for k in range(nofrectangles):
        for i in range(width - dimensions[k][0] + 1):
            for j in range(max_height - dimensions[k][1] + 1):
                for k1 in range(nofrectangles):
                    if k != k1:
                        for i1 in range(max(i-dimensions[k1][0]+1,0), min(i+dimensions[k][0], width - dimensions[k1][0] +1)):
                            for j1 in range(max(j-dimensions[k1][1]+1,0), min(j+dimensions[k][1], max_height - dimensions[k1][1] +1)):     #si dovrebbe capire graficamente                                                                                         
                                s.add(Implies(X[k][j][i], Not(X[k1][j1][i1])))
           # for w in range(dimensions[k]

    #possibili implied constraints:
           #1) in ogni i,j ci può essere al più un'origine di un rettangolo k
           #2) per ogni rettangolo k, Se X[k][j][i], allora i + dimensions[k][0] <= width
           #3) analogo per l'altezza




    #constraint di non sovrapposizione:

    check_result = s.check()


    # If satisfiable
    if check_result == sat:
        m = s.model()

        # For convenience I also want the height to be returned
        # Setting it to 0 for now, but in the end it shall contain the
        # optimal height value
        height = 0

        solutions = [X[k][j][i] for k in range(nofrectangles) for j in range(max_height - dimensions[k][1] + 1) for i in range(width - dimensions[k][0] + 1) if m.evaluate(X[k][j][i])]
        return height, solutions

    # If unsatisfiable
    return None



