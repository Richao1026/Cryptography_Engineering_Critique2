import pytest

import task4


def configure_small_tree(monkeypatch):
    monkeypatch.setattr(task4, "NUM_BLOCKS", 4)
    monkeypatch.setattr(task4, "BLOCK_SIZE", 4)
    monkeypatch.setattr(task4, "TOTAL_SIZE", 16)


def test_recover_corrupted_block_and_restore_trusted_root(monkeypatch):
    configure_small_tree(monkeypatch)

    clean_blocks = [
        b"abcd",
        b"EFGH",
        b"1234",
        b"WXYZ",
    ]
    corrupted_blocks = clean_blocks.copy()
    corrupted_blocks[2] = b"0234"

    trusted_tree = task4.build_merkle_tree_from_blocks(clean_blocks)
    corrupted_tree = task4.build_merkle_tree_from_blocks(corrupted_blocks)
    parity_blocks = task4.build_parity_blocks(clean_blocks)

    block_index, comparison_count = task4.locate_error(trusted_tree, corrupted_tree)
    recovered_block, parity_index, sibling_index = task4.recover_block(
        corrupted_blocks, block_index, parity_blocks
    )
    repaired_tree = task4.replace_node(corrupted_tree, block_index, recovered_block)

    assert block_index == 2
    assert comparison_count == 2
    assert recovered_block == clean_blocks[2]
    assert parity_index == 1
    assert sibling_index == 3
    assert repaired_tree[-1][0] == trusted_tree[-1][0]


def test_file_loaders_validate_binary_formats(monkeypatch, tmp_path):
    configure_small_tree(monkeypatch)
    clean_blocks = [b"aaaa", b"bbbb", b"cccc", b"dddd"]
    trusted_tree = task4.build_merkle_tree_from_blocks(clean_blocks)
    parity_blocks = task4.build_parity_blocks(clean_blocks)

    tree_path = tmp_path / "trusted_merkle_tree.bin"
    parity_path = tmp_path / "parity_blocks.bin"
    data_path = tmp_path / "test_128mb_corrupted.bin"

    tree_path.write_bytes(b"".join(node for level in trusted_tree for node in level))
    parity_path.write_bytes(b"".join(parity_blocks))
    data_path.write_bytes(b"".join(clean_blocks))

    assert task4.load_trusted_tree(str(tree_path)) == trusted_tree
    assert task4.load_parity_blocks(str(parity_path)) == parity_blocks
    assert task4.split_into_blocks(task4.read_binary_file(str(data_path))) == clean_blocks

    bad_parity_path = tmp_path / "bad_parity_blocks.bin"
    bad_parity_path.write_bytes(b"short")

    with pytest.raises(ValueError, match="Parity file size mismatch"):
        task4.load_parity_blocks(str(bad_parity_path))
