import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk
import sv_ttk  # Necessário: pip install sv-ttk

class FortuneBagEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Fortune Bag Editor Pro - Dark Edition")
        self.root.geometry("1200x850")
        
        # Ativa o tema Dark
        sv_ttk.set_theme("dark")

        self.items = []
        self.item_database = {} 
        self.icon_cache = {} 
        self.game_path = tk.StringVar()
        
        # Configurações de DB
        self.db_host = tk.StringVar(value="ip_do_servidor")
        self.db_user = tk.StringVar(value="postgres")
        self.db_pass = tk.StringVar(value="SENHA")
        self.db_port = tk.StringVar(value="5432")

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=40, font=('Segoe UI', 10))
        self.style.configure("Bold.TLabel", font=('Segoe UI', 10, 'bold'))

    def build_ui(self):
        # --- CONTAINER PRINCIPAL ---
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill="both", expand=True)

        # --- FRAME DE CONFIGURAÇÃO (Topo) ---
        config_frame = ttk.LabelFrame(main_container, text=" Configurações de Conexão e Client ", padding="10")
        config_frame.pack(fill="x", pady=5)

        conn_grid = ttk.Frame(config_frame)
        conn_grid.pack(fill="x")

        fields = [("Host:", self.db_host), ("User:", self.db_user), ("Pass:", self.db_pass), ("Port:", self.db_port)]
        for i, (label, var) in enumerate(fields):
            ttk.Label(conn_grid, text=label).grid(row=0, column=i*2, padx=5)
            show = "*" if label == "Pass:" else ""
            ttk.Entry(conn_grid, textvariable=var, width=15, show=show).grid(row=0, column=i*2+1, padx=5)

        ttk.Button(config_frame, text="Selecionar Pasta Raiz do Jogo", command=self.select_game_path).pack(side="left", pady=10)
        ttk.Label(config_frame, textvariable=self.game_path, foreground="#57a2ff").pack(side="left", padx=15)

        # --- CORPO CENTRAL (Input e Tabela) ---
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill="both", expand=True, pady=10)

        # Esquerda: Inputs
        input_panel = ttk.Frame(content_frame, width=300)
        input_panel.pack(side="left", fill="y", padx=5)

        # Box ID Principal
        box_frame = ttk.LabelFrame(input_panel, text=" ID da Box Alvo ", padding=10)
        box_frame.pack(fill="x", pady=5)
        self.box_id_entry = ttk.Entry(box_frame, font=('Segoe UI', 12, 'bold'))
        self.box_id_entry.pack(fill="x")
        ttk.Button(box_frame, text="🔍 CARREGAR BOX DO BANCO", command=self.load_box).pack(fill="x", pady=5)

        # Multi-Add Panel
        multi_frame = ttk.LabelFrame(input_panel, text=" Adicionar em Massa (Multi-ID) ", padding=10)
        multi_frame.pack(fill="x", pady=10)
        
        ttk.Label(multi_frame, text="IDs (ex: 100,105-110):").pack(anchor="w")
        self.multi_ids_entry = ttk.Entry(multi_frame)
        self.multi_ids_entry.pack(fill="x", pady=2)

        m_grid = ttk.Frame(multi_frame)
        m_grid.pack(fill="x", pady=5)
        
        # Campos de controle do Multi-Add
        ttk.Label(m_grid, text="Qty:").grid(row=0, column=0)
        self.m_qty = ttk.Entry(m_grid, width=8); self.m_qty.insert(0, "1"); self.m_qty.grid(row=0, column=1)
        
        ttk.Label(m_grid, text="Prob:").grid(row=1, column=0)
        self.m_prob = ttk.Entry(m_grid, width=8); self.m_prob.insert(0, "0.1"); self.m_prob.grid(row=1, column=1)
        
        ttk.Label(m_grid, text="Set Inicial:").grid(row=2, column=0)
        self.m_set_start = ttk.Entry(m_grid, width=8); self.m_set_start.insert(0, "1"); self.m_set_start.grid(row=2, column=1)

        ttk.Button(multi_frame, text="➕ Adicionar Lista", style="Accent.TButton", command=self.add_multiple).pack(fill="x", pady=10)

        # Direita: Tabela
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(side="right", fill="both", expand=True)

        columns = ("ItemID", "Name", "Qty", "Probability", "SET")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="tree headings")
        self.tree.heading("#0", text="Ícone")
        self.tree.column("#0", width=60, anchor="center")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)
        self.tree.column("Name", width=250, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # --- BARRA INFERIOR ---
        bottom_bar = ttk.Frame(main_container)
        bottom_bar.pack(fill="x", pady=10)

        ttk.Button(bottom_bar, text="🗑️ Remover Selecionado (DB+Lista)", command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(bottom_bar, text="🧹 Limpar Visão", command=self.clear_list).pack(side="left", padx=5)
        
        self.btn_save = ttk.Button(bottom_bar, text="💾 SALVAR ALTERAÇÕES NO BANCO", command=self.insert_into_db)
        self.btn_save.pack(side="right", padx=5)

    # --- LÓGICA ---

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
                        for line in f.readlines()[1:]:
                            parts = line.split("|")
                            if len(parts) >= 10:
                                self.item_database[parts[0].strip()] = {"icon": parts[1].strip(), "name": parts[9].strip()}
                                count += 1
                except: pass
        messagebox.showinfo("Sucesso", f"Client lido: {count} itens carregados.")

    def get_icon(self, icon_id):
        if not icon_id or not self.game_path.get(): return None
        if icon_id in self.icon_cache: return self.icon_cache[icon_id]
        icon_path = os.path.join(self.game_path.get(), "UI", "itemicon", f"{icon_id}.dds")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.icon_cache[icon_id] = photo
                return photo
            except: return None
        return None

    def add_item_to_list(self, item_id, qty, prob, set_value):
        info = self.item_database.get(str(item_id), {"icon": "", "name": "Desconhecido"})
        icon_img = self.get_icon(info["icon"])
        self.tree.insert("", "end", image=icon_img if icon_img else "",
                         values=(item_id, info["name"], qty, prob, set_value))
        self.items.append([item_id, qty, prob, set_value])

    def add_multiple(self):
        try:
            raw_ids = self.multi_ids_entry.get().replace(" ", "")
            qty = int(self.m_qty.get())
            prob = float(self.m_prob.get())
            current_set = int(self.m_set_start.get())
            
            parts = raw_ids.split(",")
            for part in parts:
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    for i in range(start, end + 1):
                        self.add_item_to_list(i, qty, prob, current_set)
                else:
                    self.add_item_to_list(int(part), qty, prob, current_set)
            messagebox.showinfo("Sucesso", "Itens adicionados à lista.")
        except Exception as e:
            messagebox.showerror("Erro", f"Verifique os campos do Multi-Add: {e}")

    def get_conn(self):
        return psycopg2.connect(host=self.db_host.get(), database="gf_ls",
                                user=self.db_user.get(), password=self.db_pass.get(), port=self.db_port.get())

    def load_box(self):
        try:
            box_id = int(self.box_id_entry.get())
            conn = self.get_conn(); cur = conn.cursor()
            cur.execute("SELECT item_id, item_num, probability, set FROM fortune_bag WHERE id = %s ORDER BY sequence", (box_id,))
            rows = cur.fetchall()
            self.clear_list()
            for r in rows: self.add_item_to_list(r[0], r[1], r[2], r[3])
            conn.close()
        except Exception as e: messagebox.showerror("Erro DB", str(e))

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        if messagebox.askyesno("Confirmar", "Isso removerá os itens da lista E do Banco de Dados. Continuar?"):
            try:
                box_id = int(self.box_id_entry.get())
                conn = self.get_conn(); cur = conn.cursor()
                
                for item in selected:
                    item_values = self.tree.item(item)['values']
                    item_id = item_values[0]
                    # Deleta do banco
                    cur.execute("DELETE FROM fortune_bag WHERE id = %s AND item_id = %s", (box_id, item_id))
                    # Deleta da interface
                    idx = self.tree.index(item)
                    self.tree.delete(item)
                    if idx < len(self.items): del self.items[idx]
                
                conn.commit(); conn.close()
                messagebox.showinfo("Sucesso", "Removido do Banco e da Lista.")
            except Exception as e: messagebox.showerror("Erro ao remover", str(e))

    def clear_list(self):
        self.tree.delete(*self.tree.get_children())
        self.items.clear()

    def insert_into_db(self):
        if not self.items: return
        try:
            box_id = int(self.box_id_entry.get())
            conn = self.get_conn()
            cur = conn.cursor()

            # 1. Buscar o que JÁ EXISTE no banco para essa Box
            cur.execute("SELECT item_id FROM fortune_bag WHERE id = %s", (box_id,))
            existing_ids = {str(row[0]) for row in cur.fetchall()}

            items_to_process = []
            duplicates = []

            # 2. Separar o que é novo do que é duplicado
            for item in self.items:
                if str(item[0]) in existing_ids:
                    duplicates.append(str(item[0]))
                items_to_process.append(item)

            # 3. Se houver duplicatas, perguntar ao usuário
            mode = "insert" # padrão
            if duplicates:
                msg = f"Os seguintes IDs já existem na Box {box_id}:\n{', '.join(duplicates[:10])}...\n\n"
                msg += "Deseja ATUALIZAR os existentes ou PULAR as duplicatas?"
                
                # Custom message box
                choice = messagebox.askyesnocancel("Itens Duplicados Detectados", msg, 
                                                  detail="Sim: Atualizar Existentes\nNão: Pular Duplicatas\nCancelar: Parar tudo")
                
                if choice is True: # Sim = Atualizar
                    mode = "update"
                elif choice is False: # Não = Pular
                    mode = "skip"
                else: # Cancelar
                    return

            # 4. Processar a Inserção/Atualização
            cur.execute("SELECT COALESCE(MAX(sequence), 0) FROM fortune_bag WHERE id = %s", (box_id,))
            seq = cur.fetchone()[0] + 1

            for item_id, qty, prob, set_val in items_to_process:
                is_duplicate = str(item_id) in existing_ids
                
                if is_duplicate:
                    if mode == "skip":
                        continue
                    elif mode == "update":
                        cur.execute("""
                            UPDATE fortune_bag 
                            SET item_num = %s, probability = %s, set = %s 
                            WHERE id = %s AND item_id = %s
                        """, (qty, prob, set_val, box_id, item_id))
                else:
                    # Inserção de item novo
                    cur.execute("""
                        INSERT INTO fortune_bag (id, sequence, set, item_id, item_num, probability, 
                        bulletin, white, green, blue, yellow, note)
                        VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, 0, 0, '')
                    """, (box_id, seq, set_val, item_id, qty, prob))
                    seq += 1

            conn.commit()
            messagebox.showinfo("Sucesso", "Sincronização concluída com sucesso!")
            cur.close()
            conn.close()
            self.load_box() # Recarrega a lista para mostrar o estado real do DB

        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha na operação: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FortuneBagEditor(root)
    root.mainloop()
