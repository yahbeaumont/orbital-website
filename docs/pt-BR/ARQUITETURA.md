# Arquitetura

## Contexto

Este site é a superfície de marketing e de produto de uma marca de hardware. A marca vende máquinas que rodam modelos de pesos abertos localmente. O site publica 45 rotas por idioma, em português e inglês, a partir de um repositório único, no Firebase Hosting. Nada é renderizado sob demanda: o visitante recebe um arquivo gerado na máquina de build.

Daí saem duas consequências. A primeira: toda decisão no nível da página, seja roteamento, pareamento de idiomas, URL canônica, dados estruturados ou preço, precisa estar resolvida antes do deploy. A segunda: o único código de runtime é o pouco JavaScript que roda no navegador e as funções serverless atrás dos caminhos de compra e de suporte.

## Componentes e responsabilidades

**Módulos de conteúdo.** O texto fica em dicionários Python, uma subárvore por locale, dentro do módulo que cuida daquela família de página. Dados que atravessam páginas moram em módulos próprios: preços e identidade de produto num deles, velocidade de geração dos modelos noutro, entradas de case e suas relações num terceiro, conversão de moeda num quarto. Esses módulos carregam só dados, nenhuma marcação.

**Shell compartilhado.** Um módulo expõe como funções o header, o rodapé, a barra de região, a gaveta de compra e o conjunto de ícones. Treze dos dezesseis geradores de página importam esse módulo. Assim, rótulo de navegação, link jurídico e seletor de idioma existem uma vez só, e qualquer mudança alcança todas as páginas no build seguinte.

**Geradores de página.** São dezesseis scripts, um por família: home, produtos, linha compacta, especificações, sistema operacional, Ultra, modelos, sobre, hubs, cases, growth, demo, latência, jurídico, composição de notebook e injeção de tags. Cada script lê o seu dicionário de conteúdo, chama as funções do shell e grava `index.html` na árvore do idioma. A estrutura de uma família só é definida no gerador dela.

**Pós-processamento.** Cinco scripts rodam depois dos geradores. Um troca imagens de interface pelas variantes em inglês. Outro acrescenta cards sociais às páginas que não têm. Outro anexa um hash de conteúdo a toda referência de CSS e JavaScript. Outro reconstrói `sitemap.xml` e `robots.txt` a partir dos arquivos publicados. O último regera o mapa de redirects.

**Orquestrador.** O `tools/build_all.py` roda os dezesseis geradores e as cinco etapas de pós-processamento como subprocessos, numa ordem fixa, e encerra no primeiro status diferente de zero. Ele define o contrato de "o que é um build".

**Camada de hospedagem.** O Firebase Hosting serve o diretório de saída, termina o TLS, aplica os headers de segurança e de cache e avalia as regras de redirect. A lista de ignore da publicação é a fronteira entre o repositório e a superfície pública.

**Functions.** Três functions HTTPS na mesma região cuidam da criação da sessão de pagamento, da consulta de status do pedido e do webhook do provedor de pagamento, além de envio de e-mail e encaminhamento de eventos de analytics. Todos os segredos de que o produto precisa ficam nelas.

## Fronteiras e contratos

*Do repositório para a superfície pública.* A configuração de hospedagem publica a raiz do repositório, mas ignora ferramental, documentação, functions, arquivos de ambiente, arquivos zip, markdown e metadados do repositório. O que não está nessa lista é público por padrão. Por isso a lista vale como controle de segurança, não como arrumação.

*Do build para o navegador.* Os geradores são donos da marcação. Os scripts do navegador nunca constroem um trecho de página: eles só mexem em estado que a marcação já declara, como classes para animação de reveal, um transform para parallax e `aria-hidden` para overlays. Uma página sem o seu script continua legível e navegável.

*Do navegador para as functions.* O navegador envia identificador de produto, quantidade e endereço. Preço, moeda e total nunca saem dele. A função resolve esses valores no próprio catálogo e rejeita identificador que não conhece.

*Do provedor de pagamento para as functions.* O webhook confere a assinatura contra o corpo bruto da requisição antes de qualquer efeito. Requisição sem assinatura ou com assinatura divergente não produz efeito colateral nenhum.

*Da imagem para o fallback.* O parallax mira um `<img>` por id. Se a imagem falha, um handler inline revela um chassi em CSS, que é o irmão anterior da imagem, e um observer copia o transform da imagem para o chassi. Os ids ficam na imagem, não num wrapper. Essa regra vale para qualquer outra marcação.

## Uma requisição pelo site

Um visitante pede uma página de produto. O CDN responde com um arquivo gerado em tempo de build; não existe render na origem. O documento declara o idioma, a URL canônica e três alternates `hreflang`, além de dados estruturados `Product` e `Offer` cujo preço saiu do módulo de preços durante o build. CSS e JavaScript chegam com um hash de conteúdo na query string, então um navegador que ainda guarda a cópia antiga busca a nova depois do deploy. No navegador rodam o script de shell, que cuida da barra de região e do header, e o script de interação, que cuida de reveals, modais e da gaveta de compra. Escolher um produto grava no local storage apenas identificadores e quantidades. Confirmar a compra leva à página de checkout, que chama a função de pagamento; a função valida a requisição, resolve os preços no servidor, cria uma sessão hospedada e devolve uma URL de redirect. Mais tarde, a página de confirmação consulta o status do pedido numa segunda função, que devolve o e-mail mascarado.

Um build segue a mesma lógica na direção contrária. Um módulo de conteúdo muda, o `build_all.py` regera todas as páginas, as etapas de pós-processamento recarimbam os assets e reconstroem o sitemap a partir do que existe em disco, e a saída é publicada.

## Modelo de dados conceitual

*Locale.* Duas instâncias, `pt-br` e `en`, cada uma com prefixo de URL, moeda e um conjunto de rotas.

*Rota.* Um caminho dentro de um locale, materializado como diretório com um `index.html`. Carrega tipo de página, URL canônica, um flag `noindex` opcional e uma chave de identidade usada no pareamento.

*Par de locale.* Duas rotas, uma por locale, que compartilham a chave de identidade. A chave costuma ser o caminho; um mapa de alias pequeno resolve os slugs que diferem entre idiomas. Um par pode ficar incompleto, e par incompleto não gera alternate `hreflang`.

*Produto.* Identificador, nome de exibição, nome de modelo, conjunto de especificações e preço por moeda. Aparece no catálogo, nas páginas de modelo, na tabela de comparação, na gaveta, na sacola e nos dados estruturados.

*Entrada de case.* Slug, setor, narrativa, conjunto de métricas, uma citação opcional, lista de FAQ e dois links de relação escolhidos pelo problema em comum.

*Documento jurídico.* Slug, corpo aprovado, data de vigência e locale. O gerador pagina e marca o documento; não reescreve.

## Decisões de deploy

A saída vai commitada para o repositório, porque o site é o artefato e o diff é a revisão. O deploy é um release de hospedagem desse diretório, com as regras de header e de redirect vindas da configuração. A política de cache é conservadora de propósito: HTML e assets revalidam, e a invalidação de asset fica por conta do hash de conteúdo, não da duração do cache. Páginas arquivadas continuam na árvore, mas ficam fora do sitemap e recebem `noindex` por uma regra de header.

## Limites conhecidos

O pipeline não tem modo incremental: cada execução reescreve todas as páginas e os diffs ficam grandes. O HTML sai de concatenação de strings, sem validador no pipeline, então marcação malformada só aparece no navegador. A dependência de ordem é implícita: o sitemap só está certo porque roda depois dos geradores. O mapa de alias para slugs traduzidos é mantido à mão. Os dados estruturados vêm dos mesmos módulos do texto visível, o que mantém os dois consistentes, mas nada valida o resultado contra um schema antes do deploy.
