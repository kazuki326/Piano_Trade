# Piano_Trade

This repository contains a prototype script that fetches recent business news via RSS feeds and attempts to pick related Japanese stocks. The script downloads the feeds, extracts simple keywords from article titles and descriptions, and maps those keywords to stock tickers using a small sample dictionary.

## Requirements

The script relies only on the Python standard library (Python 3.8+). No external packages are needed.

## Usage

Run the following command to execute the scraper and print the detected tickers:

```bash
python3 main.py
```

## Testing

Unit tests can be executed with:

```bash
python3 -m unittest discover -s tests
```
