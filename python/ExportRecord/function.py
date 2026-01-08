def Bodydtype(mapping: dict, value: str):

    if not mapping or not value:
        return value  
    key = str(value).lower()
    return mapping.get(key, value) 

def VehicleType(mapping: dict, value: str):

    if not mapping or not value:
        return '' 
    key = str(value).lower()
    return mapping.get(key,"Car")

def FuleType(mapping,value):
    if not mapping or not value:
        return value  
    key = str(value).lower()
    return mapping.get(key, value) 
    
def TransmissionType(mapping,value):
    if not mapping or not value:
        return value  
    key = str(value).lower()
    return mapping.get(key, value)     

def SetMake(mapping,value):
    if not mapping or not value:
        return value  
    key = str(value).lower()
    return mapping.get(key, value)     
    
def DataFields(dataset, data: dict):

    return {
       
        'title': data.get('title'),
        'make_id': SetMake(dataset.get('Make'),data.get("make_id")),
        'model_id': data.get("model_id"),
        'variant_id': data.get("variant_id"),
        'body_id':Bodydtype(dataset.get("Body Type"),data.get("body_id")) ,
        'vehicle_id':VehicleType(dataset.get("Vehicle"),data.get("body_id")) ,
        'year': data.get('year'),
        'center_id': data.get('center_id'),
        'color': data.get('color'),
        'vin': data.get('vin'),
        'lot': data.get('lot'),

        # Vehicle Specs
        'doors': data.get('doors'),
        'seats':data.get('seats'),
        'fuel_type': FuleType(dataset.get("Fuel Type"),data.get('fuel_type')),
        'fuel_details': data.get('fuel_type'),
        'transmission': TransmissionType(dataset.get("Transmission Type"),data.get('transmission')),
        'transmission_details': data.get('transmission'),
        'cc': data.get('cc'),
        'keys': data.get('keys'),
        'engine_runs': data.get('engine_runs'),
        'mileage': data.get("mileage",0),
        'mileage_warranted': data.get('mileage_warranted'),
        'former_keepers': data.get('former_keepers'),
        'vat_status': data.get('vat_status'),

        # Dates
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'mot_expiry_date': data.get('mot_expiry_date'),
        'mot_due': data.get('mot_due'),
        'inspection_date': data.get('inspection_date'),
        'dor': data.get('dor'),
        
        
        # Documents & Reports
        'v5': data.get('v5'),
        'reg': data.get('reg') or data.get("reg"),
        'service_history': data.get('service_history'),
        'no_of_services': data.get('no_of_services'),
        'number_of_services_details': data.get('number_of_services_details'),
        'last_service': data.get('last_service'),
        'last_service_mileage': data.get('last_service_mileage'),
        'dvsa_mileage': data.get('dvsa_mileage'),
        'inspection_report': data.get('inspection_report'),
        'other_report': data.get('other_report'),
        'service_notes': data.get('service_notes'),
        'vendor': data.get('vendor'),
        
        #  Condition & Features
        'grade': data.get('grade', ""),
        'tyres_condition': data.get('tyres_condition'),
        'general_condition': data.get('general_condition'),
        'brakes': data.get('brakes'),
        'hubs': data.get('hubs'),
        'features': data.get('features'),
        'equipment': data.get('equipment'),
        'additional_information': data.get('additional_information'),
        'imported': data.get('imported'),
        'declarations': data.get('declarations'),
        'damaged_images': data.get('damaged_images'),
        'damage_details': data.get('damage_details'),

        # Media
        'images': data.get('images'),
    }
