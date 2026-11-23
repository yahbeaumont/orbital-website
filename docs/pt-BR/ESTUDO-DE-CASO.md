# Estudo de caso: um site de produto bilíngue sem framework

## O problema

O briefing era um site para uma marca de hardware: quatro máquinas que rodam modelos de linguagem de pesos abertos localmente, um sistema operacional que vem com elas, uma biblioteca de cases, uma seção de empresa, suporte e o conjunto jurídico, em português e inglês, com um checkout no fim do funil. A referência visual era uma página de produto de uma empresa com time de design e biblioteca de componentes. A restrição de entrega era um engenheiro, nenhum design system e nenhum servidor de aplicação.

A resposta óbvia era um framework. Eu peguei o caminho oposto, e este documento é sobre o que isso comprou e o que custou.

Dois fatos decidiram. O primeiro era que o site é majoritariamente estático: nada em uma página de produto depende de quem pergunta. O segundo era que o conteúdo muda em rajadas e chega do cliente em documentos, planilhas e e-mails, o que significa que o problema real do site não é interatividade, é manter quarenta e cinco páginas por idioma consistentes enquanto o texto continua mudando.

## Restrições

Sem framework, sem bundler, sem runtime para as páginas. Toda página precisava abrir pelo sistema de arquivos antes de ser publicada, o que descarta qualquer coisa que exija um servidor para montar marcação. Os assets chegaram tarde: renders, fotos e capturas de interface vieram depois de as páginas estarem desenhadas. O texto chegou em dois idiomas em momentos diferentes, então um idioma estava sempre à frente do outro. O site precisava ser indexável desde o primeiro deploy, com URLs canônicas e alternates de idioma corretos, porque uma marca de hardware compete por termos de busca com conteúdo de empresas que têm time editorial.

E precisava ser revisável. Uma pessoa, sem QA, sem ambiente de staging com tráfego real: o diff do git é a revisão, e uma mudança que toca quarenta páginas precisa ser legível como uma decisão.

## O que foi construído

Um pipeline de geradores em Python, e um site estático que é a sua saída.

Cada família de página tem um script que recebe um dicionário de conteúdo e devolve HTML. Dezesseis deles: home, produtos, a linha compacta, especificações, a seção do sistema operacional, o topo de linha, as páginas de modelo, sobre, os hubs, cases, páginas de growth, uma demo de latência, o conjunto jurídico, uma composição de notebook e injeção de tags. Treze importam o mesmo módulo de shell, que é dono do header, do rodapé, da barra de região e da gaveta de compra. O conteúdo vive em dicionários com chave por locale, ao lado do gerador que o consome. Fatos que atravessam páginas vivem em módulos dedicados: preços e identidade de produto, velocidades de geração dos modelos, entradas de case e as suas relações, conversão de moeda.

O `tools/build_all.py` roda os geradores como subprocessos em ordem fixa e para na primeira falha. Depois deles, cinco etapas de pós-processamento: imagens de interface trocadas pelas variantes em inglês, cards sociais adicionados onde a página não tem, um hash de conteúdo anexado a toda referência de CSS e JavaScript, o sitemap reconstruído a partir dos arquivos em disco e o mapa de redirects regenerado.

Ao redor disso: 19 folhas de estilo, 10 arquivos JavaScript divididos por responsabilidade e três funções serverless para as operações que precisam de um segredo, de uma assinatura ou de um catálogo em que o navegador não pode ser confiado.

## As quatro partes difíceis

**Manter os números verdadeiros em 90 lugares.** Os mesmos quatro números apareciam na home, em quatro páginas de modelo, numa tabela de comparação, nos dados estruturados e na gaveta. A primeira versão os tinha digitados em cada página, e a tabela de comparação acabou discordando de uma página de modelo. A correção foi estrutural: um módulo é dono dos valores, e todo consumidor o importa, incluindo o construtor de JSON-LD e o painel de especificações. A parte interessante é a disciplina que isso impõe: um número em prosa também precisa vir de algum lugar, então as narrativas de case recebem os seus números como argumentos. Quando o cliente mudou um valor, uma edição se propagou para os dois idiomas e para todos os tipos de página, e o diff provou isso.

**Pareamento de idiomas que sobrevive a páginas ausentes.** Português e inglês não são as mesmas rotas com um prefixo. Dois slugs são traduzidos em vez de transliterados, e algumas páginas existem em um idioma antes do outro. O sitemap é gerado percorrendo a árvore publicada, pulando as páginas marcadas como `noindex` e pareando o que resta pela identidade de caminho, com um mapa de alias para os slugs traduzidos. Cada página carrega uma URL canônica igual ao seu caminho real e três alternates, com `x-default` apontando para o inglês. O modo de falha contra o qual eu tive de desenhar é uma página que existe mas não deveria ser anunciada, ou um par que parece completo e não é. Os dois são tratados em tempo de build, porque em tempo de requisição não há lógica para consultar.

**Moeda que calcula.** As páginas de case falam de custo, economia e payback. Escrever esses números à mão em duas moedas produz duas histórias que discordam. Em vez disso, os valores são guardados uma vez como inteiros na moeda de operação, convertidos em tempo de build com uma taxa fixa, arredondados por faixa para que o resultado leia como um número redondo, e formatados para o locale. O payback é derivado: preço na moeda da página dividido pela economia mensal. A consequência é que o mesmo case pode mostrar um payback diferente em cada idioma, e isso está correto, porque cada página fecha a sua aritmética na sua própria moeda. Aceitar uma diferença visível entre idiomas foi a decisão editorial mais difícil do projeto.

**Um hero que funciona antes de os renders existirem.** A imagem do hero é um PNG transparente que o parallax move, e os ids que o script mira ficam no próprio `<img>`. Quando o arquivo está faltando, um handler de erro inline revela um chassi desenhado em CSS, e um mutation observer copia o transform da imagem para o chassi, para que o movimento continue. Isso deu uma página que parecia pronta antes de a fotografia chegar, e deixou uma restrição permanente: o id não pode migrar para um wrapper, e o chassi precisa continuar sendo o irmão anterior da imagem. Está documentado como uma regra que não pode ser quebrada, que é a forma honesta de descrever uma decisão que agora custa manutenção.

## O que mudou no caminho

O ponto de partida era HTML editado à mão com uma folha de estilo compartilhada, e uma cópia arquivada dessas páginas ainda está na árvore. O primeiro gerador foi escrito para as quatro páginas de modelo, que eram as mais repetitivas, e ele carrega o esqueleto completo da página inline; o módulo de shell compartilhado veio depois, quando as outras famílias precisaram do mesmo header e rodapé. O sitemap começou como uma lista mantida à mão e virou uma varredura da árvore publicada depois que a lista ficou desatualizada mais de uma vez.

O modelo de idioma foi a outra mudança. Traduzir o texto string por string produz um inglês que lê como português traduzido, então os dois idiomas são escritos separadamente e mantidos lado a lado como dicionários. Uma página é escrita duas vezes por escolha e não uma vez por fórmula, e o pareamento entre idiomas acontece no roteamento e nos metadados, não no texto.

A última mudança foi de escopo: o site ganhou uma biblioteca de cases, uma seção de negócios e um conjunto jurídico, e o número de geradores cresceu com ele. Foi aí que o pipeline se pagou. Cada nova família era um script e um dicionário, não uma nova arquitetura.

## O que eu faria diferente

Eu colocaria um validador de HTML e um verificador de links no pipeline. Concatenação de strings significa que marcação malformada é encontrada olhando a página, e em 90 URLs ninguém olha todas. Eu também adicionaria um modo incremental: um rebuild completo reescreve todas as páginas, então os diffs são grandes e uma mudança de uma palavra é indistinguível de uma reestruturação.

Eu substituiria os dicionários de conteúdo por uma linguagem de template de verdade e um schema para o modelo de conteúdo, porque os dicionários não têm tipo e uma chave faltando é uma exceção em tempo de build. E eu geraria um pequeno conjunto de asserções por página a partir dos mesmos módulos: que o preço na marcação bate com o preço no JSON-LD, que todo link interno resolve, que todo alvo de `hreflang` existe. Tudo isso é barato em tempo de build e caro de descobrir em produção.

A questão do framework eu responderia do mesmo jeito. Ele teria trocado a camada de geradores por uma árvore de dependências e não teria tocado no problema que realmente doeu, que era a consistência dos fatos entre idiomas e tipos de página.
