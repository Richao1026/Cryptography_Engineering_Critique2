
import hashlib
import time
import sys

# 定義常數
FILE_PATH = 'test_128mb.bin'
NUM_BLOCKS = 128  # 依據作業要求：2^7 個區塊
BLOCK_SIZE = (128 * 1024 * 1024) // NUM_BLOCKS  # 每個區塊 1MB

def hash_data(data: bytes) -> bytes:
    """計算 SHA-256 並回傳二進位結果"""
    return hashlib.sha256(data).digest()

def main():
    # --- 步驟 0：讀取檔案 ---
    try:
        with open(FILE_PATH, 'rb') as f:
            raw_data = f.read()
    except FileNotFoundError:
        print(f"錯誤：找不到 {FILE_PATH}。請先執行 data_gen/generate_128mb.py。")
        return

    print("="*40)
    print(" 步驟 1: Single Hash (All-or-Nothing)")
    print("="*40)
    
    # 紀錄單一雜湊開始時間
    start_time_single = time.time()
    
    # 對整份 128MB 檔案做一次 SHA-256
    single_hash_result = hashlib.sha256(raw_data).hexdigest()
    
    # 計算花費時間
    single_hash_time = time.time() - start_time_single

    print(f"Single Hash 結果: {single_hash_result}")
    print(f"計算時間: {single_hash_time:.6f} 秒\n")


    print("="*40)
    print(f" 步驟 2: Merkle Tree (2^{int(math.log2(NUM_BLOCKS))} Blocks)")
    print("="*40)
    
    # 紀錄 Merkle Tree 開始時間
    start_time_merkle = time.time()
    
    # 1. 將 128MB 檔案切分成 128 個 1MB 的區塊 (Leaves)
    blocks = [raw_data[i * BLOCK_SIZE : (i + 1) * BLOCK_SIZE] for i in range(NUM_BLOCKS)]
    
    # 2. 對每個底部區塊進行雜湊，形成葉節點 (Leaf nodes)
    current_level = [hash_data(block) for block in blocks]
    
    internal_nodes_memory = 0
    
    # 3. 由下往上建構 Merkle Tree
    while len(current_level) > 1:
        next_level = []
        # 兩兩一組將相鄰節點合併
        for i in range(0, len(current_level), 2):
            left_node = current_level[i]
            right_node = current_level[i+1]
            
            # 將左右節點的雜湊值串接後，再做一次 SHA-256
            parent_node = hash_data(left_node + right_node)
            next_level.append(parent_node)
            
            # 累加「內部節點」的記憶體開銷
            internal_nodes_memory += sys.getsizeof(parent_node)
            
        current_level = next_level
    
    # 樹根就是最後剩下的一個節點
    merkle_root = current_level[0].hex()
    
    # 計算花費時間
    merkle_tree_time = time.time() - start_time_merkle

    print(f"Merkle Root: {merkle_root}")
    print(f"建構時間: {merkle_tree_time:.6f} 秒")
    print(f"內部節點記憶體開銷: {internal_nodes_memory} Bytes")
    print("="*40)

if __name__ == "__main__":
    import math
    main()