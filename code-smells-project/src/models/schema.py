"""Esquema do banco, dados iniciais e migração de senhas legadas. Executa uma vez, na inicialização."""
import logging

from werkzeug.security import generate_password_hash

from src.constants.usuario import PREFIXOS_HASH_SENHA, TIPO_ADMIN, TIPO_CLIENTE

logger = logging.getLogger(__name__)

_TABELAS = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # DEFAULT 'pendente' corresponde a constants.pedido.StatusPedido.PENDENTE
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

_PRODUTOS_INICIAIS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Senhas de demonstração, gravadas já com hash
_USUARIOS_INICIAIS = [
    ("Admin", "admin@loja.com", "admin123", TIPO_ADMIN),
    ("João Silva", "joao@email.com", "123456", TIPO_CLIENTE),
    ("Maria Santos", "maria@email.com", "senha123", TIPO_CLIENTE),
]


def _migrar_senhas_legadas(conn):
    """Converte para hash as senhas ainda em texto puro (bancos criados antes da correção)."""
    usuarios = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    migracoes = [
        (generate_password_hash(u["senha"]), u["id"])
        for u in usuarios
        if u["senha"] is not None and not u["senha"].startswith(PREFIXOS_HASH_SENHA)
    ]
    if migracoes:
        conn.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", migracoes)
        logger.info("Senhas legadas convertidas para hash: %s", len(migracoes))


def init_database(database):
    with database.transaction() as conn:
        for ddl in _TABELAS:
            conn.execute(ddl)

        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                _PRODUTOS_INICIAIS,
            )
            conn.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [(n, e, generate_password_hash(s), t) for n, e, s, t in _USUARIOS_INICIAIS],
            )

        _migrar_senhas_legadas(conn)
