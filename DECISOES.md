# Decisões técnicas

Cada decisão traz o que foi feito, por quê, o que custa e o que eu faria com mais tempo.

---

## 1. Como a importação roda de forma assíncrona

**Decisão:** a fila é a própria tabela `importacoes` no PostgreSQL, consumida por um processo `worker` separado da API.

O `POST /api/importacoes` só valida a extensão e o tamanho, grava o arquivo (`bytea`) com status `PENDENTE` e responde `202` com o id. Com o arquivo de 9,5 MB e 30 mil linhas, a resposta levou cerca de 0,5 s. O worker reivindica o trabalho com:

```sql
UPDATE importacoes SET status = 'PROCESSANDO', worker_id = :eu, heartbeat_em = now() ...
WHERE id = (SELECT id FROM importacoes WHERE status = 'PENDENTE' OR (status = 'PROCESSANDO' AND heartbeat_em < now() - lease)
            ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED)
```

O `SKIP LOCKED` permite rodar vários workers sem que dois peguem a mesma importação. O front acompanha o progresso por polling de 1 s, só enquanto o status é `PENDENTE` ou `PROCESSANDO`.

**Por quê:** o case já exige PostgreSQL. Uma fila no banco dá transação única entre "dados gravados" e "progresso registrado", que é o que garante a retomada (decisão 3). Com Celery e Redis, eu teria duas fontes de verdade para sincronizar e mais um serviço para subir.

**Custo:** o worker consulta a tabela a cada 1 s quando está ocioso. É barato, porque o índice parcial `ix_importacoes_fila` só contém importações não terminadas, mas não é instantâneo. O arquivo também fica no banco, o que é aceitável para planilhas de alguns MB, mas não para centenas.

**Com mais tempo:** `LISTEN/NOTIFY` para acordar o worker na hora, arquivo em object storage (S3) com só a referência no banco, e Server-Sent Events no lugar do polling do front.

---

## 2. Como reimportar o mesmo arquivo não duplica dados

**Decisão:** cada entidade tem uma chave natural com `UNIQUE` no banco, e toda gravação é upsert (`INSERT ... ON CONFLICT`):

| Entidade | Identidade | Constraint |
|---|---|---|
| Cliente | CPF | `uq_clientes_cpf` |
| Empresa | CNPJ | `uq_empresas_cnpj` |
| Vínculo | cliente + empresa + matrícula | `uq_vinculos_cliente_empresa_matricula` |
| Linha rejeitada | importação + número da linha | `uq_linha_invalida` |

Subir o mesmo arquivo de novo cria uma **nova importação**, para manter o histórico de quem mandou o quê e quando, mas não cria nenhum cliente, empresa ou vínculo a mais. O teste `test_reimportar_o_mesmo_arquivo_nao_duplica` cobre isso. Com o arquivo de 30 mil linhas importado duas vezes, o banco terminou com os mesmos 28.800 clientes e 28.800 vínculos.

**Por quê:** a garantia fica no banco, não no código. Mesmo dois workers processando arquivos com o mesmo CPF ao mesmo tempo não conseguem criar duplicata. No pior caso, um deles falha a constraint, o lote volta e é refeito.

**Custo:** se o parceiro mudar a matrícula de um funcionário, o sistema entende como um vínculo novo e o antigo continua lá. Também guardo o SHA-256 do arquivo, mas não bloqueio reenvio: reprocessar é inofensivo e às vezes é o que se quer, depois de corrigir uma regra.

**Com mais tempo:** avisar na tela "este arquivo já foi importado em dd/mm" usando o hash, e marcar como encerrado o vínculo que deixou de aparecer nas planilhas daquele parceiro.

---

## 3. Como uma importação interrompida termina (ou é retomada)

**Decisão:** o arquivo é processado em lotes de 200 linhas. **Cada lote é uma transação** que grava, junto, os clientes, empresas e vínculos, as linhas rejeitadas, os contadores (`processadas`, `importadas`, `invalidas`) e o checkpoint `proxima_linha`, além de renovar o `heartbeat_em`.

Se o processo morrer no meio de um lote, a transação inteira é desfeita, e o banco fica exatamente como estava no fim do lote anterior. Quando o heartbeat passa de 60 s sem ser renovado, outro worker reivindica a importação e continua de `proxima_linha`. Como as gravações são upserts (decisão 2), refazer um lote nunca duplica nada.

Proteções extras:
- antes de cada lote, o worker trava a linha da importação e confere se ela ainda é dele. Um worker "zumbi" que volta depois de perder a vez para sozinho (`ImportacaoPerdida`);
- depois de 5 tentativas, a importação vai para `FALHOU` com mensagem, em vez de ficar presa em `PROCESSANDO`;
- idade e datas futuras são avaliadas na **data do envio**, não na data em que o lote roda. Retomar no dia seguinte não muda o resultado.

**Testado de verdade:** subi um arquivo de 30 mil linhas, matei o worker com `kill -9` no meio, e o segundo worker registrou `importação 3 retomada a partir da linha 200 de 30000`. No fim, os contadores bateram com o número de registros. Há também um teste automatizado da mesma situação (`test_queda_no_meio_retoma_sem_duplicar`).

**Custo:** até 60 s de espera para a retomada começar, que é o lease. Um lease menor retoma mais rápido, mas arrisca dois workers disputarem uma importação legítima e lenta.

**Com mais tempo:** heartbeat numa thread separada, para permitir lotes longos com lease curto.

---

## 4. Como resolvi os conflitos da seção 3.3

| Situação | Decisão | Motivo |
|---|---|---|
| Mesmo CNPJ com razão social ou nome fantasia diferentes | Fica a **primeira grafia** recebida. A correção é feita na tela de empresas e vale para todas as fichas. | Não há como saber automaticamente qual grafia está certa. Trocar a cada importação faria o nome da empresa mudar sozinho na tela. |
| Mesmo CPF com nomes diferentes (`Jose Carlos Ferreira` x `J. C. Ferreira`) | Se a **data de nascimento é a mesma**, é a mesma pessoa, e fica o **nome mais completo**: uma grafia sem abreviação vence uma abreviada; em empate, mantém a atual. | O nome mais completo é o mais útil para o comercial. A data de nascimento é o desempate objetivo. |
| Mesmo CPF com **data de nascimento diferente** | A linha é **rejeitada** com o motivo "CPF já cadastrado para outra pessoa…". | Provavelmente é um CPF digitado errado. Aceitar colocaria o vínculo de uma pessoa na ficha de outra, e no consignado isso vira proposta de crédito para a pessoa errada. |
| Linhas exatamente duplicadas no arquivo | Contam como importadas e não geram registro novo (upsert). | São idempotentes. Rejeitar assustaria o usuário sem motivo. |

Regras que tomei além das pedidas:
- **Edição manual vence a planilha.** Depois que alguém edita o cadastro de um cliente na tela, as importações seguintes só atualizam os vínculos dele, não o cadastro.
- **Cliente excluído não volta pela importação.** A linha é rejeitada com o motivo e a data da exclusão. Reativar sozinho desfaria a decisão do comercial.
- **Campo vazio na planilha não apaga dado existente.** Um telefone em branco na carga nova não remove o telefone que já estava salvo.

**Com mais tempo:** em vez de rejeitar o conflito de CPF, mandar a linha para uma fila de **revisão humana** com os dois cadastros lado a lado (é o diferencial 5 do case).

---

## 5. Regras de validação além das listadas

A seção 3.3 avisa que "o arquivo tem mais coisa". Estas também rejeitam a linha:

- **E-mail em formato inválido** (`sueli.marconi@`, `j..ferreira104@…`). Importar um e-mail quebrado ou descartá-lo sem avisar são piores que pedir a correção ao parceiro.
- **Admissão antes dos 14 anos de idade**, a idade mínima de trabalho no Brasil, como aprendiz. No arquivo de exemplo, as linhas 30, 59, 86 e 98 têm admissão aos 13 anos.
- **Data de nascimento ou de admissão no futuro.**

E estas **não** rejeitam: telefone fora do padrão vira vazio, sexo diferente de F/M vira vazio, CEP inválido vira vazio. São dados de contato secundários que não justificam perder o cliente.

**Resultado com o arquivo de exemplo** (`.xlsx` e `.csv` dão o mesmo resultado): 116 linhas, **98 importadas e 18 rejeitadas**. São 97 clientes, porque a linha 103 é duplicata exata da 12. As 18 rejeitadas são:
- as 11 regras da seção 3.3 (linhas 106 a 117, exceto 112);
- e-mail inválido (105, 112);
- admissão antes dos 14 anos (30, 59, 86, 98; a 111 e a 115 também têm esse motivo, junto com outro);
- CPF com outra data de nascimento (102).

---

## 6. Persistir ou cachear a proposta do motor?

**Decisão:** **não persisto** a proposta no banco. O **front** a mantém em cache por 10 minutos na sessão (React Query, `staleTime`), e o backend não guarda nada.

**Por que não persistir:** a proposta é determinística *neste simulador*, mas um motor real não é. Taxa, margem e política de crédito mudam, e uma proposta gravada vira uma oferta vencida exibida como atual. Gravar também aumenta a quantidade de dado financeiro pessoal guardado (LGPD) sem necessidade de negócio.

**Por que cachear no front:** reabrir a mesma ficha, ou voltar da edição para ela, não deve gastar a cota de 10 consultas por minuto. Dez minutos é curto o bastante para não mostrar proposta velha.

**Custo de cada escolha:**

| | Ganha | Perde |
|---|---|---|
| Sem cache | Sempre a resposta atual do motor | Cada abertura de ficha gasta cota; o 429 aparece fácil |
| Cache no front (escolhido) | Navegação normal não gasta cota | Cada usuário e cada aba têm o próprio cache |
| Cache no backend com TTL | Cota compartilhada rende mais para a equipe | Mais um componente (Redis) e decidir quando invalidar |
| Persistir no banco | Histórico de propostas, auditoria | Oferta vencida exibida como atual; mais dado sensível guardado |

**Com mais tempo**, e com um motor real com cota compartilhada pela empresa, eu colocaria um cache de alguns minutos no backend. Se houvesse necessidade de auditoria ("o que foi oferecido a quem"), gravaria um registro separado da proposta efetivamente apresentada, e não um cache.

**Sobre o rate limit:** a janela é deslizante (cada chamada conta por exatos 60 s), fica em memória e é por IP de origem. Funciona com uma instância da API. Com várias instâncias, precisaria ficar no Redis, e o `X-Forwarded-For` só é confiável atrás do nosso próprio proxy.

---

## 7. Busca e índices

| Filtro | Como funciona | Índice |
|---|---|---|
| Nome parcial, sem acento nem caixa | Coluna `nome_busca` (sem acento, minúsculas), gravada junto com o nome. Cada palavra digitada vira um `LIKE '%termo%'`, então "jose ferreira" acha "José Carlos Ferreira". | `ix_clientes_nome_busca_trgm`: GIN trigram (`pg_trgm`), o único tipo de índice que atende `LIKE` com `%` no começo |
| CPF completo ou parcial | `cpf LIKE '346033%'` | `ix_clientes_cpf_prefixo` com `bpchar_pattern_ops`; o índice único comum não atende `LIKE` em collation diferente de C |
| CNPJ | `EXISTS` em vínculos da empresa | `uq_empresas_cnpj` e `ix_vinculos_empresa (empresa_id, cliente_id)` |
| Ordenar por nome ou por importação | `ORDER BY ..., id` (id desempata, para a paginação não repetir nem pular linha) | `ix_clientes_ordem_nome`, `ix_clientes_ordem_importacao` |

Todos os índices de clientes são **parciais** (`WHERE excluido_em IS NULL`), porque a busca nunca mostra excluídos.

A importação, com a fila e as constraints, está descrita nas decisões 1 e 2.

**Por que `nome_busca` em vez da extensão `unaccent`:** a função `unaccent()` não é `IMMUTABLE`, então não pode ser usada direto num índice. Gravar a forma normalizada na escrita é mais simples e deixa a busca previsível.

**Com mais tempo:** paginação por cursor (keyset) no lugar de `OFFSET`, que fica lento nas últimas páginas de bases grandes, e `pg_trgm` com similaridade para tolerar erro de digitação.

---

## 8. "Saber de qual importação veio cada dado" e histórico do cliente

**Decisão:** duas camadas.

1. **Por registro:** cliente, empresa e vínculo guardam `importacao_origem_id` (quem criou) e `ultima_importacao_id` (quem atualizou por último). Rejeições ficam em `linhas_invalidas`, ligadas à importação.
2. **Por campo, com valor antigo:** a tabela `alteracoes_cliente` (migration `0003`) guarda uma entrada por importação ou edição manual que **mudou algo** no cliente. Cada entrada tem a lista de mudanças: campo, valor anterior e valor novo. Campos de vínculo (cargo, admissão, salário, margem) levam o contexto "Empresa · matrícula N", e um vínculo novo aparece como "Novo vínculo". A ficha mostra isso como uma linha do tempo.

**Regras:**
- a primeira importação grava "cliente criado", sem lista de mudanças;
- reimportar sem mudança **não grava nada** (o histórico mostra o que mudou, não toda vez que a planilha passou);
- campo vazio na planilha não apaga dado, então também não vira mudança;
- depois de uma edição manual, a planilha não mexe mais no cadastro, mas mudanças de vínculo continuam aparecendo;
- o diff é calculado no mesmo lote e na mesma transação que grava os dados: se o lote for desfeito numa queda, o histórico também é;
- apagar a importação não apaga o histórico: `importacao_id` vira `NULL` e a descrição ("Importação #2 (arquivo.csv)") continua. A tela marca "importação apagada".

**Por que JSONB com a lista de mudanças, e não uma linha por campo:** a tela mostra "o que esta importação mudou" como um bloco, e uma linha por evento deixa isso numa só leitura. Um `CHECK` garante que a coluna é sempre uma lista, e outro que só "criação" pode vir sem mudanças. Para perguntar "quem mudou o telefone" em toda a base, um índice GIN em `mudancas` resolveria.

**Com mais tempo:** guardar o usuário que editou (hoje não há login) e um botão para restaurar um valor antigo.

---

## 9. Performance da importação

A primeira versão gravava linha a linha e fazia cerca de 90 linhas por segundo. O gargalo não era o banco: era o SQLAlchemy montando 4 instruções por linha. Mudei para operações em conjunto por lote:

1. uma consulta trava todos os clientes do lote (`WHERE cpf IN (...) FOR UPDATE`);
2. conflitos e regras de nome são decididos em memória, na ordem das linhas;
3. empresas, clientes novos, vínculos e linhas rejeitadas vão em inserções em massa, com uma instrução compilada uma vez e executada com todos os parâmetros do lote.

Com o arquivo de 30 mil linhas, foram **cerca de 1.100 linhas por segundo** na primeira carga e **1.900** na reimportação (medido localmente). Os mesmos 62 testes passaram antes e depois da mudança.

**Com mais tempo:** `COPY` para uma tabela temporária e `INSERT ... SELECT` com o upsert, que chega a dezenas de milhares de linhas por segundo.

---

## 10. Apagar uma importação

**Decisão:** cada importação tem um botão de apagar, no histórico e na página da importação. Ele remove **só o que existia apenas por causa daquela planilha**:

- um vínculo sai se não apareceu em nenhuma outra importação;
- um cliente sai se ficou sem nenhum vínculo;
- uma empresa sai se ficou sem nenhum vínculo;
- quem também veio de outra planilha **fica**, e a origem e a última importação dele são recalculadas a partir das importações que sobraram.

Para saber "em quais importações este vínculo apareceu", a migration `0002` criou a tabela `vinculo_importacoes`, preenchida a cada lote. Sem ela, com só origem e última importação, apagar a planilha #2 levaria junto clientes que também vieram da #1.

**Prévia antes de confirmar:** `GET /api/importacoes/{id}/exclusao` executa a mesma exclusão dentro de uma transação e desfaz no fim. A tela mostra quantos clientes, vínculos e empresas saem e quantos clientes ficam. Como é o mesmo código do `DELETE`, a prévia nunca diverge do resultado.

**Proteções:** tudo numa transação, e uma importação pendente ou em andamento não pode ser apagada (`409`).

**Custo:** quem fica, fica com os **dados atuais**. Se a #2 mudou o telefone da Maria e você apaga a #2, o telefone novo continua. A tela avisa isso na prévia. O valor antigo não se perde: está no histórico da ficha (item 8), marcado como "importação apagada".

**Com mais tempo:** usar o histórico para desfazer, ao apagar, as mudanças que a importação fez nos clientes que ficam. Não fiz porque exige decidir o que acontece quando uma importação posterior ou uma edição manual mexeu no mesmo campo depois.

---

## 11. Linhas aceitas de cada importação

**Decisão:** a tabela `linhas_importadas` (migration `0004`) guarda cada linha aceita, espelhando `linhas_invalidas`: número da linha, cliente, vínculo e o que a linha fez. Na tela da importação, "Aceitas" e "Rejeitadas" são duas abas, e os números da lista de importações abrem cada uma direto (`?aba=aceitas` ou `?aba=rejeitadas`).

**O que cada linha fez:**

| Resultado | Quando |
|---|---|
| Cliente novo | o CPF entrou na base por esta linha |
| Vínculo novo | o cliente já existia (ou entrou numa linha anterior) e esta linha trouxe outro emprego |
| Atualizou dados | mudou o cadastro do cliente ou o vínculo desta linha; o antes e depois está no histórico do cliente (item 8) |
| Sem mudança | os dados já estavam iguais na base |
| Repetida no arquivo | mesmo cliente, empresa e matrícula de uma linha anterior da mesma planilha |

**Por quê:** o número de linhas na aba é sempre igual ao contador "importadas". No arquivo de exemplo, 98 linhas aceitas viram 97 clientes, e a aba mostra por quê: a linha 103 aparece como "Repetida no arquivo". Reimportar o mesmo arquivo mostra 98 linhas "Sem mudança", o que confirma que nada foi duplicado nem alterado.

**Proteções:** a gravação acontece no mesmo lote e na mesma transação dos dados, com `UNIQUE (importacao_id, linha)` e `ON CONFLICT DO NOTHING`. Na retomada depois de uma queda, nenhuma linha aparece duas vezes (coberto em `test_queda_no_meio_retoma_sem_duplicar`).

**Custo:** cliente e empresa aparecem com os dados **atuais**, não com os da época da importação. O que mudou fica no histórico do cliente. Importações feitas antes da migration aparecem com os vínculos que trouxeram (de `vinculo_importacoes`), mas sem número de linha nem resultado, e a tela avisa.

---

## 12. Front-end

As decisões do front (React Query para estado de servidor, filtros na URL, os três estados em toda requisição, proposta em paralelo com tratamento do 429) estão em [`frontend/README.md`](frontend/README.md#decisões).
