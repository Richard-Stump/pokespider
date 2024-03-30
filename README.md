# PokeSpider 
A web crawler designed to scrape pokemon card prices from [TCGPlayer.com](https://www.tcgplayer.com/) and export them to .csv files. 

## Installation
1) Install Python 3, if you do not have it already.
2) Create a new virtual environment:
    ```ps1
    python -m venv venv
    ```
3) Enter the virtual environment:

    Powershell:
    ```ps1
    . .venv\Scripts\Activate.ps1
    ```

    cmd.exe:
    ```bat
    . .venv\Scripts\activate.bat
    ```

    Linux:
    ```sh
    source .venv/bin/activate
    ```

4) Install dependencies:
    ```ps1
    pip install -r requirements
    playwright install
    ```

## Running
1) Enter the virtual environment, if you are not in it already. (See step 3 of the installation instructions)
2) Run the crawler with the following command:
    ```ps1
    scrapy crawl 'main`
    ```
3) A window will pop up with a list of sets that can be scrapped. Check the ones that you want and then close the window. 
4) Wait and eventually it should complete. 

## Other Notes:

### Important Files for Making edits
| File                      | Purpose                               |
|---------------------------|---------------------------------------|
| settings.py               | Settings for Scrapy and the spider    |
| pipelines.py              | Pipeline that takes items and outputs them to CSV files. |
| items.py                  | The data structure for the scraped data   |
| spiders/main_spider.py    | The spider code that handles requesting and parsing data. | 

### Dependencies:
| Dependency | Min Version | Reason Used | Notes |
|------------|-------------|-------------|-------|
| scrapy        | 2.11.0    | Framework that orchestrates the scraping process and provides a CLI tool for running the scaper. |
| playwright    | 1.15      | Runs a headless browser that downloads dynamic content. |
| scrapy-playwright | Special | Implements a Scrapy download handler that lets scrapy download pages using playwright. | This project uses a [fork of scrapy-playwright](https://github.com/sanzenwin/scrapy-playwright/tree/supporting_for_windows) that lets it run on Windows, rather than just Linux. This is included in source form in this project rather than as a submodule 
| wxPython      | 4.2.1     | Used to implement the set selector window |