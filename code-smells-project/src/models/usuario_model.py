"""Acesso a dados de usuários. Consultas parametrizadas; a senha é sempre um hash (nunca texto puro)."""


class UsuarioModel:
    def listar_todos(self, conn):
        return [dict(row) for row in conn.execute("SELECT * FROM usuarios").fetchall()]

    def buscar_por_id(self, conn, usuario_id):
        row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return dict(row) if row else None

    def listar_por_email(self, conn, email):
        """Não há restrição de unicidade de e-mail no esquema: devolve todos os usuários com o e-mail."""
        return [dict(row) for row in conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()]

    def criar(self, conn, nome, email, senha_hash, tipo):
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        return cursor.lastrowid
