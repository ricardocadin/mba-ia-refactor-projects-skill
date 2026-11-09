---
name: refactor-arch
description: Audita e refatora a arquitetura de um projeto backend para o padrão MVC, em 3 fases (análise, auditoria com relatório, refatoração validada), independente de linguagem ou framework. Use sempre que o usuário pedir para refatorar para MVC, auditar a arquitetura, achar anti-patterns, code smells, God Class, SQL injection, credenciais hardcoded, APIs deprecated ou "organizar" um projeto legado, mesmo que não cite o nome da skill. Executa na pasta raiz do projeto, sem argumentos (`/refactor-arch`).
---

# refactor-arch

Analisa, audita e refatora o projeto da pasta atual para o padrão MVC, corrigindo anti-patterns **sem mudar o comportamento da aplicação**. Funciona para qualquer stack: o conhecimento específico vem dos arquivos de `references/`, não deste arquivo.

O alvo é sempre a pasta onde a skill foi invocada. Não há argumentos.

## Como trabalhar

Execute as 3 fases **em sequência** (1 → 2 → 3). A Fase 3 só começa depois que o usuário responder "sim" à pergunta da Fase 2.

Por que esse desenho: um usuário que herda um projeto legado precisa confiar que nada será alterado antes de ele ver o diagnóstico, e que depois da alteração tudo continua funcionando. Por isso as Fases 1 e 2 só leem, a aprovação é explícita, e a Fase 3 trabalha em blocos pequenos, cada um validado antes do seguinte.

## Arquivos de referência

Leia cada arquivo **no momento em que a fase correspondente começa**, não todos de uma vez.

| Arquivo | Fase | Para quê |
|---|---|---|
| `references/project-analyzer.md` | 1 | Heurísticas de detecção de stack, banco, arquitetura e formato da saída da análise |
| `references/anti-patterns-catalog.md` | 2 | Catálogo AP-01..AP-14 com sinais de detecção e severidade (inclui APIs deprecated, AP-12) |
| `references/report-template.md` | 2 e 3 | Formato do relatório de auditoria (Fase 2) e do bloco de refatoração concluída (Fase 3) |
| `references/mvc-architecture.md` | 3 | Camadas e responsabilidades do MVC alvo |
| `references/refactoring-playbook.md` | 3 | Transformações PB-01..PB-14 com exemplos antes/depois (o PB-xx corrige o AP-xx) |
| `references/validation-guide.md` | 3 | Como subir a aplicação, gravar o baseline e provar que nada quebrou |
| `scripts/compare.py` | 3 | Compara baseline x after (status, corpo, campos voláteis, listas sem ordem) |

---

## Fase 1 — Análise do projeto

**Objetivo:** entender o projeto antes de julgar qualquer coisa.

1. Leia `references/project-analyzer.md`.
2. Analise o projeto conforme as instruções desse arquivo.
3. Detecte linguagem, framework (com a versão **declarada** nos arquivos do projeto), banco de dados, dependências e artefatos.
4. Identifique a arquitetura atual.
5. Imprima o resultado **exatamente** no formato de saída do `project-analyzer.md`. Não invente outro formato.
6. Aplique o **checklist da Fase 1** (seção "Checklist de validação") e imprima-o preenchido, com a evidência de cada item. Corrija a análise antes de seguir se algum item falhar.

Em seguida, siga direto para a Fase 2 (não há pausa aqui).

## Fase 2 — Auditoria

**Objetivo:** identificar os problemas e produzir um relatório auditável.

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Cruze o código do projeto com os sinais de detecção do catálogo, usando o resultado da Fase 1 para saber onde olhar.
3. Verifique sempre APIs deprecated (AP-12). Se a versão do framework não estiver declarada, o item vai para `Not Verified`, não vira finding.
4. Para cada finding, registre o arquivo e a linha exatos e a evidência. Um problema sem `arquivo:linha` não entra no relatório. Se a correção do finding mudar o que a aplicação aceita ou devolve (nova validação, rota protegida, campo removido, default de execução), marque a recomendação como `Requer decisão humana`, explicando o que precisa ser decidido.
5. Monte o relatório seguindo o `report-template.md` (parte da Fase 2) e confira o checklist de validação do template antes de entregar.
6. Grave o relatório em `reports/audit-project-N.md`, dentro da pasta `reports/` na **raiz do repositório git** (obtenha com `git rev-parse --show-toplevel`; não é a pasta do projeto analisado). Se não houver repositório git, pergunte ao usuário onde gravar. Escolha `N` assim: (a) se já existir um `audit-project-*.md` cuja linha `Project:` seja igual ao nome do projeto analisado, reaproveite o número dele e substitua o arquivo (é uma nova execução do mesmo projeto); (b) senão, use o maior número existente + 1, ou `1` se a pasta não tiver nenhum `audit-project-*.md`. Crie `reports/` se necessário. Exceção: se o relatório existente do mesmo projeto já contém o bloco `PHASE 3: REFACTORING COMPLETE`, não o substitua: pergunte ao usuário o que fazer. Gravar o relatório antes da pergunta de confirmação é permitido (é a única escrita das Fases 1 e 2).
7. Aplique o **checklist da Fase 2** (seção "Checklist de validação"), corrigindo o relatório se algum item falhar, e mostre ao usuário o relatório, o caminho do arquivo e o checklist preenchido. O último item (pausa e confirmação) é marcado só depois do passo 8.
8. **Pare e faça exatamente esta pergunta, esperando a resposta real do usuário:**

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- Se a resposta for `y`, `yes` ou `sim`: prossiga para a Fase 3.
- Qualquer outra resposta, ou nenhuma resposta: finalize a execução. Não presuma consentimento, não repita a pergunta em tom de insistência e não inicie a Fase 3 por conta própria.

O mínimo esperado é de 5 findings, mas **não complete a lista para chegar a um número**. Reporte o que tem evidência; se houver menos de 5, diga isso claramente no relatório.

## Fase 3 — Refatoração

**Objetivo:** reestruturar o projeto para o padrão MVC preservando o comportamento.

### 3.0 Preparação

1. Confirme que o usuário respondeu sim explicitamente na Fase 2. Se houver dúvida, volte e pergunte.
2. Leia `references/mvc-architecture.md`, `references/refactoring-playbook.md` e `references/validation-guide.md`.
3. **Levante todas as decisões humanas e pergunte ao usuário ANTES da primeira edição**, uma a uma, com opções claras. A lista não se limita aos findings marcados "Requer decisão humana" no relatório. Inclua: (a) cada ponto "Decisão humana" dos playbooks PB-xx que você vai aplicar; (b) toda mudança de comportamento que a refatoração causaria, mesmo as pequenas: entrada que hoje é aceita e passaria a ser rejeitada (ou o inverso), validações novas, defaults de execução (host, debug, porta, variável de ambiente obrigatória), formato de erro, campos removidos ou acrescentados, efeitos de negócio que passam a ser executados; (c) partes de um finding que você pretende deixar de fora. Registre as decisões; mudança de comportamento sem decisão registrada é regressão. **Nenhum item pode ficar "pendente de decisão" no bloco da Fase 3 sem ter sido perguntado antes.** Se surgir uma decisão nova durante a implementação, pare e pergunte antes de continuar.
4. Siga o `validation-guide.md` à risca. Em especial: informe ao usuário, em uma linha, o que vai rodar (instalação de dependências em ambiente isolado, subida da aplicação) e **siga em frente sem pedir novo "sim"**: o consentimento da Fase 2 já cobre a Fase 3. Use um diretório temporário **fora do projeto** para artefatos. Endpoints destrutivos (apagar tudo, resetar banco, executar SQL arbitrário) não são executados sem autorização explícita.

### 3.1 Baseline (antes da primeira edição)

Execute os Passos 0 e 1 do `validation-guide.md`: prepare o ambiente, suba a aplicação, grave status e corpo de cada endpoint (incluindo caminhos de erro) e a PoC de cada vulnerabilidade que será corrigida. Se a aplicação original não subir, **pare** e consulte o usuário: sem baseline não há como provar que a refatoração preservou o comportamento.

### 3.2 Plano e ciclo de refatoração

1. Monte um plano com a estrutura MVC alvo e a ordem dos blocos, usando os PB-xx do playbook. Adapte ao contexto: em um monolito, crie as camadas; em um projeto que já tem alguma separação, preserve o que está adequado e corrija só o que o relatório apontou. Não reorganize por reorganizar.
2. Trabalhe em **blocos pequenos**, um de cada vez. Para cada bloco:
   1. confirme que a aplicação está funcionando antes de mexer (estado anterior);
   2. aplique a transformação do playbook ao escopo delimitado;
   3. suba a aplicação e verifique o comportamento (Passo 2 do guia);
   4. se algo quebrou, corrija ou desfaça **só o que você acabou de alterar** antes de continuar.
3. **Nunca avance para o próximo bloco se o atual quebrou ou introduziu um problema.** O erro mais barato de achar é o do bloco que acabou de ser aplicado.

### 3.3 Verificação final e entrega

1. Execute os Passos 3 e 4 do guia: boot limpo, comparação completa com o baseline (`scripts/compare.py`), reexecução da detecção do catálogo e das PoCs gravadas no baseline.
2. Aplique o **checklist da Fase 3** (seção "Checklist de validação"). Item que falha volta para o ciclo do 3.2 e é corrigido; não encerre com item pendente sem declará-lo e explicar o motivo ao usuário.
3. Gere o **bloco da Fase 3** conforme a seção "Bloco da Fase 3" do `report-template.md` e acrescente-o ao final do mesmo arquivo `reports/audit-project-N.md` gravado na Fase 2, sem reescrever a parte da Fase 2, seguido do **checklist da Fase 3 preenchido** (com a evidência de cada item). A estrutura em `New Project Structure` vem do sistema de arquivos real.
4. Remova os artefatos temporários só depois de gravar o bloco; confirme que não restou processo escutando a porta.
5. Rode `git status` e informe ao usuário o que foi criado e alterado. **Não faça commit nem push**: isso é decisão do usuário.

---

## Regras

- **Fases 1 e 2 são somente leitura.** Não use Write, Edit nem qualquer comando que altere arquivos do projeto. A única exceção é gravar `reports/audit-project-N.md` na raiz do repositório. Subir a aplicação e instalar dependências só acontecem na Fase 3.
- **A aprovação da Fase 2 é obrigatória** e vem do usuário, de verdade. Sem resposta, não prossiga.
- **Nunca presuma.** Todo problema reportado tem arquivo e linha e se apoia nos arquivos de referência. O que não pôde ser verificado vai para `Not Verified`, com o motivo.
- **A refatoração preserva o comportamento.** Mudanças de comportamento só as listadas em "Mudanças de comportamento aceitáveis" do guia, com decisão do usuário registrada. O resto é regressão.
- **Relate com honestidade.** Cada ✓ do bloco da Fase 3 corresponde a uma verificação executada. O que não foi verificado é declarado.
- **Agnóstica de tecnologia.** Não assuma Python, Node ou qualquer stack: derive comandos de start, porta e dependências dos arquivos do próprio projeto (README, scripts, manifestos).

## Checklist de validação

Este é o critério de aceite da skill. Ele é o **portão de saída de cada fase**: ao terminar a fase, avalie cada item, **um por um, com evidência concreta**, e imprima o checklist preenchido para o usuário. Sem a evidência, o item não é marcado.

Como preencher:

- `[x]` somente quando você executou a verificação indicada em "Como verificar" e ela passou. Escreva a evidência ao lado (comando, contagem, `arquivo:linha`).
- `[ ]` quando não passou ou não foi verificado, com o motivo. Corrija e reavalie antes de seguir para a próxima fase. Só encerre com um item pendente se o usuário foi informado do motivo.
- `n/a` é permitido apenas onde o item diz "se aplicável" (APIs deprecated), com a justificativa (por exemplo, "nenhuma API deprecated encontrada; versões declaradas em requirements.txt").
- Não marque por inferência ("deve estar certo"). Marcar sem verificar é pior do que deixar pendente.

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente — *Como verificar:* confira a extensão predominante dos arquivos-fonte e o manifesto de dependências.
- [ ] Framework detectado corretamente — *Como verificar:* confira o import/uso real no código e a versão declarada no manifesto (sem versão declarada: "não confirmado").
- [ ] Domínio da aplicação descrito corretamente — *Como verificar:* a descrição se apoia nas rotas, nas tabelas/entidades e nos nomes de módulos lidos, não em suposição.
- [ ] Número de arquivos analisados condiz com a realidade — *Como verificar:* liste os arquivos-fonte do projeto (excluindo dependências, caches e ambientes virtuais) e compare a contagem com a informada na análise.

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência — *Como verificar:* passe o checklist de validação do próprio `report-template.md` item a item.
- [ ] Cada finding tem arquivo e linhas exatos — *Como verificar:* releia cada `arquivo:linha` citado e confirme que a evidência está de fato ali.
- [ ] Findings ordenados por severidade (CRITICAL → LOW) — *Como verificar:* a tabela e a seção Findings seguem a mesma ordem, e a contagem do Summary bate com o total.
- [ ] Mínimo de 5 findings identificados — *Como verificar:* conte os findings. Com menos de 5, o item fica pendente e o relatório diz isso, sem inflar a lista.
- [ ] Detecção de APIs deprecated incluída (se aplicável) — *Como verificar:* o AP-12 foi avaliado; há findings de deprecated, ou itens em `Not Verified`, ou a constatação de que não há nenhuma (`n/a` justificado).
- [ ] Skill pausa e pede confirmação antes da Fase 3 — *Como verificar:* a pergunta da Fase 2 foi feita e a resposta do usuário foi recebida. Esse item só é marcado depois da resposta.

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC — *Como verificar:* a árvore real tem as camadas de `mvc-architecture.md` (config, models, views/routes, controllers, middlewares) e os arquivos estão nelas.
- [ ] Configuração extraída para módulo de config (sem hardcoded) — *Como verificar:* as buscas do AP-02 e AP-13 do catálogo não encontram segredos, portas ou caminhos fora do módulo de config.
- [ ] Models criados para abstrair dados — *Como verificar:* o acesso a dados (SQL/ORM) está só nos models; as buscas do AP-01, AP-05 e AP-07 não encontram acesso a dados em controllers ou rotas.
- [ ] Views/Routes separadas para visualização ou roteamento — *Como verificar:* o registro de rotas está em módulo próprio, separado da lógica dos controllers.
- [ ] Controllers concentram o fluxo da aplicação — *Como verificar:* os controllers recebem a requisição, validam a entrada, chamam os models e devolvem a resposta, sem SQL nem regra de negócio pesada.
- [ ] Error handling centralizado — *Como verificar:* existe um único tratador global registrado e os controllers não têm `catch` genérico devolvendo detalhe interno (busca do AP-10 vazia).
- [ ] Entry point claro — *Como verificar:* há um único ponto de entrada (composition root) que só monta e inicia a aplicação.
- [ ] Aplicação inicia sem erros — *Como verificar:* boot limpo do Passo 3.1 do `validation-guide.md`, com o log sem exceções.
- [ ] Endpoints originais respondem corretamente — *Como verificar:* `scripts/compare.py` entre baseline e after, com todos os endpoints do baseline em `OK` ou `CHANGED` (mudança intencional aprovada) e nenhum `FAIL`.

O checklist da Fase 3 preenchido é gravado no relatório logo após o bloco da Fase 3, para o usuário conferir depois.
