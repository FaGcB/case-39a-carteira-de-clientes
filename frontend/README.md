# Carteira: frontend

React 18 + TypeScript (strict) + Vite 8, React Router 7 e TanStack Query 5. Testes com Vitest 5.

## Rodar

Pré-requisito: Node 20+ (testado com Node 22).

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # testes (Vitest)
npm run lint       # ESLint
npm run build      # checagem de tipos + build de produção
```

O front não tem regra de negócio nem dados próprios: tudo vem da API. Em
desenvolvimento, o Vite encaminha `/api` para `http://localhost:8000` (o backend
rodando com `uvicorn`). Para outro endereço, use `VITE_PROXY_API=http://host:porta npm run dev`.
No Docker, o nginx da imagem faz o mesmo encaminhamento. Como rodar tudo junto está
no [README da raiz](../README.md).

## Telas e URLs

| URL | Tela |
|---|---|
| `/` | Painel com totais e última importação |
| `/importacoes` | Envio de arquivo e histórico (`?pagina=`) |
| `/importacoes/:id` | Progresso ao vivo e abas de linhas aceitas e rejeitadas (`?aba=aceitas\|rejeitadas&resultado=&pagina=`) |
| `/clientes` | Busca, paginação e ordenação (`?nome=&documento=&ordem=nome\|importacao&direcao=asc\|desc&pagina=`) |
| `/clientes/:id` | Ficha com vínculos e proposta |
| `/clientes/:id/editar` | Edição de cliente |
| `/empresas` | Lista de empresas |
| `/empresas/:id` | Ficha da empresa com os clientes vinculados (`?nome=&pagina=`) |
| `/empresas/:id/editar` | Edição de empresa |

Todo filtro, página e ordenação vive na URL: mandar o link é mandar o resultado.

## Organização

```
src/api/types.ts      contrato da API (formatos de resposta)
src/api/http.ts       único ponto que chama fetch; converte falhas em ApiError
src/api/endpoints.ts  uma função por endpoint
src/api/queries.ts    hooks do TanStack Query (cache, polling, invalidação)
src/lib/              formatação pt-BR, cálculo da parcela, hooks de URL
src/components/       layout, estados (carregando/vazio/erro), formulários
src/pages/            uma tela por rota
```

## Contrato com o backend

Erros sempre como `{ "mensagem": string, "erros"?: { "<campo>": string } }`.
Campos aninhados usam ponto (`endereco.cep`) e caem no campo certo do formulário.

| Método | Rota | Resposta |
|---|---|---|
| GET | `/api/resumo` | `Resumo` |
| POST | `/api/importacoes` (multipart, campo `arquivo`) | `202` + `Importacao` |
| GET | `/api/importacoes?pagina&tamanho` | `Paginado<Importacao>` |
| GET | `/api/importacoes/:id` | `Importacao` |
| GET | `/api/importacoes/:id/linhas-invalidas?pagina&tamanho` | `Paginado<LinhaInvalida>` |
| GET | `/api/clientes?nome&documento&ordem&direcao&pagina&tamanho` | `Paginado<ClienteResumo>` |
| GET / PUT / DELETE | `/api/clientes/:id` | `Cliente` / `Cliente` / `204` |
| GET | `/api/empresas?busca&pagina&tamanho` | `Paginado<Empresa>` |
| GET / PUT | `/api/empresas/:id` | `Empresa` |
| GET | `/api/motor/proposta?cpf=` | `Proposta`, ou `429` com `Retry-After` |

Os tipos estão em `src/api/types.ts`.

## Decisões

- **TanStack Query para estado de servidor.** Cache, cancelamento, `keepPreviousData`
  na paginação e polling condicional saem prontos. Estado local fica só no que é de
  tela (texto digitado antes do debounce, diálogo aberto).
- **Progresso por polling de 1s**, só enquanto o status é `PENDENTE`/`PROCESSANDO`.
  É simples, funciona atrás de qualquer proxy e basta para o volume do caso.
  Com mais tempo: Server-Sent Events.
- **Visual** com a identidade 39A sobre a referência NU.FINANCE (Dribbble): menu lateral preto, amarelo como ação principal, laranja-avermelhado para rejeições e alertas.
- **Proposta sem retry automático.** O 429 mostra uma contagem regressiva a partir
  do `Retry-After`, e o botão só libera quando ela termina. A proposta fica 10 min
  em cache na sessão, porque reabrir a mesma ficha não deve gastar a cota.
- **Proposta em paralelo.** Vindo da listagem, o CPF segue no state da navegação e
  a consulta ao motor começa junto com a da ficha. Em link direto ou F5, começa assim
  que a ficha devolve o CPF. Nos dois casos a ficha nunca espera a proposta.
- **Parcela comparada com a maior margem individual**, não com a soma: o desconto
  acontece numa folha só. A listagem mostra a soma, indicada no título da coluna.
- **Erros da API**: 4xx não são reenviados; rede/5xx tentam mais uma vez. Erros com
  campo aparecem sob o campo; os demais, numa faixa no topo do formulário.
