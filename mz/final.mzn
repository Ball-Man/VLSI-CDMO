include "globals.mzn";

% Input
int: width;
int: n;
% Array of circuits (pairs): circuits[i, j] selects the j-th dimension of the
% i-th circuit (dimension 0 is the width, dimension 1 is the height).
array[1..n, 0..1] of int: circuits;
array[1..n] of int: areas = [circuits[i, 0] * circuits[i, 1]| i in 1..n];
int: max_height = sum(col(circuits, 1));
int: min_height = max([max(areas) div width, max(col(circuits, 1))]);

var min_height..max_height: height;
array[1..n, 0..1] of var 0..max(
  [max_height - min(col(circuits, 1)),
   width - min(col(circuits, 0))]): positions;

constraint diffn(
  col(positions, 0),
  col(positions, 1),
  col(circuits, 0),
  col(circuits, 1));

% Constrain domain
constraint min(positions) >= 0;
constraint max([positions[i, 0] + circuits[i, 0]| i in 1..n]) <= width;
constraint height = max([positions[i, 1] + circuits[i, 1]| i in 1..n]);


% Contrain overlapping rectangles
/*
constraint forall(i in 1..n, j in 1..n where i < j) (
  not circuit_collision(i, j)
);*/

predicate circuit_collision(int: a, int: b) = (
  positions[a, 0] < positions[b, 0] + circuits[b, 0]
   /\ positions[a, 0] + circuits[a, 0] > positions[b, 0]
   /\ positions[a, 1] < positions[b, 1] + circuits[b, 1]
   /\ positions[a, 1] + circuits[a, 1] > positions[b, 1]
);

% Redundant constraints
constraint cumulative(
  col(positions, 0), col(circuits, 0), col(circuits, 1), height);
constraint cumulative(
  col(positions, 1), col(circuits, 1), col(circuits, 0), width);

% Simmetry breaking constraints
constraint lex_lesseq(
  col(positions, 0),
  [width - positions[i, 0] - circuits[i, 0]| i in 1..n]);

/*
constraint lex_lesseq(
  col(positions, 1),
  [height - positions[i, 1] - circuits[i, 1]| i in 1..n]);
*/
%height = 18;
solve
  :: seq_search([
    int_search([height], input_order, indomain_min),
    int_search(positions, dom_w_deg, indomain_min)])
  minimize height;
%solve satisfy;

output [
  "\(width) \(height)\n\(n)\n",
] ++ [
  "\(circuits[i, 0]) \(circuits[i, 1]) \(positions[i, 0]) \(positions[i, 1])\n"
  | i in 1..n
];
