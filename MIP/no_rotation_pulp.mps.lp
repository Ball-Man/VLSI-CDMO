\* no_rotation *\
Minimize
OBJ: height
Subject To
diffn_0_1_0: 11 diffn_0_1_b_0 - x_0 + x_1 <= 8
diffn_0_1_1: 11 diffn_0_1_b_1 + x_0 - x_1 <= 8
diffn_0_1_2: 21 diffn_0_1_b_2 - y_0 + y_1 <= 16
diffn_0_1_3: 19 diffn_0_1_b_3 + y_0 - y_1 <= 16
diffn_0_1_b_sum: diffn_0_1_b_0 + diffn_0_1_b_1 + diffn_0_1_b_2 + diffn_0_1_b_3
 >= 1
diffn_0_2_0: 13 diffn_0_2_b_0 - x_0 + x_2 <= 8
diffn_0_2_1: 11 diffn_0_2_b_1 + x_0 - x_2 <= 8
diffn_0_2_2: 19 diffn_0_2_b_2 - y_0 + y_2 <= 16
diffn_0_2_3: 19 diffn_0_2_b_3 + y_0 - y_2 <= 16
diffn_0_2_b_sum: diffn_0_2_b_0 + diffn_0_2_b_1 + diffn_0_2_b_2 + diffn_0_2_b_3
 >= 1
diffn_0_3_0: 13 diffn_0_3_b_0 - x_0 + x_3 <= 8
diffn_0_3_1: 11 diffn_0_3_b_1 + x_0 - x_3 <= 8
diffn_0_3_2: 21 diffn_0_3_b_2 - y_0 + y_3 <= 16
diffn_0_3_3: 19 diffn_0_3_b_3 + y_0 - y_3 <= 16
diffn_0_3_b_sum: diffn_0_3_b_0 + diffn_0_3_b_1 + diffn_0_3_b_2 + diffn_0_3_b_3
 >= 1
diffn_1_2_0: 13 diffn_1_2_b_0 - x_1 + x_2 <= 8
diffn_1_2_1: 11 diffn_1_2_b_1 + x_1 - x_2 <= 8
diffn_1_2_2: 19 diffn_1_2_b_2 - y_1 + y_2 <= 16
diffn_1_2_3: 21 diffn_1_2_b_3 + y_1 - y_2 <= 16
diffn_1_2_b_sum: diffn_1_2_b_0 + diffn_1_2_b_1 + diffn_1_2_b_2 + diffn_1_2_b_3
 >= 1
diffn_1_3_0: 13 diffn_1_3_b_0 - x_1 + x_3 <= 8
diffn_1_3_1: 11 diffn_1_3_b_1 + x_1 - x_3 <= 8
diffn_1_3_2: 21 diffn_1_3_b_2 - y_1 + y_3 <= 16
diffn_1_3_3: 21 diffn_1_3_b_3 + y_1 - y_3 <= 16
diffn_1_3_b_sum: diffn_1_3_b_0 + diffn_1_3_b_1 + diffn_1_3_b_2 + diffn_1_3_b_3
 >= 1
diffn_2_3_0: 13 diffn_2_3_b_0 - x_2 + x_3 <= 8
diffn_2_3_1: 13 diffn_2_3_b_1 + x_2 - x_3 <= 8
diffn_2_3_2: 21 diffn_2_3_b_2 - y_2 + y_3 <= 16
diffn_2_3_3: 19 diffn_2_3_b_3 + y_2 - y_3 <= 16
diffn_2_3_b_sum: diffn_2_3_b_0 + diffn_2_3_b_1 + diffn_2_3_b_2 + diffn_2_3_b_3
 >= 1
height_max1_0: height - y_0 >= 3
height_max1_1: height - y_1 >= 5
height_max1_2: height - y_2 >= 3
height_max1_3: height - y_3 >= 5
height_max2_0: height + 16 height_b_0 - y_0 <= 19
height_max2_1: height + 16 height_b_1 - y_1 <= 21
height_max2_2: height + 16 height_b_2 - y_2 <= 19
height_max2_3: height + 16 height_b_3 - y_3 <= 21
height_sum_b: height_b_0 + height_b_1 + height_b_2 + height_b_3 = 1
horizontal_symmetry_0_0: 8 horizontal_symmetry_0_b_0 + 2 x_0 <= 13
horizontal_symmetry_0_b_sum: horizontal_symmetry_0_b_0 >= 1
horizontal_symmetry_1_0: 9 horizontal_symmetry_1_b_0 + 2 x_0 <= 13
horizontal_symmetry_1_1: 9 horizontal_symmetry_1_b_1 - 2 x_0 <= 3
horizontal_symmetry_1_2: 8 horizontal_symmetry_1_b_2 + 2 x_1 <= 13
horizontal_symmetry_1_b_sum: horizontal_symmetry_1_b_0
 + horizontal_symmetry_1_b_1 + horizontal_symmetry_1_b_2 >= 1
horizontal_symmetry_2_0: 9 horizontal_symmetry_2_b_0 + 2 x_0 <= 13
horizontal_symmetry_2_1: 9 horizontal_symmetry_2_b_1 + 2 x_1 <= 13
horizontal_symmetry_2_2: 9 horizontal_symmetry_2_b_2 - 2 x_0 <= 3
horizontal_symmetry_2_3: 9 horizontal_symmetry_2_b_3 - 2 x_1 <= 3
horizontal_symmetry_2_4: 8 horizontal_symmetry_2_b_4 + 2 x_2 <= 11
horizontal_symmetry_2_b_sum: horizontal_symmetry_2_b_0
 + horizontal_symmetry_2_b_1 + horizontal_symmetry_2_b_2
 + horizontal_symmetry_2_b_3 + horizontal_symmetry_2_b_4 >= 1
horizontal_symmetry_3_0: 9 horizontal_symmetry_3_b_0 + 2 x_0 <= 13
horizontal_symmetry_3_1: 9 horizontal_symmetry_3_b_1 + 2 x_1 <= 13
horizontal_symmetry_3_2: 9 horizontal_symmetry_3_b_2 + 2 x_2 <= 11
horizontal_symmetry_3_3: 9 horizontal_symmetry_3_b_3 - 2 x_0 <= 3
horizontal_symmetry_3_4: 9 horizontal_symmetry_3_b_4 - 2 x_1 <= 3
horizontal_symmetry_3_5: 9 horizontal_symmetry_3_b_5 - 2 x_2 <= 5
horizontal_symmetry_3_6: 8 horizontal_symmetry_3_b_6 + 2 x_3 <= 11
horizontal_symmetry_3_b_sum: horizontal_symmetry_3_b_0
 + horizontal_symmetry_3_b_1 + horizontal_symmetry_3_b_2
 + horizontal_symmetry_3_b_3 + horizontal_symmetry_3_b_4
 + horizontal_symmetry_3_b_5 + horizontal_symmetry_3_b_6 >= 1
optimal_solution: height >= 8
vertical_symmetry_0_0: - height + 16 vertical_symmetry_0_b_0 + 2 y_0 <= 13
vertical_symmetry_0_b_sum: vertical_symmetry_0_b_0 >= 1
vertical_symmetry_1_0: - height + 17 vertical_symmetry_1_b_0 + 2 y_0 <= 13
vertical_symmetry_1_1: height + 17 vertical_symmetry_1_b_1 - 2 y_0 <= 19
vertical_symmetry_1_2: - height + 16 vertical_symmetry_1_b_2 + 2 y_1 <= 11
vertical_symmetry_1_b_sum: vertical_symmetry_1_b_0 + vertical_symmetry_1_b_1
 + vertical_symmetry_1_b_2 >= 1
vertical_symmetry_2_0: - height + 17 vertical_symmetry_2_b_0 + 2 y_0 <= 13
vertical_symmetry_2_1: - height + 17 vertical_symmetry_2_b_1 + 2 y_1 <= 11
vertical_symmetry_2_2: height + 17 vertical_symmetry_2_b_2 - 2 y_0 <= 19
vertical_symmetry_2_3: height + 17 vertical_symmetry_2_b_3 - 2 y_1 <= 21
vertical_symmetry_2_4: - height + 16 vertical_symmetry_2_b_4 + 2 y_2 <= 13
vertical_symmetry_2_b_sum: vertical_symmetry_2_b_0 + vertical_symmetry_2_b_1
 + vertical_symmetry_2_b_2 + vertical_symmetry_2_b_3 + vertical_symmetry_2_b_4
 >= 1
vertical_symmetry_3_0: - height + 17 vertical_symmetry_3_b_0 + 2 y_0 <= 13
vertical_symmetry_3_1: - height + 17 vertical_symmetry_3_b_1 + 2 y_1 <= 11
vertical_symmetry_3_2: - height + 17 vertical_symmetry_3_b_2 + 2 y_2 <= 13
vertical_symmetry_3_3: height + 17 vertical_symmetry_3_b_3 - 2 y_0 <= 19
vertical_symmetry_3_4: height + 17 vertical_symmetry_3_b_4 - 2 y_1 <= 21
vertical_symmetry_3_5: height + 17 vertical_symmetry_3_b_5 - 2 y_2 <= 19
vertical_symmetry_3_6: - height + 16 vertical_symmetry_3_b_6 + 2 y_3 <= 11
vertical_symmetry_3_b_sum: vertical_symmetry_3_b_0 + vertical_symmetry_3_b_1
 + vertical_symmetry_3_b_2 + vertical_symmetry_3_b_3 + vertical_symmetry_3_b_4
 + vertical_symmetry_3_b_5 + vertical_symmetry_3_b_6 >= 1
width_0: x_0 <= 5
width_1: x_1 <= 5
width_2: x_2 <= 3
width_3: x_3 <= 3
Bounds
 0 <= height <= 16
 0 <= x_0 <= 5
 0 <= x_1 <= 5
 0 <= x_2 <= 3
 0 <= x_3 <= 3
 0 <= y_0 <= 13
 0 <= y_1 <= 11
 0 <= y_2 <= 13
 0 <= y_3 <= 11
Generals
height
x_0
x_1
x_2
x_3
y_0
y_1
y_2
y_3
Binaries
diffn_0_1_b_0
diffn_0_1_b_1
diffn_0_1_b_2
diffn_0_1_b_3
diffn_0_2_b_0
diffn_0_2_b_1
diffn_0_2_b_2
diffn_0_2_b_3
diffn_0_3_b_0
diffn_0_3_b_1
diffn_0_3_b_2
diffn_0_3_b_3
diffn_1_2_b_0
diffn_1_2_b_1
diffn_1_2_b_2
diffn_1_2_b_3
diffn_1_3_b_0
diffn_1_3_b_1
diffn_1_3_b_2
diffn_1_3_b_3
diffn_2_3_b_0
diffn_2_3_b_1
diffn_2_3_b_2
diffn_2_3_b_3
height_b_0
height_b_1
height_b_2
height_b_3
horizontal_symmetry_0_b_0
horizontal_symmetry_1_b_0
horizontal_symmetry_1_b_1
horizontal_symmetry_1_b_2
horizontal_symmetry_2_b_0
horizontal_symmetry_2_b_1
horizontal_symmetry_2_b_2
horizontal_symmetry_2_b_3
horizontal_symmetry_2_b_4
horizontal_symmetry_3_b_0
horizontal_symmetry_3_b_1
horizontal_symmetry_3_b_2
horizontal_symmetry_3_b_3
horizontal_symmetry_3_b_4
horizontal_symmetry_3_b_5
horizontal_symmetry_3_b_6
vertical_symmetry_0_b_0
vertical_symmetry_1_b_0
vertical_symmetry_1_b_1
vertical_symmetry_1_b_2
vertical_symmetry_2_b_0
vertical_symmetry_2_b_1
vertical_symmetry_2_b_2
vertical_symmetry_2_b_3
vertical_symmetry_2_b_4
vertical_symmetry_3_b_0
vertical_symmetry_3_b_1
vertical_symmetry_3_b_2
vertical_symmetry_3_b_3
vertical_symmetry_3_b_4
vertical_symmetry_3_b_5
vertical_symmetry_3_b_6
End
