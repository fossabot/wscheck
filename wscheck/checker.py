import re

RULES = {
    'WSW001': 'Bad line ending',
    'WSW002': 'Tailing whitespace',
    'WSW003': 'Indentation is not multiple of 2',
    'WSW004': 'Indentation with non-space character',
    'WSW005': 'No newline at end of file',
    'WSW006': 'Too many newline at end of file',
}


class WhitespaceChecker(object):
    _LINE_TEMPLATE = re.compile(r'([^\n\r]*)(\r\n|\r|\n|)', re.MULTILINE)
    _TAILING_WHITESPACE_TEMPLATE = re.compile(r'\s+$')
    _LINE_INDENT_TEMPLATE = re.compile(r'^\s+')
    _NOT_SPACES_TEMPLATE = re.compile(r'[^ ]')

    def __init__(self, excluded_rules=None):
        """
        :type excluded_rules: list or None
        """
        excluded_rules = excluded_rules or []

        self._rules = {
            rule_id: rule_message
            for rule_id, rule_message in RULES.items()
            if rule_id not in excluded_rules
        }
        if not self._rules:
            raise RuntimeError('No rules to check')

        self._checkers = [
            self._check_by_lines,
            self._check_eof
        ]

        self._issues = []

    @property
    def issues(self):
        """
        :rtype: list
        """
        return self._issues

    def check_file(self, file_path):
        """
        :type file_path: str
        """
        lines = self._read_file_lines_w_eol(file_path)
        for checker in self._checkers:
            checker(file_path, lines)

    def _read_file_lines_w_eol(self, file_path):
        """
        :type file_path: str
        :rtype: list
        """
        with open(file_path) as fd:
            file_content = fd.read()
        lines = self._LINE_TEMPLATE.findall(file_content)

        # Workaround: can not match end of string in multi line regexp
        if len(lines) > 1 and lines[-2][1] == '':
            lines.pop()

        return lines

    def _check_by_lines(self, file_path, lines):
        """
        :type file_path: str
        :type lines: list
        """
        for line, line_text_eol in enumerate(lines, start=1):
            line_text, line_eol = line_text_eol

            if 'WSW001' in self._rules:
                if not line_eol == '' and not line_eol == '\n':
                    self._add_issue(rule='WSW001', path=file_path, line=line, col=len(line_text) + 1, context=line_text,
                                    message_suffix='{!r}'.format(line_eol))

            if 'WSW002' in self._rules:
                tailing_whitespace_match = self._TAILING_WHITESPACE_TEMPLATE.search(line_text)
                if tailing_whitespace_match is not None:
                    self._add_issue(rule='WSW002', path=file_path, line=line, col=tailing_whitespace_match.start() + 1, context=line_text)

            if line_text.strip() == '':
                continue

            indent_match = self._LINE_INDENT_TEMPLATE.match(line_text)
            if indent_match is not None:
                line_indent = indent_match.group()

                if 'WSW003' in self._rules:
                    if not len(line_indent.replace('\t', '    ')) % 2 == 0:
                        self._add_issue(rule='WSW003', path=file_path, line=line, col=len(line_indent), context=line_text)

                if 'WSW004' in self._rules:
                    character_match = self._NOT_SPACES_TEMPLATE.search(line_indent)
                    if character_match is not None:
                        self._add_issue(rule='WSW004', path=file_path, line=line, col=character_match.start() + 1,
                                        context=line_text)

    def _add_issue(self, rule, path, line, col, context, message_suffix=None):
        """
        :type rule: str
        :type path: str
        :type line: int
        :type col: int
        :type context: str
        :type message_suffix: str or None
        """
        self._issues.append({'rule': rule, 'path': path, 'line': line, 'col': col, 'context': context,
                            'message_suffix': message_suffix})

    def _check_eof(self, file_path, lines):
        """
        :type file_path: str
        :type lines: list
        """
        if len(lines) == 0:
            return

        empty_lines = 0
        for line_text, _ in reversed(tuple(lines)):
            if not line_text == '':
                break
            empty_lines += 1

        if 'WSW005' in self._rules:
            if empty_lines == 0:
                line_text = lines[-1][0]
                self._add_issue(rule='WSW005', path=file_path, line=len(lines), col=len(line_text) + 1, context=line_text)
        if 'WSW006' in self._rules:
            if empty_lines > 1:
                shift = min(len(lines), empty_lines + 1)
                line_text = lines[-shift][0]
                self._add_issue(rule='WSW006', path=file_path, line=len(lines) - shift + 1, col=len(line_text) + 1,
                                context=line_text, message_suffix='(+{})'.format(empty_lines - 1))