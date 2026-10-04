# Prospective structural candidate-pool extension

During initial-population screening, before any reachability pilot or final comparison, many low-weight grid/Shor check sets already attain tier three. Add five deterministic check-basis variants: dense checkerboard grids of widths 3,4,5; dense rectangular Shor 4x4; mixed-generator affine CSS 15.

The dense transform replaces each generator of a Pauli type with its product with every preceding generator of that same type. It is triangular and invertible; stabilizer rank, logical dimension and distance are preserved. It increases measured check weights/overlaps without inserting an optimized architecture. The mixed affine variant replaces one X generator by its product with one Z generator, as in the original control recipe. No V0.3 outcome is used. These remain controls of their named parent codes and cannot be counted as new independent code families.

Use the original screening, target, pilot, and admission rules unchanged. Do not extend the pool further based on final outcomes. This extension tests genuinely different extraction-check architectures, with honest shared-parent dependence, rather than simply enlarging qubit count. Report all original rejections and the timing of this extension.

For mixed X/Z products the input format retains unsigned Hermitian generators. A product may differ by a minus sign, selecting a different consistent stabilizer eigensector. The preserved equivalence is the binary symplectic stabilizer module and distance, not necessarily the identical signed encoded subspace. Dense same-Pauli CSS products do not have this sign ambiguity. No mixed representation is claimed as a new code family.
