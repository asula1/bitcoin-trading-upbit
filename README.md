# Bitcoin Automated Trading Bot

This project implements an automated Bitcoin trading system that integrates with the Upbit cryptocurrency exchange, featuring advanced trading strategies, backtesting capabilities, and a web-based dashboard.

## Features

- **Upbit API Integration**: Secure communication with Upbit exchange for real-time market data and order execution
- **Multiple Trading Strategies**:
  - Moving Average (MA) crossover strategy
  - RSI-based trading
  - MACD-based signals
  - Volatility Breakout strategy (with K-value optimization)
  - Percentage-based trading
  - Combined strategy with indicator voting
- **Backtesting Framework**: Test strategies against historical data to evaluate performance
- **Web Dashboard**: Real-time monitoring of portfolio, trades, and signals using Streamlit
- **Docker Support**: Easy deployment with containerization
- **Configurable Trading Parameters**: Adjustable settings for risk management and strategy optimization

## Getting Started

### Prerequisites

- Python 3.8+
- Upbit API credentials (access key and secret key)
- Docker (optional, for containerized deployment)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/asula1/jocoding-trading.git
cd jocoding-trading
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API credentials:
   - Copy `config/config.ini` and fill in your Upbit API credentials
   - Adjust trading parameters as needed

### Usage

#### Running the Trading Bot

```bash
./run.sh
```

#### Running the Dashboard

```bash
./run_dashboard.sh
```

#### Running Backtests

```bash
./run_backtest.sh
```

#### Using Docker

```bash
./run_docker.sh
```

## Structure

- `src/upbit_api.py`: Handles Upbit API communication
- `src/data_analyzer.py`: Processes market data and calculates indicators
- `src/trading_strategies.py`: Implements various trading strategies
- `src/trading_bot.py`: Core trading logic and execution
- `src/dashboard.py`: Web-based monitoring interface
- `main.py`: Application entry point
- `backtest.py`: Strategy backtesting framework

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the book "Cryptocurrency Trading" resources
- Inspired by various trading strategy implementations from the cryptocurrency community