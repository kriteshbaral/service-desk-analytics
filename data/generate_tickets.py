"""
Generate a realistic, fully synthetic IT service desk ticket dataset.

The organisation ("Harbourline Regional Services") is fictional. No real
people or real company data are used. The random seed is fixed so the
dataset is identical every time the script runs.

Output: data/tickets.csv (one row per ticket, 12 months of activity)
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 2026
random.seed(SEED)

START = datetime(2025, 10, 1)
END = datetime(2026, 9, 30, 23, 59)
OUT = Path(__file__).parent / "tickets.csv"

# --- Reference data ---------------------------------------------------------

# category: (share of volume, typical resolution hours, L1 can fix?, subcategories)
CATEGORIES = {
    "Password & Access": (0.30, 0.6, True,
                          ["Password reset", "Account locked", "MFA reset", "Shared mailbox access"]),
    "Hardware":          (0.17, 20.0, False,
                          ["Laptop fault", "Monitor/dock", "Peripheral", "Device replacement"]),
    "Software":          (0.16, 6.0, True,
                          ["Install request", "Application error", "Licence request", "Update failure"]),
    "Network & Wi-Fi":   (0.12, 5.0, False,
                          ["Wi-Fi drop-outs", "VPN connection", "No network", "Slow connection"]),
    "Email & M365":      (0.12, 3.0, True,
                          ["Outlook not syncing", "Teams issue", "OneDrive sync", "Distribution list"]),
    "Printing":          (0.09, 4.0, True,
                          ["Printer offline", "Paper jam/fault", "Driver install", "Scan to email"]),
    "Onboarding":        (0.04, 30.0, False,
                          ["New starter setup", "Leaver offboarding"]),
}

# priority: (share, first-response target mins, resolution target hours)
PRIORITIES = {
    "P1 - Critical": (0.02, 15, 4),
    "P2 - High":     (0.10, 30, 8),
    "P3 - Medium":   (0.55, 240, 24),
    "P4 - Low":      (0.33, 480, 72),
}

# site: (share, extra resolution delay multiplier for on-site work)
SITES = {
    "Darwin CBD":     (0.48, 1.0),
    "Palmerston":     (0.22, 1.1),
    "Katherine":      (0.16, 1.9),
    "Alice Springs":  (0.14, 2.3),
}

CHANNELS = {"Phone": 0.38, "Email": 0.27, "Self-service portal": 0.25, "Walk-in": 0.10}

L1_AGENTS = ["A. Nguyen", "B. Okafor", "C. Patel", "D. Wilson"]
L2_AGENTS = ["E. Murray", "F. Santos"]

# Monthly volume shape (1.0 = average). February spike = new starters and
# start of the school/financial half-year.
MONTH_WEIGHT = {10: 0.95, 11: 0.98, 12: 0.75, 1: 0.85, 2: 1.35, 3: 1.12,
                4: 0.95, 5: 1.02, 6: 1.05, 7: 1.10, 8: 0.98, 9: 0.96}
# Weekday shape: Monday busiest, weekends very quiet.
WEEKDAY_WEIGHT = [1.45, 1.10, 1.0, 0.95, 0.85, 0.08, 0.05]

AVG_TICKETS_PER_WEEKDAY = 17


def weighted_choice(options):
    keys = list(options)
    weights = [options[k] if not isinstance(options[k], tuple) else options[k][0] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


def created_times():
    """Yield ticket creation timestamps day by day."""
    day = START
    while day <= END:
        expected = AVG_TICKETS_PER_WEEKDAY * MONTH_WEIGHT[day.month] * WEEKDAY_WEIGHT[day.weekday()]
        count = max(0, int(random.gauss(expected, expected ** 0.5)))
        for _ in range(count):
            # Business-hours peak around 9am and 1pm
            hour = min(17, max(7, int(random.gauss(random.choice([9.2, 13.3]), 1.6))))
            yield day.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        day += timedelta(days=1)


def build_ticket(n, created):
    category = weighted_choice(CATEGORIES)
    share, base_hours, l1_fixable, subs = CATEGORIES[category]
    subcategory = random.choice(subs)

    # Priority depends a little on category (network outages skew higher)
    priority = weighted_choice(PRIORITIES)
    if category == "Network & Wi-Fi" and subcategory == "No network" and random.random() < 0.5:
        priority = "P2 - High"
    if category == "Onboarding":
        priority = "P3 - Medium"
    _, fr_target_min, res_target_h = PRIORITIES[priority]

    site = weighted_choice(SITES)
    site_mult = SITES[site][1]
    channel = weighted_choice(CHANNELS)
    if category == "Password & Access" and random.random() < 0.55:
        channel = "Phone"  # people locked out phone in

    # Who resolved it
    if l1_fixable and random.random() < 0.82:
        group, agent = "Service Desk (L1)", random.choice(L1_AGENTS)
    elif category == "Network & Wi-Fi":
        group, agent = "Network Team", "G. Hughes"
    elif category == "Onboarding":
        group, agent = "Systems Team", "H. Kaur"
    else:
        group, agent = "Desktop Support (L2)", random.choice(L2_AGENTS)

    # First response (minutes). Monday mornings and Feb are slower.
    fr_base = {"P1 - Critical": 8, "P2 - High": 20, "P3 - Medium": 90, "P4 - Low": 200}[priority]
    load = WEEKDAY_WEIGHT[created.weekday()] * MONTH_WEIGHT[created.month]
    first_response_min = max(1, int(random.expovariate(1 / (fr_base * load))))

    # Resolution time (hours)
    hours = random.lognormvariate(0, 0.75) * base_hours
    if group in ("Desktop Support (L2)",) and category == "Hardware":
        hours *= site_mult  # on-site hardware work at remote sites is slower
    if priority == "P1 - Critical":
        hours *= 0.35
    elif priority == "P2 - High":
        hours *= 0.6
    hours *= 0.85 + 0.3 * load  # busy periods slow everything down
    # A ticket can't be resolved before its first response
    if first_response_min > hours * 60:
        first_response_min = max(1, int(hours * 60 * random.uniform(0.3, 0.9)))
    resolved = created + timedelta(hours=hours)

    # Recurring printer fault at one site (planted pattern)
    if category == "Printing" and site == "Katherine" and random.random() < 0.5:
        subcategory = "Printer offline"

    # Re-opened tickets: Wi-Fi fixes that are closed too quickly come back
    reopen_p = 0.04
    if category == "Network & Wi-Fi" and hours < 2:
        reopen_p = 0.22
    if category == "Printing" and site == "Katherine":
        reopen_p = 0.18
    reopened = random.random() < reopen_p

    status = "Closed"
    if resolved > END:
        status, resolved = "Open", None

    breached = None
    if resolved is not None:
        breached = (resolved - created) > timedelta(hours=res_target_h)

    # Satisfaction survey: ~40% respond; breaches and re-opens score lower
    csat = ""
    if resolved is not None and random.random() < 0.40:
        score = random.choices([5, 4, 3, 2, 1], weights=[52, 30, 10, 5, 3])[0]
        if breached:
            score = max(1, score - random.choice([1, 1, 2]))
        if reopened:
            score = max(1, score - 1)
        csat = score

    return {
        "ticket_id": f"INC{100000 + n}",
        "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
        "first_response_at": (created + timedelta(minutes=first_response_min)).strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": resolved.strftime("%Y-%m-%d %H:%M:%S") if resolved else "",
        "status": status,
        "priority": priority,
        "category": category,
        "subcategory": subcategory,
        "site": site,
        "channel": channel,
        "assigned_group": group,
        "assigned_agent": agent,
        "response_target_min": fr_target_min,
        "resolution_target_hours": res_target_h,
        "reopened": int(reopened),
        "csat_score": csat,
    }


def main():
    tickets = [build_ticket(i, t) for i, t in enumerate(sorted(created_times()), start=1)]
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(tickets[0]))
        writer.writeheader()
        writer.writerows(tickets)
    print(f"Wrote {len(tickets):,} tickets to {OUT}")


if __name__ == "__main__":
    main()
