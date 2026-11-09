"""Acesso a dados de produtos. Consultas sempre parametrizadas; sem estado e sem commit
(a transação é aberta pelo Service)."""


class ProdutoModel:
    def listar_todos(self, conn):
        return [dict(row) for row in conn.execute("SELECT * FROM produtos").fetchall()]

    def buscar_por_id(self, conn, produto_id):
        row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return dict(row) if row else None

    def criar(self, conn, nome, descricao, preco, estoque, categoria):
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    def atualizar(self, conn, produto_id, nome, descricao, preco, estoque, categoria):
        conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    def deletar(self, conn, produto_id):
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, conn, termo, categoria=None, preco_min=None, preco_max=None):
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        return [dict(row) for row in conn.execute(query, params).fetchall()]

    def baixar_estoque(self, conn, produto_id, quantidade):
        """Baixa condicional: só altera se houver estoque suficiente. Devolve True se baixou."""
        cursor = conn.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount == 1

    def devolver_estoque(self, conn, produto_id, quantidade):
        conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id))
