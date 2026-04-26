import re


_RE_LABEL = re.compile(r"^L(\d+):$")
_RE_GOTO = re.compile(r"^goto\s+L(\d+)$", re.IGNORECASE)
_RE_IFFALSE = re.compile(r"^ifFalse\s+(.+?)\s+goto\s+L(\d+)$", re.IGNORECASE)


def _process_assignment(line, indent, temp_map, out_lines):
    if not line or _RE_LABEL.match(line) or _RE_GOTO.match(line) or _RE_IFFALSE.match(line):
        return
    if "=" not in line:
        return

    left, right = line.split("=", 1)
    left = left.strip()
    right = right.strip()

    def needs_parens(expr: str) -> bool:
        # if temp expands to an expression, keep grouping when inlined
        return any(op in expr for op in (" + ", " - ", " * ", " / ", " > ", " < ", "==", "!=", ">=", "<="))

    # expand temps using what we already know (word-boundary safe)
    for temp, val in temp_map.items():
        rep = f"({val})" if needs_parens(val) else val
        # Use real word boundaries so `t2` doesn't match inside `t20`
        right = re.sub(rf"\b{re.escape(temp)}\b", rep, right)

    if left.startswith("t"):
        temp_map[left] = right
    else:
        out_lines.append(f"{indent}{left} = {right}")


def _process_assignment_slice(tac_lines, indent, temp_map, out_lines):
    for raw in tac_lines:
        _process_assignment(raw.strip(), indent, temp_map, out_lines)


def tac_to_python(tac_code):
    lines = [ln.strip() for ln in (tac_code or "").strip().splitlines() if ln.strip()]

    # map: label_id -> line_index
    label_pos = {}
    for idx, line in enumerate(lines):
        m = _RE_LABEL.match(line)
        if m:
            label_pos[int(m.group(1))] = idx

    py = []
    temp_map = {}

    def convert_range(start, end, indent):
        i = start
        while i < end:
            line = lines[i]

            # while pattern:
            # Ls:
            # ifFalse <cond> goto Le
            # ...body...
            # goto Ls
            # Le:
            m_label = _RE_LABEL.match(line)
            if m_label:
                s_label = int(m_label.group(1))
                if i + 1 < end:
                    m_if = _RE_IFFALSE.match(lines[i + 1])
                    if m_if:
                        cond = m_if.group(1).strip()
                        e_label = int(m_if.group(2))
                        e_idx = label_pos.get(e_label)
                        if e_idx is not None and e_idx < end:
                            # must have goto back to start somewhere before end label
                            back_goto_idx = None
                            for j in range(i + 2, e_idx):
                                mg = _RE_GOTO.match(lines[j])
                                if mg and int(mg.group(1)) == s_label:
                                    back_goto_idx = j
                                    break
                            if back_goto_idx is not None:
                                py.append(f"{indent}while {cond}:")
                                body_indent = indent + "    "
                                body_lines = lines[i + 2 : back_goto_idx]
                                before_len = len(py)
                                _process_assignment_slice(body_lines, body_indent, temp_map, py)
                                if len(py) == before_len:
                                    py.append(f"{body_indent}pass")
                                i = e_idx + 1
                                continue

            # if/if-else pattern:
            # ifFalse <cond> goto Lelse
            # ...then...
            # goto Lend
            # Lelse:
            # ...else (optional) ...
            # Lend:
            m_if = _RE_IFFALSE.match(line)
            if m_if:
                cond = m_if.group(1).strip()
                else_label = int(m_if.group(2))
                else_idx = label_pos.get(else_label)
                if else_idx is not None and else_idx < end:
                    goto_end_idx = None
                    end_label = None
                    for j in range(i + 1, else_idx):
                        mg = _RE_GOTO.match(lines[j])
                        if mg:
                            goto_end_idx = j
                            end_label = int(mg.group(1))
                            break
                    end_idx = label_pos.get(end_label) if end_label is not None else None
                    if goto_end_idx is not None and end_idx is not None and end_idx < end:
                        py.append(f"{indent}if {cond}:")
                        then_indent = indent + "    "
                        before_then = len(py)
                        _process_assignment_slice(lines[i + 1 : goto_end_idx], then_indent, temp_map, py)
                        if len(py) == before_then:
                            py.append(f"{then_indent}pass")

                        before_else = len(py)
                        else_buf = []
                        _process_assignment_slice(lines[else_idx + 1 : end_idx], then_indent, temp_map, else_buf)
                        if else_buf:
                            py.append(f"{indent}else:")
                            py.extend(else_buf)

                        i = end_idx + 1
                        continue

            # fallback: just assignments
            _process_assignment(line, indent, temp_map, py)
            i += 1

    convert_range(0, len(lines), "")
    return "\n".join(py).strip()