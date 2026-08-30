def check_dress_code(shoulders, midriff, knees):

    violations = []

    if not shoulders["covered"]:
        violations.append("Shoulders exposed")

    if not midriff["covered"]:
        violations.append("Midriff exposed")

    if not knees["covered"]:
        violations.append("Knees exposed")

    passed = len(violations) == 0

    return {
        "passed": passed,
        "violations": violations
    }