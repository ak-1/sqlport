
CREATE FUNCTION map_matches (txt text)
  RETURNS text
AS $$
    r = ""
    quote = False
    charset = False
    for c in txt:
        if quote:
            quote = False
        elif c == "]":
            charset = False
        elif charset:
            pass
        elif c == "[":
            charset = True
        elif c == "\\":
            quote = True
        elif c == "?":
            c = "_"
        elif c == "*":
            c = "%"
        r += c
    return r
$$ LANGUAGE plpython3u;
