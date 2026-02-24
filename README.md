

# 🛠️ Fortune Bag Editor Pro

**Ferramenta completa para gestão de banco de dados do Grand Fantasia (PostgreSQL).** Este editor foi projetado para simplificar a administração de itens de Fortune Bag, substituindo queries manuais por uma interface visual, rápida e segura.

## 🚀 O que a ferramenta faz?

### 📦 Gestão Inteligente de Itens

* **Importação em Massa (Multi-Add):** Permite adicionar centenas de itens de uma só vez usando listas separadas por vírgula (ex: `101,102`) ou intervalos de IDs (ex: `2000-2050`).
* **Configuração Dinâmica:** No ato de adicionar múltiplos itens, você já define a **Quantidade**, **Probabilidade** e o **Set Inicial** para todos eles.
* **Proteção de Dados:** Antes de salvar, a ferramenta verifica se os itens já existem na Box e abre uma janela de decisão:
* **Atualizar:** Sobrescreve os valores dos itens que já estão no banco.
* **Pular:** Mantém o que já está no banco e ignora as duplicatas da lista.
* **Cancelar:** Aborta a operação sem alterar nada.



### 🔍 Integração com o Client

* **Visualização de Ícones:** Lê automaticamente os arquivos de imagem (`.dds`) da pasta `UI/itemicon` do seu jogo, facilitando a identificação visual de cada item.
* **Sincronização de Nomes:** Carrega os nomes reais dos itens lendo os arquivos `C_Item.ini` e `C_ItemMall.ini` do seu próprio Client.

### 🗄️ Manipulação Direta do Banco (gf_ls)

* **Load Box:** Carrega instantaneamente todos os itens que já estão cadastrados em uma determinada Box ID diretamente do PostgreSQL.
* **Remoção Sincronizada:** Ao selecionar e remover um item na interface, o programa oferece a opção de **deletar permanentemente** a linha correspondente no banco de dados.
* **Inserção Segura:** Calcula automaticamente a sequência (`sequence`) correta para que os novos itens entrem na ordem certa após os já existentes.

### 🎨 Interface e Usabilidade

* **Tema Dark:** Design moderno e escuro para maior conforto visual.
* **Tabela Detalhada:** Exibe ícone, ID, nome, quantidade, probabilidade e o número do Set em uma lista organizada.
* **Portabilidade:** Um único arquivo executável que não precisa de instalação.

---

## 📥 Download do Executável

Clique no link abaixo para baixar o editor pronto para uso:

# [➔ CLIQUE AQUI PARA BAIXAR O EDITOR](https://drive.google.com/file/d/1Xb4AGdq5NXVLmNXcfJjnPoSAT9jnNX92/view?usp=sharing)

---

## 📖 Manual de Uso

1. **Conexão:** Informe o IP do Host, Usuário e Senha do PostgreSQL (Porta padrão 5432).
2. **Caminho do Jogo:** Clique em **"Selecionar Pasta Raiz"** e aponte para a pasta principal do seu Client.
3. **Edição:** * Coloque o ID da Box desejada.
* Use **LOAD BOX** para ver o conteúdo atual.
* Adicione novos itens individualmente ou via **Multi-ID**.


4. **Finalização:** Clique em **SALVAR ALTERAÇÕES NO BANCO** e escolha como lidar com possíveis duplicatas.

> **⚠️ NOTA:** Por ser um executável compilado via PyInstaller, o Windows SmartScreen pode exibir um alerta. O programa é uma ferramenta administrativa segura que interage apenas com o banco de dados configurado por você.

---
