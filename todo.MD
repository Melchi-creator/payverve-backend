# Task list

## Transfer:

- Create:
  > within payverve
  ``` json
  {
      "option": "PayVerve",
      "account_number": "string",
      "amount": "string",
      "narration": "string",
      "wallet": 0
  }
  ```
  > Other Banks
  ```json
  {
      "option": "Other Banks",
      "account_number": "string",
      "amount": "string",
      "narration": "string",
      "wallet": 0,
      "additional_info": {
        "bank_name": "string",
        "country": "AF",
        "bank_swift": "string",
        "type": "Local",
        "exchange_rate": "string"
    }      
  }
  ```
  