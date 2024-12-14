from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

from my_parser import CppInterpreter

app = FastAPI()

class TextRequest(BaseModel):
    code: str
    return_type: str

class TextResponse(BaseModel):
    received_json: dict

@app.post("/post_code", response_model=TextResponse)
async def post_code(data: TextRequest):
    try:
        code = data.code
        type = data.return_type  

        parser = CppInterpreter(code=code, return_type=type)
        output_json = json.loads(parser.run())
        
        if output_json.get("status") == "error":
            raise HTTPException(status_code=400, detail=output_json["message"])
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON from parser: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    return TextResponse(received_json=output_json)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
