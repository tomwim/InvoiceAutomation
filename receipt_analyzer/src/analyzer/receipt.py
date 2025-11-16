from typing import List, Any
from azure.ai.documentintelligence.models import AnalyzedDocument
from dataclasses import dataclass, field

@dataclass
class AnalyzedValue():
    value : Any = None
    confidence : float = None

    def __init__(self, value, confidence : float):
        self.value = value
        self.confidence = confidence

@dataclass
class TotalAmount(AnalyzedValue):
    currency : str = None

    def __init__(self, value : float, currency : str, confidence : float):
        super().__init__(value=value, confidence=confidence)
        self.currency = currency

@dataclass
class TaxDetails():
    amount : TotalAmount = None
    net_amount : TotalAmount = None
    rate : AnalyzedValue = None
    description : AnalyzedValue = None
    
    def __init__(self, amount : TotalAmount, net_amount : TotalAmount, rate : AnalyzedValue, description : AnalyzedValue):
        self.amount = amount
        self.net_amount = net_amount
        self.rate = rate
        self.description = description

@dataclass
class Item():
    confidence : float = None
    price : TotalAmount = None
    total_price : TotalAmount = None
    confidence : float = None
    quantity : AnalyzedValue = None
    description : AnalyzedValue = None

    def __init__(self, confidence : float, price : TotalAmount, total_price : TotalAmount, quantity : AnalyzedValue, description : AnalyzedValue):
        self.confidence = confidence
        self.price = price
        self.total_price = total_price
        self.quantity = quantity
        self.description = description

@dataclass
class AnalyzedReceipt():
    id = id

    country : AnalyzedValue = None
    merchant : AnalyzedValue = None
    merchant_address : AnalyzedValue = None
    time : AnalyzedValue = None
    date : AnalyzedValue = None
    total_price : TotalAmount = None
    total_tax : TotalAmount = None
    tax_details : TaxDetails = None
    # items : List[Item] = []
    items : List['Item'] = field(default_factory=list)

    def __init__(self, id : str):
        self.id = id
        self.items = []

    @classmethod
    def from_analyzed_document(cls, id : str, document : AnalyzedDocument):
        receipt = AnalyzedReceipt(id=id)

        receipt.country = AnalyzedValue(
            value=document.fields['CountryRegion'].value_country_region,
            confidence=document.fields['CountryRegion'].confidence
        )

        receipt.merchant = AnalyzedValue(
            value=document.fields['MerchantName'].value_string,
            confidence=document.fields['MerchantName'].confidence
        )

        receipt.merchant_address = AnalyzedValue(
            value=document.fields['MerchantAddress'].content,
            confidence=document.fields['MerchantAddress'].confidence
        )

        receipt.time = AnalyzedValue(
            value=document.fields['TransactionTime'].value_time or "Unknown",
            confidence=document.fields['TransactionTime'].confidence
        )

        receipt.date = AnalyzedValue(
            value=document.fields['TransactionDate'].content,
            confidence=document.fields['TransactionDate'].confidence
        )

        receipt.total_price = TotalAmount(
            value=document.fields['Total'].value_currency.amount,
            currency=document.fields['Total'].value_currency.currency_code,
            confidence=document.fields['Total'].confidence
        )

        receipt.total_tax = TotalAmount(
            value=document.fields['TotalTax'].value_currency.amount,
            currency=document.fields['TotalTax'].value_currency.currency_code,
            confidence=document.fields['TotalTax'].confidence
        )

        tax_details_obj = document.fields['TaxDetails'].value_array[0].value_object
        receipt.tax_details = TaxDetails(
            amount=TotalAmount(
                value=tax_details_obj['Amount'].value_currency.amount,
                currency=tax_details_obj['Amount'].value_currency.currency_code,
                confidence=tax_details_obj['Amount'].confidence
            ),
            net_amount=TotalAmount(
                value=tax_details_obj['NetAmount'].value_currency.amount,
                currency=tax_details_obj['NetAmount'].value_currency.currency_code,
                confidence=tax_details_obj['NetAmount'].confidence
            ),
            rate=AnalyzedValue(
                value=tax_details_obj['Rate'].value_number,
                confidence=tax_details_obj['Rate'].confidence
            ),
            description=AnalyzedValue(
                value=tax_details_obj['Description'].value_string,
                confidence=tax_details_obj['Description'].confidence
            )
        )
        
        for item in document.fields['Items'].value_array:
            item_object = item.value_object
            receipt.items.append(
                Item(
                    confidence=item.confidence,
                    description=AnalyzedValue(
                        value=item_object['Description'].value_string,
                        confidence=item_object['Description'].confidence
                    ),
                    quantity=AnalyzedValue(
                        value=item_object['Quantity'].value_number,
                        confidence=item_object['Quantity'].confidence
                    ),
                    price=TotalAmount(
                        value=item_object['Price'].value_currency.amount,
                        currency=item_object['Price'].value_currency.currency_code,
                        confidence=item_object['Price'].confidence
                    ),
                    total_price=TotalAmount(
                        value=item_object['TotalPrice'].value_currency.amount,
                        currency=item_object['TotalPrice'].value_currency.currency_code,
                        confidence=item_object['TotalPrice'].confidence
                    )
                )
            )

        return receipt
        
def remove_confidence(input) -> dict:
    """
    Recursively process nested dict/list structures:
    - Remove 'confidence' fields
    - If a dict only has 'value', extract just the value
    - Otherwise keep the dict with value and other fields (e.g., currency)
    """
    if isinstance(input, dict):
        # Remove confidence and recursively process
        cleaned = {k: remove_confidence(v) for k, v in input.items() if k != 'confidence'}
        
        # If only 'value' remains, extract it
        if set(cleaned.keys()) == {'value'}:
            return cleaned['value']
        
        return cleaned
    elif isinstance(input, list):
        return [remove_confidence(item) for item in input]
    return input

    