import re
import json

class ConfigParserError(Exception):
    pass

class ConfigParser:
    def __init__(self, text):
        self.text = text
        self.variables = {}
        self.position = 0
        self.length = len(self.text)

    def parse(self):
        self.skip_spaces()
        result = None
        while not self.end_reached():
            self.skip_spaces()
            if self.peek_keyword("var"):
                self.expect_keyword("var")
                self.skip_spaces()
                var_name = self.parse_name()
                self.skip_spaces()
                self.expect_symbol(":=")
                self.skip_spaces()
                val = self.parse_value()
                self.variables[var_name] = self.resolve_constants(val)
            else:
                result = self.parse_value()
                self.skip_spaces()
                if not self.end_reached():
                    raise ConfigParserError("Синтаксическая ошибка: неожиданные данные после результата.")
        output = {"variables": self.variables}
        if result is not None:
            output["_result"] = self.resolve_constants(result)
        return output

    def resolve_constants(self, val):
        if isinstance(val, str):
            # Обрабатываем константные ссылки внутри строки
            return self.replace_const_refs_in_string(val)
        elif isinstance(val, (int, float)):
            return val
        elif isinstance(val, list):
            return [self.resolve_constants(v) for v in val]
        elif isinstance(val, dict):
            return {k: self.resolve_constants(v) for k, v in val.items()}
        elif isinstance(val, tuple) and val[0] == "const_ref":
            name = val[1]
            if name not in self.variables:
                raise ConfigParserError(f"Неопределенная константа: {name}")
            return self.resolve_constants(self.variables[name])
        else:
            return val

    def replace_const_refs_in_string(self, s):
        # Ищем все константные ссылки вида .{имя}. и заменяем их значениями
        pattern = r'\.\{([a-zA-Z][a-zA-Z0-9]*)\}\.'

        def replacer(match):
            var_name = match.group(1)
            if var_name not in self.variables:
                raise ConfigParserError(f"Неопределенная константа: {var_name}")
            return str(self.variables[var_name])

        return re.sub(pattern, replacer, s)

    def skip_spaces(self):
        while self.position < self.length and self.text[self.position].isspace():
            self.position += 1

    def peek(self, length=1):
        return self.text[self.position:self.position+length] if self.position + length <= self.length else ''

    def consume(self, length=1):
        res = self.text[self.position:self.position+length]
        self.position += length
        return res

    def expect_symbol(self, sym):
        if self.text[self.position:self.position+len(sym)] == sym:
            self.position += len(sym)
        else:
            raise ConfigParserError(f"Ожидался символ '{sym}'")

    def peek_keyword(self, kw):
        saved_pos = self.position
        self.skip_spaces()
        if self.text.startswith(kw, self.position):
            end_pos = self.position + len(kw)
            if end_pos == self.length or not self.text[end_pos].isalnum():
                self.position = saved_pos
                return True
        self.position = saved_pos
        return False

    def expect_keyword(self, kw):
        if self.text.startswith(kw, self.position):
            self.position += len(kw)
            if self.position < self.length and self.text[self.position].isalnum():
                raise ConfigParserError(f"Некорректное использование ключевого слова '{kw}'")
        else:
            raise ConfigParserError(f"Ожидалось ключевое слово '{kw}'")

    def parse_name(self):
        pattern = r'[a-zA-Z][a-zA-Z0-9]*'
        match = re.match(pattern, self.text[self.position:])
        if not match:
            raise ConfigParserError("Ожидалось корректное имя")
        name = match.group(0)
        self.position += len(name)
        return name

    def parse_number(self):
        pattern = r'[+-]?\d+(\.\d+)?'
        match = re.match(pattern, self.text[self.position:])
        if match:
            num_str = match.group(0)
            self.position += len(num_str)
            return float(num_str) if '.' in num_str else int(num_str)
        return None

    def parse_string(self):
        if self.text.startswith("[[", self.position):
            self.position += 2
            end_pos = self.text.find("]]", self.position)
            if end_pos == -1:
                raise ConfigParserError("Не закрытая строка: отсутствует ']]'")
            s = self.text[self.position:end_pos]
            self.position = end_pos + 2
            # Здесь строки могут содержать константные ссылки, которые нужно заменить
            return self.resolve_constants(s)
        return None

    def parse_const_ref(self):
        if self.text.startswith(".{", self.position):
            self.position += 2
            name = self.parse_name()
            if self.text[self.position] != '}':
                raise ConfigParserError("Ожидался символ '}' в константной ссылке")
            self.position += 1
            if self.text[self.position] != '.':
                raise ConfigParserError("Ожидался символ '.' после '}' в константной ссылке")
            self.position += 1
            return ("const_ref", name)
        return None

    def parse_array(self):
        if self.text.startswith("array(", self.position):
            self.position += len("array(")
            arr = []
            while True:
                self.skip_spaces()
                if self.peek() == ')':
                    self.consume()
                    break
                val = self.parse_value()
                arr.append(val)
                self.skip_spaces()
                if self.peek() == ',':
                    self.consume()
                elif self.peek() == ')':
                    self.consume()
                    break
                else:
                    raise ConfigParserError("Ожидался ',' или ')' в массиве")
            return arr
        return None

    def parse_value(self):
        self.skip_spaces()
        val = self.parse_number()
        if val is not None:
            return val
        val = self.parse_string()
        if val is not None:
            return val
        val = self.parse_const_ref()
        if val is not None:
            return self.resolve_constants(val)
        val = self.parse_array()
        if val is not None:
            return val
        raise ConfigParserError("Ожидалось значение (число, строка, массив или константная ссылка)")

    def end_reached(self):
        self.skip_spaces()
        return self.position >= self.length

def remove_comments(text):
    # Удаление однострочных комментариев: || до конца строки
    text = re.sub(r'\|\|.*', '', text)
    # Удаление многострочных комментариев: /+ ... +/
    text = re.sub(r'/\+.*?\+/', '', text, flags=re.DOTALL)
    return text
