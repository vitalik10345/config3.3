import argparse
import sys
import json
from config_parser import ConfigParser, ConfigParserError, remove_comments

def main():
    parser = argparse.ArgumentParser(description="Преобразователь конфигураций в JSON")
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Входной конфигурационный файл')
    parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Файл для вывода JSON')
    args = parser.parse_args()

    input_text = args.input.read()
    input_text = remove_comments(input_text)

    parser = ConfigParser(input_text)
    try:
        result = parser.parse()
        json.dump(result, args.output, ensure_ascii=False, indent=2)
    except ConfigParserError as e:
        print("Ошибка парсинга:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
