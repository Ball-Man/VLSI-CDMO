from gurobipy import GRB

def reify_or(arr, big_m, model, key):
    '''Linearize the or.
    It require to pass the constraint in the form "a_ij*x_j - B_i <= 0"
    big_m is calculated as such: M_i = -B_i + SUM_j max(a_ij*l_j , a_ij*u_j)
    where l_j and u_j are the upper bound for a_ij.'''

    # To encode C1 \/ ... \/ Cm we introduce b1, ..., bm in {0,1},
    # we impose sum(b) >=1 and for each Ci = SUM_ij a_ij * x_j <= B_i
    # we add the constraint SUM_ij a_ij * x_j - B_i <= M*(1-bi)
    # 
    # Where M is a "big enough" constant. if x_j in l_j..u_j we can define 
    # a Big-M for each equation: M_i = -B_i + SUM_ij max{a_ij*l_j, a_ij*u_j}

    b = []
    for i in range(len(arr)):
        b.append(model.addVar(vtype=GRB.BINARY, name=f"{key}_b_{i}"))
        model.addConstr(arr[i] <= big_m[i]*(1-b[i]), name=f"{key}_{i}")
    model.addConstr(sum(b) >= 1, name=f"{key}_b_sum")

def lex_less(arr1, arr2, dom1, dom2, model, key):
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

    # x1 <= y1 /\
    #     (x1 != y1 \/ x2 <= y2) /\             -> x1 - y1 + 1 <= 0 \/ y1 - x1 + 1 <= 0 \/ x2 - y2 <= 0
    #     (x1 != y1 \/ x2 != y2 \/ x3 <= y3)    -> x1 - y1 + 1 <= 0 \/ y1 - x1 + 1 <= 0 \/ x2 - y2 + 1 <= 0 \/ y2 - x2 + 1 <= 0 \/ x3 - y3 <= 0
    #     ...


    # x1 != y1   ->   x1 < y1 \/ x1 > y1   ->   x1 <= y1 - 1 \/ x1 >= y1 + 1   ->   x1 - y1 + 1 <= 0 \/ -x1 + y1 +1 <= 0
    for i in range(len(arr1)):
        reify_or(
            [ arr1[k] - arr2[k] + 1 for k in range(0,i)] +   # x_k < y_k \/
            [-arr1[k] + arr2[k] + 1 for k in range(0,i)] +   # x_k > y_k \/
            [arr1[i] - arr2[i]],                            # x_i <= y_i
            [1 + dom1[k][1] - dom2[k][0] for k in range(0,i)] + #  B = -1, Mk = 1 + max(dom1[k]) + max(-1*dom2[k][0], -1*dom2[k][1])   ->   1 + dom1[k][1] - dom2[k][0]
            [1 - dom1[k][0] + dom2[k][1] for k in range(0,i)] + #  B = -1, Mk = 1 + max(-1*dom1[k][0], -1*dom1[k][1]) + max(dom2[k])   ->   1 - dom1[k][0] + dom2[k][1]
            [dom1[i][1]], model, f"{key}_{i}")
    
def linear_max(arr, dom, y, model, key):
    ''' Max constraint.
        
        linear_max([x1, x2, ..., xk], [(l_1,u_1), (l_2,u_2), ..., (l_k,u_k)], model, key)
    '''

    # y = max(x1, x2, ..., xk): 
    #   y >= xi for i in 1..k
    #   y <= xi + (umax - l_i)*(1-b_i)
    # Where umax = max(u_1, u_2, ..., u_k) and b_i = 1 -> xi = max(x1, x2, ..., xk)

    b = []
    u_max = max(dom[i][1] for i in range(len(arr)))
    for i in range(len(arr)):
        b.append(model.addVar(vtype=GRB.BINARY, name=f"{key}_b_{i}"))
        model.addConstr(y >= arr[i], name=f"{key}_max1_{i}")
        model.addConstr(y <= arr[i] + (u_max - dom[i][0])*(1-b[i]), name=f"{key}_max2_{i}")

    model.addConstr(sum(b) == 1, f"{key}_sum_b")
    return y