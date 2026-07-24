Row-echelon form (REF) and reduced row-echelon form (RREF) are the **workhorses** of linear algebra — most concrete computations route through them. Here are the main jobs they do, several of which you've already met under other names:

**1. Solving systems of linear equations** — the original purpose. You row-reduce the augmented matrix [A | b]. REF gets you to a "staircase," then you back-substitute; RREF goes all the way so the answer just sits in the last column (no back-substitution). This is Gaussian / Gauss-Jordan elimination.

**2. Diagnosing how many solutions exist** — read it off the reduced form:
- a pivot in every variable column → **unique solution**
- a free variable (a column with no pivot) → **infinitely many**
- a row like [0 0 0 | 5] (a contradiction) → **no solution**

**3. Finding the rank** — the rank equals the **number of pivots** after reduction. This is exactly the "数主元" rule from your earlier note. Rank then tells you the dimension of the image, whether vectors are independent, etc.

**4. Testing linear independence / whether vectors form a basis** — stack the vectors as rows (or columns) and reduce. Full pivots (no zero rows) ⇔ independent. For a square matrix, full rank ⇔ nonsingular ⇔ they form a basis.

**5. Computing the inverse A⁻¹** — augment [A | I] and row-reduce the left block to I; the right block becomes A⁻¹. If the left block can't reach I (a zero row appears), the matrix is singular and has no inverse.

**6. Finding the solution space / null space** — the free variables after reduction parametrize all solutions of Ax = 0. This is what you used to extract eigenvectors: solving (A − λI)v = 0 is just row-reducing and reading off the free variables.

**7. Finding a basis for the column space or row space** — the pivot columns of the original matrix form a basis for the column space; the nonzero rows of the RREF form a basis for the row space.

The unifying idea: **row reduction strips a matrix down to its essential information** — how many independent pieces of data it really carries (rank), and what the solution structure looks like — without changing the solution set. RREF is special because it's **unique** for any given matrix, so it's the canonical "fully simplified" form; REF is faster to reach but not unique.

Quick mental map of where each shines: **REF** is enough for solving systems (with back-substitution) and counting rank; **RREF** is what you want when you need the answer or the inverse read off directly, or when you need a canonical form to compare matrices.
