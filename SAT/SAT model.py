from z3 import *
from itertools import combinations

#Generic cardinality constraints

def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one(bool_vars):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

def exactly_one(bool_vars):
    return at_most_one(bool_vars) + [at_least_one(bool_vars)]
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
    
    max_x_pos = [width - dimensions[k][0] for k in range(nofrectangles)]
    
    X = [[[Bool(f'x_{i}_{j}_{k}') for i in range(width)] for j in range(max_height)] for k in range(nofrectangles)]
    #Voglio che X[i][j][k] == 1 se e solo se l'origine del rettangolo k è nelle coordinate i,j
    
    s = Solver()

    #vincolo che esattamente una delle variabili-altezza sia T:
    s.add(exactly_one(Height))

    for k in range(nofrectangles):  #ogni rettangolo ha esattamente un'origine
        s.add(exactly_one([[X[k][j][i] for i in range(width)] for j in range(max_height)]))




    #constraint di non sovrapposizione:

    s.check()
    m = s.model()
    
    print(X)






