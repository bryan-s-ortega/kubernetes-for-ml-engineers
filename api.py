from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional
from faker import Faker
import csv
from io import StringIO
from datetime import datetime, date
import uuid
import random

app = FastAPI(title="Random Dataset Generator API")
fake = Faker()

class DataField(BaseModel):
    name: str = Field(..., description="Name of the field in the dataset")
    data_type: str = Field(
        ...,
        description="Type of data to generate",
        examples=[
            "name", "email", "address", "integer", "float", "date", "boolean",
            "string", "uuid", "ipv4", "ipv6", "phone_number",
            "random_digit", "random_digit_not_null", "random_letter",
            "random_element", "random_elements", "randomize_nb_elements"
        ],
    )
    options: Optional[Dict[str, Union[int, float, str, List[str]]]] = Field(
        None, description="Optional parameters for the data type (e.g., min, max, choices)"
    )

class DatasetRequest(BaseModel):
    num_records: int = Field(10, ge=1, description="Number of records to generate")
    fields: List[DataField] = Field(..., min_items=1, description="List of fields to include in the dataset")
    format: str = Field("json", description="Output format", examples=["json", "csv"])

def generate_random_data(data_type: str, options: Optional[Dict[str, Union[int, float, str, List[str]]]] = None):
    if data_type == "name":
        return fake.name()
    elif data_type == "email":
        return fake.email()
    elif data_type == "address":
        return fake.address()
    elif data_type == "integer":
        min_val = options.get("min", 0) if options else 0
        max_val = options.get("max", 100) if options else 100
        return fake.random_int(min=min_val, max=max_val)
    elif data_type == "float":
        min_val = options.get("min", 0.0) if options else 0.0
        max_val = options.get("max", 1.0) if options else 1.0
        return fake.pyfloat(min_value=min_val, max_value=max_val)
    elif data_type == "date":
        start_date = options.get("start_date") if options else "-30y"
        end_date = options.get("end_date") if options else "now"
        try:
            return fake.date_between(start_date=start_date, end_date=end_date).isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for start_date or end_date (e.g., YYYY-MM-DD or relative like -10y)")
    elif data_type == "boolean":
        return fake.boolean()
    elif data_type == "string":
        length = options.get("length", 10) if options else 10
        return fake.pystr(min_chars=length, max_chars=length)
    elif data_type == "uuid":
        return str(uuid.uuid4())
    elif data_type == "ipv4":
        return fake.ipv4()
    elif data_type == "ipv6":
        return fake.ipv6()
    elif data_type == "phone_number":
        return fake.phone_number()
    elif data_type == "random_digit":
        return fake.random_digit()
    elif data_type == "random_digit_not_null":
        return fake.random_digit_not_null()
    elif data_type == "random_letter":
        return fake.random_letter()
    elif data_type == "random_element":
        choices = options.get("choices") if options and isinstance(options.get("choices"), list) else ["A", "B", "C"]
        return fake.random_element(elements=choices)
    elif data_type == "random_elements":
        elements = options.get("elements") if options and isinstance(options.get("elements"), list) else ["item1", "item2", "item3"]
        num = options.get("num", 2) if options else 2
        return fake.random_elements(elements=elements, num=num)
    elif data_type == "randomize_nb_elements":
        elements = options.get("elements") if options and isinstance(options.get("elements"), list) else ["val1", "val2"]
        max_nb = options.get("max_nb", 5) if options else 5
        return fake.randomize_nb_elements(elements=elements, max=max_nb)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported data type: {data_type}")

@app.post("/generate-data")
async def generate_dataset(request_data: DatasetRequest):
    """
    Generates a random dataset based on the provided specifications.
    """
    datasets = []
    for _ in range(request_data.num_records):
        record = {}
        for field in request_data.fields:
            try:
                record[field.name] = generate_random_data(field.data_type, field.options)
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generating data for field '{field.name}': {str(e)}")

        datasets.append(record)

    if request_data.format == "json":
        return datasets
    elif request_data.format == "csv":
        if not datasets:
            return StreamingResponse(iter(['']), media_type="text/csv")
        output = StringIO()
        field_names = [field.name for field in request_data.fields]
        writer = csv.DictWriter(output, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(datasets)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported output format: {request_data.format}")

@app.get("/supported-data-types")
async def get_supported_data_types():
    """
    Lists the supported data types for generating random data.
    """
    return {
        "supported_types": [
            "name", "email", "address", "integer", "float", "date", "boolean",
            "string", "uuid", "ipv4", "ipv6", "phone_number",
            "random_digit", "random_digit_not_null", "random_letter",
            "random_element", "random_elements", "randomize_nb_elements"
        ],
        "integer_options": ["min", "max"],
        "float_options": ["min", "max"],
        "date_options": ["start_date (YYYY-MM-DD or relative like -10y)", "end_date (YYYY-MM-DD or relative like now)"],
        "string_options": ["length (integer)"],
        "random_element_options": ["choices (list of strings)"],
        "random_elements_options": ["elements (list of strings)", "num (integer, number of elements to pick)"],
        "randomize_nb_elements_options": ["elements (list of strings)", "max_nb (integer, maximum number of elements)"]
    }