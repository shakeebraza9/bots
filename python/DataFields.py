import re

def safe_int(value, default=""):

    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return default
            value = (
                value.replace("€", "")
                     .replace(",", "")
                     .replace(" ", "")
            )

        return int(float(value))
    except (ValueError, TypeError):
        return default
def to_int1(value, default=""):
    try:
        if value is None:
            return default
        value = str(value)
        value = value.encode("ascii", "ignore").decode()
        for ch in ["£", "€", ",", " "]:
            value = value.replace(ch, "")

        if value == "":
            return default

        return int(float(value))
    except Exception as e:

        return default

def DataFields(data):


    def to_int(value, default=""):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return {
        # Basic
        'title': data.get('Title'),
        "make_id": data.get("Make") or data.get("Manufacturer"),
        "model_id": data.get("Model"),
        "variant_id": data.get("Variant") or data.get("Derivative"),
        'body_id': data.get('Body type') or data.get("Body Type"),
        'year': data.get('Year'),
        'center_id': data.get('Center'),
        'color': data.get('Colour'),
        'vin': data.get('VIN'),
        'lot': data.get('Lot'),

        # Vehicle Specs
        'doors' : to_int(data.get('doors') or data.get('Doors')),
        'seats': to_int(data.get('seats')  or data.get("Seats")),
        'fuel_type': data.get('Fuel Type'),
        'fuel_details': data.get('Fuel Type'),
        'transmission': data.get('Transmission'),
        'transmission_details': data.get('Transmission'),
        'euro_status': data.get('Euro Status') or data.get('Euro status'),
        'cc': data.get('CC'),
        'keys': data.get('Keys'),
        'engine_runs': data.get('Non Runner'),
        'mileage': data.get("Mileage",""),
        'mileage_warranted': data.get('Mileage Warranted',""),
        'former_keepers': data.get('Former Keepers', ""),
        'vat_status': data.get('VAT Status') or data.get("VAT status"),

        # Bidding & Pricing
        'bidding_history': data.get('Bidding History'),
        'last_bid': to_int1(
            data.get('Last Bid')
            or data.get('LAST BID')
            or data.get('Last bid')
            or data.get('last_bid')
            or data.get('Last Bid ')
        ),
        'bidding_status': data.get('Bidding Status') or data.get("bidding_status") or data.get('Bidding status'),
        'cap_new': safe_int(data.get('Cap New')),
        'cap_retail': safe_int(
            data.get('Cap Retail') or data.get('CAP retail')
        ),
        'cap_clean': safe_int(
            data.get('CAP Clean') or data.get('CAP clean')
        ),
        'cap_average': safe_int(data.get('CAP Average')),
        'cap_below': safe_int(data.get('CAP Below')),

        'glass_new': safe_int(data.get('Glass New')),
        'glass_retail': safe_int(data.get('Glass Retail')),
        'glass_trade': safe_int(data.get('Glass Trade')),
        'autotrader_retail_value': data.get('Autotrader Retail Value', ""),
        'autotrader_trade_value': data.get('Autotrader Trade Value', ""),
        'buy_now_price': data.get('buy_now_price'),

        # Dates
        'start_date': data.get('Start Date'),
        'start_time': data.get('Start Time'),
        'end_date': data.get('end_date'),
        'mot_expiry_date': data.get('MOT Expiry Date'),
        'mot_due': data.get('MOT Due'),
        'inspection_date': data.get('Inspection date'),
        'dor': data.get('D.O.R'),

        # Documents & Reports
        'v5': data.get('V5'),
        'reg': data.get('Reg') or data.get("reg"),
        'service_history': data.get('Service History'),
        'no_of_services': to_int(data.get('No of Service', "")),
        'number_of_services_details': data.get('number_of_services_details'),
        'last_service': data.get('Last Service'),
        'last_service_mileage': to_int(data.get('Last service mileage', "")),
        'dvsa_mileage': data.get('dvsa_mileage'),
        'inspection_report': data.get('Inspection Report'),
        'other_report': data.get('other_report'),
        'service_notes': data.get('Service Notes'),
        'vendor': data.get('vendor') or data.get("Vendor"),

        # Condition & Features
        'grade': to_int(data.get('Grade', "")),
        'tyres_condition': data.get('Tyres Condition'),
        'general_condition': data.get('General Condition'),
        'brakes': data.get('brakes'),
        'hubs': data.get('hubs'),
        'features': data.get('features'),
        'equipment': data.get('Equipment'),
        'additional_information': data.get('Additional information'),
        'imported': to_int(data.get('imported', "")),
        'declarations': data.get('declarations'),
        'damaged_images': data.get('Damaged_images'),
        'damage_details': data.get('Damage_details'),

        # Media
        'images': data.get('Images'),
    }
