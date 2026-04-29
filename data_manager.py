# 腳本功能：系統配置(JSON)、XML數據解析、錯誤紀錄 (合併單一模組)
import os, sys, json, traceback
import xml.etree.ElementTree as ET

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

CONFIG_FILE = "settings.json"
CRASH_LOG = "crash_report.txt"

def log_error(msg):
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(f"--- {traceback.format_exc()} ---\n{msg}\n\n")
    except: pass

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception as e: log_error(f"加載設定失敗: {e}")
    return {}

def save_settings(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e: log_error(f"儲存設定失敗: {e}")

def parse_yunxi_xml(filename):
    try:
        root = None
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
        except:
            for enc in ['gb18030', 'utf-8']:
                try:
                    with open(filename, 'r', encoding=enc) as f:
                        root = ET.fromstring(f.read())
                    break
                except: continue
        
        if root is None: return None, "無法解析檔案編碼"
        items_data = []
        pack_list = root.find('LitsPack') or root.find('ListPack')
        if pack_list is None: return None, "找不到有效的板件節點"

        for node in (pack_list.findall('PacknigData') or pack_list.findall('PackingData')):
            def get_t(tag):
                n = node.find(tag)
                return n.text.strip() if n is not None and n.text else ""
            
            items_data.append({
                "Barcode": get_t('二维条码'),
                "Order": get_t('订单编号'),
                "Customer": get_t('客户名'),
                "Cabinet": get_t('柜体名'),
                "Part": get_t('部件名'),
                "Material": get_t('材料名'),
                "L": get_t('长度'),
                "W": get_t('宽度'),
                "T": get_t('厚度'),
                "Status": get_t('打包状态') or get_t('_status'),
                "PackNum": get_t('包号') or get_t('_number')
            })
            
        user_limit = None
        limit_node = root.find('UserPackLimit')
        if limit_node is not None:
            try: user_limit = float(limit_node.text)
            except: pass

        return {"items": items_data, "limit": user_limit}, None
    except Exception as e: return None, str(e)

def save_yunxi_xml(filename, packs_data, unscanned_items, pack_limit):
    try:
        root = ET.Element("SmartDuctData")
        ET.SubElement(root, "UserPackLimit").text = str(pack_limit)
        lits_pack = ET.SubElement(root, "LitsPack")

        for pack_num, items in packs_data.items():
            for item in items:
                node = ET.SubElement(lits_pack, "PacknigData")
                ET.SubElement(node, "二维条码").text = str(item["Barcode"])
                ET.SubElement(node, "订单编号").text = str(item["Order"])
                ET.SubElement(node, "客户名").text = str(item["Customer"])
                ET.SubElement(node, "柜体名").text = str(item["Cabinet"])
                ET.SubElement(node, "部件名").text = str(item["Part"])
                ET.SubElement(node, "材料名").text = str(item["Material"])
                ET.SubElement(node, "长度").text = str(item["L"])
                ET.SubElement(node, "宽度").text = str(item["W"])
                ET.SubElement(node, "厚度").text = str(item["T"])
                ET.SubElement(node, "打包状态").text = "已扫描"
                ET.SubElement(node, "包号").text = str(pack_num)
                ET.SubElement(node, "_status").text = "已扫描"
                ET.SubElement(node, "_number").text = str(pack_num)

        for item in unscanned_items:
            node = ET.SubElement(lits_pack, "PacknigData")
            ET.SubElement(node, "二维条码").text = str(item["Barcode"])
            ET.SubElement(node, "订单编号").text = str(item["Order"])
            ET.SubElement(node, "客户名").text = str(item["Customer"])
            ET.SubElement(node, "柜体名").text = str(item["Cabinet"])
            ET.SubElement(node, "部件名").text = str(item["Part"])
            ET.SubElement(node, "材料名").text = str(item["Material"])
            ET.SubElement(node, "长度").text = str(item["L"])
            ET.SubElement(node, "宽度").text = str(item["W"])
            ET.SubElement(node, "厚度").text = str(item["T"])

        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        return True
    except Exception as e:
        log_error(f"存檔失敗: {e}")
        return False