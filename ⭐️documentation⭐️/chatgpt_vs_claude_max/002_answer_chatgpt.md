In linear algebra, **row-echelon form (REF)** and **reduced row-echelon form (RREF)** are used to simplify matrices so that systems of linear equations become easier to analyze and solve.

## 1. Row-echelon form (REF)

A matrix is in row-echelon form when:

1. All zero rows are at the bottom.
2. The first nonzero number in each row, called a **pivot**, is farther right than the pivot in the row above.
3. All entries below each pivot are zero.

Example:

[
\begin{bmatrix}
1 & 2 & -1 & 3\
0 & 1 & 4 & 2\
0 & 0 & 5 & 10
\end{bmatrix}
]

REF is mainly used for **Gaussian elimination**. After converting an augmented matrix to REF, you can solve the system using **back-substitution**.

For example, the last row may represent:

[
5z=10
]

so (z=2). Then you substitute (z) into the row above to find (y), and continue upward to find (x).

## 2. Reduced row-echelon form (RREF)

RREF satisfies all the REF conditions, plus:

1. Every pivot equals (1).
2. Each pivot is the only nonzero entry in its column, meaning entries both above and below it are zero.

Example:

[
\begin{bmatrix}
1 & 0 & 0 & 2\
0 & 1 & 0 & -1\
0 & 0 & 1 & 3
\end{bmatrix}
]

This matrix directly gives:

[
x=2,\qquad y=-1,\qquad z=3
]

No back-substitution is needed.

## What are they used for?

### Solving systems of linear equations

They help determine whether a system has:

* one unique solution,
* infinitely many solutions,
* or no solution.

For example, a row like

[
\begin{bmatrix}
0 & 0 & 0 & 5
\end{bmatrix}
]

represents

[
0=5,
]

which is impossible, so the system has **no solution**.

A row like

[
\begin{bmatrix}
0 & 0 & 0 & 0
\end{bmatrix}
]

does not add a new equation and may indicate that the system has **free variables** and infinitely many solutions.

### Finding the rank of a matrix

The **rank** is the number of pivot positions, or equivalently, the number of nonzero rows in REF or RREF.

For example:

[
\begin{bmatrix}
1 & 2 & 3\
0 & 1 & 4\
0 & 0 & 0
\end{bmatrix}
]

has two pivots, so its rank is (2).

### Finding pivot and free variables

Pivot columns correspond to **basic variables**. Non-pivot columns correspond to **free variables**.

For example:

[
\begin{bmatrix}
1 & 0 & 3 & 4\
0 & 1 & -2 & 5
\end{bmatrix}
]

The first two columns contain pivots, so (x_1) and (x_2) are pivot variables. The third column has no pivot, so (x_3) is a free variable.

### Finding bases for vector spaces

REF and RREF can help find:

* a basis for the row space,
* a basis for the column space,
* a basis for the null space.

One important detail: the nonzero rows of the REF or RREF form a basis for the **row space**, but for the **column space**, you use the corresponding pivot columns from the **original matrix**, not from the reduced matrix.

### Checking linear independence

If every column has a pivot, the columns are linearly independent.

If at least one column does not have a pivot, the columns are linearly dependent.

### Finding matrix inverses

To find (A^{-1}), place (A) beside the identity matrix:

[
[A\mid I]
]

Then row-reduce it. If you obtain

[
[I\mid A^{-1}],
]

the right side is the inverse.

## REF versus RREF

| REF                                | RREF                                   |
| ---------------------------------- | -------------------------------------- |
| Zeros below each pivot             | Zeros above and below each pivot       |
| Pivots do not have to equal (1)    | Every pivot equals (1)                 |
| Usually requires back-substitution | Solutions can usually be read directly |
| Not unique                         | Unique for every matrix                |

The main idea is:

**REF makes a system easier to solve, while RREF makes its complete solution structure easy to see.**
