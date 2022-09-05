from z3 import *

def lex_less(arr1, arr2):
    ''' Lexicographic ordering constraint.

    lex_less([x1, x2, ..., xk], [y1, y2, ..., yk],
        [(l_x1,u_x1), (l_x2,u_x2), ..., (l_xk,u_xk)],
        [(l_y1,u_y1), (l_y2,u_y2), ..., (l_yk,u_yk)],
        model, key)

    x1 <= y1
    /\ (x1 = y1 -> x2 <= y2)
    /\ ((x1 = y1 /\ x1 = y2) -> x2 <= y2) /\ ...
    /\ ((x1 = y1 /\ x2 = y2 /\ ... /\ xk-1 = yk-1) -> xk <= yk)
    '''

    return And([Implies(
            And([arr1[k] == arr2[k] for k in range(i)]),
            arr1[i] <= arr2[i]) for i in range(len(arr1))])

    
def max(arr, y):
    ''' Max constraint.
        linear_max([x1, x2, ..., xk], max)

        return (and_clauses, or_clauses)
    '''

    # y = max(x1, x2, ..., xk): 
    #   y >= xi for i in 1..k
    #   y <= xi + (umax - l_i)*(1-b_i)
    # Where umax = max(u_1, u_2, ..., u_k) and b_i = 1 -> xi = max(x1, x2, ..., xk)
    
    return And([
        And([y >= arr[i] for i in range(len(arr))]),
        Or([y == arr[i] for i in range(len(arr))])
    ])