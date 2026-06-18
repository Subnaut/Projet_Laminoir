import random
from datetime import date, datetime, timedelta

random.seed(42)

start_date = date(2023, 6, 17)
end_date = date(2026, 6, 17)

# Générer toutes les dates de start à end inclus
dates = []
current = start_date
while current <= end_date:
    dates.append(current)
    current += timedelta(days=1)

# 10 horaires fixes par jour (toutes les ~2h24 de 08h00 à 22h24)
hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

for cage_num in range(1, 7):
    lines = []
    for d in dates:
        for h in hours:
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            dt = datetime(d.year, d.month, d.day, h, minute, second)
            temp = random.randint(20, 100)
            vib = round(random.uniform(0.01, 10.00), 2)
            vib_str = f"{vib:.2f}".replace(".", ",")
            lines.append(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - Température: {temp}°C - Vibration: {vib_str}")

    path = f"c:/Users/Subnaut/Desktop/Cours/3DATETL/Projet_cage_laminoir/cage{cage_num}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"cage{cage_num}.txt : {len(lines)} lignes écrites")
