def generate_schedule(nurses, shifts):
    # Simplified scheduling logic
    schedule = {}
    for i, nurse in enumerate(nurses):
        schedule[nurse] = shifts[i % len(shifts)]
    return schedule
