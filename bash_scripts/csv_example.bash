curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
           "num_records": 3,
           "fields": [
             {
               "name": "product_name",
               "data_type": "random_element",
               "options": {
                 "choices": ["Laptop", "Mouse", "Keyboard"]
               }
             },
             {
               "name": "price",
               "data_type": "float",
               "options": {
                 "min": 10.0,
                 "max": 500.0
               }
             }
           ],
           "format": "csv"
         }' \
     http://127.0.0.1:5005/generate-data