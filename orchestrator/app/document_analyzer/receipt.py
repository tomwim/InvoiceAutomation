from typing import List
from azure.ai.documentintelligence.models import AnalyzedDocument

class AnalyzedValue():
    def __init__(self, value, confidence : float):
        self.value = value
        self.confidence = confidence

class TotalAmount(AnalyzedValue):
    def __init__(self, value : float, currency : str, confidence : float):
        super().__init__(value=value, confidence=confidence)
        self.currency = currency

class TaxDetails():
    def __init__(self, amount : TotalAmount, net_amount : TotalAmount, rate : AnalyzedValue, description : AnalyzedValue):
        self.amount = amount
        self.net_amount = net_amount
        self.rate = rate
        self.desctription = description

class Item():
    def __init__(self, confidence : float, price : TotalAmount, total_price : TotalAmount, quantity : AnalyzedValue, description : AnalyzedValue):
        self.confidence = confidence
        self.price = price
        self.total_price = total_price
        self.quantity = quantity
        self.description = description

class AnalyzedReceipt():
    def __init__(self, id : str):
        self.id = id

        self.country : AnalyzedValue = None
        self.merchant : AnalyzedValue = None
        self.merchant_address : AnalyzedValue = None
        self.time : AnalyzedValue = None
        self.date : AnalyzedValue = None
        self.total_price : TotalAmount = None
        self.total_tax : TotalAmount = None
        self.tax_details : TaxDetails = None
        self.items : List[Item] = []

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
            value=document.fields['TransactionTime'].value_time,
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
        
    

    