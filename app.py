from flask import Flask, render_template, request
import subprocess
from converter import tac_to_python   # 🔥 important
from analysis_tools import analyze

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    code = ""
    tac_output = ""
    python_output = ""
    lex_output = ""
    parse_tree_json = ""
    error = ""
    parse_message = ""

    if request.method == "POST":
        code = (request.form.get("code") or "").strip()

        try:
            lex_output, parse_tree_json, parse_message = analyze(code)

            # Run compiler (3AC generator)
            result = subprocess.run(
                ["compiler.exe"],
                input=code,
                text=True,
                capture_output=True
            )

            tac_output = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            # yacc/bison errors often go to stdout in this project
            if "Error:" in tac_output:
                error = tac_output
                tac_output = ""
            elif result.returncode != 0:
                error = stderr or "Compilation failed."
            elif stderr:
                # Some tools print warnings on stderr; surface them.
                error = stderr

            # Convert 3AC → Python
            if tac_output and not error:
                python_output = tac_to_python(tac_output)

        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        code=code,
        tac_output=tac_output,
        python_output=python_output,
        lex_output=lex_output,
        parse_tree_json=parse_tree_json,
        parse_message=parse_message,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=False)