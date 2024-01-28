# PokeSpider 
A Web Crawler to scrape pokemon card prices from tcgplayer.com

## Installing:
1) Install Python 3

2) Create a virtual environment:
    ```sh
    python -m venv .venv
    ```

3) Enter the virtual environment:

    Linux:
    ```sh
    source .venv/bin/activate
    ```

    Windows
    ```ps
    ```

4) Install dependencies:
    ```
    pip instal -r requirements.txt
    playwright install
    ```

## Running:
1) Run the following command while in the virtual environment:
    ```sh
    scrapy crawl 'Main Spider' -o out.xlxs
    ```