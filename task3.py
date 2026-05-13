import hashlib
import os
import time


ORIGINAL_FILE = "test_128mb.bin"
REPLACEMENT_FILE = "test_1mb.bin"

NUM_BLOCKS = 128
BLOCK_SIZE = 1024 * 1024
TOTAL_SIZE = NUM_BLOCKS * BLOCK_SIZE


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def read_binary_file(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()


def split_into_blocks(data: bytes) -> list:
    if len(data) != TOTAL_SIZE:
        raise ValueError(f"File size mismatch: expected {TOTAL_SIZE} bytes, got {len(data)} bytes")

    blocks = []
    for i in range(NUM_BLOCKS):
        start = i * BLOCK_SIZE
        end = start + BLOCK_SIZE
        blocks.append(data[start:end])
    return blocks


def build_merkle_tree_from_blocks(blocks: list) -> list:
    tree = []

    current_level = [sha256(block) for block in blocks]
    tree.append(current_level)

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            parent_hash = sha256(current_level[i] + current_level[i + 1])
            next_level.append(parent_hash)
        tree.append(next_level)
        current_level = next_level

    return tree


def replace_node(tree: list, block_index: int, new_block: bytes) -> list:
    if not 0 <= block_index < NUM_BLOCKS:
        raise ValueError(f"Block index must be between 0 and {NUM_BLOCKS - 1}")

    if len(new_block) != BLOCK_SIZE:
        raise ValueError(f"Replacement block must be exactly {BLOCK_SIZE} bytes")

    updated_tree = [level.copy() for level in tree]
    current_idx = block_index

    # Update the changed leaf first.
    updated_tree[0][current_idx] = sha256(new_block)

    # Recompute only the affected path from leaf to root.
    for level in range(len(updated_tree) - 1):
        parent_idx = current_idx // 2
        left_idx = parent_idx * 2
        right_idx = left_idx + 1

        left_hash = updated_tree[level][left_idx]
        right_hash = updated_tree[level][right_idx]
        updated_tree[level + 1][parent_idx] = sha256(left_hash + right_hash)

        current_idx = parent_idx

    return updated_tree


def get_block_index() -> int:
    while True:
        try:
            block_index = int(input(f"Enter block index to replace (0 ~ {NUM_BLOCKS - 1}): "))
            if 0 <= block_index < NUM_BLOCKS:
                return block_index
            print("Out of range.")
        except ValueError:
            print("Invalid input. Please enter an integer.")


def main():
    print("=" * 40)
    print(" Task 3: Efficient Node Replacement")
    print("=" * 40)

    if not os.path.exists(ORIGINAL_FILE):
        print(f"Error: '{ORIGINAL_FILE}' not found. Please run data_gen/generate_128mb.py first.")
        return

    if not os.path.exists(REPLACEMENT_FILE):
        print(f"Error: '{REPLACEMENT_FILE}' not found. Please run data_gen/generate_1mb.py first.")
        return

    print("1. Loading original data...")
    original_data = read_binary_file(ORIGINAL_FILE)
    replacement_block = read_binary_file(REPLACEMENT_FILE)
    original_blocks = split_into_blocks(original_data)

    print("2. Building original Merkle Tree...")
    original_tree = build_merkle_tree_from_blocks(original_blocks)
    original_root = original_tree[-1][0]

    block_index = get_block_index()

    print("3. Updating Merkle Tree with replace_node()...")
    start_time_path_update = time.time()
    updated_tree = replace_node(original_tree, block_index, replacement_block)
    path_update_time = time.time() - start_time_path_update
    updated_root_path = updated_tree[-1][0]

    print("4. Rebuilding full Merkle Tree for verification...")
    updated_blocks = original_blocks.copy()
    updated_blocks[block_index] = replacement_block

    start_time_full_rebuild = time.time()
    rebuilt_tree = build_merkle_tree_from_blocks(updated_blocks)
    full_rebuild_time = time.time() - start_time_full_rebuild
    updated_root_full = rebuilt_tree[-1][0]

    verification_result = updated_root_path == updated_root_full

    if path_update_time > 0:
        speedup = full_rebuild_time / path_update_time
    else:
        speedup = float("inf")

    print("\n[Output]")
    print(f"Original Root              : {original_root.hex()}")
    print(f"Updated Root (replace_node): {updated_root_path.hex()}")
    print(f"Updated Root (full tree)   : {updated_root_full.hex()}")
    print(f"Verification Result        : {'PASS' if verification_result else 'FAIL'}")
    print(f"Path Update Time           : {path_update_time:.6f} seconds")
    print(f"Full Reconstruction Time   : {full_rebuild_time:.6f} seconds")
    print(f"Performance Comparison     : {speedup:.2f}x faster")
    print("=" * 40)


if __name__ == "__main__":
    main()
