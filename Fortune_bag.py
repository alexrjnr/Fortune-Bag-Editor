import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk

# Certifique-se de ter o Pillow instalado: pip install Pillow

class FortuneBagEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Fortune Bag Editor Pro")
        self.root.geometry("1100x750") # Aumentei um pouco a altura da janela

        self.items = []
        self.item_database = {} 
        self.icon_cache = {} 
        self.game_path = tk.StringVar()
        
        # Configurações de DB (dbname fixo como gf_ls)
        self.db_host = tk.StringVar(value="ip_do_servidor")
        self.db_user = tk.StringVar(value="postgres")
        self.db_pass = tk.StringVar(value="SENHA")
        self.db_port = tk.StringVar(value="5432")

        # --- AJUSTE DE ESPAÇAMENTO (ESTILO) ---
        self.style = ttk.Style()
        self.style.theme_use('default') # Garante que o estilo seja aplicado corretamente
        self.style.configure("Treeview", 
                             rowheight=45,      # Altura da linha aumentada para não sobrepor o ícone
                             font=('Segoe UI', 10)) # Fonte um pouco mais moderna
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))

        self.build_ui()

    def build_ui(self):
        # --- FRAME DE CONFIGURAÇÃO ---
        config_frame = tk.LabelFrame(self.root, text="Conexão e Caminhos")
        config_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(config_frame, text="Host:").grid(row=0, column=0, padx=2)
        tk.Entry(config_frame, textvariable=self.db_host, width=15).grid(row=0, column=1)
        
        tk.Label(config_frame, text="User:").grid(row=0, column=2, padx=2)
        tk.Entry(config_frame, textvariable=self.db_user, width=10).grid(row=0, column=3)
        
        tk.Label(config_frame, text="Pass:").grid(row=0, column=4, padx=2)
        tk.Entry(config_frame, textvariable=self.db_pass, show="*", width=10).grid(row=0, column=5)
        
        tk.Label(config_frame, text="Port:").grid(row=0, column=6, padx=2)
        tk.Entry(config_frame, textvariable=self.db_port, width=6).grid(row=0, column=7)

        tk.Button(config_frame, text="Selecionar Pasta Raiz", command=self.select_game_path, bg="#e1e1e1").grid(row=0, column=8, padx=10)
        tk.Label(config_frame, textvariable=self.game_path, fg="blue", font=("Arial", 8)).grid(row=0, column=9)

        # --- FRAME DE ENTRADA ---
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Box ID:").grid(row=0, column=0)
        self.box_id_entry = tk.Entry(input_frame, width=8)
        self.box_id_entry.grid(row=0, column=1, padx=2)

        tk.Label(input_frame, text="Item ID:").grid(row=0, column=2)
        self.item_id_entry = tk.Entry(input_frame, width=8)
        self.item_id_entry.grid(row=0, column=3, padx=2)

        tk.Label(input_frame, text="Qty:").grid(row=0, column=4)
        self.item_qty_entry = tk.Entry(input_frame, width=5)
        self.item_qty_entry.grid(row=0, column=5, padx=2)

        tk.Label(input_frame, text="Prob:").grid(row=0, column=6)
        self.item_prob_entry = tk.Entry(input_frame, width=8)
        self.item_prob_entry.grid(row=0, column=7, padx=2)

        tk.Label(input_frame, text="SET:").grid(row=0, column=8)
        self.item_set_entry = tk.Entry(input_frame, width=5)
        self.item_set_entry.grid(row=0, column=9, padx=2)

        tk.Button(input_frame, text="Add Item", command=self.add_item, bg="#d4edda").grid(row=0, column=10, padx=10)

        # MULTI ADD
        multi_frame = tk.Frame(self.root)
        multi_frame.pack(pady=5)
        tk.Label(multi_frame, text="Multi Item IDs:").grid(row=0, column=0)
        self.multi_ids_entry = tk.Entry(multi_frame, width=40)
        self.multi_ids_entry.grid(row=0, column=1, padx=5)
        tk.Button(multi_frame, text="Add Multiple", command=self.add_multiple).grid(row=0, column=2)

        # --- TABELA ---
        columns = ("ItemID", "Name", "Qty", "Probability", "SET")
        self.tree = ttk.Treeview(self.root, columns=columns, show="tree headings", height=15)
        
        self.tree.heading("#0", text="Icon")
        self.tree.column("#0", width=60, anchor="center")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.column("Name", width=300, anchor="w")

        # Scrollbar para a tabela
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(pady=10, fill="both", expand=True, padx=10, side="left")
        scrollbar.pack(side="right", fill="y", pady=10)

        # --- BOTÕES INFERIORES ---
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10, side="bottom")

        tk.Button(bottom_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=0, padx=5)
        tk.Button(bottom_frame, text="Clear List", command=self.clear_list).grid(row=0, column=1, padx=5)
        tk.Button(bottom_frame, text="LOAD BOX (DB)", command=self.load_box, bg="#cce5ff").grid(row=0, column=2, padx=5)
        tk.Button(bottom_frame, text="INSERT INTO DB", command=self.insert_into_db, bg="#f8d7da").grid(row=0, column=3, padx=5)

    # --- LÓGICA DE ARQUIVOS ---
    def select_game_path(self):
        path = filedialog.askdirectory()
        if path:
            self.game_path.set(path)
            self.parse_ini_files(path)

    def parse_ini_files(self, root_path):
        db_path = os.path.join(root_path, "data", "db")
        files = ["C_Item.ini", "C_ItemMall.ini"]
        self.item_database.clear()
        
        count = 0
        for file_name in files:
            full_path = os.path.join(db_path, file_name)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="big5", errors="ignore") as f:
                        lines = f.readlines()[1:] 
                        for line in lines:
                            if not line.strip(): continue
                            parts = line.split("|")
                            if len(parts) >= 10:
                                item_id = parts[0].strip()
                                icon_id = parts[1].strip()
                                name = parts[9].strip()
                                self.item_database[item_id] = {"icon": icon_id, "name": name}
                                count += 1
                except Exception as e:
                    print(f"Erro ao ler {file_name}: {e}")
        
        messagebox.showinfo("Sucesso", f"Database local carregada: {count} itens.")

    def get_icon(self, icon_id):
        if not icon_id: return None
        if icon_id in self.icon_cache: return self.icon_cache[icon_id]

        icon_path = os.path.normpath(os.path.join(self.game_path.get(), "UI", "itemicon", f"{icon_id}.dds"))
        
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.icon_cache[icon_id] = photo
                return photo
            except Exception as e:
                print(f"Erro ao processar ícone {icon_id}: {e}")
                return None
        return None

    def add_item_to_list(self, item_id, qty, prob, set_value):
        iid_str = str(item_id)
        info = self.item_database.get(iid_str, {"icon": "", "name": "Item Desconhecido"})
        icon_img = self.get_icon(info["icon"])
        
        node = self.tree.insert("", "end", image=icon_img if icon_img else "",
                                values=(item_id, info["name"], qty, prob, set_value))
        self.items.append((item_id, qty, prob, set_value))

    def add_item(self):
        try:
            item_id = int(self.item_id_entry.get())
            qty = int(self.item_qty_entry.get())
            prob = float(self.item_prob_entry.get())
            set_val = int(self.item_set_entry.get())
            self.add_item_to_list(item_id, qty, prob, set_val)
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos nos campos.")

    def add_multiple(self):
        raw = self.multi_ids_entry.get().replace(" ", "")
        try:
            qty = int(self.item_qty_entry.get())
            prob = float(self.item_prob_entry.get())
        except:
            messagebox.showerror("Erro", "Defina Qty e Probabilidade.")
            return

        try:
            parts = raw.split(",")
            next_set = 1
            for part in parts:
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    for i in range(start, end + 1):
                        self.add_item_to_list(i, qty, prob, next_set)
                        next_set += 1
                else:
                    self.add_item_to_list(int(part), qty, prob, next_set)
                    next_set += 1
        except:
            messagebox.showerror("Erro", "Formato de Multi-ID inválido.")

    def remove_selected(self):
        selected = self.tree.selection()
        for item in reversed(selected):
            idx = self.tree.index(item)
            self.tree.delete(item)
            del self.items[idx]

    def clear_list(self):
        self.tree.delete(*self.tree.get_children())
        self.items.clear()

    def get_conn(self):
        return psycopg2.connect(
            host=self.db_host.get(),
            database="gf_ls",
            user=self.db_user.get(),
            password=self.db_pass.get(),
            port=self.db_port.get()
        )

    def load_box(self):
        try:
            box_id = int(self.box_id_entry.get())
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT item_id, item_num, probability, set 
                FROM fortune_bag WHERE id = %s ORDER BY sequence
            """, (box_id,))
            rows = cur.fetchall()
            self.clear_list()
            for r in rows:
                self.add_item_to_list(r[0], r[1], r[2], r[3])
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro DB", str(e))

    def insert_into_db(self):
        if not self.items: return
        try:
            box_id = int(self.box_id_entry.get())
            conn = self.get_conn()
            cur = conn.cursor()

            cur.execute("SELECT COALESCE(MAX(sequence), 0) FROM fortune_bag WHERE id = %s", (box_id,))
            seq = cur.fetchone()[0] + 1

            for item_id, qty, prob, set_val in self.items:
                cur.execute("""
                    INSERT INTO fortune_bag (id, sequence, set, item_id, item_num, probability, 
                    bulletin, white, green, blue, yellow, note)
                    VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, 0, 0, '')
                """, (box_id, seq, set_val, item_id, qty, prob))
                seq += 1

            conn.commit()
            messagebox.showinfo("Sucesso", "Itens inseridos com sucesso!")
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro DB", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = FortuneBagEditor(root)
    root.mainloop()