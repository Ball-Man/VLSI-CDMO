import docplex.mp
from docplex.mp.model import Model

def solve(width, n, circuits, sort_column_row = False, export_file=None):
    m = Model("mip1")
    m.set_time_limit(5*60)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([circuits[i][0] for i in range(n)]), sum([circuits[i][0] for i in range(n)]))
    

    x = []
    y = []
    for i in range(n):
        x.append(m.integer_var(name=f"x_{i}"))
        y.append(m.integer_var(name=f"y_{i}"))
        m.add_constraint(x[i] <= width - circuits[i][0], ctname=f"width_{i}")
    
    print(f"Best height: {min_height}")
    
    height = m.integer_var(name="height")
    linear_max(
        [y[i] + circuits[i][1] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, m, "height")
        
    m.add_constraint(height >= min_height, ctname="optimal_solution")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            reify_or(
                [
                    -x[i] + x[j] + circuits[j][0],
                    -x[j] + x[i] + circuits[i][0],
                    -y[i] + y[j] + circuits[j][1],
                    -y[j] + y[i] + circuits[i][1]
                ],
                [
                    circuits[j][0] + width,
                    circuits[i][0] + width,
                    circuits[j][1] + max_height,
                    circuits[i][1] + max_height
                ], m, f"diffn_{i}_{j}_")



    # Symmetry breaking
    # Horizontal
    lex_less(x, [width - x[i] - circuits[i][0] for i in range(0,n)], [(0, width) for _ in range(0,n)], [(0, width) for _ in range(0,n)], m, "horizontal_symmetry")

    # Vertical
    lex_less(y, [height - y[i] - circuits[i][1] for i in range(0,n)], [(0, max_height) for _ in range(0,n)], [(0, max_height) for _ in range(0,n)], m, "vertical_symmetry")
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1]:
                lex_less([x[i], y[i]], [x[j], y[j]], [(0,width), (0,max_height)], [(0,width), (0,max_height)], m, f"equal_{i}_{j}")


    
    if sort_column_row:
        # Same width and same column sort by size in descending order 
        # w[i] = w[j] /\ h[i] < h[j] |= (x[i] = x[j] /\ h[i] = y[j] - y[i]) -> y[j] < y[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][0] == circuits[j][0]:
                    (h,k) = (i,j) if circuits[i][1] < circuits[j][1] else (j,i) # if h[i] > h[j] swap i with j

                    reify_or(
                        [
                            x[h] - x[k] + 1,                        # x[i] <= x[j] - 1
                            x[k] - x[h] + 1,                        # x[i] >= x[j] + 1
                            y[k] - y[h] - circuits[h][1] + 1,       # h[i] <= y[j] - y[i] - 1
                            y[h] - y[k] + circuits[h][1] + 1,       # h[i] >= y[j] - y[i] + 1
                            y[k] - y[h] + 1                         # y[j] <= y[i] - 1
                        ],
                        [
                            1 + width,                              # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            1 + width,                              # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            - circuits[h][1] + 1 + max_height,      # - h[i] + 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            circuits[h][1] + 1 + max_height,        # h[i] + 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            1 + max_height                          # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                        ], m, f"same_column_{h}_{k}"
                    )


        # Same height and same row in ascending order 
        # h[i] = h[j] /\ w[i] < w[j] |= (y[i] = y[j] /\ w[i] = x[j] - x[i]) -> x[j] < x[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][1] == circuits[j][1]:
                    (h,k) = (i,j) if circuits[i][0] < circuits[j][0] else (j,i) # if h[i] > h[j] swap i with j

                    reify_or(
                        [
                            y[h] - y[k] + 1,                        # y[i] <= y[j] - 1
                            y[k] - y[h] + 1,                        # y[i] >= y[j] + 1
                            x[k] - x[h] - circuits[h][0] + 1,       # w[i] <= x[j] - x[i] - 1
                            x[h] - x[k] + circuits[h][0] + 1,       # w[i] >= x[j] - x[i] + 1
                            x[k] - x[h] + 1                         # x[j] <= x[i] - 1
                        ],
                        [
                            1 + max_height,                         # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            1 + max_height,                         # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            - circuits[h][0] + 1 + width,           # - w[i] + 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            circuits[h][0] + 1 + width,             # w[i] + 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            1 + width                               # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                        ], m, f"same_column_{h}_{k}"
                    )

    
    
    m.minimize(height)
    sol = m.solve()
    print(m.solve_details)
    if export_file is not None:
        m.write(export_file)
        print(f"Model exported in {export_file}")

    rect = [(circuits[i][0], circuits[i][1], round(sol.get_value(x[i])), round(sol.get_value(y[i]))) for i in range(n)]
    return {"result": {"width": width, "height": round(sol.get_value(height)), "rect": rect},
            "statistics": m.get_statistics().__dict__,
            "status": m.solve_details.status}



def reify_or(arr, big_m, model, key):
    b = []
    for i in range(len(arr)):
        b.append(model.binary_var(name=f"{key}_b_{i}"))
        model.add_constraint(arr[i] <= big_m[i]*(1-b[i]), ctname=f"{key}_{i}")
    model.add_constraint(sum(b) >= 1, ctname=f"{key}_b_sum")

def lex_less(arr1, arr2, dom1, dom2, model, key):
    for i in range(len(arr1)):
        reify_or(
            [ arr1[k] - arr2[k] + 1 for k in range(0,i)] +   # x_k < y_k \/
            [-arr1[k] + arr2[k] + 1 for k in range(0,i)] +   # x_k > y_k \/
            [arr1[i] - arr2[i]],                            # x_i <= y_i
            [1 + dom1[k][1] - dom2[k][0] for k in range(0,i)] + #  B = -1, Mk = 1 + max(dom1[k]) + max(-1*dom2[k][0], -1*dom2[k][1])   ->   1 + dom1[k][1] - dom2[k][0]
            [1 - dom1[k][0] + dom2[k][1] for k in range(0,i)] + #  B = -1, Mk = 1 + max(-1*dom1[k][0], -1*dom1[k][1]) + max(dom2[k])   ->   1 - dom1[k][0] + dom2[k][1]
            [dom1[i][1]], model, f"{key}_{i}")
    
def linear_max(arr, dom, y, model, key):
    b = []
    u_max = max(dom[i][1] for i in range(len(arr)))
    for i in range(len(arr)):
        b.append(model.binary_var(name=f"{key}_b_{i}"))
        model.add_constraint(y >= arr[i], ctname=f"{key}_max1_{i}")
        model.add_constraint(y <= arr[i] + (u_max - dom[i][0])*(1-b[i]), ctname=f"{key}_max2_{i}")

    model.add_constraint(sum(b) == 1, ctname=f"{key}_sum_b")
    return y