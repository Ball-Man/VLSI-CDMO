include "globals.mzn";

% Input
int: width;
int: n;
% Array of circuits (pairs): circuits[i, j] selects the j-th dimension of the
% i-th circuit (dimension 0 is the width, dimension 1 is the height).
array[1..n, 0..1] of int: circuits;
array[1..n] of int: areas = [circuits[i, 0] * circuits[i, 1]| i in 1..n];

/*
Minimum height is given by the max between the highest given circuit and the
the minimal bounding box height (total area divided by width).
Maximum height is given by the sum of all the heights of the given circuits.
*/
int: max_height = sum(col(circuits, 1));
int: min_height = max([sum(areas) div width, max(col(circuits, 1))]);

var min_height..max_height: height;
array[1..n, 0..1] of var 0..max(
  [max_height - min(col(circuits, 1)),
   width - min(col(circuits, 0))]): positions;

% Constrain overlapping rectangles
constraint diffn(
  col(positions, 0),
  col(positions, 1),
  col(circuits, 0),
  col(circuits, 1));

% Constrain domain
constraint max([positions[i, 0] + circuits[i, 0]| i in 1..n]) <= width;
constraint height = max([positions[i, 1] + circuits[i, 1]| i in 1..n]);

% Redundant constraints
% The task implicitly solves a scheduling task with limited resources
% on both axes.
constraint redundant_constraint(cumulative(
  col(positions, 0), col(circuits, 0), col(circuits, 1), height));
constraint redundant_constraint(cumulative(
  col(positions, 1), col(circuits, 1), col(circuits, 0), width));

% Symmetry breaking constraints
/*
Horizontal symmetry is given by solutions where all the elements are "flipped"
so that circuit_new_x = width - circuit_x - circuit_width.
By imposing lexicographic ordering we avoid the existence of such a solution.
*/
constraint symmetry_breaking_constraint(lex_lesseq(
  col(positions, 0),
  [width - positions[i, 0] - circuits[i, 0]| i in 1..n]));

% Vertical symmetry can be broken similarly. Currently disabled since I suspect
% soem interference with the horizontal one.
constraint symmetry_breaking_constraint(lex_lesseq(
  col(positions, 1),
  [height - positions[i, 1] - circuits[i, 1]| i in 1..n]));


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

array[0..1, 1..n] of var dom_array(positions): sorted_positions_r =
  array2d(0..1, 1..n,
    reverse(sort_by(col(positions, 0), weighted_areas))
    ++ reverse(sort_by(col(positions, 1), weighted_areas))
  );

solve
  :: seq_search([
    int_search([height], input_order, indomain_min),
    int_search([sorted_positions_r[j, i]| j in 0..1, i in 1..n], input_order,
               indomain_min)])
  minimize height;
%solve satisfy;

output [
  "\(width) \(height)\n\(n)\n",
] ++ [
  "\(circuits[i, 0]) \(circuits[i, 1]) \(positions[i, 0]) \(positions[i, 1])\n"
  | i in 1..n
];
