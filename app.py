from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from user import User
from service import upload_documents, ask_question

app = FastAPI()

origins=["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

@app.get("/", tags=["Health Check"])
async def check_health():
    return JSONResponse(content={"success": "true"})

@app.post("/document-uploader")
async def document_uploader(username: str = Form(...), files: list[UploadFile] = File(...)):
    user = User(username=username)
    response, status_code = await upload_documents(user, files)
    if status_code == 200:
        return {response}
    else:
        raise HTTPException(status_code=status_code, detail=response)

@app.post("/question-answerer")
async def question_answerer(username: str = Form(...), question: str = Form(...), api_key = File(None)):
    user = User(username=username)
    response, status_code = await ask_question(user, question, api_key)
    if status_code == 200:
        return {response}
    else:
        raise HTTPException(status_code=status_code, detail=response)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)