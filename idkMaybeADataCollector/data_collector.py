import os
from classes.BrowserDataScrapper import BrowserDataScrapper
from classes.AppDataScrapper import AppDataScrapper



data_collector = [
       BrowserDataScrapper(),
       AppDataScrapper()
    ]


print(data_collector[0][10])


