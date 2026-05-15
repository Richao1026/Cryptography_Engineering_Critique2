import hashlib
import os


CORRUPTED_FILE = "test_128mb_corrupted.bin"
TRUSTED_TREE_FILE = "trusted_merkle_tree.bin"
PARITY_FILE = "parity_blocks.bin"

NUM_BLOCKS = 128
BLOCK_SIZE = 1024 * 1024
TOTAL_SIZE = NUM_BLOCKS * BLOCK_SIZE
HASH_SIZE = 32


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def read_binary_file(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()


def expected_total_size() -> int:
    return NUM_BLOCKS * BLOCK_SIZE


def validate_power_of_two_block_count() -> None:
    if NUM_BLOCKS <= 0 or NUM_BLOCKS & (NUM_BLOCKS - 1):
        raise ValueError("NUM_BLOCKS must be a positive power of two")


def split_into_blocks(data: bytes) -> list[bytes]:
    expected_size = expected_total_size()
    if len(data) != expected_size:
        raise ValueError(f"File size mismatch: expected {expected_size} bytes, got {len(data)} bytes")

    blocks = []
    for i in range(NUM_BLOCKS):
        start = i * BLOCK_SIZE
        end = start + BLOCK_SIZE
        blocks.append(data[start:end])
    return blocks


def xor_blocks(block_a: bytes, block_b: bytes) -> bytes:
    if len(block_a) != len(block_b):
        raise ValueError(f"Block size mismatch: {len(block_a)} bytes vs {len(block_b)} bytes")
    return bytes(a ^ b for a, b in zip(block_a, block_b))


def build_parity_blocks(blocks: list[bytes]) -> list[bytes]:
    validate_blocks(blocks)

    parity_blocks = []
    for i in range(0, NUM_BLOCKS, 2):
        parity_blocks.append(xor_blocks(blocks[i], blocks[i + 1]))
    return parity_blocks


def validate_blocks(blocks: list[bytes]) -> None:
    if len(blocks) != NUM_BLOCKS:
        raise ValueError(f"Expected {NUM_BLOCKS} blocks, got {len(blocks)} blocks")

    for index, block in enumerate(blocks):
        if len(block) != BLOCK_SIZE:
            raise ValueError(f"Block {index} size mismatch: expected {BLOCK_SIZE} bytes, got {len(block)} bytes")


def build_merkle_tree_from_blocks(blocks: list[bytes]) -> list[list[bytes]]:
    validate_power_of_two_block_count()
    validate_blocks(blocks)

    tree = []
    current_level = [sha256(block) for block in blocks]
    tree.append(current_level)

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            next_level.append(sha256(current_level[i] + current_level[i + 1]))
        tree.append(next_level)
        current_level = next_level

    return tree


def level_sizes() -> list[int]:
    validate_power_of_two_block_count()

    sizes = []
    size = NUM_BLOCKS
    while size >= 1:
        sizes.append(size)
        size //= 2
    return sizes


def load_trusted_tree(filepath: str) -> list[list[bytes]]:
    data = read_binary_file(filepath)
    sizes = level_sizes()
    expected_size = sum(sizes) * HASH_SIZE

    if len(data) != expected_size:
        raise ValueError(f"Trusted tree file size mismatch: expected {expected_size} bytes, got {len(data)} bytes")

    tree = []
    offset = 0
    for level_size in sizes:
        level = []
        for _ in range(level_size):
            level.append(data[offset:offset + HASH_SIZE])
            offset += HASH_SIZE
        tree.append(level)

    return tree


def load_parity_blocks(filepath: str) -> list[bytes]:
    data = read_binary_file(filepath)
    expected_size = (NUM_BLOCKS // 2) * BLOCK_SIZE

    if len(data) != expected_size:
        raise ValueError(f"Parity file size mismatch: expected {expected_size} bytes, got {len(data)} bytes")

    return [
        data[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE]
        for i in range(NUM_BLOCKS // 2)
    ]


def validate_tree_shape(tree: list[list[bytes]], name: str) -> None:
    sizes = level_sizes()
    if len(tree) != len(sizes):
        raise ValueError(f"{name} tree level count mismatch: expected {len(sizes)}, got {len(tree)}")

    for level_index, expected_size in enumerate(sizes):
        if len(tree[level_index]) != expected_size:
            raise ValueError(
                f"{name} tree level {level_index} size mismatch: "
                f"expected {expected_size}, got {len(tree[level_index])}"
            )


def locate_error(trusted_tree: list[list[bytes]], corrupted_tree: list[list[bytes]]) -> tuple[int, int]:
    validate_tree_shape(trusted_tree, "Trusted")
    validate_tree_shape(corrupted_tree, "Corrupted")

    if trusted_tree[-1][0] == corrupted_tree[-1][0]:
        return -1, 0

    comparisons = 0
    current_idx = 0

    # One comparison per tree level: if the left child is trusted, infer the
    # corrupted node is in the right child because the parent root already differs.
    for level in range(len(trusted_tree) - 2, -1, -1):
        left_child_idx = current_idx * 2
        right_child_idx = left_child_idx + 1

        comparisons += 1
        if corrupted_tree[level][left_child_idx] != trusted_tree[level][left_child_idx]:
            current_idx = left_child_idx
        else:
            current_idx = right_child_idx

    return current_idx, comparisons


def recover_block(
    blocks: list[bytes],
    corrupted_block_index: int,
    parity_blocks: list[bytes],
) -> tuple[bytes, int, int]:
    validate_blocks(blocks)

    if not 0 <= corrupted_block_index < NUM_BLOCKS:
        raise ValueError(f"Block index must be between 0 and {NUM_BLOCKS - 1}")

    if len(parity_blocks) != NUM_BLOCKS // 2:
        raise ValueError(f"Expected {NUM_BLOCKS // 2} parity blocks, got {len(parity_blocks)}")

    for index, block in enumerate(parity_blocks):
        if len(block) != BLOCK_SIZE:
            raise ValueError(f"Parity block {index} size mismatch: expected {BLOCK_SIZE} bytes, got {len(block)} bytes")

    parity_index = corrupted_block_index // 2
    if corrupted_block_index % 2 == 0:
        sibling_index = corrupted_block_index + 1
    else:
        sibling_index = corrupted_block_index - 1

    recovered_block = xor_blocks(parity_blocks[parity_index], blocks[sibling_index])
    return recovered_block, parity_index, sibling_index


def replace_node(tree: list[list[bytes]], block_index: int, new_block: bytes) -> list[list[bytes]]:
    validate_tree_shape(tree, "Merkle")

    if not 0 <= block_index < NUM_BLOCKS:
        raise ValueError(f"Block index must be between 0 and {NUM_BLOCKS - 1}")

    if len(new_block) != BLOCK_SIZE:
        raise ValueError(f"Replacement block must be exactly {BLOCK_SIZE} bytes")

    updated_tree = [level.copy() for level in tree]
    current_idx = block_index
    updated_tree[0][current_idx] = sha256(new_block)

    for level in range(len(updated_tree) - 1):
        parent_idx = current_idx // 2
        left_idx = parent_idx * 2
        right_idx = left_idx + 1
        updated_tree[level + 1][parent_idx] = sha256(updated_tree[level][left_idx] + updated_tree[level][right_idx])
        current_idx = parent_idx

    return updated_tree


def print_missing_file(filepath: str, generator_hint: str) -> bool:
    if os.path.exists(filepath):
        return False
    print(f"Error: '{filepath}' not found. Please run {generator_hint} first.")
    return True


def main() -> None:
    print("=" * 40)
    print(" Task 4: Advanced Self-Healing")
    print("=" * 40)

    missing_inputs = [
        print_missing_file(CORRUPTED_FILE, "data_gen/generate_corrupted.py"),
        print_missing_file(TRUSTED_TREE_FILE, "data_gen/export_trusted_merkle_tree.py"),
        print_missing_file(PARITY_FILE, "data_gen/export_parity_blocks.py"),
    ]
    if any(missing_inputs):
        return

    print("1. Loading corrupted data, trusted Merkle Tree, and parity blocks...")
    corrupted_data = read_binary_file(CORRUPTED_FILE)
    corrupted_blocks = split_into_blocks(corrupted_data)
    trusted_tree = load_trusted_tree(TRUSTED_TREE_FILE)
    parity_blocks = load_parity_blocks(PARITY_FILE)

    print("2. Building Merkle Tree from corrupted data...")
    corrupted_tree = build_merkle_tree_from_blocks(corrupted_blocks)

    print("3. Locating corrupted block using trusted Merkle Tree...")
    corrupted_block_idx, comparison_count = locate_error(trusted_tree, corrupted_tree)

    trusted_root = trusted_tree[-1][0]
    corrupted_root = corrupted_tree[-1][0]

    if corrupted_block_idx == -1:
        print("\n[Output]")
        print(f"Trusted Merkle Root        : {trusted_root.hex()}")
        print(f"Corrupted File Root        : {corrupted_root.hex()}")
        print("Corrupted Block Index      : None")
        print(f"Comparison Count           : {comparison_count}")
        print("Verification Result        : PASS (file already matches trusted root)")
        print("=" * 40)
        return

    print("4. Recovering corrupted block with XOR parity and sibling block...")
    recovered_block, parity_index, sibling_index = recover_block(
        corrupted_blocks,
        corrupted_block_idx,
        parity_blocks,
    )

    print("5. Repairing Merkle Tree with replace_node()...")
    repaired_tree = replace_node(corrupted_tree, corrupted_block_idx, recovered_block)
    repaired_root = repaired_tree[-1][0]
    verification_result = repaired_root == trusted_root

    print("\n[Output]")
    print(f"Trusted Merkle Root        : {trusted_root.hex()}")
    print(f"Corrupted File Root        : {corrupted_root.hex()}")
    print(f"Corrupted Block Index      : {corrupted_block_idx}")
    print(f"Comparison Count           : {comparison_count}")
    print(f"Parity Block Index Used    : {parity_index}")
    print(f"Sibling Block Index        : {sibling_index}")
    print(f"Repaired Merkle Root       : {repaired_root.hex()}")
    print(f"Verification Result        : {'PASS' if verification_result else 'FAIL'}")
    print("=" * 40)


if __name__ == "__main__":
    main()
