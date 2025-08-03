# FMP Stock Screener Connector for Claude

This is a powerful MCP connector that integrates the **Financial Modeling Prep (FMP)** stock screening API directly into your Claude Desktop. It allows you to use natural, conversational language to find stocks that match complex criteria, transforming Claude into an expert financial analyst assistant.

Instead of navigating clunky web interfaces with dozens of dropdowns, you can simply ask Claude what you're looking for.

## How to Use

Because this is an MCP connector, usage is entirely conversational. You just talk to Claude and it will use the `screen_for_stocks` tool automatically when it detects a relevant query. The key is to be clear about your criteria.

Claude understands how to translate concepts like "large cap" or "high dividend" into the specific numerical filters required by the API.

### **Example Prompts**

Here are some examples of what you can ask, from simple to complex:

#### **Basic Screening**

* `Find me some stocks in the healthcare sector.`
* `Show me 10 Canadian tech companies.`
* `List stocks on the NASDAQ exchange.`

#### **Quantitative & Financial Queries**

* `Find stocks with a market cap over $500 billion.`
* `Show me companies with a stock price under $20.`
* `Are there any stocks with a dividend yield greater than 5%?`
* `Find stocks with high volume today.`

#### **Combining Multiple Criteria**

* `Find me US-based technology stocks with a market cap over $200 billion and a dividend.`
* `Show me 15 industrial stocks on the NYSE with a price lower than $100.`
* `I'm looking for highly active healthcare stocks. Find me some with a daily volume over 10 million shares.`

## Available Filters Reference

This connector gives Claude access to a wide range of filtering parameters. Here is a complete list for your reference when making advanced queries:

| Parameter                 | Type    | Description                                             |
| ------------------------- | ------- | ------------------------------------------------------- |
| `marketCapMoreThan`       | Integer | Stocks with a market capitalization above this value.   |
| `marketCapLowerThan`      | Integer | Stocks with a market capitalization below this value.   |
| `priceMoreThan`           | Float   | Stocks with a share price above this value.             |
| `priceLowerThan`          | Float   | Stocks with a share price below this value.             |
| `betaMoreThan`            | Float   | Stocks with a beta (volatility) above this value.       |
| `betaLowerThan`           | Float   | Stocks with a beta (volatility) below this value.       |
| `volumeMoreThan`          | Integer | Stocks with an average daily volume above this value.   |
| `volumeLowerThan`         | Integer | Stocks with an average daily volume below this value.   |
| `dividendMoreThan`        | Float   | Stocks with an annual dividend per share above this value.|
| `dividendLowerThan`       | Float   | Stocks with an annual dividend per share below this value.|
| `dividendYieldMoreThan`   | Float   | Stocks with a dividend yield (in %) above this value.   |
| `dividendYieldLowerThan`  | Float   | Stocks with a dividend yield (in %) below this value.   |
| `isActivelyTrading`       | Boolean | Set to `true` to only include actively traded stocks.   |
| `sector`                  | String  | Filter by sector (e.g., `Technology`, `Healthcare`).    |
| `industry`                | String  | Filter by industry (e.g., `Software - Infrastructure`). |
| `country`                 | String  | Filter by country code (e.g., `US`, `CA`, `DE`).        |
| `exchange`                | String  | Filter by stock exchange (e.g., `NASDAQ`, `NYSE`).      |
| `limit`                   | Integer | The maximum number of stocks to return (defaults to 20).|

## Setup

This connector requires a free API key from [Financial Modeling Prep](https://financialmodelingprep.com/developer). The key must be stored in a `.env` file in the connector's directory with the variable name `FMP_API_KEY`.

Installation is managed via the `mcp install` command as per the Claude Desktop connector documentation.