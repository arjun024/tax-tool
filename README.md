## Automated Personal Tax Preparing Tool for VMW-AVGO Merger

This is a python based tool automatically calculates the cost basis of the VMW-AVGO merger. It can generate all data 
without the need for manually inputting per-lot information; you just need to download two files from E*Trade.

This tool processes Gain & Loss file downloaded from ETRADE. It generates tax info for each row(lot). It also generates
tax summary across all lots and AVGO cash in lieu fractional share info if applicable.

## USAGE

```text
usage: tax.py [-h] [-c CASH] [-s STOCK] input output

positional arguments:
  input                     gain & loss csv file path
  output                    output file path, without file extension

options:
  -h, --help                show this help message and exit
  -c CASH, --cash CASH      vmware share count liquidated for cash
  -s STOCK, --stock STOCK   vmware share count liquidated for stock
  -f, --force               force espp lot to use qualifying disposition, default to false
```

#### Usage example

```text
cd tool-dir
python3 tax.py gain-loss.csv output -c 459 -s 500 -f
```

#### Prepare Input Parameter

- Gain & Loss file: from ETRADE website, select `Stock Plan (AVGO) ACCOUNT` -> `My Account` tab -> `Gains & Losses` ->
  click `Download`. Either `Download Collapsed` or `Download Expanded` are ok.
    - A xlsx file will be downloaded.
    - Open it in Excel or Numbers or Google Sheet and save/download it as csv file, use "Comma Separated Values" option if applicable.
- VMware share count liquidated for cash & stock: from ETRADE website, select `Stock Plan (AVGO) ACCOUNT` ->
  `Tax Information` tab -> `statements` -> download 12/31/2023 Single Account Statement. On the last page of this
  statement:
    - find row with `UNACCEPTED SHARES` comments, the `Quantity` number is the share count liquidated for cash
    - find row with `TENDER PAYMERNT` comments, the `Quantity` number is the share count liquidated for stock

#### Output

This tool generates two files, one in text format, another with the same name in csv format. Both files contain
tax info for each lot, in addition, the text file contains tax summary cross all lots and AVGO cash in lieu fractional
share info. In generated files, each lot has a row id field which is id of the corresponding row from Gain & Loss input
file, so we can easily correlate between computed lot from output and reported lot from input.

#### Turbo Tax Filing

For each stock transaction reported on 1099-B, find the corresponding row(lot) in generated tax file by acquire date and
share count.

- Use `Box 1d Proceeds` value generated by script to populate Turbo Tax `Box 1d - Proceeds` field. If you already
  imported from ETRADE, verify value generated by script matches imported one.
- Use `Filing Cost Basis` value generated by script to populate Turbo Tax `Cost basis or adjusted cost basis` field

![Alt text](img/tt-1.png?raw=true "enter total proceeds")
![Alt text](img/tt-2.png?raw=true "enter total cost base")

#### Potential AVGO Cost Base Adjustment For Last ESPP Lot

Generated AVGO cost base can be used as is except the last ESPP lot acquired on 08/31/2022, which is the only one with 
disqualifying disposition as of merge date. It's ESPP disposition status will be transitioned to qualifying after 
03/01/2024. If you didn't sell the converted AVGO shares of that lot before 03/01/2024, pass `-f` to command line 
input, which will force espp to be considered as qualifying disposition, so AVGO shares fo this lot will have more
favorable (higher) cost base.

## Reference

https://investors.broadcom.com/financial-information/tax-information

## License

This repo is free for non-commercial use. If you want to use any of it commercially, please contact me.

## Disclaim

Tool is for information and knowledge sharing purpose. Author is not tax professional, assumes no responsibility or
liability for any errors or omissions in the content of this tool.