# General libraries
# Nothing to import

# Probius libraries
# Nothing to import

def generate_testcase(VNFs):
    cases = []

    for VNF in VNFs:
        case = []
        case.append(VNF)
        cases.append(case)

    return cases

def generate_testcases(VNFs):
    count = len(VNFs)

    cases = []
    n_cases = pow(2, count)

    for base in range(count):
        for n_case in range(n_cases):
            case = []

            for bit in range(count):
                if (n_case & (1 << bit)) > 0:
                    case.append(VNFs[(bit + base) % count])

            if case not in cases and len(case) > 1:
                cases.append(case)

    return cases

def load_VNF_policies(VNFs, policy_file):
    policies = []

    with open(policy_file) as data_file:
        for line in data_file:
            line = line.strip("\n")
            line = line.replace(" ", "")

            if "#" in line:
                continue

            if line.count("&"):
                operand = line.split("&")

                if operand[0] not in VNFs or operand[1] not in VNFs:
                    print "Error: %s" % line
                    exit(-1)

                policies.append({"operator":"&", "operand1":operand[0], "operand2":operand[1]})
            elif line.count("|"):
                operand = line.split("|")

                if operand[0] not in VNFs or operand[1] not in VNFs:
                    print "Error: %s" % line
                    exit(-1)

                policies.append({"operator":"|", "operand1":operand[0], "operand2":operand[1]})
            elif line.count(">"):
                operand = line.split(">")

                if operand[0] not in VNFs or operand[1] not in VNFs:
                    print "Error: %s" % line
                    exit(-1)

                policies.append({"operator":">", "operand1":operand[0], "operand2":operand[1]})

    return policies

def verify_testcases(VNFs, all_cases, policies):
    cases = []

    for case in all_cases:
        passed = True

        for policy in policies:
            if policy["operand1"] not in case and policy["operand2"] not in case:
                continue

            if policy["operator"] == "&":
                if policy["operand1"] in case and policy["operand2"] not in case:
                    passed = False
                    break
                elif policy["operand1"] not in case and policy["operand2"] in case:
                    passed = False
                    break

            if policy["operator"] == "|":
                if policy["operand1"] in case and policy["operand2"] in case:
                    passed = False
                    break

            if policy["operator"] == ">":
                if policy["operand1"] in case and policy["operand2"] in case:
                    if case.index(policy["operand1"]) >= case.index(policy["operand2"]):
                        passed = False
                        break

        if passed == True:
            cases.append(case)

    return cases
