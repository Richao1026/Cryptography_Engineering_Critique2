import hashlib
import os

NUM_BLOCKS = 128
BLOCK_SIZE = 1024 * 1024
HASH_SIZE = 32 
def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def build_merkle_tree(filepath: str) -> list:
    with open(filepath, 'rb') as f:
        raw_data = f.read()

    # 切分 128 個區塊
    blocks = [raw_data[i * BLOCK_SIZE : (i + 1) * BLOCK_SIZE] for i in range(NUM_BLOCKS)]
    
    tree = []
    # Level 0: 葉節點
    current_level = [sha256(block) for block in blocks]
    tree.append(current_level)

    # 由下而上建構
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            parent_hash = sha256(current_level[i] + current_level[i+1])
            next_level.append(parent_hash)
        tree.append(next_level)
        current_level = next_level

    return tree

def load_trusted_tree(filepath: str) -> list:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"找不到 {filepath}")

    tree = []
    # 完整二元樹的每層節點數量 (128 -> 64 -> ... -> 1)
    level_sizes = [128, 64, 32, 16, 8, 4, 2, 1] 
    
    with open(filepath, 'rb') as f:
        for size in level_sizes:
            level = []
            for _ in range(size):
                level.append(f.read(HASH_SIZE))
            tree.append(level)
            
    return tree

def locate_error(trusted_tree: list, corrupted_tree: list):
    comparisons = 0
    current_idx = 0  # 從最高層 (Root) 的 index 0 開始
    
    # 從次高層 (Root 的下一層) 一路往下走訪到 Level 0 (Leaves)
    # len(trusted_tree) 為 8 (即 Level 0 ~ 7)
    for level in range(len(trusted_tree) - 2, -1, -1):
        left_child_idx = 2 * current_idx
        right_child_idx = 2 * current_idx + 1
        
        comparisons += 1
        
        # 關鍵：為了維持精準的 log2(n) 比較次數，我們只檢查左子節點
        if corrupted_tree[level][left_child_idx] != trusted_tree[level][left_child_idx]:
            # 左邊的 Hash 不同，代表錯誤在左子樹
            current_idx = left_child_idx
        else:
            # 左邊相同，代表錯誤必然在右子樹 (省去對右節點的比對)
            current_idx = right_child_idx
            
    # 當迴圈結束時，level 已經走到 0，此時的 current_idx 就是損毀的 block index
    return current_idx, comparisons

def main():
    trusted_tree_path = 'trusted_merkle_tree.bin'
    corrupted_data_path = 'test_128mb_corrupted.bin'
    
    print("="*40)
    print(" Task 2: Efficient Error Localization")
    print("="*40)
    
    print("1. Loading Trusted Merkle Tree...")
    trusted_tree = load_trusted_tree(trusted_tree_path)
    
    print("2. Build Merkle Tree from corrupted data...")
    corrupted_tree = build_merkle_tree(corrupted_data_path)
    
    print("3. Locating the corruputed block...")
    corrupted_block_idx, comp_count = locate_error(trusted_tree, corrupted_tree)
    
    # 取出 Root (在 tree 的最後一層的第 0 個元素)
    trusted_root_hex = trusted_tree[-1][0].hex()
    corrupted_root_hex = corrupted_tree[-1][0].hex()
    
    print("\n[Output]")
    print(f"Trusted Merkle Root  : {trusted_root_hex}")
    print(f"Corrupted File Root  : {corrupted_root_hex}")
    print(f"Corrupted Block Index: {corrupted_block_idx}")
    print(f"Comparison Count     : {comp_count}")
    print("="*40)

if __name__ == "__main__":
    main()