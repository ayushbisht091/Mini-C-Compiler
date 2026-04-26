def tac_to_python(tac_code):
    lines = tac_code.strip().split("\n")
    temp_map = {}
    python_lines = []
    indent = ""

    for line in lines:
        line = line.strip()

        if line.startswith("while"):
            python_lines.append(line)
            indent = "    "
            continue

        if "=" not in line:
            continue

        left, right = line.split("=")
        left = left.strip()
        right = right.strip()

        for temp in temp_map:
            right = right.replace(temp, temp_map[temp])

        if left.startswith("t"):
            temp_map[left] = right
        else:
            python_lines.append(indent + f"{left} = {right}")

    return "\n".join(python_lines)