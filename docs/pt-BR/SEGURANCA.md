# Segurança e privacidade

## O que está sendo protegido

**A superfície publicada.** O HTML, o CSS, o JavaScript e as imagens servidos pelo CDN. A ameaça aqui não é perda de dados, é uma página que executa código que não deveria, ou que serve algo que o build pretendia manter privado.

**A fronteira do repositório.** A configuração de hospedagem do site publica um diretório. Tudo que está dentro desse diretório e não está explicitamente excluído é público, o que faz da lista de ignore na publicação um controle de segurança: ferramental, documentação, fontes das functions, arquivos de ambiente, arquivos compactados e metadados do repositório não podem ser alcançáveis.

**Conteúdo comercial antes da publicação.** Preços, especificações de modelo, narrativas de case e texto jurídico são aprovados em um lugar e gerados dentro das páginas. Um gerador que lê o módulo errado, ou uma página que contorna a fonte única, publica um número não aprovado.

**A passagem de bastão do comércio.** A sessão de pagamento, a consulta de status do pedido e o webhook. O site nunca vê dados de cartão, mas lida com o identificador de uma sessão e com o endereço de e-mail associado a um pedido.

**Privacidade do visitante.** O estado de consentimento de analytics, a preferência de região e o conteúdo da sacola, que ficam no local storage e nunca saem do navegador.

## Fronteiras de confiança

1. **Da máquina de build para a saída estática.** Os geradores são confiáveis. A saída deles não é verificada por nenhuma checagem automatizada antes do deploy, então a fronteira é a revisão do diff gerado.
2. **Do navegador para a hospedagem.** O navegador não é confiável. Tudo que ele recebe é público, cacheável e inspecionável.
3. **Do navegador para as functions.** As requisições chegam de qualquer lugar. Origem, método, tipo de conteúdo, tamanho do corpo e taxa são verificados antes de qualquer trabalho acontecer.
4. **Do provedor de pagamento para as functions.** O webhook é um endpoint não autenticado até a assinatura ser verificada sobre o corpo bruto. Antes dessa checagem, a requisição é tratada como hostil.
5. **De scripts de terceiros para a página.** O tag manager é o único script de terceiros autorizado a executar, e ele é limitado pela política de segurança de conteúdo e pelo estado de consentimento.

## Ameaças consideradas

**Exposição de metadados do repositório.** A configuração de hospedagem publicava a raiz do repositório. Diretórios com ponto, ferramental, documentação e fontes das functions eram excluídos por uma lista de padrões que não cobria tudo. A lista agora é explícita e trata todo caminho não publicável como uma exclusão nomeada, e as rotas arquivadas são servidas com um header `noindex` em vez de removidas, para que URLs antigas não possam ser usadas para chegar a conteúdo aposentado no índice.

**Injeção pela marcação gerada.** O texto é escrito, não fornecido pelo usuário, então o vetor realista é um valor que chega ao HTML sem escape: um nome de produto, uma métrica de case, um parágrafo jurídico com um e comercial. Espera-se que os geradores façam escape do texto interpolado e mantenham a marcação em template literals e não em dados. Isso é convenção, não regra imposta, e é o ponto mais fraco de um pipeline baseado em strings.

**Clickjacking e framing.** Páginas e functions enviam `X-Frame-Options: DENY` e `frame-ancestors 'none'`.

**Cross-site scripting por uma dependência comprometida.** Não há árvore de pacotes para comprometer: nenhum framework, nenhuma biblioteca buscada de um registry ou de um CDN público. O único script de terceiros é o tag manager, que a política de segurança de conteúdo limita aos endpoints de analytics de que ele realmente precisa, enquanto bloqueia `object`, `base` e frames desconhecidos.

**Abuso da sessão de pagamento.** A função de sessão aceita apenas POST de uma origem na allowlist, exige JSON, rejeita corpos acima de um limite pequeno de tamanho, valida o identificador de catálogo e a quantidade e aplica rate limit por instância. Os preços são resolvidos no servidor, então um cliente adulterado não consegue mudar um valor.

**Falsificação de webhook.** A assinatura é verificada contra o corpo bruto antes de qualquer efeito colateral. Uma requisição sem assinatura não produz e-mail nem mudança de estado.

**Enumeração de status de pedido.** A função de status aceita apenas GET, valida o identificador, aplica rate limit por instância com `Retry-After` e devolve um endereço de e-mail mascarado, para que um link de confirmação compartilhado não revele o endereço completo do comprador.

**Coleta excessiva de analytics.** O consentimento vem negado por padrão, definido antes de o tag manager carregar, e é atualizado apenas por uma escolha explícita guardada no local storage. A barra de região usa session storage, então não precisa de consentimento e não deixa nada para trás depois que a aba fecha.

## Controles implementados

| Controle | Onde |
|---|---|
| Política de segurança de conteúdo com uma lista explícita de origens | Regra de header na hospedagem |
| `X-Frame-Options`, `frame-ancestors`, `Permissions-Policy`, `Referrer-Policy`, `nosniff`, HSTS | Regras de header na hospedagem |
| Política de cache que revalida HTML e assets, com URLs de asset com hash de conteúdo | Hospedagem mais uma etapa de build |
| Lista de ignore na publicação cobrindo ferramental, docs, functions, arquivos de ambiente, arquivos compactados e diretórios com ponto | Configuração de hospedagem |
| `noindex` nas rotas arquivadas | Regra de header com escopo no caminho do arquivo |
| Nenhum segredo em arquivo servido | Convenção de build; segredos vivem no ambiente das functions |
| Resolução de preço no servidor | Catálogo da função de sessão |
| Verificação de assinatura sobre o corpo bruto | Função de webhook |
| Rate limit por instância, limite de tamanho do corpo, checagem de tipo de conteúdo, allowlist de origem | Funções de sessão e de status |
| E-mail mascarado na página de status, escape de HTML antes da renderização | Função de status e página de confirmação |
| Consentimento negado por padrão, atualizado na escolha | Bootstrap inline gerado em tempo de build |
| `security.txt` com um contato e uma janela de validade | `/.well-known/` |

A política de segurança de conteúdo permite scripts e estilos inline. Isso é um compromisso deliberado e documentado: o site é estático e carrega um número pequeno de blocos inline por página, incluindo o bootstrap de analytics, e substituí-los por hashes exigiria regenerar hashes em todo build e quebraria o snippet do tag manager. A política ainda bloqueia toda origem externa que não está na lista, que é a parte que importa para um comprometimento de um script de terceiros.

## O que não está garantido

O rate limit é por instância de function e não barra uma origem distribuída; não há WAF nem limitador de borda na frente das functions. Não há checagem de disponibilidade nem alerta de erro. O pipeline não valida HTML, links nem dados estruturados antes do deploy, então uma página quebrada é descoberta lendo. O escape na marcação gerada depende da disciplina dos geradores. Os números de case fornecidos para as páginas de case foram entregues como projeções, e o site os apresenta como conteúdo publicado; este repositório não os repete e não descreve nenhum deles como resultado medido. Nada aqui afirma conformidade legal, certificação ou garantia de segurança para as operações da marca.

## Como relatar um problema

Os dados de contato de segurança e a janela de divulgação estão publicados em `/.well-known/security.txt` no site no ar. Relatos sobre este repositório também podem passar pelo formulário de contato ligado à página de suporte do site. Inclua a URL, o comportamento observado e os passos para reproduzir, e dê tempo para uma correção antes de publicar detalhes.
