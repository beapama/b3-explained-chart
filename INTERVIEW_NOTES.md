# Interview notes — B3 Moves, Explained

Material de preparação. Cada decisão: **o que** foi feito, **por quê** e o
**trade-off**. Números na seção "Números".

## Arquitetura em 5 linhas
1. **Preços**: `yfinance` baixa o histórico diário ajustado de 5 ações + Ibovespa → `data/prices/*.json`.
2. **Detecção**: z-score do retorno diário contra os 60 pregões anteriores; |z| ≥ 2,5 vira evento, comparado com o Ibovespa (mercado vs ação).
3. **Contexto + IA**: para cada evento NOVO, até 10 manchetes do Google News → Claude Haiku 5.5 devolve JSON validado (motivo, explicação, tipo, confiança, fontes por número) → `data/events/*.json` (cache).
4. **Eval**: checagens automáticas em todos os eventos + amostra rotulada de 15 → `data/eval/summary.json`.
5. **Entrega**: GitHub Actions roda tudo às 19:00 (Brasília) em dias úteis, faz commit dos dados e publica o site estático no GitHub Pages.

---

## 1. Setup e dados
- **Um único `src/config.py`** (tickers, caminhos, parâmetros). *Por quê:* todas as etapas leem a mesma fonte de verdade; mudar o limiar ou o modelo é uma linha.
- **Dados versionados no Git (`data/`), sem banco.** *Por quê:* o site estático lê os JSONs direto; o histórico do Git vira registro de auditoria do que a IA disse e quando. *Trade-off:* não escala para milhares de tickers; aí seria banco/object storage.
- **Chave só em `.env` (local) e GitHub Secrets (CI).** `load_dotenv(override=True)`: o `.env` local vence variáveis antigas do terminal; no CI não há `.env`.
- **Preço ajustado (`auto_adjust=True`).** *Por quê:* sem ajuste, a data ex-dividendo parece uma queda forte e vira evento falso.
- **Baixar o histórico inteiro a cada execução** (não incremental). *Por quê:* 6 requisições grátis e pega ajustes retroativos. *Trade-off:* um pouco mais de banda, muito menos código.
- **Guarda de qualidade:** o Yahoo devolveu o último dia com preço `NaN` perto da meia-noite. Linhas com `NaN` são descartadas (com aviso) e `json.dumps(allow_nan=False)` faz o script falhar se algo escapar, porque `NaN` não é JSON válido e quebraria o site.
- **Risco conhecido:** `yfinance` não é API oficial; pode quebrar ou ser bloqueado. Em produção: fornecedor de dados pago.

## 2. Detecção de movimentos fortes
- **Z-score rolante em vez de corte fixo em %.** *Por quê:* cada ação é julgada pela própria volatilidade. MGLU3 precisa de ~8% para ser "forte", ITUB4 de ~3,5%. Um corte fixo de 5% encheria a MGLU3 de eventos e ignoraria os bancos.
- **Média e desvio só com dias anteriores (`shift(1)`).** *Por quê:* se o próprio dia entrasse, a queda inflaria o desvio e esconderia a si mesma (e seria look-ahead).
- **Janela de 60 dias, limiar 2,5.** Testei 20/60 dias × 2,0/2,5/3,0. 20 dias = desvio instável; 2,0 ≈ 95 eventos (caro de explicar e rotular); 3,0 ≈ 15. 60/2,5 → 53 eventos, ~1 por ação por mês.
- **Aquecimento:** 100 dias extras de histórico para a janela estar cheia no primeiro dia dos 12 meses.
- **Mercado vs ação:** "market" se o Ibovespa teve |z| ≥ 2 na mesma direção; também guardo o retorno em excesso (ação − Ibov). *Trade-off:* mais simples que retorno anormal ajustado por beta (CAPM), que é próximo passo.
- **Ressalva estatística:** retornos têm caudas grossas, então z = 2,5 não é "1% de chance"; é um ranking de dias incomuns.
- **Checagem que valeu a pena:** MGLU3 −58% em 26/10 parecia erro de dado; as notícias confirmaram que foi real (maior queda diária desde 1994, após a eleição).

## 3. Notícias (a parte de busca do "RAG")
- **Google News RSS.** *Por quê:* grátis, sem chave, aceita filtro de data, cobre Valor/InfoMoney/Estadão. *Trade-off:* não oficial, só manchetes (sem corpo), links de redirecionamento do Google, resultados variam a cada chamada.
- **Janela = pregão anterior → dia seguinte.** *Por quê:* a queda de segunda (26/10) veio da eleição de domingo; o dia seguinte traz as matérias "por que caiu".
- **Busca da empresa = nome + termos de mercado** (`"Petrobras" (ações OR PETR4 OR Ibovespa OR bolsa)`). Só o nome trazia concurso e patrocínio.
- **Busca de mercado com palavras de direção** nos eventos "market": `(Ibovespa OR bolsa) (cai OR queda OR despenca OR sobe OR dispara OR alta)`.
- **10 manchetes, 5 da empresa + 5 do mercado** (eventos de mercado), deduplicadas pelo título normalizado.
- **Análise de falha (história principal da entrevista):** depois do backfill, 13/53 eventos ficaram "sem explicação". Olhando o que o modelo recebeu: nos dias de queda geral, as notícias da empresa ocupavam todas as vagas e as do Ibovespa (onde estava a causa) eram cortadas. O ITUB4 no dia da eleição (−13,7%) recebeu 5 manchetes sobre uma aquisição. **O problema era a busca, não o modelo** — ele acertou ao não inventar causa. Três iterações medidas: 13 → 12 (cota de vagas) → 9 (busca com palavras de direção). Nos eventos de mercado: 5/22 → 1/22 sem explicação.
- **Não determinismo:** o Google muda os resultados a cada busca e o modelo pode rotular um dia ambíguo de forma diferente. Por isso guardo junto de cada evento as manchetes que o modelo viu, e o eval roda sobre elas.

## 4. Explicação com IA
- **Modelo Claude Haiku 5.5** (US$ 0,10 / 0,50 por milhão de tokens). *Por quê:* a tarefa é leitura curta de ~10 manchetes, não raciocínio profundo. Trocar de modelo é uma constante no config.
- **Saída estruturada com Pydantic (`messages.parse`).** *Por quê:* a API é restrita ao esquema (enums para tipo e confiança) e o SDK valida de novo do nosso lado. Nada de regex em texto livre.
- **O modelo cita o NÚMERO da fonte, não a URL.** *Por quê:* o código troca número por link, então link inventado é impossível por construção; número fora da lista é descartado e registrado. Também economiza tokens (URLs do Google têm ~200 caracteres).
- **"Sem explicação clara" é resposta válida** (+ `type: "unknown"`). *Por quê:* o modelo não é empurrado a inventar causa. Acrescentei `unknown` às três categorias da especificação.
- **"Use apenas as manchetes".** *Por quê:* toda explicação pode ser auditada contra as fontes mostradas no site.
- **Contexto do detector no prompt** (retorno, z, Ibovespa, escopo): ajuda a separar macro de empresa.
- **Toda chamada registra tokens, custo e latência** → custos reais, não estimativas.

## 5. Cache, pipeline e backfill
- **Cache por (ticker, data).** *Por quê:* evento explicado nunca volta para a API; o custo diário é proporcional a eventos novos (0 a 2), não ao histórico.
- **Salva após cada evento.** *Por quê:* se cair no meio, a próxima execução continua de onde parou; evento com erro é tentado de novo depois.
- **`--dry-run`** mostra quantos eventos e o custo estimado antes de gastar.
- **Log por execução** (`data/eval/runs.jsonl`): eventos novos, falhas, custo, duração.
- **Trade-off do cache:** se o prompt mudar, eventos antigos ficam com a explicação antiga. Solução: apagar e reprocessar (~US$ 0,03) ou pôr a versão do prompt na chave.

## 6. Avaliação
- **Duas camadas.** (1) Automática, em todos os 53 eventos, grátis: toda fonte citada estava na lista enviada; abstenções sem fontes e com tipo `unknown`; respostas reais citam ≥ 1 fonte; concordância detector × IA nos dias de mercado. (2) Amostra rotulada de 15.
- **Amostra estratificada e fixa** (semente 42: 4 macro, 4 empresa, 3 setor, 4 sem explicação). *Por quê:* uma amostra aleatória seria quase toda macro e não testaria se as abstenções estavam certas.
- **100% de fontes válidas é esperado** (citação por número), então é teste de regressão, não descoberta. A pergunta real ("a causa está certa?") precisa de julgamento.
- **Quem rotulou: um modelo maior (Claude Opus 5.5) como juiz, não à mão.** *Trade-off:* rápido, mas o juiz pode ter os mesmos pontos cegos. Mitigações: modelo diferente e maior; justificativa escrita por linha; o site informa quem rotulou. **Nunca dizer "rotulei à mão"** — dizer "LLM como juiz, revisado por mim".
- **Padrão de erro principal:** em dias só da ação e com manchetes fracas, o modelo arrisca um motivo fraco com confiança baixa em vez de se abster (VALE3: "novo vento favorável"). Todas as abstenções estavam certas. Próximo passo: "se a confiança seria baixa, abstenha-se" e medir de novo nos mesmos 15.
- **Calibração útil:** com confiança alta, acertou 93% das vezes; por isso o site mostra a confiança.

## 7. Site
- **Estático, sem framework nem build:** um HTML, um CSS, um JS lendo JSON. GitHub Pages hospeda de graça; nada para manter rodando.
- **`src/build_site.py` monta `_site/`** com a página e só os dados que o navegador precisa — mesmo comando local e no CI, então o que eu testo é o que vai ao ar.
- **lightweight-charts fixado em 5.0.9.** *Por quê:* uma versão nova poderia mudar a API e quebrar o site sem aviso.
- **Estilo de editoria de gráficos de jornal financeiro:** o título é a conclusão calculada dos dados ("PETR4 teve 12 dias de movimento forte em 12 meses; 6 vieram de notícias do setor"), linha de números-chave, gráfico grande com o evento anotado por uma linha guia e a explicação ao lado.
- **Paleta de cereja na identidade, cores distintas nos dados.** Os três tons da paleta são o mesmo vermelho e não distinguiriam tipos de evento (principalmente para daltônicos). Então vinho/framboesa/rosé vão no visual, e os marcadores usam framboesa + verde + ameixa, validados com um script que simula daltonismo nos temas claro e escuro. O tema escuro tem cores escolhidas para ele, não invertidas.
- **Linha de preço neutra:** cor significa só "tipo de evento". O tipo também está na letra (M/S/E/?) e a direção na ponta do marcador, então nada depende só da cor.
- **Marcadores próprios em HTML** em vez dos da biblioteca (letras minúsculas e ilegíveis): disco de 22px, área de toque de 40px, foco por teclado. *Trade-off:* eu reposiciono no zoom/rolagem.
- **Tabela de eventos** = versão acessível dos marcadores e o jeito fácil de escolher no celular.
- **Texto de notícia é entrada não confiável:** vai para a página com `textContent`, links só `http(s)` → sem XSS por manchete maliciosa.
- **A avaliação está na própria página**, inclusive quem rotulou: o visitante vê os limites, não só as promessas.
- **Conferido renderizando** (prints em computador/celular, claro/escuro): achou estouro de largura no celular (item de grid não encolhe sem `min-width: 0`) e um rótulo de eixo errado.

## 8. Automação (GitHub Actions)
- **Um workflow, dois jobs:** `update` (agendado ou manual: pipeline → eval → commit de `data/` se mudou) e `deploy` (monta `_site/` → GitHub Pages). Push que só mexe no site pula o `update`: republica sem chamar a API.
- **Horário `0 22 * * 1-5` = 19:00 em Brasília** (UTC-3, sem horário de verão desde 2019), ~1h após o fechamento da B3, quando o Yahoo já tem o dia completo. O cron do GitHub é em UTC e pode atrasar alguns minutos — irrelevante para um job diário.
- **Feriados sem calendário:** sem pregão novo, não há evento novo nem custo.
- **Idempotente:** rodar de novo (botão manual, retry) nunca explica o mesmo evento duas vezes, graças ao cache.
- **`concurrency`:** duas execuções nunca gravam `data/` ao mesmo tempo.
- **Permissões mínimas** (`contents: write`, `pages: write`, `id-token: write`); chave nos Secrets.
- **Modo de falha:** se Yahoo ou API falham, o job falha, nada é gravado, o deploy não acontece e o site fica com os últimos dados bons.
- **Sem loop:** commits feitos pelo bot com `GITHUB_TOKEN` não disparam workflows.

## 9. Versão em inglês (para recrutadores)
- **Um site com troca de idioma, não duas cópias.** *Por quê:* duas cópias obrigariam a corrigir tudo duas vezes. Todo texto da tela vem de um dicionário por idioma no `app.js`; o HTML não tem texto que a troca não alcance.
- **Formato por idioma:** "R$ 43,17 · 4 nov 2026" em português, "R$ 43.17 · Nov 4, 2026" em inglês. A moeda continua real.
- **Ordem de escolha do idioma:** `?lang=en` no link > última escolha (localStorage) > idioma do navegador > português. Escolhido no `<head>`, antes de desenhar a página, para não piscar o idioma errado. O link do README/currículo cai direto no inglês.
- **Textos da IA:** eventos novos recebem inglês **na mesma chamada** (o esquema ganhou `short_reason_en` e `explanation_en`, sem custo extra). Os 53 já explicados foram **traduzidos, não reexplicados**: a explicação em português, as fontes e o eval continuam exatamente os mesmos. Custou US$ 0,0065.
- **Fallback:** se faltar o inglês num evento, o site mostra o português; nada quebra.
- **Manchetes ficam em português** (são as fontes originais), com a nota "in Portuguese".
- **`summary.json` neutro em idioma:** quem rotulou virou dado (`model`, `method`, `human_reviewed`) e o site escreve a frase em cada língua.
- **Custo honesto:** o custo de tradução entra no total, mas não no custo por explicação.

## 10. Qualidade de código
- **Sem comentários; docstrings no lugar.** *Por quê:* comentário envelhece e mente; nome claro + docstring descreve o contrato (o que a função faz e por quê) e aparece no `help()`/editor. Python em estilo Google, JS com JSDoc, workflow com `name:` em cada passo.
- **Ruff** (`pyproject.toml`): lint + pydocstyle obriga docstring em toda função pública; `ruff format` padroniza o estilo.
- **Constantes nomeadas** em vez de números mágicos (`PIN_OFFSET_PX`, `FOCUS_WINDOW_DAYS`, `TickMarkType.Year`), funções pequenas de render.
- **Como provei que a refatoração não quebrou nada:** renderizei o site antigo e o novo no Edge headless e comparei o texto da página: zero diferenças, em PT e EN.
- **O "porquê" de decisões de infra** (horário do cron, versão fixada da biblioteca) saiu dos comentários e ficou aqui e no README.

## Incidentes (e o que aprendi)
- **Chave de API no `.env.example`, commitada localmente.** Pego revisando o diff antes do push; commit reescrito, objetos apagados, histórico verificado (0 ocorrências). Lição: revisar o diff antes de todo commit.
- **`.gitignore` padrão de Python ignorava `/site`** (pasta do mkdocs): a página não estava sendo versionada. Pego conferindo `git status` depois do commit.
- **Variável vazia injetada pelo VS Code no terminal** escondia a chave do `.env` → `override=True`.
- **Página travada em "Carregando…" logo após um deploy:** o GitHub Pages deixa o navegador guardar arquivos por 10 min; o navegador juntou o HTML novo com o JS antigo. Correção: *cache busting* no `build_site` (`app.js?v=<hash do conteúdo>`), então arquivo novo = endereço novo.
- **Marcadores deslocados no celular:** eu lia as coordenadas do gráfico antes de ele terminar de se redimensionar. Correção: reposicionar depois que o gráfico redesenha (dois `requestAnimationFrame` + evento de mudança de tamanho). Pego pelo print do site publicado.

---

## Números
- **Eventos:** 53 em 12 meses (PETR4 12, VALE3 11, ITUB4 10, MGLU3 13, WEGE3 7).
- **Tipos:** 22 macro, 14 empresa, 8 setor, 9 sem explicação; confiança 25 alta / 15 média / 13 baixa.
- **Busca, "sem explicação" de 53:** v1 13 → v2 12 → v3 9. Eventos de mercado: 5/22 → 1/22.
- **Eval automático:** 133 fontes citadas, 100% válidas, 0 números inválidos, 0 respostas incoerentes; 86,4% dos eventos "market" rotulados macro pela IA.
- **Eval rotulado** (15 eventos, LLM como juiz, revisão humana pendente): acurácia 76,7% (parcial = meio ponto), estrita 66,7%, tipo correto 86,7%. Por confiança: alta 92,9% (n=7), média 50% (n=2), baixa 66,7% (n=6). Abstenções: 5/5 corretas.
- **Tradução única dos 53 eventos para inglês:** US$ 0,0065, 79 s, 0 falhas.
- **Custo:** US$ 0,00036 por explicação (~1,5–2k tokens de entrada, 1,7–4,8 s). Backfill: 53 eventos, US$ 0,018, 264 s. Gasto total do projeto: US$ 0,035. Diário: 0–2 eventos → bem menos de US$ 0,03/mês.

## Limitações
- A IA lê só manchetes, não o texto das matérias; Google News não é oficial e varia a cada busca.
- 9/53 eventos sem explicação, quase todos dias só da ação com poucas manchetes. Respostas de confiança baixa costumam ser palpites fracos.
- Amostra do eval pequena (15) e julgada por LLM: números indicativos.
- Mercado vs ação usa z-score simples do Ibovespa, não beta.
- `yfinance` pode quebrar ou ser bloqueado nos servidores do GitHub.

## Próximos passos
- Regra "confiança baixa → abster-se" e medir de novo nos mesmos 15 eventos.
- Fatos relevantes da CVM como fonte (causas de empresa que não viram manchete).
- Suíte de testes (pytest), comparação A/B de prompts, mais tickers, alertas no Telegram.
- Retorno anormal ajustado por beta; API de notícias com texto completo.

## Perguntas prováveis (resposta curta)
- **"Como você sabe que a IA não inventa fontes?"** Ela cita números, o código converte em links; conferi 133 citações, 100% válidas.
- **"E se a IA inventar a causa?"** O prompt permite "sem explicação clara", só pode usar as manchetes, e o eval mede isso; o erro mais comum é um palpite com confiança baixa, que o site mostra como confiança baixa.
- **"Por que Haiku e não um modelo maior?"** Tarefa simples, custo de US$ 0,0004 por evento; a qualidade foi medida (93% com confiança alta). Se o eval piorar, troco uma constante.
- **"O que você faria com mais tempo?"** Regra de abstenção, fatos relevantes da CVM, testes automatizados, beta.
- **"Qual foi o problema mais difícil?"** A busca de notícias nos dias de mercado: diagnostiquei olhando o que o modelo recebeu e melhorei em três iterações medidas (13 → 9 sem explicação).
- **"Quanto custa?"** Centavos por mês; o backfill inteiro custou US$ 0,018.
