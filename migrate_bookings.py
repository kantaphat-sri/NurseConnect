import csv

HEADERS = ['id', 'client_id', 'nurse_id', 'service_type', 'date', 'time', 'address', 'notes', 'status', 'duration', 'total_price']
filename = 'bookings.csv'

with open(filename, 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

new_rows = []
for row in rows:
    new_row = {field: row.get(field, '') for field in HEADERS}
    if not new_row['time']: new_row['time'] = '09:00'
    if not new_row['duration']: new_row['duration'] = '1'
    if not new_row['total_price']: 
        rates = {
            'พาผู้ป่วยไปพบแพทย์': 250,
            'พยาบาลที่บ้าน': 400,
            'ดูแลผู้สูงอายุ': 300,
            'หัตถการที่บ้าน': 500,
            'ฟื้นฟูสมรรถภาพ': 450
        }
        new_row['total_price'] = str(rates.get(new_row['service_type'], 350))
    new_rows.append(new_row)

with open(filename, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(new_rows)
