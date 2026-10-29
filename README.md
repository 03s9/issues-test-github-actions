# 🚀 Roadmap de Evolução da Esteira CI/CD & Governança

Recomendações técnicas estruturadas pelo Codex para aprimoramento da automação de testes e segurança no GitHub Actions.

---

## 1. 🛡️ Secret Scanning com Bloqueio Preventivo (Gitleaks)
- **Objetivo**: Evitar que tokens, chaves de API, senhas ou arquivos `.env` sejam commitados e trafeguem para o repositório remoto.
- **Implementação**:
  - Habilitar o **Secret Scanning** e **Push Protection** nativo no GitHub.
  - Adicionar o step de `gitleaks` no início de cada workflow (`ci.yml`) para quebrar o build imediatamente se detectar credenciais.
  - Garantir que nenhum segredo detectado seja exposto no corpo das Issues.

## 2. 🔒 Branch Protection Rules (Blindagem da `main`)
- **Objetivo**: Impedir que código quebrado ou sem revisão chegue à branch principal.
- **Implementação**:
  - Exigir aprovação de Pull Request antes do merge na branch `main`.
  - Exigir que a verificação de status do GitHub Actions (`CI`) esteja 100% verde antes de liberar o botão de merge.
  - Bloquear `--force push` e deleção da branch `main`.

## 3. 🎯 Auto-Close Inteligente de Issues de Falha
- **Objetivo**: Fechar automaticamente issues abertas pelo bot de CI assim que a branch voltar ao estado verde (passando em todos os testes).
- **Implementação**:
  - Inserir marcador de rastreio invisível no corpo da issue: `<!-- ci-failure:main -->`.
  - Quando um push na branch principal passar com sucesso (`success`), um job consulta se há issues abertas com o marcador e as encerra com comentário: *"Resolvido com sucesso pelo commit [SHA]"*.

---

## Configuração Detalhada das Actions

### Gitleaks

Adicionar o workflow abaixo em `.github/workflows/gitleaks.yml`. O `fetch-depth: 0` garante que o Gitleaks tenha acesso ao histórico completo; o job falha quando uma credencial é detectada.

```yaml
name: Gitleaks

on:
  pull_request:
  push:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  scan:
    name: Scan for secrets
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Obrigatório apenas para repositórios pertencentes a organizações.
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

### Auto-close de Issues de Falha

Adicionar o workflow abaixo em `.github/workflows/auto-close-ci-issues.yml`. Ele é acionado somente quando o workflow `CI` termina com sucesso na `main`, localiza issues abertas com o marcador definido acima, publica o SHA responsável pela correção e fecha cada issue.

```yaml
name: Auto-close CI issues

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

permissions:
  issues: write

jobs:
  close-issues:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - name: Close resolved CI issues
        uses: actions/github-script@v9
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const marker = '<!-- ci-failure:main -->';
            const { owner, repo } = context.repo;
            const sha = context.payload.workflow_run.head_sha;

            const { data: issues } = await github.rest.issues.listForRepo({
              owner,
              repo,
              state: 'open',
              per_page: 100
            });

            for (const issue of issues) {
              if (issue.pull_request || !issue.body?.includes(marker)) continue;

              await github.rest.issues.createComment({
                owner,
                repo,
                issue_number: issue.number,
                body: `Resolvido com sucesso pelo commit ${sha}.`
              });

              await github.rest.issues.update({
                owner,
                repo,
                issue_number: issue.number,
                state: 'closed'
              });
            }
```

O nome informado em `workflows: ["CI"]` deve corresponder exatamente ao campo `name` do workflow principal de testes.
