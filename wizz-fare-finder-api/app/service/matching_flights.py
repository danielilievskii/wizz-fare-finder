from datetime import timedelta, datetime

def find_matching_flights(outbound_flights, return_flights, day_span, max_price, airport_map):
    results = []

    # Convert departureDate strings to datetime for comparison
    for ob in outbound_flights:
        ob_date = datetime.fromisoformat(ob["departureDate"])
        ob["departure_dt"] = ob_date  # Keep parsed date for matching

    for ret in return_flights:
        ret_date = datetime.fromisoformat(ret["departureDate"])
        ret["departure_dt"] = ret_date

    for ob in outbound_flights:
        for ret in return_flights:
            # Calculate day difference
            day_diff = (ret["departure_dt"].date() - ob["departure_dt"].date()).days

            # Match by day_span
            if day_diff < 0 or day_diff != day_span - 1:
                continue

            # If same day, ensure at least 4 hours gap
            if day_diff == 0:
                time_diff = (ret["departure_dt"] - ob["departure_dt"])
                if time_diff < timedelta(hours=6):
                    continue

            # Calculate total price
            total_discount_price = ob["discountPrice"] + ret["discountPrice"]
            total_original_price = ob["originalPrice"] + ret["originalPrice"]

            # Price filter
            if max_price is not None and total_discount_price > max_price:
                continue

            results.append({
                "outbound": {
                    "departureStation":  'Skopje (Macedonia) - ' + ob["departureStation"],
                    "arrivalStation": airport_map[ob["arrivalStation"]] + ' - ' + ob["arrivalStation"],
                    "discountPrice": ob["discountPrice"],
                    "originalPrice": ob["originalPrice"],
                    "departureDate": ob["departure_dt"].strftime("%Y-%m-%d"),
                    "departureTime": ob["departure_dt"].strftime("%H:%M"),
                },
                "return": {
                    "departureStation": airport_map[ret["departureStation"]] + ' - ' + ret["departureStation"],
                    "arrivalStation": 'Skopje (Macedonia) - ' + ret["arrivalStation"],
                    "discountPrice": ret["discountPrice"],
                    "originalPrice": ret["originalPrice"],
                    "departureDate": ret["departure_dt"].strftime("%Y-%m-%d"),
                    "departureTime": ret["departure_dt"].strftime("%H:%M"),
                },
                "total_discount_price": total_discount_price,
                "total_original_price": total_original_price,
            })

    # Sort by total price ascending
    results.sort(key=lambda x: x["outbound"]["departureDate"])

    return results