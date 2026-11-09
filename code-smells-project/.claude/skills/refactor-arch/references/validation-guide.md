# Guia de Validação

Como **provar** que a refatoração não quebrou nada. "Parece que funciona" não é validação.

Objetivo: o sistema deve estar funcional **antes** de a skill modificar qualquer arquivo e deve **permanecer funcional** depois de cada refatoração. Para isso, a aplicação é executada localmente, seguindo as instruções do próprio projeto, e os endpoints são exercitados com chamadas reais (por exemplo, `curl`).

## Quando usar cada parte

| Momento | Seção | Resultado |
|---|---|---|
| Início da Fase 3 (depois da aprovação do usuário e **antes da primeira edição**) | Passos 0 e 1 | Ambiente preparado e baseline gravado |
| Fase 3 (durante a refatoração) | Passo 2 | Validação incremental após cada bloco |
| Fase 3 (ao final) | Passos 3 e 4 | Comparação com o baseline e registro do resultado |

## Princípio

Você só sabe que não quebrou se souber como era antes.
**Capture o baseline ANTES de modificar qualquer arquivo do projeto.** Depois da primeira edição é tarde.

Regras de segurança do baseline:

- Grave todos os artefatos de validação (logs, respostas, cópias de banco) em um diretório **fora do projeto**, por exemplo `VAL_DIR="$(mktemp -d)"`. As Fases 1 e 2 da skill são somente leitura: a aplicação só é executada a partir do início da Fase 3, depois da aprovação do usuário e antes da primeira edição.
- Executar a aplicação pode criar arquivos (banco local, caches, logs). Depois do boot, confira com `git status` e informe ao usuário o que foi criado. Não commite esses arquivos sem decisão do usuário.
- Chamadas de escrita (POST, PUT, PATCH, DELETE) alteram dados. Veja o Passo 1.4 antes de executá-las.

---

## Passo 0 — Preparar o ambiente a partir das instruções do projeto

### 0.1 Ler as instruções de execução

Leia, nesta ordem, o que existir: `README.md`, `Makefile`, scripts em `package.json`, `docker-compose.yml`, arquivos `.env.example`. Extraia:

- Pré-requisitos (versão da linguagem, banco de dados, variáveis de ambiente).
- Comando de instalação das dependências.
- Comando de start e a **porta** em que a aplicação escuta.
- Script de seed ou de migração, se houver.

Se as instruções estiverem ausentes ou contraditórias, use o que estiver no código (ponto de entrada e configuração da porta) e registre a dúvida para o usuário. Não invente comandos.

### 0.2 Instalar dependências

| Stack | Comando típico |
|---|---|
| Python | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (no Windows: `.venv\Scripts\pip`) |
| Node | `npm install` |
| Java | `./mvnw dependency:resolve` |
| Go | `go mod download` |

Se houver script de seed, execute-o: sem dados, os endpoints não exercitam nada de real.

### 0.3 Confirmar que a porta está livre

Veja a seção "Encerrar de forma confiável" abaixo. Se a porta estiver ocupada por outro processo, não o encerre sem avisar o usuário.

---

## Passo 1 — Baseline (antes de qualquer alteração)

### 1.1 Levantar a lista real de endpoints

Extraia do código, não da documentação (que costuma estar desatualizada):

```bash
grep -rn "@app.route\|@.*_bp.route\|add_url_rule" --include=*.py .
grep -rn "app\.\(get\|post\|put\|delete\)\|router\." --include=*.js .
```

Considere também arquivos `.http`, `.rest` e coleções de API no repositório: trazem payloads prontos e válidos. Esta lista é a referência de "todos os endpoints originais".

### 1.2 Subir a aplicação e esperar ficar pronta

```bash
PORT=<porta>
VAL_DIR="$(mktemp -d)"

<comando de start> > "$VAL_DIR/baseline-boot.log" 2>&1 &
APP_PID=$!

# Espera ativa em vez de um sleep fixo (limite de 30 s)
for i in $(seq 1 30); do
    curl -s -o /dev/null "http://localhost:$PORT/" && break
    sleep 1
done
```

Se a aplicação não subir, **pare**. Mostre o `baseline-boot.log` ao usuário e pergunte como proceder. Não refatore uma aplicação que já não funciona: não haveria como provar que a refatoração a manteve funcional.

### 1.3 Gravar as respostas

Uma função simples grava status e corpo de cada chamada em arquivos separados:

```bash
probe() {   # probe <nome> <metodo> <caminho> [corpo_json]
    local name="$1" method="$2" path="$3" body="$4"
    if [ -n "$body" ]; then
        curl -s -X "$method" -H "Content-Type: application/json" -d "$body" \
            -o "$OUT/$name.body" -w "%{http_code}" "http://localhost:$PORT$path" > "$OUT/$name.status"
    else
        curl -s -X "$method" \
            -o "$OUT/$name.body" -w "%{http_code}" "http://localhost:$PORT$path" > "$OUT/$name.status"
    fi
}

OUT="$VAL_DIR/baseline"; mkdir -p "$OUT"
probe root        GET /
probe list_items  GET /items
probe item_1      GET /items/1
probe item_404    GET /items/999999        # caminho de erro
probe create_bad  POST /items '{}'         # caminho de erro (validação)
```

Para cada endpoint, grave **status code**, **corpo da resposta** e os campos-chave. Inclua os caminhos de erro (404, 400, 401), e não só o caminho feliz.

**Registre também a prova de exploração (PoC) de cada vulnerabilidade que pretende corrigir, já no baseline.** Uma PoC só vale como prova de correção se, antes da refatoração, ela **de fato explorou** a falha. Se o baseline devolver o mesmo que uma chamada normal, o payload não funciona para aquela query e a "correção" não prova nada.

- Leia a query vulnerável no código e monte o payload para ela. Um payload genérico (`' OR '1'='1`) costuma falhar quando o valor fica dentro de um `LIKE '%...%'` ou de um parêntese (`AND (nome LIKE '%X%' ...)`): é preciso fechar o parêntese e comentar o resto (`zzzz') OR 1=1-- `).
- Ajuste o payload até o baseline mostrar o efeito (por exemplo, todos os registros em vez de nenhum, ou dados de outra tabela via `UNION SELECT`), e grave essa resposta como evidência.
- Se não conseguir explorar, registre a falha como "confirmada só por inspeção do código", sem PoC.

### 1.4 Chamadas de escrita e endpoints destrutivos

Chamadas de escrita mudam o estado. Para o baseline e para a comparação final partirem do mesmo estado:

1. Se o banco for um arquivo local (por exemplo SQLite), copie-o para `$VAL_DIR` antes do baseline e restaure a cópia antes da validação final, ou use uma cópia descartável.
2. Se o banco for um serviço externo ou compartilhado, **não execute escritas** sem decisão do usuário. Registre-as como "não verificadas" com o motivo.
3. Endpoints destrutivos (apagar tudo, resetar o banco, executar comando ou SQL arbitrário) só entram no baseline com autorização explícita do usuário e contra uma cópia descartável. Por padrão, **não os execute**: registre-os como "não verificados" e valide-os apenas por inspeção do código e pela resposta a uma chamada sem efeito, se existir.

### 1.5 Encerrar de forma confiável

**Atenção:** não use `pkill -f <padrão amplo>`. O padrão pode casar com a própria linha de comando do shell e matar a sessão.

**Linux** (`ss` e `grep -P` não existem no macOS nem no Git Bash):

```bash
kill $APP_PID 2>/dev/null

# Frameworks com auto-reload (Flask debug=True, nodemon) criam um processo FILHO
# que SOBREVIVE ao kill do pai e continua segurando a porta.
for pid in $(ss -lptnH "sport = :$PORT" | grep -oP 'pid=\K[0-9]+' | sort -u); do
    kill -9 $pid 2>/dev/null
done

ss -lptn "sport = :$PORT"     # precisa sair vazio
```

**macOS:** troque o `ss` por `lsof -ti tcp:$PORT` (lista os PIDs) e encerre cada um com `kill -9`.

**Windows, PowerShell:**

```powershell
Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue   # precisa sair vazio
```

**Cuidado com o launcher do venv no Windows.** O `python.exe` de um venv é um launcher que cria uma cadeia de processos (launcher, processo da aplicação e, com auto-reload, o filho do reloader). Os processos herdam o soquete: encerrar só o PID que `Get-NetTCPConnection` mostra pode não liberar a porta, e o `OwningProcess` pode apontar para um processo que já morreu enquanto o filho continua escutando. Se a porta continuar ocupada, liste os processos que a aplicação usa e encerre **somente os do venv de validação**, pelo caminho do executável, nunca por nome genérico:

```powershell
Get-CimInstance Win32_Process |
    Where-Object { $_.ExecutablePath -like '*<diretório-do-venv>*python.exe' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Antes de encerrar, confirme na `CommandLine` que o processo é a sua aplicação. Se pertencer a outra coisa, avise o usuário.

**Windows, Git Bash** (o MSYS reescreve `/PID`, por isso as barras duplas):

```bash
netstat -ano | findstr :$PORT            # identifique o PID que escuta a porta
taskkill //PID <pid> //F                 # encerre somente esse PID
netstat -ano | findstr :$PORT            # precisa sair vazio
```

**Por que isso importa:** um processo órfão da versão antiga continua respondendo na porta. Você testa a aplicação "refatorada", recebe 200 em tudo, e na verdade está falando com o código velho: um falso positivo que valida uma refatoração quebrada.

Se dois projetos usarem a mesma porta, **valide um de cada vez** e confirme a porta livre entre eles.

---

## Passo 2 — Validação incremental durante a refatoração

Não refatore tudo e teste no fim. Após cada bloco do playbook (`refactoring-playbook.md`):

1. A aplicação ainda sobe?
2. Um endpoint representativo ainda responde com o mesmo status do baseline?

Se quebrou, o culpado é o bloco que você acabou de aplicar. Achar o erro entre 3 mudanças é trivial; entre 40, não. Corrija ou desfaça o bloco antes de seguir para o próximo.

---

## Passo 3 — Verificação final

### 3.1 Boot limpo

Encerre qualquer processo anterior (Passo 1.5), suba a aplicação refatorada e grave o log:

```bash
<comando de start> > "$VAL_DIR/after-boot.log" 2>&1 &
APP_PID=$!
for i in $(seq 1 30); do curl -s -o /dev/null "http://localhost:$PORT/" && break; sleep 1; done
grep -iE "error|traceback|exception|cannot find|ModuleNotFound" "$VAL_DIR/after-boot.log"
```

Deve subir sem exceção. Verifique também os avisos de depreciação (`DeprecationWarning` e equivalentes): se você corrigiu o AP-12, eles devem ter sumido, e isso é evidência direta para o relatório. Se o baseline não tinha nenhum aviso, registre "0 DeprecationWarnings (nenhum no baseline)" em vez de omitir a linha.

### 3.2 Comparação com o baseline

Repita as mesmas chamadas do Passo 1.3, gravando em `$VAL_DIR/after`, e compare cada endpoint:

| Verificação | Critério |
|---|---|
| Status code | Idêntico ao baseline |
| Shape da resposta | Mesmos campos (salvo remoção intencional de campo sensível) |
| Dados | Mesmos valores para a mesma entrada |
| Caminhos de erro | 404/400/401 preservados |

**Atalho:** o script `scripts/compare.py` da skill faz esta comparação inteira (status, corpo, campos voláteis e listas sem ordem) entre dois diretórios no formato do Passo 1.3: `python .claude/skills/refactor-arch/scripts/compare.py "$VAL_DIR/baseline" "$VAL_DIR/after"`. Use `--ignore campo1,campo2` para campos voláteis específicos do projeto. Código de saída 1 indica divergência a investigar. O passo a passo abaixo mostra o que o script faz.

**Fallback sem Python:** se o interpretador Python não estiver disponível (por exemplo, em projeto Node), faça a comparação manualmente seguindo o passo a passo abaixo, endpoint por endpoint, e declare no bloco da Fase 3 que a comparação foi manual.

**Normalize campos voláteis antes de comparar.** Timestamps, ids gerados e tokens mudam a cada execução e não indicam regressão. Sem `jq` instalado (comum no Windows), use o equivalente em Python, com a mesma lista de campos:

```bash
norm_py() { python -c "
import json, sys
VOL = {'criado_em', 'created_at', 'updated_at', 'token'}
def strip(o):
    if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if k not in VOL}
    if isinstance(o, list): return [strip(v) for v in o]
    return o
print(json.dumps(strip(json.load(open(sys.argv[1]))), sort_keys=True, indent=1))" "$1"; }
```

Com `jq`:

```bash
norm() { jq -S 'del(.. | .criado_em?, .created_at?, .updated_at?, .token?)' "$1"; }
diff <(norm "$VAL_DIR/baseline/list_items.body") <(norm "$VAL_DIR/after/list_items.body")
```

**Comparação insensível a ordem.** Se a implementação antiga iterava sem `ORDER BY`, a ordem dos elementos era não determinística. Compare conjuntos, não sequências:

```bash
diff <(jq -S 'sort_by(.id)' baseline.json) <(jq -S 'sort_by(.id)' after.json)
```

Comparar literalmente acusa regressão falsa e, pior, esconde as reais no ruído.

### 3.3 Verificar que os findings foram resolvidos

Reexecute a detecção dos anti-patterns do relatório de auditoria, usando os sinais do `anti-patterns-catalog.md` para a stack. Exemplos:

```bash
grep -rn "execute(.*+\|execute(f\"" --include=*.py .     # AP-01: esperado vazio
grep -rn "\`SELECT.*\${" --include=*.js .                # AP-01 em Node: esperado vazio
grep -rn "global " --include=*.py .                      # AP-06: esperado vazio
grep -rn "print(\|console\.log" src/                     # AP-14: esperado vazio (ou só em scripts utilitários)
```

E reexecute a **exploração** gravada no baseline (Passo 1.3), quando houver:

```bash
curl -s "http://localhost:$PORT/items/search?q=zzzz')%20OR%201=1--%20"
# baseline (Passo 1.3): devolveu todos os registros, logo a PoC explorava a falha
# esperado agora: lista vazia (o payload é tratado como valor literal)
```

Use exatamente a PoC gravada no baseline (o payload do exemplo acima é só ilustrativo e depende da query). Se ela não explorava a falha antes, o resultado "vazio" agora não prova nada. Provar que o ataque parou de funcionar vale mais do que afirmar que o código está seguro. Só declare um anti-pattern como eliminado se a verificação acima confirmar.

---

## Passo 4 — Registrar o resultado

O resultado é entregue ao usuário no **bloco da Fase 3** definido em `report-template.md` (seção "Bloco da Fase 3"), acrescentado ao final do relatório (`reports/audit-project-N.md`, na raiz do repositório). Aquele template é a fonte única do formato; este guia não o duplica.

Preencha com o que saiu das verificações dos Passos 2 e 3:

- `Validation`: um item de checklist (`- [x] ✓`, ou `- [ ] ✗` se falhou) por verificação **realmente executada**; o que não foi executado vai para `Not verified`.
- `Endpoint comparison`: a tabela baseline x after do Passo 3.2, uma linha por endpoint.
- `Intentional changes` e `Not verified`: com a justificativa e o motivo.

Não escreva "Zero anti-patterns remaining" sem ter reexecutado a detecção do Passo 3.3.

### Armazenamento dos artefatos

| Camada | O que guarda | Vida útil |
|---|---|---|
| Temporária (`VAL_DIR`, fora do projeto) | venv, banco descartável, logs de boot, respostas brutas do baseline e do after | Do início ao fim da Fase 3. O baseline bruto precisa existir até a comparação do Passo 3.2 |
| Persistente (relatório do projeto) | Evidência legível para o usuário conferir: tabela `Endpoint comparison`, PoCs, `Validation`, `Not verified` | Fica no repositório, no arquivo do relatório |

Só apague o `VAL_DIR` depois de gravar o bloco da Fase 3 no relatório. Se a sessão for interrompida durante a Fase 3, o baseline bruto pode se perder: refaça-o **antes** de qualquer edição. Se a refatoração já começou, informe o usuário de que o baseline original só pode ser recuperado a partir do controle de versão. Não grave logs nem respostas brutas na raiz do projeto.

## Mudanças de comportamento aceitáveis

Só estas, sempre declaradas com justificativa. Cada uma depende de decisão do usuário, e a decisão deve estar registrada antes da refatoração:

| Mudança | Anti-pattern | Justificativa |
|---|---|---|
| Rota administrativa ou de execução arbitrária passa a exigir autenticação (ou é removida) | AP-03 | Vulnerabilidade; sem controle de acesso não há forma segura de mantê-la |
| Campo sensível some da resposta (senha, chave secreta) | AP-02, AP-03 | É exatamente a correção do anti-pattern |
| Formato de erro padronizado | AP-10 | Deixa de vazar detalhe interno |
| Ordem de coleção passa a ser determinística | AP-09 | Efeito colateral da correção |
| Efeito de negócio antes só descrito em log passa a ser executado | AP-08 | A operação passa a fazer o que o log já afirmava |

Tudo o mais que mudar de comportamento é **regressão**: conserte antes de reportar.

## Se não for possível validar

Sendo impossível subir a aplicação (dependência indisponível, serviço externo obrigatório):

1. **Diga isso explicitamente** no relatório. Não escreva "✓ endpoints respondem" sem ter testado.
2. Faça a validação possível: checagem de sintaxe, resolução de imports, lint.
3. Documente o que ficou por verificar e o motivo.
4. Antes da primeira edição, peça decisão ao usuário: refatorar sem baseline aumenta o risco de regressão não detectada.

Um relatório honesto sobre validação parcial é útil. Um relatório que afirma sucesso não verificado destrói a confiança em tudo o mais que ele diz.

## Checklist final

- [ ] Instruções de execução do projeto lidas (README, scripts) e ambiente preparado
- [ ] Baseline capturado antes de qualquer edição, em diretório fora do projeto
- [ ] Aplicação do baseline subiu sem erro (caso contrário, o usuário foi consultado)
- [ ] PoC de cada vulnerabilidade confirmada como exploitável no baseline (ou registrada como "só por inspeção")
- [ ] Escritas e endpoints destrutivos tratados conforme o Passo 1.4
- [ ] Validação incremental feita após cada bloco do playbook
- [ ] Aplicação sobe sem erro após a refatoração
- [ ] Todos os endpoints originais comparados ao baseline
- [ ] Caminhos de erro preservados
- [ ] Campos voláteis normalizados e ordem tratada quando aplicável
- [ ] Portas liberadas, sem processo órfão
- [ ] Findings reverificados como resolvidos (com a mesma PoC do baseline)
- [ ] Mudanças de comportamento intencionais declaradas e aprovadas
- [ ] Bloco de validação reflete a realidade, com o que não foi verificado e o motivo
