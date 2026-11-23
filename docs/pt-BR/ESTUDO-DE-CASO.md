# Estudo de caso: um site de produto bilíngue sem framework

## O problema

O briefing era um site para uma marca de hardware: quatro máquinas que rodam modelos de linguagem de pesos abertos localmente, um sistema operacional que vem com elas, uma biblioteca de cases, uma seção de empresa, suporte e o conjunto jurídico, em português e inglês, com checkout no fim do funil. A referência visual era a página de produto de uma empresa com time de design e biblioteca de componentes. A restrição de entrega: um engenheiro, nenhum design system e nenhum servidor de aplicação.

A resposta óbvia era um framework. Fui pelo caminho oposto, e este documento trata do que isso rendeu e do que custou.

Dois fatos decidiram a questão. O primeiro: o site é quase todo estático, e nada numa página de produto depende de quem pergunta. O segundo: o conteúdo muda em rajadas e chega do cliente em documentos, planilhas e e-mails. Logo, o problema real do site não é interatividade, é manter quarenta e cinco páginas por idioma consistentes enquanto o texto não para de mudar.

## Restrições

Nada de framework, nada de bundler, nenhum runtime para as páginas. Toda página precisava abrir pelo sistema de arquivos antes de ir para o ar, o que descarta qualquer coisa que exija servidor para montar marcação. Os assets chegaram tarde: renders, fotos e capturas de interface vieram depois de as páginas estarem desenhadas. O texto chegou nos dois idiomas em momentos diferentes, então um idioma estava sempre à frente do outro. O site precisava ser indexável desde o primeiro deploy, com URLs canônicas e alternates de idioma corretos, porque marca de hardware disputa termo de busca com conteúdo de empresa que tem time editorial.

Também precisava ser revisável. Uma pessoa, sem QA e sem ambiente de staging com tráfego real: o diff do git é a revisão, e uma mudança que toca quarenta páginas precisa se ler como uma decisão só.

## O que foi construído

Um pipeline de geradores em Python, e um site estático como saída dele.

Cada família de página tem um script que recebe um dicionário de conteúdo e devolve HTML. São dezesseis: home, produtos, linha compacta, especificações, seção do sistema operacional, topo de linha, páginas de modelo, sobre, hubs, cases, páginas de growth, demo de latência, conjunto jurídico, composição de notebook e injeção de tags. Treze importam o mesmo módulo de shell, dono do header, do rodapé, da barra de região e da gaveta de compra. O conteúdo fica em dicionários com chave por locale, ao lado do gerador que o consome. Fatos que atravessam páginas ficam em módulos dedicados: preços e identidade de produto, velocidade de geração dos modelos, entradas de case e suas relações, conversão de moeda.

O `tools/build_all.py` roda os geradores como subprocessos, numa ordem fixa, e para na primeira falha. Depois vêm cinco etapas de pós-processamento: imagens de interface trocadas pelas variantes em inglês, cards sociais adicionados onde falta, hash de conteúdo anexado a toda referência de CSS e JavaScript, sitemap reconstruído a partir dos arquivos em disco e mapa de redirects regerado.

Ao redor disso: 19 folhas de estilo, 10 arquivos JavaScript divididos por responsabilidade e três funções serverless para as operações que precisam de segredo, de assinatura ou de um catálogo em que não se pode confiar no navegador.

## As quatro partes difíceis

**Manter os números verdadeiros em 90 lugares.** Os mesmos quatro números apareciam na home, em quatro páginas de modelo, na tabela de comparação, nos dados estruturados e na gaveta. A primeira versão os trazia digitados em cada página, e a tabela de comparação acabou discordando de uma página de modelo. A correção foi estrutural: um módulo é dono dos valores, e todo consumidor o importa, inclusive o construtor de JSON-LD e o painel de especificações. O interessante é a disciplina que isso impõe. Um número em prosa também precisa vir de algum lugar, então as narrativas de case recebem os seus números como argumentos. Quando o cliente mudou um valor, uma edição se espalhou pelos dois idiomas e por todos os tipos de página, e o diff mostrou isso.

**Pareamento de idiomas que sobrevive a páginas ausentes.** Português e inglês não são as mesmas rotas com um prefixo. Dois slugs são traduzidos, não transliterados, e algumas páginas existem num idioma antes do outro. O sitemap é gerado percorrendo a árvore publicada, pulando as páginas marcadas como `noindex` e pareando o resto pela identidade de caminho, com um mapa de alias para os slugs traduzidos. Cada página carrega uma URL canônica igual ao caminho real e três alternates, com `x-default` apontando para o inglês. O modo de falha contra o qual eu tive de projetar é a página que existe mas não deveria ser anunciada, ou o par que parece completo e não é. Os dois casos se resolvem em tempo de build, porque em tempo de requisição não há lógica para consultar.

**Moeda que calcula.** As páginas de case falam de custo, economia e payback. Escrever esses números à mão em duas moedas produz duas histórias que discordam. Em vez disso, os valores ficam guardados uma vez como inteiros na moeda de operação, são convertidos em tempo de build com uma taxa fixa, arredondados por faixa para o resultado ler como número redondo e formatados para o locale. O payback é derivado: preço na moeda da página dividido pela economia mensal. A consequência é que o mesmo case pode mostrar payback diferente em cada idioma, e isso está certo, porque cada página fecha a sua aritmética na moeda dela. Aceitar uma diferença visível entre idiomas foi a decisão editorial mais difícil do projeto.

**Um hero que funciona antes de os renders existirem.** A imagem do hero é um PNG transparente que o parallax move, e os ids que o script mira ficam no próprio `<img>`. Quando o arquivo falta, um handler de erro inline revela um chassi desenhado em CSS; um mutation observer copia o transform da imagem para o chassi, e o movimento segue. Isso entregou uma página com cara de pronta antes de a fotografia chegar, e deixou uma restrição permanente: o id não pode migrar para um wrapper, e o chassi precisa continuar sendo o irmão anterior da imagem. Está documentado como regra que não se quebra, que é a maneira honesta de descrever uma decisão que hoje custa manutenção.

## O que mudou no caminho

O ponto de partida era HTML editado à mão com uma folha de estilo compartilhada, e uma cópia arquivada dessas páginas continua na árvore. O primeiro gerador foi escrito para as quatro páginas de modelo, as mais repetitivas, e carrega o esqueleto completo da página inline. O módulo de shell compartilhado veio depois, quando as outras famílias passaram a precisar do mesmo header e rodapé. O sitemap começou como lista mantida à mão e virou varredura da árvore publicada depois de a lista ficar desatualizada mais de uma vez.

O modelo de idioma foi a outra mudança. Traduzir o texto string por string produz um inglês que lê como português traduzido, então os dois idiomas são escritos separadamente e mantidos lado a lado como dicionários. Uma página é escrita duas vezes por escolha, não uma vez por fórmula, e o pareamento entre idiomas acontece no roteamento e nos metadados, não no texto.

A última mudança foi de escopo: o site ganhou uma biblioteca de cases, uma seção de negócios e um conjunto jurídico, e o número de geradores cresceu junto. Foi aí que o pipeline se pagou. Cada família nova era um script e um dicionário, não uma arquitetura nova.

## O que eu faria diferente

Eu colocaria um validador de HTML e um verificador de links no pipeline. Com concatenação de strings, marcação malformada só aparece olhando a página, e em 90 URLs ninguém olha todas. Também adicionaria um modo incremental: um rebuild completo reescreve todas as páginas, então os diffs ficam grandes e uma mudança de uma palavra é indistinguível de uma reestruturação.

Eu trocaria os dicionários de conteúdo por uma linguagem de template de verdade e um schema para o modelo de conteúdo, porque os dicionários não têm tipo e uma chave ausente é exceção em tempo de build. E geraria um pequeno conjunto de asserções por página a partir dos mesmos módulos: que o preço na marcação bate com o preço no JSON-LD, que todo link interno resolve, que todo alvo de `hreflang` existe. Tudo isso é barato em tempo de build e caro de descobrir em produção.

A questão do framework eu responderia do mesmo jeito. Ele teria trocado a camada de geradores por uma árvore de dependências e não teria tocado no problema que realmente doeu, que era a consistência dos fatos entre idiomas e tipos de página.
