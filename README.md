# veiculo-dados-br

Base de dados estruturada de veículos vendidos no Brasil, com informações
de marca, modelo, versões, consumo, motor e dimensões.

## 🎯 Objetivo

Coletar, organizar e disponibilizar informações públicas sobre veículos
no Brasil de forma estruturada, reutilizável e acessível para:

- APIs
- Estudos de consumo e eficiência
- Projetos de dados
- Aplicações e pesquisas automotivas

## 🌐 Origem dos Dados

Os dados deste projeto foram extraídos a partir de **informações públicas
disponíveis no site [combustivel.app](https://combustivel.app/)**, que reúne
especificações técnicas e dados de consumo de veículos comercializados no Brasil.

A coleta foi realizada de forma automatizada (**web scraping**), respeitando:

- Apenas dados de acesso público
- Estrutura de navegação do site
- Boas práticas de crawling e cache
- Sem coleta de dados pessoais ou restritos

Este projeto **não possui vínculo oficial** com o site citado, fabricantes
de veículos ou órgãos governamentais.

## 📦 Estrutura do Projeto

```
veiculo-dados-br/
├── data/ # Dados finais exportados
│ └── veiculos_raw.json
├── database/ # SQLite + schema SQL
├── export/ # Exportadores (ex: JSON)
├── scraper/ # Scripts de coleta de dados
├── requirements.txt
└── README.md
```

## 📄 Dados Exportados

O arquivo `data/veiculos_raw.json` contém a base completa no formato:

- Marca
- Modelo
- Ano
- Versão
- Consumo (cidade / estrada)
- Tanque
- Motor
- Dimensões
- Transmissão, suspensão, freios e outros

Este arquivo pode ser utilizado diretamente via **GitHub Raw**, APIs ou pipelines de dados.

## ▶️ Como gerar o JSON

```bash
    source venv/bin/activate
    python export/exportar_json.py
```

## ⚠️ Aviso Legal

Este projeto utiliza apenas dados públicos, organizados para fins
educacionais, informativos e de pesquisa.

Todos os direitos sobre o conteúdo original pertencem aos seus respectivos
detentores. Caso o site de origem solicite ajustes, correções ou remoção
de dados, o projeto será prontamente adequado.
