"""Naive strip based first fit for 2D packing.

Used to obtain a more tractable height upper bound for the VLSI
instances.

Executes in O(n^2), with n number of circuits.

Python >= 3.8.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """Node of a binary tree.

    Only leaves of the tree can be free nodes. To each node a circuit
    can be assigned. When it happens, up to two children nodes
    shall be created (the empty space left by the given).
    """
    x: int
    y: int
    w: int
    h: int
    circuit: Optional[list[int, int]] = None
    children: list['Node'] = field(default_factory=lambda: [])

    def place(self, circuit: list[int, int]) -> bool:
        """Place a circuit in the node and create new children.

        Return a boolean representing whether the circuit could be
        placed. A circuit can't be placed if: the node is not big enough
        for it or it has already been assigned.
        """
        # Check if the circuit can be assigned
        if (self.circuit is not None or circuit[0] > self.w
                or circuit[1] > self.h):
            return False

        self.circuit = circuit

        # Compute and eventually add two new children
        # Don't add if they are zero length
        right_child = Node(self.x + circuit[0], self.y, self.w - circuit[0],
                           circuit[1])
        if right_child.is_valid:
            self.children.append(right_child)

        up_child = Node(self.x, self.y + circuit[1], self.w,
                        self.h - circuit[1])
        if up_child.is_valid:
            self.children.append(up_child)

        return True

    @property
    def is_valid(self):
        """Get whether a node is valid (not zero in size)."""
        return self.w > 0 and self.h > 0


def first_fit(node, circuit):
    """Recursively compute the first fit displacement for a circuit."""
    result = False

    # If there are children, propagate
    for child in node.children:
        result = first_fit(child, circuit)
        if result:
            break
    # Otherwise, try placing
    else:
        result = node.place(circuit)

    return result


def first_fit_all(width, circuits) -> Node:
    """Displace all circuits using first fit."""
    # Height of the first node, upper bound
    height = sum(c[1] for c in circuits)
    # print('tree height', height)
    tree = Node(0, 0, width, height)

    for c in circuits:
        result = first_fit(tree, c)
        if not result:
            raise Exception('Unsolvable. This should not be possible. '
                            'Almost certainly it\'s a bug in my program, '
                            'contact me (mistri)')

    return tree


def _get_max_height(node) -> int:
    """Recursively inspect node to obtain the maximum height reached."""
    reached = 0
    # Each node computes its maximal reached value
    if node.circuit is not None:
        reached = node.y + node.circuit[1]

    # Recursively obtain the maximal reached height
    return max((reached, *(_get_max_height(child) for child in node.children)))


def get_max_height(width, circuits) -> int:
    """Get the upper bound for an instance using the first fit method.

    The maximal is computed for both circuits and reversed(circuits),
    this is simply because this method is very sensible to monotonically
    increasing heights. By comparing both results, we fool such
    situations.
    """
    tree = first_fit_all(width, circuits)

    r_circuits = list(reversed(circuits))
    r_tree = first_fit_all(width, r_circuits)

    return min(_get_max_height(tree), _get_max_height(r_tree))
