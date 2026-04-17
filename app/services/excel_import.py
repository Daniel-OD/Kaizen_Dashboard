import pandas as pd
from io import BytesIO


def parse_excel(data: bytes):
    df = pd.read_excel(BytesIO(data))
    return df.to_dict(orient="records")
