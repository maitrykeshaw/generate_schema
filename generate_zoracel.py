from datetime import datetime
import pandas as pd
import os
import json

# Function to convert date to ISO 8601 format (YYYY-MM-DD)
def convert_to_iso_format(date_str):
    try:
        # Attempt to parse and convert the date from MM/DD/YYYY to YYYY-MM-DD
        return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # If the format is not correct or it's missing, return it as is
        return date_str

def make_variant(row, i, discount):
    name = row.get(f"variant{i}_name")
    sku = row.get(f"variant{i}_sku")
    gtin13 = row.get(f"variant{i}_gtin13")
    image = row.get(f"variant{i}_image")
    actual_price = row.get(f"variant{i}_actual_price")
    price = row.get(f"variant{i}_price")
    url = row.get(f"variant{i}_url")
    shippingCountry = row.get(f"variant{i}_shippingCountry")
    shippingCurrency = row.get(f"variant{i}_shippingCurrency")
    shippingValue = row.get(f"variant{i}_shippingValue")
    returnCountry = row.get(f"variant{i}_returnCountry")
    returnDays = row.get(f"variant{i}_returnDays")
    returnMethod = row.get(f"variant{i}_returnMethod")
    returnFees = row.get(f"variant{i}_returnFees")
    refundType = row.get(f"variant{i}_refundType")
    acceptedPaymentMethod = row.get(f"variant{i}_acceptedPaymentMethod")

    if pd.isna(name) or name == "":
        return None

    # Check for availabilityEnd date in the row (from CSV) and convert to ISO format
    availability_end_date = row.get('offer_end_date', '2025-12-31')  # Default to '2025-12-31' if not present
    availability_end_date = convert_to_iso_format(availability_end_date)  # Convert to ISO format

    offer = {
        "@type": "Offer",
        "priceCurrency": "USD",
        "price": str(price),
        "priceValidUntil": "2025-12-31",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "url": url,
        "priceSpecification": {
            "@type": "UnitPriceSpecification",
            "priceCurrency": "USD",
            "price": str(actual_price),
            "priceType": "RRP"
        }
    }

    # Add availabilityEnd date from CSV or static value in ISO format
    offer["availabilityEnds"] = availability_end_date

    # Add discount if available
    if discount and not pd.isna(discount):
        offer["discount"] = str(discount)

    # Add shipping details
    if shippingCountry and shippingCurrency and shippingValue:
        offer["shippingDetails"] = {
            "@type": "OfferShippingDetails",
            "shippingDestination": {
                "@type": "DefinedRegion",
                "addressCountry": shippingCountry
            },
            "shippingRate": {
                "@type": "MonetaryAmount",
                "value": str(shippingValue),
                "currency": shippingCurrency
            }
        }

    if returnCountry and returnDays and returnMethod and returnFees and refundType:
        offer["hasMerchantReturnPolicy"] = {
            "@type": "MerchantReturnPolicy",
            "applicableCountry": returnCountry,
            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
            "merchantReturnDays": int(returnDays),
            "returnMethod": f"https://schema.org/{returnMethod}",
            "returnFees": f"https://schema.org/{returnFees}",
            "refundType": f"https://schema.org/{refundType}"
        }

    if acceptedPaymentMethod and not pd.isna(acceptedPaymentMethod):
        methods = []
        for method in str(acceptedPaymentMethod).split(','):
            method = method.strip()
            if method.lower() in ["visa", "mastercard", "americanexpress", "discover", "paypal", "creditcard"]:
                methods.append(f"https://schema.org/{method}")
            else:
                methods.append(method)
        offer["acceptedPaymentMethod"] = methods

    return {
        "@type": "Product",
        "name": name,
        "sku": sku,
        "gtin13": gtin13,
        "image": image,
        "offers": offer
    }

def generate_schema(row):
    # Prepare manufacturer info
    manufacturer_info = None
    if not pd.isna(row.get('manufacturer_name')):
        manufacturer_info = {
            "@type": "Organization",
            "name": row.get('manufacturer_name')
        }
        if not pd.isna(row.get('manufacturer_logo')):
            manufacturer_info["logo"] = row.get('manufacturer_logo')

    # Prepare audience
    audience = None
    if not pd.isna(row.get('suitable_for')):
        audience = {
            "@type": "PeopleAudience",
            "suggestedAgeMin": 18,  # Default (customize as needed)
            "suggestedGender": row.get('suitable_for')
        }

    # Prepare brand info with logo
    brand_obj = {
        "@type": "Brand",
        "name": row['brand']
    }
    if not pd.isna(row.get('brand_logo')):
        brand_obj["logo"] = row['brand_logo']

    schema = {
        "@context": "https://schema.org/",
        "@type": "ProductGroup",
        "productGroupID": f"{row['name']}-1001",
        "name": row['name'],
        "description": row['description'],
        "image": row['image_url'],  # Using the existing image URL
        "thumbnailUrl": row['image_url'],  # Adding thumbnailUrl with the same image URL
        "brand": brand_obj,
        "sku": row['sku'],
        "mpn": row['mpn'],
        "gtin13": row['gtin13'],
        "category": row['category'],
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "Ingredients",
                "value": row['ingredients']
            },
            {
                "@type": "PropertyValue",
                "name": "Net Quantity",
                "value": row['net_quantity']
            }
        ],
        "hasVariant": [],
        "url": "https://zoracel-dental-gummy.vercel.app/",  # Added URL property at ProductGroup level
        "isFamilyFriendly": True,  # Added isFamilyFriendly property
        "countryOfOrigin": "US"  # Added countryOfOrigin property (default is "US")
    }

    # Add Certifications if present
    if not pd.isna(row.get('certifications')):
        schema["additionalProperty"].append({
            "@type": "PropertyValue",
            "name": "Certifications",
            "value": row.get('certifications')
        })

    # Add Award if present
    if not pd.isna(row.get('award')):
        schema["award"] = [award.strip() for award in str(row.get('award')).split(',')]

    # Add discount at product group level if present
    if not pd.isna(row.get('discount')):
        schema["discount"] = str(row.get('discount'))

    # Add manufacturer info if present
    if manufacturer_info:
        schema["manufacturer"] = manufacturer_info

    # Add audience if present
    if audience:
        schema["audience"] = audience

    # Add production date if present and convert to ISO format
    if not pd.isna(row.get('production_date')):
        schema["productionDate"] = convert_to_iso_format(str(row.get('production_date')))

    # Add expiration date if present and convert to ISO format
    if not pd.isna(row.get('expiration_date')):
        schema["expirationDate"] = convert_to_iso_format(str(row.get('expiration_date')))

    # Add mainEntityOfPage (URL and language)
    schema["mainEntityOfPage"] = {
        "@type": "WebPage",
        "@id": "https://zoracel-dental-gummy.vercel.app/",
        "inLanguage": "en"
    }

    for i in range(1, 10):
        variant = make_variant(row, i, row.get('discount'))
        if variant:
            schema["hasVariant"].append(variant)
    return schema

if __name__ == "__main__":
    df = pd.read_csv('zoracel_schema_sample.csv')
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_dir = now
    os.makedirs(output_dir, exist_ok=True)
    for idx, row in df.iterrows():
        schema = generate_schema(row)
        fname = f"{row['name'].replace(' ', '_')}.json"
        with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
            f.write('<script type="application/ld+json">\n')
            json.dump(schema, f, ensure_ascii=False, indent=2)
            f.write('\\n</script>')
    print(f"Sabhi schema files '{output_dir}' folder me generate ho gayi!")
