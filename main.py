# 腳本功能：系統進入點與主 UI 視窗 (完整還原最終穩定版介面)

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import time

try:
    import data_manager as dm
    import calculator as calc
except Exception as e:
    print(f"模組載入失敗，請檢查語法: {e}")
    sys.exit(1)

try:
    import pyttsx3
    import pythoncom
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class MaterialEditor(tk.Toplevel):
    """材質參數設定視窗"""
    def __init__(self, parent, current_materials, callback):
        super().__init__(parent)
        self.title("材質參數設定 (支援小數)")
        self.geometry("600x500")
        self.materials = current_materials
        self.callback = callback
        self.current_mat_name = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        left_frame = tk.LabelFrame(main_frame, text="材質列表", width=200)
        left_frame.pack(side="left", fill="y", padx=5)

        self.lb_materials = tk.Listbox(left_frame, width=20, height=20)
        self.lb_materials.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.lb_materials.bind("<<ListboxSelect>>", self.on_material_select)

        tk.Button(left_frame, text="+ 新增材質", command=self.add_material, bg="#c8e6c9").pack(fill="x", padx=5, pady=2)
        tk.Button(left_frame, text="- 刪除材質", command=self.del_material, bg="#ffcdd2").pack(fill="x", padx=5, pady=2)

        right_frame = tk.LabelFrame(main_frame, text="詳細參數設定", width=350)
        right_frame.pack(side="left", fill="both", expand=True, padx=5)

        info_frame = tk.Frame(right_frame)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        self.lbl_mat_name = tk.Label(info_frame, text="請選擇材質", font=("Arial", 12, "bold"))
        self.lbl_mat_name.pack(anchor="w")

        tk.Label(info_frame, text="預設密度 (g/cm³):").pack(anchor="w", pady=(5,0))
        self.ent_default_density = tk.Entry(info_frame)
        self.ent_default_density.pack(anchor="w", fill="x")

        rule_frame = tk.LabelFrame(right_frame, text="厚度與密度對照表")
        rule_frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("厚度 (mm)", "密度 (kg/m³)")
        self.tree_rules = ttk.Treeview(rule_frame, columns=cols, show="headings", height=8)
        self.tree_rules.heading("厚度 (mm)", text="厚度 (mm)")
        self.tree_rules.heading("密度 (kg/m³)", text="密度 (kg/m³)")
        self.tree_rules.column("厚度 (mm)", width=100, anchor="center")
        self.tree_rules.column("密度 (kg/m³)", width=120, anchor="center")
        self.tree_rules.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(rule_frame, orient="vertical", command=self.tree_rules.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_rules.configure(yscrollcommand=scrollbar.set)

        btn_rule_frame = tk.Frame(right_frame)
        btn_rule_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(btn_rule_frame, text="新增規則", command=self.add_rule).pack(side="left", padx=2)
        tk.Button(btn_rule_frame, text="刪除規則", command=self.del_rule).pack(side="left", padx=2)

        tk.Button(self, text="💾 保存並關閉", command=self.save_and_close, bg="#2196f3", fg="white", font=("Arial", 12)).pack(fill="x", padx=10, pady=10)

        self.refresh_material_list()

    def refresh_material_list(self):
        self.lb_materials.delete(0, "end")
        for mat in self.materials: self.lb_materials.insert("end", mat)

    def on_material_select(self, event):
        self.save_current_edits()
        selection = self.lb_materials.curselection()
        if not selection: return
        self.current_mat_name = self.lb_materials.get(selection[0])
        self.lbl_mat_name.config(text=f"編輯中: {self.current_mat_name}")
        mat_data = self.materials[self.current_mat_name]
        self.ent_default_density.delete(0, "end")
        self.ent_default_density.insert(0, str(mat_data.get("default", 0.75)))
        for item in self.tree_rules.get_children(): self.tree_rules.delete(item)
        rules = mat_data.get("map", {})
        sorted_thick = sorted(rules.keys(), key=lambda x: float(x))
        for t in sorted_thick: self.tree_rules.insert("", "end", values=(t, rules[t]))

    def save_current_edits(self):
        if not self.current_mat_name: return
        try: default_d = float(self.ent_default_density.get())
        except: default_d = 0.75
        new_map = {}
        for item in self.tree_rules.get_children():
            vals = self.tree_rules.item(item)['values']
            new_map[str(vals[0])] = float(vals[1])
        self.materials[self.current_mat_name] = {"default": default_d, "map": new_map}

    def add_material(self):
        name = simpledialog.askstring("新增", "請輸入材質名稱")
        if name and name not in self.materials:
            self.materials[name] = {"default": 0.75, "map": {}}
            self.refresh_material_list()

    def del_material(self):
        selection = self.lb_materials.curselection()
        if not selection: return
        name = self.lb_materials.get(selection[0])
        if messagebox.askyesno("確認", f"確定刪除 {name}？"):
            del self.materials[name]
            self.refresh_material_list()
            self.current_mat_name = None
            self.lbl_mat_name.config(text="請選擇材質")

    def add_rule(self):
        if not self.current_mat_name: return
        thick = simpledialog.askstring("新增規則", "請輸入板厚 (mm):")
        if not thick: return
        den = simpledialog.askstring("新增規則", f"請輸入 {thick.strip()}mm 對應密度 (kg/m³):")
        if not den: return
        try: self.tree_rules.insert("", "end", values=(thick.strip(), float(den.strip())))
        except ValueError: messagebox.showerror("錯誤", "數值格式不正確")

    def del_rule(self):
        for item in self.tree_rules.selection(): self.tree_rules.delete(item)

    def save_and_close(self):
        self.save_current_edits()
        self.callback(self.materials)
        self.destroy()


class YunxiWeightCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("雲熙驗單打包助手 - 重構版 (MVC 架構完整介面)")
        self.root.geometry("1200x950")
        self.root.bind("<Button-1>", self.focus_scan_entry)

        # 狀態變數
        self.all_items = []
        self.unscanned_items = []
        self.packs_data = {1: []}
        self.current_filling_pack = 1
        self.current_viewing_pack = 1
        
        self.default_density = tk.StringVar(value="0.75")
        self.pack_limit = tk.StringVar(value="20.0")
        self.memory_text_var = tk.StringVar()
        self.scan_input_var = tk.StringVar()
        
        # 排序與篩選狀態
        self.last_sort_col = None
        self.last_sort_reverse = False
        self.unscanned_sort_col = None
        self.unscanned_sort_state = 0
        
        self.filter_vars = {k: tk.StringVar() for k in ["Order", "Customer", "Cabinet", "Part", "Material", "L", "W", "T"]}
        self.filter_combos = {}
        self.scanned_filter_vars = {k: tk.StringVar() for k in ["Order", "Customer", "Cabinet", "Part", "Material", "L", "W", "T"]}
        self.scanned_filter_combos = {}

        for var in self.filter_vars.values(): var.trace_add("write", lambda *args: self.refresh_tables())
        for var in self.scanned_filter_vars.values(): var.trace_add("write", lambda *args: self.refresh_tables())
        self.scan_input_var.trace_add("write", self.on_input_change)

        # 載入設定
        settings = dm.load_settings()
        self.default_density.set(settings.get("default_density", "0.75"))
        self.pack_limit.set(settings.get("pack_limit", "20.0"))
        self.memory_text_var.set(settings.get("memory_text", ""))
        self.materials_db = settings.get("materials_db", {"防水發泡板": {"default": 0.75, "map": {"9": 740, "18": 684, "25": 726}}})

        self.setup_ui()
        self.focus_scan_entry(None)

    def speak(self, text):
        if not TTS_AVAILABLE: return
        def _run():
            try:
                pythoncom.CoInitialize()
                time.sleep(0.01)
                engine = pyttsx3.init()
                try:
                    for voice in engine.getProperty('voices'):
                        if 'chinese' in voice.name.lower() or 'taiwan' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                except: pass
                engine.say(text)
                engine.runAndWait()
            except Exception as e: dm.log_error(f"語音錯誤: {e}")
            finally:
                try: pythoncom.CoUninitialize()
                except: pass
        threading.Thread(target=_run, daemon=True).start()

    def focus_scan_entry(self, event):
        if isinstance(event, tk.Event) and isinstance(event.widget, (tk.Entry, tk.Button, tk.Listbox, ttk.Combobox)): return
        try: self.ent_scan.focus_set()
        except: pass

    # ================= UI 繪製還原 =================
    def setup_ui(self):
        # 0. 掃描區
        scan_frame = tk.Frame(self.root, bg="#bbdefb", pady=15, relief="raised", borderwidth=3)
        scan_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(scan_frame, text="🔫 掃描輸入:", font=("Arial", 16, "bold"), bg="#bbdefb", fg="#0d47a1").pack(side="left", padx=15)
        self.ent_scan = tk.Entry(scan_frame, textvariable=self.scan_input_var, font=("Arial", 18), width=35)
        self.ent_scan.pack(side="left", padx=5)
        self.ent_scan.bind("<Return>", self.on_barcode_scanned)

        # 1. 系統設定與備註
        top_frame = tk.Frame(self.root, pady=5, bg="#f5f5f5")
        top_frame.pack(fill="x", padx=5)

        setting_frame = tk.LabelFrame(top_frame, text="系統操作", padx=5, pady=5)
        setting_frame.pack(side="left", padx=5, fill="y")
        btn_frame = tk.Frame(setting_frame)
        btn_frame.grid(row=0, column=0, rowspan=3, padx=5)
        tk.Button(btn_frame, text="📂 加載 XML", command=self.load_xml, bg="#e0e0e0", width=12).pack(pady=2)
        tk.Button(btn_frame, text="💾 保存進度", command=self.save_xml, bg="#ffecb3", width=12).pack(pady=2)
        tk.Button(btn_frame, text="⚙️ 材質參數", command=self.open_material_settings, bg="#b2dfdb", width=12).pack(pady=2)

        tk.Label(setting_frame, text="通用密度:").grid(row=0, column=1, sticky="e")
        ent_density = tk.Entry(setting_frame, textvariable=self.default_density, width=5)
        ent_density.grid(row=0, column=2, sticky="w")
        ent_density.bind("<KeyRelease>", lambda e: self.save_current_settings())
        
        tk.Label(setting_frame, text="單包限重(kg):", fg="red").grid(row=1, column=1, sticky="e")
        ent_limit = tk.Entry(setting_frame, textvariable=self.pack_limit, width=5)
        ent_limit.grid(row=1, column=2, sticky="w")
        ent_limit.bind("<KeyRelease>", self.on_pack_limit_change)
        tk.Label(setting_frame, text="(無材質設定時使用)", font=("Arial", 8), fg="gray").grid(row=2, column=1, columnspan=2)

        memo_frame = tk.LabelFrame(top_frame, text="記憶備註", padx=5, pady=5)
        memo_frame.pack(side="left", padx=10, fill="both", expand=True)
        ent_memo = tk.Entry(memo_frame, textvariable=self.memory_text_var, font=("Arial", 11))
        ent_memo.pack(fill="both", expand=True, pady=5)
        ent_memo.bind("<KeyRelease>", lambda e: self.save_current_settings())

        # 2. 統計列
        info_frame = tk.Frame(self.root, bg="#fff3e0", pady=8, relief="ridge", borderwidth=2)
        info_frame.pack(fill="x", padx=10, pady=5)
        self.lbl_info_left = tk.Label(info_frame, text="總件數: 0 | 未掃描: 0", font=("Arial", 12), bg="#fff3e0")
        self.lbl_info_left.pack(side="left", padx=20)
        self.lbl_total_scanned_pieces = tk.Label(info_frame, text="已掃描總數(件): 0", font=("Arial", 12, "bold"), bg="#fff3e0", fg="#004d40")
        self.lbl_total_scanned_pieces.pack(side="left", padx=20) 
        self.lbl_scan_status = tk.Label(info_frame, text="準備就緒...", font=("Arial", 16, "bold"), fg="gray", bg="#fff3e0")
        self.lbl_scan_status.pack(side="left", padx=30, fill="x", expand=True)
        self.lbl_total_packed_count = tk.Label(info_frame, text="已打包總數: 0", font=("Arial", 14, "bold"), fg="#2e7d32", bg="#fff3e0")
        self.lbl_total_packed_count.pack(side="right", padx=20)
        self.lbl_total_weight = tk.Label(info_frame, text="總合計: 0.00 kg", font=("Arial", 14, "bold"), fg="blue", bg="#fff3e0")
        self.lbl_total_weight.pack(side="right", padx=20)

        # 3. 篩選與表格 (未掃描)
        filter_config = [("訂單", "Order", 14), ("客戶", "Customer", 10), ("櫃體", "Cabinet", 14), ("部件", "Part", 10), ("材質", "Material", 12), ("長", "L", 5), ("寬", "W", 5), ("厚", "T", 5)]
        
        filter_frame = tk.LabelFrame(self.root, text="🔍 未掃描清單篩選", padx=5, pady=5, bg="#fce4ec")
        filter_frame.pack(fill="x", padx=10, pady=(5, 0))
        for i, (label_text, var_key, width) in enumerate(filter_config):
            tk.Label(filter_frame, text=f"{label_text}:", bg="#fce4ec").grid(row=0, column=i*2, sticky="e")
            cb = ttk.Combobox(filter_frame, textvariable=self.filter_vars[var_key], width=width)
            cb.grid(row=0, column=i*2+1, padx=5)
            self.filter_combos[var_key] = cb
        tk.Button(filter_frame, text="清空", command=lambda: self.clear_filters(self.filter_vars), bg="white").grid(row=0, column=16, padx=10)

        tk.Label(self.root, text="▼ 未掃描清單 (自動比對) (點擊標題可排序)", bg="#ffebee", anchor="w", padx=10).pack(fill="x")
        cols = ("Barcode", "Order", "Customer", "Cabinet", "Part", "Material", "L", "W", "T", "Weight")
        self.tree_unscanned = ttk.Treeview(self.root, columns=cols, show="headings", height=8)
        self.setup_treeview(self.tree_unscanned, cols, self.sort_unscanned_tree)
        self.tree_unscanned.pack(fill="both", expand=True, padx=10)
        self.tree_unscanned.bind("<Double-1>", self.on_double_click_unscanned)

        # 4. 分包控制列
        pack_ctrl_frame = tk.Frame(self.root, bg="#e8f5e9", pady=5, relief="raised", borderwidth=1)
        pack_ctrl_frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Button(pack_ctrl_frame, text="<< 上一包", command=self.prev_pack, bg="white").pack(side="left", padx=10)
        self.lbl_current_pack_info = tk.Label(pack_ctrl_frame, text="📦 包號 1 (0.00 kg)", font=("Arial", 14, "bold"), bg="#e8f5e9", fg="#2e7d32")
        self.lbl_current_pack_info.pack(side="left", padx=20)
        tk.Button(pack_ctrl_frame, text="下一包 >>", command=self.next_pack, bg="white").pack(side="left", padx=10)
        self.lbl_filling_status = tk.Label(pack_ctrl_frame, text="[正在裝入: 第 1 包]", font=("Arial", 10), fg="gray", bg="#e8f5e9")
        self.lbl_filling_status.pack(side="right", padx=20)

        # 5. 篩選與表格 (已掃描)
        scanned_filter_frame = tk.LabelFrame(self.root, text="🔍 已掃描清單篩選", padx=5, pady=5, bg="#e8f5e9")
        scanned_filter_frame.pack(fill="x", padx=10, pady=(5, 0))
        for i, (label_text, var_key, width) in enumerate(filter_config):
            tk.Label(scanned_filter_frame, text=f"{label_text}:", bg="#e8f5e9").grid(row=0, column=i*2, sticky="e")
            cb = ttk.Combobox(scanned_filter_frame, textvariable=self.scanned_filter_vars[var_key], width=width)
            cb.grid(row=0, column=i*2+1, padx=5)
            self.scanned_filter_combos[var_key] = cb
        tk.Button(scanned_filter_frame, text="清空", command=lambda: self.clear_filters(self.scanned_filter_vars), bg="white").grid(row=0, column=16, padx=10)

        self.tree_scanned = ttk.Treeview(self.root, columns=cols, show="headings", height=8)
        self.setup_treeview(self.tree_scanned, cols, self.sort_scanned_tree)
        self.tree_scanned.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree_scanned.bind("<Double-1>", self.on_double_click_scanned)

    def setup_treeview(self, tree, cols, sort_command):
        col_map = {"Barcode": "條碼", "Order": "訂單", "Customer": "客戶", "Cabinet": "櫃體", "Part": "部件", "Material": "材質", "L": "長", "W": "寬", "T": "厚", "Weight": "重量"}
        col_widths = [180, 120, 100, 150, 100, 100, 50, 50, 40, 70]
        for i, col in enumerate(cols):
            tree.column(col, width=col_widths[i], anchor="center")
            tree.heading(col, text=col_map.get(col, col), command=lambda c=col: sort_command(c))

    # ================= 商業邏輯對接 =================
    def save_current_settings(self):
        dm.save_settings({
            "default_density": self.default_density.get(),
            "pack_limit": self.pack_limit.get(),
            "memory_text": self.memory_text_var.get(),
            "materials_db": self.materials_db
        })

    def open_material_settings(self):
        MaterialEditor(self.root, self.materials_db, self.on_materials_saved)

    def on_materials_saved(self, new_materials):
        self.materials_db = new_materials
        self.save_current_settings()
        for item in self.all_items:
            item["Weight"] = calc.calculate_item_weight(item["L"], item["W"], item["T"], item["Material"], self.materials_db, self.default_density.get())
        self.refresh_tables()
        messagebox.showinfo("成功", "材質參數已更新！")

    def on_pack_limit_change(self, event):
        self.save_current_settings()
        self.repack_scanned_items()

    def repack_scanned_items(self):
        all_scanned = []
        for pid in sorted(self.packs_data.keys()): all_scanned.extend(self.packs_data[pid])
        if not all_scanned: return
        self.packs_data, self.current_filling_pack = calc.repack_all_items(all_scanned, self.pack_limit.get())
        self.current_viewing_pack = self.current_filling_pack
        self.refresh_tables()

    def on_input_change(self, *args):
        text = self.scan_input_var.get().strip()
        if not text: return
        for item in self.unscanned_items:
            if item["Barcode"] == text:
                self.process_move_to_pack(item)
                self.scan_input_var.set("")
                self.lbl_scan_status.config(text=f"✅ 已掃描: {item['Part']}", fg="#2e7d32")
                self.speak("已掃描") 
                self.root.bell()
                return
        self.lbl_scan_status.config(text="🔍 比對中...", fg="orange")

    def on_barcode_scanned(self, event):
        barcode = self.scan_input_var.get().strip()
        if not barcode: return
        target_item = next((i for i in self.unscanned_items if i["Barcode"] == barcode), None)
        
        if target_item:
            self.process_move_to_pack(target_item)
            self.scan_input_var.set("")
            self.lbl_scan_status.config(text=f"✅ 已掃描: {target_item['Part']}", fg="#2e7d32")
            self.speak("已掃描")
            self.root.bell()
        else:
            found_pack = next((p for p, items in self.packs_data.items() if any(i["Barcode"] == barcode for i in items)), None)
            if found_pack:
                self.lbl_scan_status.config(text=f"⚠️ 錯誤：重複掃描 (已在第 {found_pack} 包)", fg="red")
                self.speak("重複掃描")
            else:
                self.lbl_scan_status.config(text="❌ 錯誤：找不到條碼", fg="red")
                self.speak("找不到條碼")
            self.root.bell()
            self.scan_input_var.set("")

    def process_move_to_pack(self, item):
        self.unscanned_items.remove(item)
        current_weight = sum(i["Weight"] for i in self.packs_data.get(self.current_filling_pack, []))
        if not calc.can_fit_in_pack(current_weight, item["Weight"], self.pack_limit.get()):
            self.current_filling_pack += 1
            self.packs_data[self.current_filling_pack] = []
        if self.current_filling_pack not in self.packs_data: self.packs_data[self.current_filling_pack] = []
        self.packs_data[self.current_filling_pack].append(item)
        self.current_viewing_pack = self.current_filling_pack
        self.refresh_tables()

    def prev_pack(self):
        if self.current_viewing_pack > 1:
            self.current_viewing_pack -= 1
            self.refresh_tables()

    def next_pack(self):
        if self.current_viewing_pack < max(self.packs_data.keys()):
            self.current_viewing_pack += 1
            self.refresh_tables()

    def load_xml(self):
        filenames = filedialog.askopenfilenames(filetypes=[("XML files", "*.xml")])
        if not filenames: return
        self.all_items, self.unscanned_items, self.packs_data = [], [], {1: []}
        self.current_filling_pack = self.current_viewing_pack = 1
        
        for filename in filenames:
            result, err = dm.parse_yunxi_xml(filename)
            if err: continue
            if result["limit"]: self.pack_limit.set(str(result["limit"]))
            
            for item in result["items"]:
                item["Weight"] = calc.calculate_item_weight(item["L"], item["W"], item["T"], item["Material"], self.materials_db, self.default_density.get())
                self.all_items.append(item)
                if "已" in item["Status"] or "scan" in item["Status"].lower():
                    try:
                        p_num = int(float(item["PackNum"]))
                        if p_num not in self.packs_data: self.packs_data[p_num] = []
                        self.packs_data[p_num].append(item)
                        self.current_filling_pack = max(self.current_filling_pack, p_num)
                    except: pass
                else:
                    self.unscanned_items.append(item)

        self.repack_scanned_items()
        self.update_filter_options()
        self.refresh_tables()
        self.lbl_scan_status.config(text="載入成功，請開始掃描", fg="blue")

    def save_xml(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if filename and dm.save_yunxi_xml(filename, self.packs_data, self.unscanned_items, self.pack_limit.get()):
            messagebox.showinfo("成功", "檔案儲存成功")

    # ================= 樹狀表與篩選更新 =================
    def sort_unscanned_tree(self, col):
        if self.unscanned_sort_col == col: self.unscanned_sort_state = (self.unscanned_sort_state + 1) % 3
        else: self.unscanned_sort_col, self.unscanned_sort_state = col, 1
        self.refresh_tables()

    def sort_scanned_tree(self, col):
        self.last_sort_reverse = not self.last_sort_reverse if self.last_sort_col == col else False
        self.last_sort_col = col
        self.refresh_tables()

    def update_filter_options(self):
        def get_unique(key, is_num):
            vals = {i[key] for i in self.all_items if i[key]}
            try: return [""] + sorted(list(vals), key=lambda x: float(x) if is_num else x)
            except: return [""] + sorted(list(vals))
        for k, cb in self.filter_combos.items(): cb['values'] = get_unique(k, k in ["L", "W", "T"])
        for k, cb in self.scanned_filter_combos.items(): cb['values'] = get_unique(k, k in ["L", "W", "T"])

    def clear_filters(self, filter_dict):
        for v in filter_dict.values(): v.set("")

    def check_filter(self, item, filter_dict):
        return all(not v.get().strip() or v.get().strip() == item[k] for k, v in filter_dict.items())

    def refresh_tables(self):
        for row in self.tree_unscanned.get_children(): self.tree_unscanned.delete(row)
        filtered_un = [i for i in self.unscanned_items if self.check_filter(i, self.filter_vars)]
        if self.unscanned_sort_state != 0 and self.unscanned_sort_col:
            filtered_un.sort(key=lambda x: (0, float(x.get(self.unscanned_sort_col,0))) if str(x.get(self.unscanned_sort_col,"")).replace('.','',1).isdigit() else (1, str(x.get(self.unscanned_sort_col,""))), reverse=(self.unscanned_sort_state == 2))
        for i in filtered_un: self.tree_unscanned.insert("", "end", values=(i["Barcode"], i["Order"], i["Customer"], i["Cabinet"], i["Part"], i["Material"], i["L"], i["W"], i["T"], i["Weight"]))

        for row in self.tree_scanned.get_children(): self.tree_scanned.delete(row)
        current_pack = self.packs_data.get(self.current_viewing_pack, [])
        filtered_sc = [i for i in current_pack if self.check_filter(i, self.scanned_filter_vars)]
        if self.last_sort_col:
            filtered_sc.sort(key=lambda x: float(x.get(self.last_sort_col,0)) if str(x.get(self.last_sort_col,"")).replace('.','',1).isdigit() else str(x.get(self.last_sort_col,"")), reverse=self.last_sort_reverse)
        for i in filtered_sc: self.tree_scanned.insert("", "end", values=(i["Barcode"], i["Order"], i["Customer"], i["Cabinet"], i["Part"], i["Material"], i["L"], i["W"], i["T"], i["Weight"]))

        grand_weight = sum(sum(i["Weight"] for i in items) for items in self.packs_data.values())
        grand_pieces = sum(len(items) for items in self.packs_data.values())
        valid_packs = max([p for p, items in self.packs_data.items() if items], default=0)
        
        self.lbl_info_left.config(text=f"總件數: {len(self.all_items)} | 未掃描: {len(self.unscanned_items)}")
        self.lbl_total_scanned_pieces.config(text=f"已掃描總數(件): {grand_pieces}")
        pack_weight = sum(i["Weight"] for i in current_pack)
        try: limit = float(self.pack_limit.get())
        except: limit = 20.0
        self.lbl_current_pack_info.config(text=f"📦 包號 {self.current_viewing_pack} ({pack_weight:.3f} kg / 限 {limit:.0f})", fg="#c62828" if pack_weight > limit else "#2e7d32")
        self.lbl_filling_status.config(text=f"[正在裝入: 第 {self.current_filling_pack} 包]")
        self.lbl_total_weight.config(text=f"總合計: {grand_weight:.3f} kg")
        self.lbl_total_packed_count.config(text=f"已打包總數: {valid_packs}")

    def on_double_click_unscanned(self, event):
        if not self.tree_unscanned.selection(): return
        barcode = str(self.tree_unscanned.item(self.tree_unscanned.selection())['values'][0])
        target = next((i for i in self.unscanned_items if i["Barcode"] == barcode), None)
        if target: self.process_move_to_pack(target)

    def on_double_click_scanned(self, event):
        if not self.tree_scanned.selection(): return
        barcode = str(self.tree_scanned.item(self.tree_scanned.selection())['values'][0])
        current_pack = self.packs_data[self.current_viewing_pack]
        target = next((i for i in current_pack if i["Barcode"] == barcode), None)
        if target:
            current_pack.remove(target)
            self.unscanned_items.append(target)
            self.refresh_tables()

if __name__ == "__main__":
    root = tk.Tk()
    app = YunxiWeightCalculator(root)
    root.mainloop()