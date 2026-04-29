# 腳本功能：負責重量換算演算法與裝箱 (Bin Packing) 的核心邏輯

# 功能：計算單一板件重量
def calculate_item_weight(l, w, t, material_name, materials_db, default_density):
    """
    # 註記：動態材質密度換算演算法
    根據長(L)、寬(W)、厚(T)及材質名稱，計算出精確重量(kg)。
    若材質庫有對應的特殊厚度設定則優先使用，否則使用通用密度。
    """
    try:
        length = float(l)
        width = float(w)
        thickness = float(t)
        density = 0.0

        if materials_db and material_name in materials_db:
            mat_config = materials_db[material_name]
            
            # 處理整數與小數厚度的字串對應 (例如 "18" 或 "18.5")
            thick_key = str(int(thickness)) if thickness.is_integer() else str(thickness)

            if thick_key in mat_config.get("map", {}):
                density = float(mat_config["map"][thick_key])
            else:
                density = float(mat_config.get("default", 0.75)) * 1000
        else:
            # 若無特殊材質設定，使用系統的通用密度
            density = float(default_density) * 1000

        # 體積轉換為立方公尺並乘以密度 (1立方公釐 = 1/1,000,000,000 立方公尺)
        weight = (length * width * thickness / 1_000_000_000) * density
        return round(weight, 3)
    except Exception:
        return 0.0


# 功能：檢查是否超出單包限重
def can_fit_in_pack(current_pack_weight, item_weight, pack_limit):
    """
    # 註記：裝箱邊界檢查邏輯
    判斷當前包裝加入新板件後，是否會超出限重。
    """
    try:
        limit = float(pack_limit)
        # 若包內尚無物品，即使單件本身就超重，也必須允許放入 (避免演算法死鎖無法打包)
        if current_pack_weight == 0:
            return True
        return (current_pack_weight + item_weight) <= limit
    except:
        return True # 若解析異常則預設允許放入


# 功能：重新分配所有已掃描的板件 (重新裝箱)
def repack_all_items(all_scanned_items, pack_limit):
    """
    # 註記：貪婪演算法 (Bin Packing) 重新分配
    當使用者在介面上修改「單包限重」時，系統會呼叫此函式，
    將所有已經掃描的板件依據新的限重條件「依序重新分包」。
    
    回傳值: (新的分包字典 packs_data, 最終使用的包號 current_pack)
    """
    try:
        limit = float(pack_limit)
        if limit <= 0:
            limit = 20.0 # 若輸入無效值則退回預設安全值
    except:
        limit = 20.0

    packs_data = {1: []}
    current_pack = 1

    for item in all_scanned_items:
        current_pack_items = packs_data[current_pack]
        current_weight = sum(i.get("Weight", 0.0) for i in current_pack_items)
        item_weight = item.get("Weight", 0.0)

        # 核心邏輯：若當前包裝已裝東西，且加入新件會超重，則開啟新的一包
        if current_weight > 0 and (current_weight + item_weight > limit):
            current_pack += 1
            packs_data[current_pack] = []

        packs_data[current_pack].append(item)

    return packs_data, current_pack