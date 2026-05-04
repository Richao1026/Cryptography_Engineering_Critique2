# Cryptography Engineering: Critique & Implementation 2

**Instructor:** J. R. Shieh  
**Date:** April 16, 2026  
**Deadline:** May 15, 2026, 23:59 Taiwan Time  

---

## Critique (100 points)

Please read the paper: *A digital signature based on a conventional encryption function* by Ralph C. Merkle. Then write a critique about this paper. The critique should follow these requests:

*   English text-only, about 1000-1200 words.
*   Realization of a technical specification, mechanism or algorithm to mitigate this paper.
*   Please feel free to use ChatGPT, Gemini, or other AI tools to assist your studies and let me know which answer seems more reasonable.
*   Please answer the following questions in your critique:
    *   **Name of the paper**
    *   **Summary:**
        *   What problem is the paper trying to solve?
        *   Why does the problem matter?
        *   What is the approach used to solve the problem?
        *   What is the conclusion drawn from this work?
        *   Strength(s) of the paper
        *   Weakness(es) of the paper
    *   **Your own reflection**, which can include but not limited to:
        *   What did you learn from this paper?
        *   How would you improve or extend the work if you were the author?
        *   What are the unsolved questions that you want to investigate?
        *   What are the broader impacts of this proposed technology?
        *   Else?
    *   **Realization** of a technical specification or algorithm to mitigate this paper.

---

## Implementation (100 points)

### Project Overview
In large-scale systems (e.g., 1TB files or Blockchain state databases), traditional hashing (Single Hash) is inefficient for updates and error localization. This lab requires you to implement a Dynamic Merkle Tree system capable of detecting, localizing, and replacing data blocks with O(log n) efficiency.

### Test Data Generation
Please use the code provided in E3, to ensure that the input data format is correct.
*   `generate_128mb.py`: Generate the main dataset `test_128mb.bin`, which serves as the original input file for all tasks.
*   `generate_corrupted.py`: Generate a corrupted version of the dataset by flipping a single bit. Input: `test_128mb.bin`
*   `generate_1mb.py`: Generate a single block of data used for replacement operations in Task 3.
*   `export_trusted_merkle_tree.py`: Generate the trusted Merkle Tree from the original dataset. Input: `test_128mb.bin`
*   `export_parity_blocks.py`: Generate parity blocks for error recovery in Task 4. Input `test_128mb.bin`

---

### Task 1 – Single Hash vs. Merkle Tree (Baseline)
*   **Objective:** Compare the “All-or-Nothing” approach with the Merkle Tree structure.
*   **Scenario:** Simulate a 128MB file divided into 2^7 (128) blocks.
*   **Goals:**
    *   Compute a single SHA-256 hash for the entire 128MB file.
    *   Construct a Merkle Tree for the same file.
    *   Report the time taken for initial construction and the memory overhead of storing the internal nodes of the tree.
*   **Input format:** `test_128mb.bin` (includes 128MB raw binary data).
*   **Output format:**
    1.  **Single hash result:** SHA-256 value of the whole file, Time spent calculating.
    2.  **Merkle Tree result:** Merkle Root, Time spent calculating the whole tree, Internal node memory overhead.

---

### Task 2 – Efficient Error Localization (The “Detective” Module)
*   **Objective:** Implement a top-down search algorithm to find corrupted data.
*   **Scenario:** One random bit in one block among the 128 blocks has been flipped. You have to develop the module to find which block is corrupted.
*   **Goals:**
    1.  Use the `test_128mb_corrupted.bin` file to recreate a new Merkle Tree.
    2.  Implement the `locate_error()` function along with the `trusted_merkle_tree.bin` file to find the corrupted block.
    3.  In the `locate_error()` function, record how many hash comparisons are performed during the search process.
*   **Input format:** `test_128mb_corrupted.bin`, `trusted_merkle_tree.bin`. *(No original clean data is provided).*
*   **Output format:** Trusted Root, Corrupted file root, Corrupted block index, Comparison count.
*   **Additional constraint:** You must demonstrate in the report that the number of hash comparisons is exactly H (height of the tree), which is log2(n).

---

### Task 3 – Efficient Node Replacement (The “Update” Module)
*   **Objective:** Update the global signature (Merkle Root) after modifying a single block, and demonstrate the efficiency of path update compared to full tree reconstruction.
*   **Scenario:** A user replaces the data in one block among the 128 blocks. You have to update the Merkle Tree accordingly and compute the new root efficiently.
*   **Goals:**
    1.  Use `test_128mb.bin` to recreate the original Merkle Tree.
    2.  Replace one block using the `test_1mb.bin` file.
    3.  Implement the `replace_node()` function to update only the affected path (from leaf to root).
    4.  Recompute the Merkle Root using two approaches: Path update vs. Full tree reconstruction.
    5.  Measure and compare the execution time.
*   **Input format:** `test_128mb.bin`, `test_1mb.bin`, User input block index (0~127).
*   **Output format:** Original Root, Updated Root (replace_node), Updated Root (full tree), Verification result, Execution times, Performance comparison.

---

### Task 4 – Advanced Self-Healing (The “Correction” Module)
*   **Objective:** Integrate Error Correction (XOR Parity) with Merkle Tree Detection.
*   **Scenario:** One random bit is flipped. You are given only the corrupted data, the trusted tree, and parity blocks. You must locate the corrupted block and recover the original data.
*   **Goals:**
    1.  Use `trusted_merkle_tree.bin` to verify integrity and locate the corrupted block via `locate_error()`.
    2.  Use `parity_blocks.bin` and the corresponding sibling block to reconstruct the correct block data.
    3.  Use the `replace_node()` function to restore the Merkle Tree.
    4.  Verify that the repaired Merkle Root matches the trusted root.
*   **Input format:** `test_128mb_corrupted.bin`, `trusted_merkle_tree.bin`, `parity_blocks.bin`. *(No original clean data is provided).*
*   **Output format:** Trusted Root, Corrupted file root, Corrupted block index, Comparison count, Parity block index used, Sibling block index, Repaired Merkle Root, Verification result.
*   **Additional constraint:** Demonstrate that the corrupted block can be correctly identified using only the corrupted file and the trusted Merkle Tree.

---

## Implementation Report
You must complete the following comparison table based on simulation results (n = 2^7 blocks):

| Operation | Single Hash | Merkle Tree | Improvement Factor |
| :--- | :--- | :--- | :--- |
| **Detecting Error** | Scans ? MB | Scans ? MB | |
| **Localizing Error** | Impossible | ? comparisons | |
| **Updating 1 Block** | Computes ? MB | Computes ? MB | |
| **Proof Size (Bytes)** | | | |

*Provide a thorough discussion of your findings, experimental results (execution time, memory overhead).*

---

## Grading & Submission Guidelines
*   **Critique:** 10% of final score (graded out of 100 points).
*   **Implementation:** 5% of final score (graded out of 100 points).
    *   Task 1~4: 20 points each.
    *   Report: 20 points.
*   **Late Penalty:** 0.5 points deducted per day (max 20 days).

**Upload a zip file containing:**
*   `<group_number>_project2.zip`
    *   `task1.py`, `task2.py`, `task3.py`, `task4.py`
    *   `<group_number>_critique.pdf`
    *   `<group_number>_report.pdf`
