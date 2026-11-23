# Segurança e privacidade

## O que está protegido

**A superfície publicada.** O HTML, o CSS, o JavaScript e as imagens que saem do CDN. A ameaça aqui não é perda de dados: é uma página que executa código que não deveria, ou que entrega algo que o build queria manter privado.

**A fronteira do repositório.** A configuração de hospedagem publica um diretório. Tudo que está dentro dele e não foi excluído explicitamente é público, e é por isso que a lista de ignore na publicação vale como controle de segurança: ferramental, documentação, fontes das functions, arquivos de ambiente, arquivos compactados e metadados do repositório não podem ficar acessíveis.

**Conteúdo comercial antes da publicação.** Preços, especificações de modelo, narrativas de case e texto jurídico são aprovados num lugar só e gerados dentro das páginas. Um gerador que lê o módulo errado, ou uma página que contorna a fonte única, publica número não aprovado.

**O handoff do comércio.** A sessão de pagamento, a consulta de status do pedido e o webhook. O site nunca vê dados de cartão, mas lida com o identificador de uma sessão e com o e-mail atrelado a um pedido.

**Privacidade do visitante.** Estado de consentimento de analytics, preferência de região e conteúdo da sacola, que ficam no local storage e nunca saem do navegador.

## Fronteiras de confiança

1. **Da máquina de build para a saída estática.** Os geradores são confiáveis. Nenhuma checagem automatizada verifica a saída deles antes do deploy, então a fronteira é a revisão do diff gerado.
2. **Do navegador para a hospedagem.** O navegador não é confiável. Tudo que ele recebe é público, cacheável e inspecionável.
3. **Do navegador para as functions.** As requisições chegam de qualquer lugar. Origem, método, tipo de conteúdo, tamanho do corpo e frequência de requisições passam por checagem antes de qualquer trabalho começar.
4. **Do provedor de pagamento para as functions.** O webhook é um endpoint não autenticado até a assinatura ser verificada sobre o corpo bruto. Antes dessa checagem, a requisição é tratada como hostil.
5. **De scripts de terceiros para a página.** O tag manager é o único script de terceiros autorizado a executar, e fica limitado pela política de segurança de conteúdo e pelo estado de consentimento.

## Ameaças consideradas

**Exposição de metadados do repositório.** A configuração de hospedagem publicava a raiz do repositório. Diretórios com ponto, ferramental, documentação e fontes das functions eram excluídos por uma lista de padrões que não cobria tudo. Hoje a lista é explícita e trata todo caminho não publicável como exclusão nomeada. As rotas arquivadas continuam no ar, mas com header `noindex`, em vez de serem removidas, para que URL antiga não sirva de caminho até conteúdo aposentado no índice.

**Injeção pela marcação gerada.** O texto é escrito pela equipe, não vem do usuário, então o vetor realista é um valor que chega ao HTML sem escape: nome de produto, métrica de case, parágrafo jurídico com um e comercial. A expectativa é que os geradores façam escape do texto interpolado e mantenham a marcação em template literals, não em dados. Isso é convenção, não regra imposta, e é o ponto mais fraco de um pipeline de strings.

**Clickjacking e framing.** Páginas e functions enviam `X-Frame-Options: DENY` e `frame-ancestors 'none'`.

**Cross-site scripting por dependência comprometida.** Não há árvore de pacotes para comprometer: nenhum framework, nenhuma biblioteca baixada de registry ou de CDN público. O único script de terceiros é o tag manager, que a política de segurança de conteúdo limita aos endpoints de analytics de que ele precisa, enquanto bloqueia `object`, `base` e frames desconhecidos.

**Abuso da sessão de pagamento.** A função de sessão aceita apenas POST de uma origem na allowlist, exige JSON, rejeita corpo acima de um limite pequeno, valida identificador de catálogo e quantidade e aplica rate limit por instância. Os preços são resolvidos no servidor, então cliente adulterado não consegue mudar valor nenhum.

**Falsificação de webhook.** A assinatura é verificada contra o corpo bruto antes de qualquer efeito. Requisição sem assinatura não gera e-mail nem mudança de estado.

**Enumeração de status de pedido.** A função de status aceita apenas GET, valida o identificador, aplica rate limit por instância com `Retry-After` e devolve e-mail mascarado, para que um link de confirmação compartilhado não revele o endereço completo do comprador.

**Coleta excessiva de analytics.** O consentimento vem negado por padrão, definido antes de o tag manager carregar, e só muda por escolha explícita guardada no local storage. A barra de região usa session storage, então não precisa de consentimento e não deixa nada para trás quando a aba fecha.

## Controles implementados

| Controle | Onde |
|---|---|
| Política de segurança de conteúdo com lista explícita de origens | Regra de header na hospedagem |
| `X-Frame-Options`, `frame-ancestors`, `Permissions-Policy`, `Referrer-Policy`, `nosniff`, HSTS | Regras de header na hospedagem |
| Política de cache que revalida HTML e assets, com URL de asset carregando hash de conteúdo | Hospedagem e uma etapa de build |
| Lista de ignore na publicação que cobre ferramental, docs, functions, arquivos de ambiente, arquivos compactados e diretórios com ponto | Configuração de hospedagem |
| `noindex` nas rotas arquivadas | Regra de header com escopo no caminho do arquivo |
| Nenhum segredo em arquivo servido | Convenção de build; segredos ficam no ambiente das functions |
| Resolução de preço no servidor | Catálogo da função de sessão |
| Verificação de assinatura sobre o corpo bruto | Função de webhook |
| Rate limit por instância, limite de tamanho do corpo, checagem de tipo de conteúdo, allowlist de origem | Funções de sessão e de status |
| E-mail mascarado na página de status, escape de HTML antes da renderização | Função de status e página de confirmação |
| Consentimento negado por padrão, atualizado na escolha | Bootstrap inline gerado em tempo de build |
| `security.txt` com contato e janela de validade | `/.well-known/` |

A política de segurança de conteúdo permite script e estilo inline. É um compromisso deliberado e documentado: o site é estático e carrega alguns blocos inline por página, entre eles o bootstrap de analytics. Substituí-los por hashes exigiria regerar hashes a cada build e quebraria o snippet do tag manager. A política continua bloqueando toda origem externa fora da lista, que é a parte que importa quando um script de terceiros é comprometido.

## O que não está garantido

O rate limit é por instância de function e não segura uma origem distribuída; não há WAF nem limitador de borda na frente das functions. Não existe checagem de disponibilidade nem alerta de erro. O pipeline não valida HTML, links nem dados estruturados antes do deploy, então página quebrada só é descoberta na leitura. O escape na marcação gerada depende da disciplina dos geradores. Os números de case fornecidos para as páginas de case chegaram como projeções, e o site os apresenta como conteúdo publicado; este repositório não os repete e não descreve nenhum deles como resultado medido. Nada aqui afirma conformidade legal, certificação ou garantia de segurança para as operações da marca.

## Como relatar um problema

Os dados de contato de segurança e a janela de divulgação estão publicados em `/.well-known/security.txt` no site no ar. Relatos sobre este repositório também podem ir pelo formulário de contato ligado à página de suporte do site. Inclua a URL, o comportamento observado e os passos para reproduzir, e dê tempo para a correção antes de divulgar detalhes.
