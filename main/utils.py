# main/utils.py
import datetime

def next_delivery_date(day_name):
    days_map = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6,
    }
    today = datetime.date.today()
    today_weekday = today.weekday()  # Monday=0 ... Sunday=6
    delivery_weekday = days_map[day_name.lower()]

    days_ahead = (delivery_weekday - today_weekday) % 7
    if days_ahead == 0:  # if today, schedule for next week
        days_ahead = 7
    return today + datetime.timedelta(days=days_ahead)
