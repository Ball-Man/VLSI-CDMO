include "globals.mzn";

% Input
int: width;
int: n;
% Array of circuits (pairs): circuits[i, j] selects the j-th dimension of the
% i-th circuit (dimension 0 is the width, dimension 1 is the height).
array[1..n, 0..1] of int: circuits;
array[1..n] of int: areas = [circuits[i, 0] * circuits[i, 1]| i in 1..n];

/*
A set of variables is used to discriminate which chips are rotated.
A new array of circuit sizes is defined based on this (same indexing as the
original one).
*/
array[1..n] of var bool: rotated;
array[1..n, 0..1] of var int: var_circuits;

/*
Minimum height is given by the max between the highest (or widest, taking
rotations into account) given circuit and the
the minimal bounding box height (total area divided by width).
Maximum height is given by the sum of all the maximal dimensions (assuming
we always rotate the chips so that the longest side is used as height).
*/
int: min_circuit_side = min(col(circuits, 0) ++ col(circuits, 1));
int: max_circuit_side = max(col(circuits, 0) ++ col(circuits, 1));
int: max_height = sum([max(row(circuits, i))| i in 1..n]);
int: min_height = max([sum(areas) div width, max_circuit_side]);

var min_height..max_height: height;
array[1..n] of var 0..(width - min_circuit_side): positions_x;
array[1..n] of var 0..(max_height - min_circuit_side): positions_y;

% Constrain rotations
constraint col(var_circuits, 0) = [
  if rotated[i] then circuits[i, 1] else circuits[i, 0] endif| i in 1..n
];

constraint col(var_circuits, 1) = [
  if rotated[i] then circuits[i, 0] else circuits[i, 1] endif| i in 1..n
];

% Constrain overlapping rectangles
constraint diffn(
  positions_x,
  positions_y,
  col(var_circuits, 0),
  col(var_circuits, 1));

% Constrain domain
constraint max([positions_x[i] + var_circuits[i, 0]| i in 1..n]) <= width;
constraint height = max([positions_y[i] + var_circuits[i, 1]| i in 1..n]);

% Redundant constraints
% The task implicitly solves a scheduling task with limited resources
% on both axes.
constraint redundant_constraint(cumulative(
  positions_x, col(var_circuits, 0), col(var_circuits, 1), height));
constraint redundant_constraint(cumulative(
  positions_y, col(var_circuits, 1), col(var_circuits, 0), width));

% Symmetry breaking constraints
/*
Horizontal symmetry is given by solutions where all the elements are "flipped"
so that circuit_new_x = width - circuit_x - circuit_width.
By imposing lexicographic ordering we avoid the existence of such a solution.
*/
constraint symmetry_breaking_constraint(lex_lesseq(
  positions_x,
  [width - positions_x[i] - var_circuits[i, 0]| i in 1..n]));

% Vertical symmetry can be broken similarly.
constraint symmetry_breaking_constraint(lex_lesseq(
  positions_y,
  [height - positions_y[i] - var_circuits[i, 1]| i in 1..n]));

% Break symmetry with identical chips
% However, these instances (without rotation) do not present identical chips
constraint symmetry_breaking_constraint(
  forall (i in 1..n, j in 1..n where i < j) (
    if var_circuits[i, 0] == var_circuits[j, 0]
       /\ var_circuits[i, 1] == var_circuits[j, 1]
       \/ var_circuits[i, 0] == var_circuits[j, 1]
       /\ var_circuits[j, 0] == var_circuits[i, 1] then
      lex_lesseq([positions_x[i], positions_y[i]],
                 [positions_x[j], positions_y[j]])
    endif
  )
);

% Square circuits do not need to be rotated
constraint symmetry_breaking_constraint(
  forall (i in 1..n) (
    if circuits[i, 0] == circuits[i, 1] then
      rotated[i] = false
    endif
  )
);

% Search strategy
/*
Variables (position coordinates) are selected following decreasing area order.
Intuitively, bigger elements shall be placed first. Moreover, such ordering
takes into account the rectangularity of each plate (areas are weighted by the
complementary rectangularity index). Apparently, square-like objects are more
critical than elongated ones.
*/
array[1..n] of float: weighted_areas = [
  (1 - abs(circuits[i, 0] - circuits[i, 1]) / (circuits[i, 0] + circuits[i, 1]))
  * areas[i]
  | i in 1..n
];

array[0..1, 1..n] of var dom_array(positions_x) union dom_array(positions_y):
  sorted_positions_r =
  array2d(0..1, 1..n,
    reverse(sort_by(positions_x, weighted_areas))
    ++ reverse(sort_by(positions_y, weighted_areas))
  );

solve
  :: seq_search([
    int_search([height], input_order, indomain_min),
    bool_search(rotated, input_order, indomain_min),
    int_search([sorted_positions_r[j, i]| j in 0..1, i in 1..n], input_order,
               indomain_min)])
  minimize height;
%solve satisfy;

output [
  "\(width) \(height)\n\(n)\n",
] ++ [
  "\(var_circuits[i, 0]) \(var_circuits[i, 1]) "
  ++ "\(positions_x[i]) \(positions_y[i])\n"
  | i in 1..n
];
