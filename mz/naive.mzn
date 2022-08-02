% Input
int: width;
int: n;
% Array of circuits (pairs): circuits[i, j] selects the j-th dimension of the
% i-th circuit (dimension 0 is the width, dimension 1 is the height).
array[1..n, 0..1] of int: circuits;

solve satisfy;
