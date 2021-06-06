import ply.lex as lex
import re

tokens = {
    # Storage class specifier
    "EXTERN",
    "AUTO",
    "STATIC",
    "REGISTER",

    # Flow control - for, if
    "FOR",
    "IF",
    "ELSE",
    "DO",
    "WHILE",
    "SWITCH",
    "CASE",
    "DEFAULT",
    "GOTO",
    "RETURN",
    "BREAK",
    "CONTINUE",

    # Variable type - int, float
    "INT",
    "FLOAT",
    "VOID",
    "CHAR",
    "SHORT",
    "LONG",
    "DOUBLE",
    "SIGNED",
    "UNSIGNED",    
    "CONST",
    "ENUM",
    "STRUCT",
    "UNION",
    "VOLATILE",
    "TYPEDEF",

    # Operators
    "COMMA",
    "COLON",
    "SEMICOLON",
    "LEFT_PARENTHESIS",
    "RIGHT_PARENTHESIS",
    "LEFT_BRACKET",
    "RIGHT_BRACKET",
    "LEFT_BRACE",
    "RIGHT_BRACE",
    "ELLIPSIS" # ...
    "ASSIGN",
    "SIZEOF",
    "DOT",
    "ARROW",
    "LEFT_SHIFT",
    "RIGHT_SHIFT"
    "ASSIGN_LEFT_SHIFT",
    "ASSIGN_RIGHT_SHIFT",

    # Calculation - +, -, *, /, ++
    "PLUS",
    "MINUS",
    "MUL",
    "DIV",
    "PLUS_PLUS",
    "MINUS_MINUS",
    "MOD",
    "ASSIGN_PLUS",
    "ASSIGN_MINUS",
    "ASSIGN_MUL",
    "ASSIGN_DIV",
    "ASSIGN_MOD"

    # Comparison - >, <
    "GREATER",
    "LESS",
    "EQUAL",
    "NOT_EQUAL",
    "GREATER_EQUAL",
    "LESS_EQUAL",
    "AMPERSAND",
    "PIPE",
    "TILDE",
    "CIRCUMFLEX", # ^
    "SHARP" # #
    "EXCLAMATION",
    "QUESTION",
    "AMPERSAND_AMPERSAND",
    "PIPE_PIPE",
    "ASSIGN_AMPERSAND",
    "ASSIGN_PIPE",
    "ASSIGN_CIRCUMFLEX"

    # Pointer - *, &
    "ASTERISK",
    #"ADDRESS_OPERATOR", # &

    # tokens
    "ID",
    "FLOAT_NUM",
    "STRING",
    "CHARACTER",
}

# type

reserved_words = {
    # Storage class specifier
    "EXTERN",
    "AUTO",
    "STATIC",
    "REGISTER",

    # Flow control - for, if
    "FOR",
    "IF",
    "ELSE",
    "DO",
    "WHILE",
    "SWITCH",
    "CASE",
    "DEFAULT",
    "GOTO",
    "RETURN",
    "BREAK",
    "CONTINUE",

    # Variable type - int, float
    "INT",
    "FLOAT",
    "VOID",
    "CHAR",
    "SHORT",
    "LONG",
    "DOUBLE",
    "SIGNED",
    "UNSIGNED",    
    "CONST",
    "ENUM",
    "STRUCT",
    "UNION",
    "VOLATILE",
    "TYPEDEF",

    # Operators
    "SIZEOF",

    # tokens
    "ID",
    "FLOAT_NUM",
    "STRING",
    "CHARACTER",
    }
}

# Operators
t_COMMA = r","
t_COLON = r":"
t_SEMICOLON = r";"
t_LEFT_PARENTHESIS = r"\("
t_RIGHT_PARENTHESIS = r"\)"
t_LEFT_BRACKET = r"\["
t_RIGHT_BRACKET = r"\]"
t_LEFT_BRACE = r"{"
t_RIGHT_BRACE = r"}"
t_ELLIPSIS = r"\.\.\." # ...
t_ASSIGN = r"="
t_DOT = r"\."
t_ARROW = r"->"
t_LEFT_SHIFT = r"<<"
t_RIGHT_SHIFT = r">>"
t_ASSIGN_LEFT_SHIFT = r"<<="
t_ASSIGN_RIGHT_SHIFT = r">>="

# Calculation - +, -, *, /, ++
t_PLUS = r"\+"
t_MINUS = r"-"
t_MUL = r"\*"
t_DIV = r"/" # r'
t_PLUS_PLUS = r"\+\+"
t_MINUS_MINUS = r"\-\-"
t_MOD = r"%"
t_ASSIGN_PLUS = r"\+="
t_ASSIGN_MINUS = r"-="
t_ASSIGN_MUL = r"\*="
t_ASSIGN_DIV = r"/="
t_ASSIGN_MOD = r"%="

# Comparison - >, <
t_GREATER = r">"
t_LESS = r"<"
t_EQUAL = r"=="
t_NOT_EQUAL = r"!="
t_GREATER_EQUAL = r">="
t_LESS_EQUAL = r"<="
t_AMPERSAND = r"&"
t_PIPE = r"\|"
t_TILDE = r"~"
t_CIRCUMFLEX = r"\^" # r"^" # ^ 
t_SHARP = r"#" # r"\#" # #
t_EXCLAMATION = r"!"
t_QUESTION = r"\?"
t_AMPERSAND_AMPERSAND = r"&&"
t_PIPE_PIPE = r"\|\|"
t_ASSIGN_AMPERSAND = r"&="
t_ASSIGN_PIPE = r"\|="
t_ASSIGN_CIRCUMFLEX = r"\^="

# Pointer - *, &
t_ASTERISK = r"\*"
#t_ADDRESS_OPERATOR", # &