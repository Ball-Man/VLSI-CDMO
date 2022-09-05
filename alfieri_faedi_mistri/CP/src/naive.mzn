% Input
int: width;
int: n;
% Array of circuits (pairs): circuits[i, j] selects the j-th dimension of the
% i-th circuit (dimension 0 is the width, dimension 1 is the height).
array[1..n, 0..1] of int: circuits;

var 0..10000: height;
array[1..n, 0..1] of var int: positions;

% Constrain domain
constraint min(positions) >= 0;
constraint max([positions[i, 0] + circuits[i, 0]| i in 1..n]) <= width;
constraint height = max([positions[i, 1] + circuits[i, 1]| i in 1..n]);

% Contrain overlapping rectangles
constraint forall(i in 1..n, j in 1..n where i < j) (
  not circuit_collision(i, j)
);

predicate circuit_collision(int: a, int: b) = (
  positions[a, 0] < positions[b, 0] + circuits[b, 0]
   /\ positions[a, 0] + circuits[a, 0] > positions[b, 0]
   /\ positions[a, 1] < positions[b, 1] + circuits[b, 1]
   /\ positions[a, 1] + circuits[a, 1] > positions[b, 1]
);

solve minimize height;

output [
  "\(width) \(height)\n\(n)\n",
] ++ [
  "\(circuits[i, 0]) \(circuits[i, 1]) \(positions[i, 0]) \(positions[i, 1])\n"
  | i in 1..n
];
