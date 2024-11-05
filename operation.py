from random import randint, choice, uniform

def random_operation():
    option = randint(1, 5)

    operator_a = choice((uniform(-500, -1), uniform(1, 500)))
    operator_b = choice((uniform(-500, -1), uniform(1, 500)))

    match option:
        case 1:
            return f"({operator_a:.2f}) + ({operator_b:.2f})", operator_a + operator_b
        case 2:
            return f"({operator_a:.2f}) - ({operator_b:.2f})", operator_a - operator_b
        case 3:
            return f"({operator_a:.2f}) * ({operator_b:.2f})", operator_a * operator_b
        case 4:
            return f"({operator_a:.2f}) / ({operator_b:.2f})", operator_a / operator_b
        case 5:
            return f"({operator_a:.2f}) % ({operator_b:.2f})", operator_a % operator_b
