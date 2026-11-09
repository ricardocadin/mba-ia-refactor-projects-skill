# Template do Relatório (Fases 2 e 3)

Documento de referência que define o formato padronizado do relatório. Ele tem duas partes, geradas em momentos diferentes e gravadas no mesmo arquivo (`reports/audit-project-N.md`, na raiz do repositório; `N` é reaproveitado se já existir relatório do mesmo projeto, ou o próximo número livre; ver o passo 6 da Fase 2 no `SKILL.md`):

1. **Relatório de auditoria (Fase 2):** a estrutura em "Estrutura do relatório".
2. **Bloco de refatoração concluída (Fase 3):** acrescentado ao final do mesmo arquivo depois da validação, conforme "Bloco da Fase 3". A parte da Fase 2 não é reescrita.

## Objetivo

O relatório de auditoria (Fase 2) apenas **reporta** os anti-patterns encontrados, com localização exata. Ele não corrige nem altera código. O bloco da Fase 3 registra o que foi alterado e **a evidência de que a aplicação continua funcional**, para o usuário conferir.

## Estrutura do relatório

```
# ARCHITECTURE AUDIT REPORT

Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<M> lines of code

## Summary
Date:    <YYYY-MM-DD>
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Achados por severidade
| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | <nome do catálogo> | `arquivo:linha` | <observação se relevante> | <resumo curto da correção> |
| ... | | | | | |

## Findings

### [CRITICAL] <Nome do anti-pattern> (AP-XX)
File: <caminho:linha> (+ demais ocorrências, se houver)
Description: <o que está errado, concretamente — cite o identificador ou valor real>
Evidence: <trecho curto de código, comando executado ou saída observada>
Impact: <consequência prática se não for corrigido>
Recommendation: <ação objetiva> (→ PB-XX)

### [CRITICAL] <próximo>
...

### [HIGH] <...>
### [MEDIUM] <...>
### [LOW] <...>

## Not Verified
- <AP-XX ou item>: <o que não foi verificado> | Reason: <motivo>

(Se tudo foi verificado, escreva: "All catalog items were verified".)


### Total: <N> findings
```

## Bloco da Fase 3

Gerado ao final da Fase 3, depois da validação do `validation-guide.md`, e acrescentado ao final do arquivo do relatório:

```
# PHASE 3: REFACTORING COMPLETE

## New Project Structure
<árvore real de diretórios e arquivos após a refatoração>

## Validation
- [x] ✓ Application boots without errors
- [x] ✓ <N>/<N> endpoints respond correctly
- [x] ✓ Status codes match baseline
- [x] ✓ <n>/<N> findings resolved (re-detected with the catalog signals)
- [x] ✓ Zero anti-patterns remaining
- [x] ✓ <vulnerabilidade> PoC no longer exploitable
- [x] ✓ 0 DeprecationWarnings (was <n>)
- [ ] ✗ <verificação executada que falhou ou ficou pendente>: <descrição>

### Intentional changes
- <mudança de comportamento, com justificativa e a decisão do usuário>

### Not verified
- <o que ficou sem verificação>: <motivo>

### Endpoint comparison
| Method | Path | Baseline | After | Result |
|---|---|:---:|:---:|:---:|
| GET | /exemplo | 200 | 200 | OK |
| ... | | | | |
```

### Checklist de validação preenchido
Logo após o bloco, grave o **checklist da Fase 3** do `SKILL.md` já preenchido: uma linha por item, `[x]` com a evidência (comando, contagem ou `arquivo:linha`) ou `[ ]` com o motivo. Ele existe para o usuário conferir o resultado sem refazer a validação.

### Regras de preenchimento do bloco da Fase 3
- `New Project Structure`: gerada a partir do sistema de arquivos depois da refatoração, nunca de memória. Mostre só os diretórios e arquivos que existem, com a função de cada camada quando não for óbvia (por exemplo, `app.py (composition root)`).
- `Validation` é uma lista de checklist, um item por verificação. **Um item `- [x] ✓` só aparece se a verificação correspondente foi executada e passou.** Se não foi executada, o item vai para `### Not verified` com o motivo. Se foi executada e falhou, use `- [ ] ✗` com a descrição e corrija antes de entregar.
- `Zero anti-patterns remaining` só aparece (como `- [x] ✓`) quando a detecção do Passo 3.3 do `validation-guide.md` foi reexecutada e não encontrou nenhum. Caso contrário, escreva `- [ ] ✗ <n> anti-patterns remaining: AP-XX (motivo)` e liste os pendentes.
- Não use linhas de `=` nem texto corrido: o título é `# PHASE 3: REFACTORING COMPLETE`, e `Intentional changes` e `Not verified` são subseções (`###`) com um item de lista por linha.
- As linhas de PoC (uma por vulnerabilidade com PoC gravada no baseline) e de `DeprecationWarnings` só entram se houver finding correspondente (por exemplo, AP-01 e AP-12). Para DeprecationWarnings sem ocorrência no baseline, use `0 DeprecationWarnings (nenhum no baseline)`.
- `### Intentional changes`: toda mudança de comportamento declarada, com a justificativa e a decisão do usuário (ver "Mudanças de comportamento aceitáveis" no `validation-guide.md`). Se não houve, escreva "none".
- `### Not verified`: tudo o que ficou sem verificação (por exemplo, endpoints destrutivos, escritas em banco compartilhado), sempre com o motivo. Aqui **não entram decisões humanas ainda não tomadas**: elas devem ter sido perguntadas ao usuário antes da refatoração (passo 3.0 do `SKILL.md`). Se tudo foi verificado, escreva "All items were verified".
- `Endpoint comparison`: uma linha por endpoint do baseline (incluindo caminhos de erro), com o status antes e depois. `Result` é `OK` quando o status e o corpo normalizado são idênticos, `CHANGED` para mudança intencional listada em `Intentional changes` e `FAIL` para regressão (que precisa ser corrigida antes de entregar). Endpoints não executados aparecem como `SKIPPED`, também listados em `Not verified`.

## Regras de preenchimento

### Cabeçalho
- `Project`: nome do diretório raiz do projeto analisado.
- `Stack`: linguagem e framework com a versão **declarada** nos arquivos de dependência. Se a versão não estiver declarada, escreva "versão não confirmada".
- `Files`: quantidade de arquivos de código-fonte analisados e total aproximado de linhas.

### Summary
- `Date`: data de geração do relatório, no formato `YYYY-MM-DD`. Este é o único campo de data do relatório e fica somente no Summary.
- A contagem por severidade deve bater com o número de findings listados na tabela e na seção Findings.

### Tabela "Achados por severidade"
- Serve para resumo rápido e consulta. Cada linha corresponde a um finding da seção Findings.
- `#`: numeração sequencial, seguindo a ordem de severidade.
- `Problema`: nome do anti-pattern conforme o catálogo (`anti-patterns-catalog.md`).
- `Localização`: sempre no formato `arquivo:linha`, entre crases. Para intervalo, use `arquivo:linha-inicial-linha-final`.
- `Observações`: preencher só quando houver algo relevante. Caso contrário, deixar vazio.
- `Ação proposta`: versão mais objetiva, concisa e resumida da `Recommendation` do finding correspondente: uma frase curta, sem detalhar a implementação e sem a referência ao playbook. Se o item depender de decisão humana, isso deve aparecer aqui também.

### Findings
- Cada finding traz os campos `File`, `Description`, `Evidence`, `Impact` e `Recommendation`.
- O título segue o formato `### [SEVERIDADE] Nome do anti-pattern (AP-XX)`, com o nome e o ID do catálogo.
- `File`: traz a primeira ocorrência e, entre parênteses, as demais (`(+ outras ocorrências)`), todas no formato `caminho:linha`. Não crie listas separadas de ocorrências dentro do finding; as ocorrências ficam somente no campo `File`.
- `Recommendation`: aponta para o playbook de refatoração com `(→ PB-XX)`. O número do `PB-XX` é o mesmo do `AP-XX` do catálogo. Quando a correção depender de decisão externa (humana), a recomendação deve deixar isso claro, por exemplo: `Requer decisão humana: <o que precisa ser decidido>`. Isso vale sempre que a correção mudar o que a aplicação aceita ou devolve (nova validação que rejeita entrada hoje aceita, rota que passa a exigir autenticação, campo removido, default de execução diferente).
- Findings de APIs deprecated seguem o mesmo formato, com o ID `AP-12`.
- Um mesmo anti-pattern pode gerar mais de um finding. Não se limita a um finding por AP: problemas distintos do mesmo AP (conforme a granularidade definida no catálogo, como as duas partes do AP-03) são reportados separadamente. Cada um tem título próprio, nome descritivo distinto e o mesmo `AP-XX`.

### Not Verified
- Liste tudo o que a auditoria **não conseguiu verificar**, sempre com o motivo. Exemplos: API possivelmente deprecated cuja versão não está declarada; sinal que exige linter ou execução que não estava disponível; trecho que não pôde ser lido.
- Cada item cita o anti-pattern ou o assunto, o que não foi verificado e o motivo (`Reason`).
- Itens não verificados não entram na contagem de findings.
- Se tudo foi verificado, escreva a frase padrão indicada no template.

## Regras gerais

1. **Ordenação:** sempre da maior para a menor severidade: CRITICAL, HIGH, MEDIUM, LOW. A ordem vale para a tabela e para a seção Findings.
2. **Referência obrigatória:** use sempre a referência `caminho:linha` para os arquivos.
3. **Sem suposição:** não presuma nem infira nada. Todo achado deve conter pelo menos uma linha de referência. Um achado sem linha de referência não entra no relatório.
4. **Somente reportar (Fase 2):** a geração do relatório de auditoria não realiza correção nem alteração de código. O objetivo é reportar os itens encontrados.

## Checklist de validação do relatório

Antes de entregar o relatório, confirme cada item:

- [ ] Todo finding está relacionado a um anti-pattern do catálogo (título com `AP-XX`).
- [ ] Nenhum apontamento está sem referência de linha (`caminho:linha`).
- [ ] Nenhum problema foi inferido sem relação com um anti-pattern do catálogo.
- [ ] Os itens que dependem de decisão externa (humana) para correção deixam isso claro na recomendação.
- [ ] Os achados estão ordenados por severidade (CRITICAL, HIGH, MEDIUM, LOW), na tabela e nos Findings.
- [ ] A contagem do Summary bate com o número de findings da tabela e da seção Findings.
- [ ] O que não pôde ser verificado está listado em Not Verified, com o motivo.

### Bloco da Fase 3

- [ ] `New Project Structure` reflete a árvore real após a refatoração.
- [ ] Cada linha `✓` de `Validation` corresponde a uma verificação realmente executada.
- [ ] `Endpoint comparison` cobre todos os endpoints do baseline, sem nenhum `FAIL`.
- [ ] Toda diferença de comportamento está em `Intentional changes`, com justificativa e aprovação.
- [ ] `Not verified` lista o que ficou de fora e o motivo.
