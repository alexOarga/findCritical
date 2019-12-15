# findCritical

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

## Table of Contents
- [Download](#Download)
- [Install](#install)
 	- [CLI/GUI](#CLI/GUI)
 	- [WEB](#WEB)
- [Usage](#usage)
 	- [CLI](#CLI)
 	- [GUI](#GUI)
 	- [WEB](#WEB)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Download
### Windows
[TODO](TODO)
### Linux
[TODO](TODO)

## Install source

### CLI/GUI
```sh
$ pip3 install -r build/requirements.txt
```

### WEB
```sh
$ pip3 install -r main/WEB/requirements.txt
```

## Run source
### CLI
```sh
$ python3 /main/CLI/FindCritical.py [-h] [-v] -i <input file> 
                        [-o <output file>]
                       [-swD <output file>] [-sF <output file>]
                       [-swDF <output file>]
                       
optional arguments:
  -h, --help           show this help message and exit
  -v, --verbose        Print feedback while running.
  -i <input file>      Input metabolic model. Allowed file formats: .xml .json
                       .yml 
  -o <output file>     Output spreadsheet file with results. Allowed file
                       formats: .xls .ods
  -swD <output file>   Save output model without Dead End Metabolites. Allowed
                       file formats: .xml .json .yml 
  -sF <output file>    Save output model with reactions bounds updated with
                       Flux Variability Analysis. Allowed file formats: .xml
                       .json .yml 
  -swDF <output file>  Save output model with reactions bounds updated with
                       Flux Variability Analysis and without Dead End
                       Metabolites. Allowed file formats: .xml .json .yml
```

### GUI
```
$ python3 main/GUI/run_GUI.py
```
### WEB
```
$ sudo service redis-server start
#   Change secret-key in 'main/WEB/DjangoProject/settings.py'
$ python3 manage.py runserver
```
Go to http://127.0.0.1:8000/app/

## Maintainers

[@alexOarga](https://github.com/alexOarga)

## Contributing

Feel free to dive in! [Open an issue](https://github.com/alexOarga/findCritical/issues/new) or submit PRs.

Standard Readme follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

## License

[MIT](LICENSE) © Alex Oarga
