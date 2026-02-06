

## バリデーション
```py
from pydantic import BaseModel

class EmployeementBase(BaseModel):
@field_validator('qualifications')
@classmethod
def validate_qualifications(cls, v: Optional[str]) -> Optional[str]:
    ...

class ...Response(BaseModel):
    Field=Field(default=None,min_length=1,max_length=10)
```



