import pandas as pd
import json
import os
from datetime import datetime

def make_variant(row, idx, product_url):
    name = row.get(f'variant{idx}_name')
    sku = row.get(f'variant{idx}_sku')
    gtin13 = row.get(f'variant{idx}_gtin13')
    image = row.get(f'variant{idx}_image')
    actual_price = row.get(f'variant{idx}_actual_price')
    price = row.get(f'variant{idx}_price')
    # url = row.get(f'variant{idx}_url')  # Now ignored, always using product_url
    shippingCountry = row.get(f'variant{idx}_shippingCountry')
    shippingCurrency = row.get(f'variant{idx}_shippingCurrency')
    shippingValue = row.get(f'variant{idx}_shippingValue')
    returnCountry = row.get(f'variant{idx}_returnCountry')
    returnDays = row.get(f'variant{idx}_returnDays')
    returnMethod = row.get(f'variant{idx}_returnMethod')
    returnFees = row.get(f'variant{idx}_returnFees')
    refundType = row.get(f'variant{idx}_refundType')
    acceptedPaymentMethod = row.get(f'variant{idx}_acceptedPaymentMethod')

    if pd.isna(name) or pd.isna(sku) or pd.isna(gtin13) or pd.isna(image) or pd.isna(price) or pd.isna(product_url):
        return None

    offer = {
        "@type": "Offer",
        "priceCurrency": "USD",
        "price": str(price),
        "priceValidUntil": "2025-12-31",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "url": product_url  # Always use main product URL
    }

    # Show MRP/actual price as priceSpecification
    if not pd.isna(actual_price):
        offer["priceSpecification"] = {
            "@type": "UnitPriceSpecification",
            "priceCurrency": "USD",
            "price": str(actual_price),
            "priceType": "RRP"
        }

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
    schema = {
        "@context": "https://schema.org/",
        "@type": "ProductGroup",
        "productGroupID": f"{row['name']}-1001",
        "name": row['name'],
        "description": row['description'],
        "image": [row['image_url']],
        "brand": {
            "@type": "Brand",
            "name": row['brand']
        },
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
        "hasVariant": []
    }
    # Product URL add karo
    product_url = row['product_url'] if 'product_url' in row and not pd.isna(row['product_url']) else None
    if product_url:
        schema["url"] = product_url
    # Key Benefits add karo agar hai
    if 'key_benefits' in row and not pd.isna(row['key_benefits']):
        schema["additionalProperty"].append({
            "@type": "PropertyValue",
            "name": "Key Benefits",
            "value": row['key_benefits']
        })
    for i in range(1, 10):
        variant = make_variant(row, i, product_url)
        if variant:
            schema["hasVariant"].append(variant)
    return schema

def main():
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
            f.write('\n</script>')
    print(f"Sabhi schema files '{output_dir}' folder me generate ho gayi!")

if __name__ == "__main__":
    main()